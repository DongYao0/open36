<template>
  <!-- Header -->
  <div class="fv-header">
    <div class="fv-header-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="24" height="24">
        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
      </svg>
    </div>
    <div class="fv-header-text">
      <h1 class="fv-header-title">我的收藏</h1>
      <p class="fv-header-desc">收藏的帖子</p>
    </div>
  </div>

  <!-- Tabs -->
  <div class="fv-tabs">
    <button class="fv-tab" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">
      全部收藏
      <span v-if="posts.length" class="fv-tab-count">{{ posts.length }}</span>
    </button>
    <button class="fv-tab" :class="{ active: activeTab === 'recent' }" @click="activeTab = 'recent'">
      最近收藏
    </button>
  </div>

  <!-- List -->
  <div class="fv-list">
    <div
      v-for="(item, i) in filteredPosts"
      :key="item.id"
      class="fv-item"
      :style="{ animationDelay: `${i * 50}ms` }"
    >
      <div class="fv-item-icon" @click="goToPost(item.post_id)">
        <svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" width="18" height="18">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <div class="fv-item-body" @click="goToPost(item.post_id)">
        <h4 class="fv-item-title">{{ item.title || '（帖子已删除）' }}</h4>
        <div class="fv-item-meta">
          <span v-if="item.views_count">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            {{ item.views_count }} 浏览
          </span>
          <span>{{ formatDate(item.created_at) }} 收藏</span>
        </div>
      </div>
      <button class="fv-item-remove" @click="removeFav(item)" title="取消收藏">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  </div>

  <div v-if="filteredPosts.length === 0 && !loading" class="fv-empty">
    <div class="fv-empty-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
      </svg>
    </div>
    <p>暂无收藏帖子</p>
    <p class="fv-empty-hint">浏览论坛时点击收藏按钮即可添加</p>
  </div>
  <div v-if="loading" class="fv-loading"><span class="spinner"></span></div>
  <div v-if="hasMore && !loading" class="fv-load-more">
    <button class="btn btn-text" @click="loadMore">加载更多</button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/format'
import { getMyFavorites, toggleFavorite } from '@/api/interaction'

const router = useRouter()
const ui = useUIStore()
const auth = useAuthStore()
const activeTab = ref('all')
const posts = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(false)

const filteredPosts = computed(() => {
  if (activeTab.value === 'recent') {
    const weekAgo = Date.now() - 7 * 86400000
    return posts.value.filter(p => new Date(p.created_at).getTime() > weekAgo)
  }
  return posts.value
})

async function fetchFavorites(p = 1) {
  if (!auth.canPost) return
  loading.value = true
  try {
    const res = await getMyFavorites({ page: p, page_size: 20 })
    const data = res?.data || res || {}
    const results = data.results || []
    posts.value = p === 1 ? results : [...posts.value, ...results]
    hasMore.value = !!data.next
    page.value = p
  } catch (e) {
    console.warn('Failed to fetch favorites:', e)
    if (p === 1) posts.value = []
  } finally { loading.value = false }
}

function loadMore() { fetchFavorites(page.value + 1) }

async function removeFav(item) {
  try {
    await toggleFavorite(item.post_id)
    posts.value = posts.value.filter(p => p.id !== item.id)
    ui.showToast('已取消收藏', 'info')
  } catch (e) { ui.showToast('操作失败', 'error') }
}

function goToPost(postId) { router.push({ name: 'PostDetail', params: { id: postId } }) }

onMounted(() => { fetchFavorites(1) })
</script>

<style scoped>
.fv-header {
  display: flex; align-items: center; gap: var(--s-base);
  padding: var(--s-lg); margin-bottom: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
}
.fv-header-icon {
  width: 48px; height: 48px; border-radius: var(--r-md); flex-shrink: 0;
  background: rgba(25,118,210,0.08); color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(25,118,210,0.15);
}
.fv-header-title { font-size: 22px; font-weight: 700; margin-bottom: 2px; }
.fv-header-desc { font-size: 14px; color: var(--text-secondary); }

.fv-tabs { display: flex; gap: 0; margin-bottom: var(--s-lg); border-bottom: 1px solid var(--divider); }
.fv-tab {
  display: flex; align-items: center; gap: var(--s-xs);
  padding: var(--s-sm) var(--s-lg); font-size: 14px; font-weight: 500;
  color: var(--text-secondary); border-bottom: 2px solid transparent;
  transition: all var(--t-fast);
}
.fv-tab:hover { color: var(--text-primary); }
.fv-tab.active { color: var(--primary); border-bottom-color: var(--primary); }
.fv-tab-count {
  font-size: 11px; background: var(--bg-dark); color: var(--text-secondary);
  padding: 1px 6px; border-radius: 999px;
}
.fv-tab.active .fv-tab-count { background: var(--primary-bg); color: var(--primary); }

.fv-list { display: flex; flex-direction: column; }
.fv-item {
  display: flex; align-items: center; gap: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  padding: var(--s-base) var(--s-lg); margin-bottom: var(--s-sm);
  transition: all var(--t-fast); animation: fvFadeUp 350ms ease-out both;
}
.fv-item:hover { border-color: var(--primary); box-shadow: 0 2px 8px rgba(25,118,210,0.06); }
.fv-item-icon {
  width: 40px; height: 40px; border-radius: var(--r-sm); flex-shrink: 0;
  background: rgba(25,118,210,0.06); color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all var(--t-fast);
}
.fv-item-icon:hover { background: rgba(25,118,210,0.12); }
.fv-item-body { flex: 1; min-width: 0; cursor: pointer; }
.fv-item-title { font-size: 15px; font-weight: 500; margin-bottom: 2px; transition: color var(--t-fast); }
.fv-item-body:hover .fv-item-title { color: var(--primary); }
.fv-item-meta { display: flex; align-items: center; gap: var(--s-base); font-size: 12px; color: var(--text-disabled); }
.fv-item-meta span { display: flex; align-items: center; gap: 3px; }
.fv-item-remove {
  width: 32px; height: 32px; border-radius: var(--r-sm); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-disabled); transition: all var(--t-fast);
}
.fv-item-remove:hover { background: rgba(244,67,54,0.08); color: var(--error); }

.fv-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.fv-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-secondary); }
.fv-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
.fv-empty-hint { font-size: 13px; color: var(--text-disabled); margin-top: var(--s-xs); }
.fv-load-more { text-align: center; padding: var(--s-base); }

@keyframes fvFadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
