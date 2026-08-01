<template>
  <div class="tf">
    <!-- 板块头部 -->
    <div class="tf-header" :style="headerStyle">
      <div class="tf-header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="24" height="24">
          <path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/>
        </svg>
      </div>
      <div class="tf-header-text">
        <h1 class="tf-title">{{ section.name || '技术交流' }}</h1>
        <p class="tf-desc">{{ section.description || '分享编程技术和开发经验，讨论最新技术趋势' }}</p>
      </div>
      <router-link
        v-if="auth.canPost"
        to="/forum/post/new?section_id=1"
        class="tf-new"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        发布新帖
      </router-link>
    </div>

    <!-- 帖子列表 -->
    <div v-if="loading" class="tf-loading"><span class="spinner"></span></div>

    <div v-else-if="posts.length === 0" class="tf-empty">
      <div class="tf-empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      </div>
      <p>暂无帖子</p>
      <p class="tf-empty-hint">成为第一个发帖的人吧</p>
    </div>

    <div v-else class="tf-list">
      <div
        v-for="(post, i) in posts"
        :key="post.id"
        class="tf-item"
        :class="{ pinned: post.is_pinned }"
        :style="{ animationDelay: `${i * 40}ms` }"
        @click="goPost(post)"
      >
        <div class="tf-item-main">
          <div class="tf-item-title-row">
            <span v-if="post.is_pinned" class="tf-pin" :title="post.pin_type === 'global' ? '全局置顶' : '板块置顶'">置顶</span>
            <h3 class="tf-item-title">{{ post.title }}</h3>
          </div>
          <p v-if="post.summary || post.content_preview" class="tf-item-summary">{{ post.summary || post.content_preview }}</p>
          <div class="tf-item-meta">
            <span class="tf-author">
              <img v-if="post.author?.avatar_url" :src="post.author.avatar_url" class="avatar avatar-xs" alt="" />
              <span class="tf-author-dot"></span>
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
            <span class="tf-time">{{ formatDate(post.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="hasMore && !loading" class="tf-load-more">
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
const sectionKey = computed(() => route.meta.forumSection || 'tech')
const section = computed(() => sectionStore.getSection(sectionKey.value) || {})

const headerStyle = computed(() => {
  const color = section.value.color || '#1976D2'
  return { '--tf-color': color }
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
.tf-header {
  display: flex; align-items: center; gap: var(--s-base);
  padding: var(--s-lg); margin-bottom: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
}
.tf-header-icon {
  width: 48px; height: 48px; border-radius: var(--r-md); flex-shrink: 0;
  background: color-mix(in srgb, var(--tf-color, #1976D2) 10%, transparent);
  color: var(--tf-color, #1976D2);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid color-mix(in srgb, var(--tf-color, #1976D2) 20%, transparent);
}
.tf-header-text { flex: 1; min-width: 0; }
.tf-title { font-size: 22px; font-weight: 700; margin-bottom: 2px; }
.tf-desc { font-size: 14px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tf-new {
  display: inline-flex; align-items: center; gap: var(--s-xs);
  background: var(--tf-color, #1976D2); color: #fff;
  padding: 8px 16px; border-radius: 999px; font-size: 14px; font-weight: 500;
  transition: all var(--t-fast); flex-shrink: 0; text-decoration: none;
}
.tf-new:hover { filter: brightness(1.1); }

.tf-list { display: flex; flex-direction: column; }
.tf-item {
  display: flex; gap: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  padding: var(--s-base) var(--s-lg); margin-bottom: var(--s-sm);
  cursor: pointer; transition: all var(--t-fast); animation: tfFadeUp 350ms ease-out both;
}
.tf-item:hover { border-color: var(--tf-color, #1976D2); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.tf-item.pinned { border-left: 3px solid var(--tf-color, #1976D2); }
.tf-item-main { flex: 1; min-width: 0; }
.tf-item-title-row { display: flex; align-items: center; gap: var(--s-xs); margin-bottom: 4px; }
.tf-pin {
  flex-shrink: 0; font-size: 11px; padding: 1px 6px; border-radius: 4px;
  background: color-mix(in srgb, var(--tf-color, #1976D2) 12%, transparent);
  color: var(--tf-color, #1976D2); font-weight: 600;
}
.tf-item-title {
  font-size: 15px; font-weight: 500; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; transition: color var(--t-fast);
}
.tf-item:hover .tf-item-title { color: var(--tf-color, #1976D2); }
.tf-item-summary {
  font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.tf-item-meta { display: flex; align-items: center; gap: var(--s-base); font-size: 12px; color: var(--text-disabled); flex-wrap: wrap; }
.tf-item-meta span { display: flex; align-items: center; gap: 3px; }
.tf-author { color: var(--text-secondary); }
.tf-author-dot { width: 3px; height: 3px; border-radius: 50%; background: var(--text-disabled); }
.tf-time { margin-left: auto; }

.tf-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.tf-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-secondary); }
.tf-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
.tf-empty-hint { font-size: 13px; color: var(--text-disabled); margin-top: var(--s-xs); }
.tf-load-more { text-align: center; padding: var(--s-base); }

@keyframes tfFadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
