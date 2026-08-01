<template>
  <div class="res-page">
    <!-- 搜索栏 -->
    <div class="res-search-bar">
      <div class="res-search-inner">
        <svg class="res-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          class="res-search-input"
          placeholder="搜索资源..."
          @input="onSearch"
        />
        <button v-if="searchQuery" class="res-search-clear" @click="clearSearch">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 资源卡片网格 -->
    <div class="res-grid">
      <div
        v-for="(post, i) in filteredPosts"
        :key="post.id"
        class="res-card"
        :style="{ animationDelay: `${i * 60}ms` }"
        @click="goPost(post)"
      >
        <!-- 卡片头部：头像 + 作者 + 时间 -->
        <div class="res-card-header">
          <img
            :src="`https://ui-avatars.com/api/?name=${encodeURIComponent(post.author)}&background=F59E0B&color=fff&size=40`"
            class="res-card-avatar"
          />
          <div class="res-card-author-info">
            <span class="res-card-author">{{ post.author }}</span>
            <span class="res-card-time">{{ formatDate(post.createdAt) }}</span>
          </div>
          <div v-if="post.pinned" class="res-card-pin-badge">精选</div>
        </div>

        <!-- 卡片主体：标题 + 简介 -->
        <div class="res-card-body">
          <h3 class="res-card-title">{{ post.title }}</h3>
          <p class="res-card-desc">{{ post.summary || post.content }}</p>
        </div>

        <!-- 卡片底部：统计 -->
        <div class="res-card-footer">
          <div class="res-card-stats">
            <span class="res-card-stat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
              {{ post.views }}
            </span>
            <span class="res-card-stat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M12 19V5M5 12l7-7 7 7"/>
              </svg>
              {{ post.votes }}
            </span>
            <span class="res-card-stat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              {{ post.replyCount }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 状态 -->
    <div v-if="loading" class="res-loading"><span class="spinner"></span></div>
    <div v-if="!loading && filteredPosts.length === 0" class="res-empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
      </svg>
      <p>{{ fetchError || '暂无资源，成为第一个分享者吧' }}</p>
    </div>
    <div ref="sentinel" class="scroll-sentinel"></div>

    <!-- 发布按钮 -->
    <router-link v-if="auth.canPost" to="/resources/new" class="res-fab" title="分享资源">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="24" height="24">
        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
    </router-link>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'
import { getPosts } from '@/api/post'
import { formatDate } from '@/utils/format'

const router = useRouter()
const sectionStore = useSectionStore()
const auth = useAuthStore()
const fetchError = ref('')
const loading = ref(false)
const posts = ref([])
const currentPage = ref(1)
const totalCount = ref(0)
const sentinel = ref(null)
const searchQuery = ref('')
let observer = null
const PAGE_SIZE = 12

const hasMore = computed(() => posts.value.length < totalCount.value)

const filteredPosts = computed(() => {
  if (!searchQuery.value.trim()) return posts.value
  const q = searchQuery.value.trim().toLowerCase()
  return posts.value.filter(p =>
    p.title.toLowerCase().includes(q) ||
    (p.summary || p.content).toLowerCase().includes(q) ||
    p.author.toLowerCase().includes(q)
  )
})

function onSearch() { /* 实时过滤，computed 自动处理 */ }

function clearSearch() { searchQuery.value = '' }

