<template>
  <div class="sf">
    <!-- 板块头部 -->
    <div class="sf-header" :style="headerStyle">
      <div class="sf-header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="24" height="24">
          <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
        </svg>
      </div>
      <div class="sf-header-text">
        <h1 class="sf-title">{{ section.name || '资源分享' }}</h1>
        <p class="sf-desc">{{ section.description || '分享学习资源、资料和工具' }}</p>
      </div>
      <router-link
        v-if="auth.canPost"
        to="/forum/post/new?section_id=2"
        class="sf-new"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        发布资源
      </router-link>
    </div>

    <!-- 帖子列表 -->
    <div v-if="loading" class="sf-loading"><span class="spinner"></span></div>

    <div v-else-if="posts.length === 0" class="sf-empty">
      <div class="sf-empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      </div>
      <p>暂无资源分享</p>
      <p class="sf-empty-hint">成为第一个分享资源的人吧</p>
    </div>

    <div v-else class="sf-list">
      <div
        v-for="(post, i) in posts"
        :key="post.id"
        class="sf-item"
        :class="{ pinned: post.is_pinned }"
        :style="{ animationDelay: `${i * 40}ms` }"
        @click="goPost(post)"
      >
        <div class="sf-item-main">
          <div class="sf-item-title-row">
            <span v-if="post.is_pinned" class="sf-pin" :title="post.pin_type === 'global' ? '全局置顶' : '板块置顶'">置顶</span>
            <h3 class="sf-item-title">{{ post.title }}</h3>
          </div>
          <p v-if="post.summary || post.content_preview" class="sf-item-summary">{{ post.summary || post.content_preview }}</p>
          <div class="sf-item-meta">
            <span class="sf-author">
              <span class="sf-author-dot"></span>
              {{ post.author?.nickname || '游客' }}
            </span>
            <span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              {{ post.views_count }}
            </span>
            <span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/></svg>
              {{ post.replies_count }}
            </span>
            <span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
              {{ post.likes_count }}
            </span>
            <span class="sf-time">{{ formatDate(post.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="hasMore && !loading" class="sf-load-more">
      <button class="btn btn-text" @click="loadMore">加载更多</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSectionStore } from '@/stores/section'
import { getPosts } from '@/api/post'
import { formatDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const sectionStore = useSectionStore()

// 板块标识由路由 meta 提供（tech / share）
const sectionKey = computed(() => route.meta.forumSection || 'share')
const section = computed(() => sectionStore.getSection(sectionKey.value) || {})

const headerStyle = computed(() => {
  const color = section.value.color || '#7C4DFF'
  return { '--sf-color': color }
})

const posts = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(false)

async function fetchPosts(p = 1) {
  loading.value = true
  try {
    const sectionId = sectionStore.getSectionId(sectionKey.value) || (sectionKey.value === 'tech' ? 1 : 2)
    const res = await getPosts({
      section_id: sectionId,
      page: p,
      page_size: 20,
      ordering: '-is_pinned,-created_at',
    })
    const data = res?.data || res || {}
    const results = data.results || []
    posts.value = p === 1 ? results : [...posts.value, ...results]
    hasMore.value = !!data.next
    page.value = p
  } catch (e) {
    console.warn('Failed to fetch posts:', e)
    if (p === 1) posts.value = []
  } finally {
    loading.value = false
  }
}

function loadMore() { fetchPosts(page.value + 1) }

function goPost(post) {
  router.push({ name: 'PostDetail', params: { id: post.id } })
}

onMounted(async () => {
  if (!sectionStore.sections.some(s => s.key === sectionKey.value && s.id)) {
    await sectionStore.fetchSections()
  }
  fetchPosts(1)
})
</script>

<style scoped>
.sf-header {
  display: flex; align-items: center; gap: var(--s-base);
  padding: var(--s-lg); margin-bottom: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
}
.sf-header-icon {
  width: 48px; height: 48px; border-radius: var(--r-md); flex-shrink: 0;
  background: color-mix(in srgb, var(--sf-color, #7C4DFF) 10%, transparent);
  color: var(--sf-color, #7C4DFF);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid color-mix(in srgb, var(--sf-color, #7C4DFF) 20%, transparent);
}
.sf-header-text { flex: 1; min-width: 0; }
.sf-title { font-size: 22px; font-weight: 700; margin-bottom: 2px; }
.sf-desc { font-size: 14px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sf-new {
  display: inline-flex; align-items: center; gap: var(--s-xs);
  background: var(--sf-color, #7C4DFF); color: #fff;
  padding: 8px 16px; border-radius: 999px; font-size: 14px; font-weight: 500;
  transition: all var(--t-fast); flex-shrink: 0; text-decoration: none;
}
.sf-new:hover { filter: brightness(1.1); }

.sf-list { display: flex; flex-direction: column; }
.sf-item {
  display: flex; gap: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  padding: var(--s-base) var(--s-lg); margin-bottom: var(--s-sm);
  cursor: pointer; transition: all var(--t-fast); animation: sfFadeUp 350ms ease-out both;
}
.sf-item:hover { border-color: var(--sf-color, #7C4DFF); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.sf-item.pinned { border-left: 3px solid var(--sf-color, #7C4DFF); }
.sf-item-main { flex: 1; min-width: 0; }
.sf-item-title-row { display: flex; align-items: center; gap: var(--s-xs); margin-bottom: 4px; }
.sf-pin {
  flex-shrink: 0; font-size: 11px; padding: 1px 6px; border-radius: 4px;
  background: color-mix(in srgb, var(--sf-color, #7C4DFF) 12%, transparent);
  color: var(--sf-color, #7C4DFF); font-weight: 600;
}
.sf-item-title {
  font-size: 15px; font-weight: 500; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; transition: color var(--t-fast);
}
.sf-item:hover .sf-item-title { color: var(--sf-color, #7C4DFF); }
.sf-item-summary {
  font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.sf-item-meta { display: flex; align-items: center; gap: var(--s-base); font-size: 12px; color: var(--text-disabled); flex-wrap: wrap; }
.sf-item-meta span { display: flex; align-items: center; gap: 3px; }
.sf-author { color: var(--text-secondary); }
.sf-author-dot { width: 3px; height: 3px; border-radius: 50%; background: var(--text-disabled); }
.sf-time { margin-left: auto; }

.sf-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.sf-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-secondary); }
.sf-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
.sf-empty-hint { font-size: 13px; color: var(--text-disabled); margin-top: var(--s-xs); }
.sf-load-more { text-align: center; padding: var(--s-base); }

@keyframes sfFadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
