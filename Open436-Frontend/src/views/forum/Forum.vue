<template>
  <!-- Hero -->
  <div class="fm-hero">
    <div class="fm-hero-mesh"></div>
    <div class="fm-hero-content">
      <div class="fm-hero-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="28" height="28">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <h1 class="fm-hero-title">技术论坛</h1>
      <p class="fm-hero-desc">交流技术、分享经验、碰撞思想</p>
      <div class="fm-hero-stats">
        <div class="fm-stat">
          <span class="fm-stat-num">{{ totalCount }}</span>
          <span class="fm-stat-label">帖子</span>
        </div>
        <div class="fm-stat-div"></div>
        <div class="fm-stat">
          <span class="fm-stat-num">{{ sectionStore.forumSections.filter(s => s.key !== 'all').length }}</span>
          <span class="fm-stat-label">板块</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Posts -->
  <div class="fm-list">
    <div
      v-for="(post, i) in posts"
      :key="post.id"
      class="fm-post"
      :class="{ 'fm-post-pinned': post.pinned }"
      :style="{ animationDelay: `${i * 50}ms` }"
      @click="goPost(post)"
    >
      <div class="fm-post-accent" :style="{ background: getSectionColor(post.section) }"></div>
      <div class="fm-post-body">
        <div class="fm-post-header">
          <span class="fm-post-section" :style="{ color: getSectionColor(post.section), background: getSectionBg(post.section) }">
            {{ getSectionName(post.section) }}
          </span>
          <span v-if="post.pinned" class="fm-post-pin">
            <svg viewBox="0 0 24 24" fill="currentColor" width="11" height="11"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
            置顶
          </span>
          <span class="fm-post-author">u/{{ post.author }}</span>
          <span class="fm-post-dot">·</span>
          <span class="fm-post-time">{{ formatDate(post.createdAt) }}</span>
        </div>
        <h3 class="fm-post-title">{{ post.title }}</h3>
        <p class="fm-post-preview">{{ post.content }}</p>
        <div class="fm-post-footer">
          <span class="fm-post-stat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
            {{ post.votes }}
          </span>
          <span class="fm-post-stat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            {{ post.replyCount }}
          </span>
        </div>
      </div>
      <div class="fm-post-arrow">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="9 18 15 12 9 6"/></svg>
      </div>
    </div>
  </div>

  <div v-if="loading" class="fm-loading"><span class="spinner"></span></div>
  <div v-if="!loading && posts.length === 0" class="fm-empty">
    <div class="fm-empty-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    </div>
    <p>{{ fetchError || '暂无帖子，快来发布第一篇吧' }}</p>
  </div>
  <div ref="sentinel" class="scroll-sentinel"></div>

  <!-- FAB -->
  <router-link v-if="auth.canPost" to="/forum/post/new" class="fm-fab" title="发帖">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="24" height="24">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  </router-link>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
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
let observer = null
const PAGE_SIZE = 10

const onSidebarSelect = inject('forumOnSidebarSelect', null)
if (onSidebarSelect) {
  onSidebarSelect(() => { currentPage.value = 1; fetchPosts(1) })
}

const activeSectionId = computed(() => {
  const key = sectionStore.activeSection
  if (key === 'all') return null
  return sectionStore.getSectionId(key)
})
const hasMore = computed(() => posts.value.length < totalCount.value)

function getSectionName(key) { return sectionStore.getSection(key)?.name || '' }
function getSectionColor(key) { return sectionStore.getSection(key)?.color || '#1976D2' }
function getSectionBg(key) { return (sectionStore.getSection(key)?.color || '#1976D2') + '12' }