async function fetchResources(page = 1) {
  loading.value = true
  try {
    const sectionId = sectionStore.getSectionId('share')
    if (!sectionId) { loading.value = false; return }
    const res = await getPosts({ section_id: sectionId, page, page_size: PAGE_SIZE })
    const data = res?.data || {}
    totalCount.value = data.count || 0
    const results = (data.results || []).map(p => ({
      id: p.id,
      title: p.title,
      summary: p.summary || '',
      content: p.content_preview || p.content || '',
      author: p.author?.nickname || `用户${p.author?.user_id || ''}`,
      views: p.views_count || 0,
      votes: p.likes_count || 0,
      replyCount: p.replies_count || 0,
      pinned: p.is_pinned,
      createdAt: p.created_at
    }))
    if (page === 1) posts.value = results
    else posts.value.push(...results)
    currentPage.value = page
  } catch (e) {
    fetchError.value = e?.response?.data?.message || e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (loading.value || !hasMore.value) return
  fetchResources(currentPage.value + 1)
}

function goPost(post) { router.push(`/resources/${post.id}`) }

onMounted(async () => {
  await sectionStore.fetchSections()
  fetchResources(1)
  observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => { observer?.disconnect() })
</script>

<style scoped>
.res-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--s-lg);
}

/* ---- 搜索栏 ---- */
.res-search-bar {
  position: sticky;
  top: 60px;
  z-index: 10;
  padding: var(--s-lg) 0;
  background: var(--bg);
}
.res-search-inner {
  display: flex;
  align-items: center;
  gap: var(--s-sm);
  background: var(--bg-secondary, #f5f7fa);
  border: 1px solid var(--divider);
  border-radius: 12px;
  padding: 10px 16px;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.res-search-inner:focus-within {
  border-color: #F59E0B;
  box-shadow: 0 0 0 3px rgba(245,158,11,0.12);
}
.res-search-icon { color: var(--text-disabled); flex-shrink: 0; }
.res-search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  color: var(--text-primary);
  outline: none;
}
.res-search-input::placeholder { color: var(--text-disabled); }
.res-search-clear {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-disabled);
  padding: 2px;
  border-radius: 4px;
  display: flex;
}
.res-search-clear:hover { color: var(--text-secondary); background: rgba(0,0,0,0.05); }

/* ---- 卡片网格 ---- */
.res-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: var(--s-xl);
  margin-bottom: var(--s-xl);
}

/* ---- 单个卡片 ---- */
.res-card {
  background: var(--bg);
  border: 1px solid var(--divider);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.25s ease;
  animation: resFadeUp 400ms ease-out both;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 200px;
}
.res-card:hover {
  border-color: #F59E0B;
  box-shadow: 0 8px 28px rgba(245,158,11,0.12);
  transform: translateY(-3px);
}

/* 卡片头部 */
.res-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.res-card-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
  object-fit: cover;
}
.res-card-author-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.res-card-author {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}
.res-card-time {
  font-size: 12px;
  color: var(--text-disabled);
}
.res-card-pin-badge {
  font-size: 11px;
  font-weight: 600;
  color: #D97706;
  background: rgba(245,158,11,0.1);
  padding: 2px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}

/* 卡片主体 */
.res-card-body {
  flex: 1;
}
.res-card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.res-card-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 卡片底部 */
.res-card-footer {
  border-top: 1px solid var(--divider);
  padding-top: 12px;
}
.res-card-stats {
  display: flex;
  gap: var(--s-md);
}
.res-card-stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-disabled);
}

/* ---- 状态 ---- */
.res-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.res-empty {
  text-align: center;
  padding: var(--s-3xl) var(--s-lg);
  color: var(--text-secondary);
}
.res-empty svg { color: var(--text-disabled); opacity: 0.4; margin-bottom: var(--s-base); }
.scroll-sentinel { height: 1px; }

/* ---- FAB ---- */
.res-fab {
  position: fixed;
  bottom: var(--s-xl);
  right: var(--s-xl);
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #F59E0B, #F97316);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(245,158,11,0.35);
  transition: all var(--t-fast);
  z-index: 40;
}
.res-fab:hover {
  transform: scale(1.1) rotate(90deg);
  box-shadow: 0 12px 32px rgba(245,158,11,0.45);
}

/* ---- Animation ---- */
@keyframes resFadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .res-page { padding: 0 var(--s-sm); }
  .res-grid { grid-template-columns: 1fr; }
  .res-fab { bottom: var(--s-lg); right: var(--s-lg); }
}
</style>