async function fetchPosts(page = 1) {
  loading.value = true
  try {
    const params = { page, page_size: PAGE_SIZE }
    if (activeSectionId.value) params.section_id = activeSectionId.value
    const res = await getPosts(params)
    const data = res?.data || {}
    totalCount.value = data.count || 0
    const results = (data.results || []).map(p => {
      const sec = sectionStore.getSectionById(p.section?.section_id)
      return {
        id: p.id, title: p.title,
        content: p.content_preview || p.content || '',
        author: p.author?.nickname || `用户${p.author?.user_id || ''}`,
        section: sec?.key || '',
        votes: p.likes_count || 0, replyCount: p.replies_count || 0,
        pinned: p.is_pinned, createdAt: p.created_at
      }
    })
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
  fetchPosts(currentPage.value + 1)
}
function goPost(post) { router.push(`/forum/post/${post.id}`) }

onMounted(() => {
  sectionStore.fetchSections()
  fetchPosts(1)
  observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => { observer?.disconnect() })
</script>

<style scoped>
/* ---- Hero ---- */
.fm-hero {
  position: relative; padding: 48px 32px 40px;
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 40%, #BFDBFE 100%);
  border-radius: var(--r-lg); margin-bottom: var(--s-xl); overflow: hidden;
}
.fm-hero-mesh {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(25,118,210,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(25,118,210,0.04) 1px, transparent 1px);
  background-size: 32px 32px;
}
.fm-hero-content { position: relative; z-index: 1; }
.fm-hero-icon {
  width: 52px; height: 52px; border-radius: var(--r-md);
  background: rgba(25,118,210,0.1); color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: var(--s-base); border: 1px solid rgba(25,118,210,0.2);
}
.fm-hero-title { font-size: 28px; font-weight: 700; color: #1E3A5F; letter-spacing: -0.5px; margin-bottom: var(--s-sm); }
.fm-hero-desc { font-size: 15px; color: #3B6EA5; max-width: 400px; line-height: 1.6; margin-bottom: var(--s-lg); }
.fm-hero-stats { display: flex; align-items: center; gap: var(--s-lg); }
.fm-stat { display: flex; align-items: baseline; gap: var(--s-xs); }
.fm-stat-num { font-size: 24px; font-weight: 700; color: #1E3A5F; font-variant-numeric: tabular-nums; }
.fm-stat-label { font-size: 13px; color: #3B6EA5; }
.fm-stat-div { width: 1px; height: 28px; background: rgba(25,118,210,0.2); }

/* ---- Post List ---- */
.fm-list { display: flex; flex-direction: column; }
.fm-post {
  display: flex; align-items: center; gap: 0;
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  margin-bottom: var(--s-sm); cursor: pointer; overflow: hidden;
  transition: all var(--t-fast); animation: fmFadeUp 400ms ease-out both;
}
.fm-post:hover { border-color: var(--primary); box-shadow: 0 4px 16px rgba(25,118,210,0.08); transform: translateY(-1px); }
.fm-post-pinned { border-left: 3px solid var(--warning); }
.fm-post-accent { width: 4px; align-self: stretch; flex-shrink: 0; }
.fm-post-body { flex: 1; padding: var(--s-base) var(--s-lg); min-width: 0; }
.fm-post-header { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-sm); flex-wrap: wrap; }
.fm-post-section {
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px;
}
.fm-post-pin {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: 11px; font-weight: 600; color: var(--warning);
  background: rgba(255,152,0,0.08); padding: 2px 8px; border-radius: 999px;
}
.fm-post-author { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.fm-post-dot { color: var(--text-disabled); font-size: 12px; }
.fm-post-time { font-size: 12px; color: var(--text-disabled); }
.fm-post-title { font-size: 16px; font-weight: 600; margin-bottom: var(--s-xs); line-height: 1.4; }
.fm-post-preview {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: var(--s-sm);
}
.fm-post-footer { display: flex; gap: var(--s-base); }
.fm-post-stat {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--text-disabled); font-weight: 500;
}
.fm-post-arrow { color: var(--text-disabled); padding-right: var(--s-base); transition: all var(--t-fast); flex-shrink: 0; }
.fm-post:hover .fm-post-arrow { transform: translateX(4px); color: var(--primary); }

/* ---- States ---- */
.fm-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.fm-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-secondary); }
.fm-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
.scroll-sentinel { height: 1px; }

/* ---- FAB ---- */
.fm-fab {
  position: fixed; bottom: var(--s-xl); right: var(--s-xl);
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  color: #fff; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8px 24px rgba(25,118,210,0.35);
  transition: all var(--t-fast); z-index: 40;
}
.fm-fab:hover { transform: scale(1.1) rotate(90deg); box-shadow: 0 12px 32px rgba(25,118,210,0.45); }
@media (max-width: 959px) { .fm-fab { bottom: var(--s-lg); right: var(--s-lg); } }

/* ---- Animation ---- */
@keyframes fmFadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 599px) {
  .fm-hero { padding: 32px 20px 28px; }
  .fm-hero-title { font-size: 22px; }
  .fm-post-body { padding: var(--s-sm) var(--s-base); }
}
</style>
