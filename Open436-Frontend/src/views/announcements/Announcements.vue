<template>
  <!-- Header -->
  <div class="ann-header">
    <div class="ann-header-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="24" height="24">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
    </div>
    <div class="ann-header-text">
      <h1 class="ann-header-title">系统通知</h1>
      <p class="ann-header-desc">平台公告与重要通知</p>
    </div>
  </div>

  <!-- Pinned -->
  <template v-if="pinnedPosts.length > 0">
    <div v-for="post in pinnedPosts" :key="post.id" class="ann-pinned" @click="goPost(post)">
      <div class="ann-pinned-stripe"></div>
      <div class="ann-pinned-body">
        <div class="ann-pinned-badge">
          <svg viewBox="0 0 24 24" fill="currentColor" width="12" height="12"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
          置顶
        </div>
        <h3 class="ann-pinned-title">{{ post.title }}</h3>
        <p class="ann-pinned-preview">{{ post.content }}</p>
        <div class="ann-pinned-meta">
          <span>{{ post.author }}</span>
          <span class="ann-dot">·</span>
          <span>{{ formatDate(post.createdAt) }}</span>
        </div>
      </div>
      <div class="ann-pinned-arrow">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><polyline points="9 18 15 12 9 6"/></svg>
      </div>
    </div>
  </template>

  <!-- Timeline -->
  <div class="ann-timeline">
    <template v-for="(group, date) in groupedPosts" :key="date">
      <div class="ann-date-marker">
        <span class="ann-date-text">{{ date }}</span>
      </div>
      <div
        v-for="(post, i) in group"
        :key="post.id"
        class="ann-item"
        :style="{ animationDelay: `${i * 60}ms` }"
        @click="goPost(post)"
      >
        <div class="ann-item-dot"></div>
        <div class="ann-item-line"></div>
        <div class="ann-item-content">
          <div class="ann-item-header">
            <h4 class="ann-item-title">{{ post.title }}</h4>
            <span class="ann-item-time">{{ formatTime(post.createdAt) }}</span>
          </div>
          <p class="ann-item-preview">{{ post.content }}</p>
          <div class="ann-item-footer">
            <span class="ann-item-author">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              {{ post.author }}
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>

  <div v-if="loading" class="ann-loading"><span class="spinner"></span></div>
  <div v-if="!loading && posts.length === 0" class="ann-empty">
    <div class="ann-empty-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
    </div>
    <p>{{ fetchError || '暂无公告' }}</p>
  </div>
  <div ref="sentinel" class="scroll-sentinel"></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { getPosts } from '@/api/post'

const router = useRouter()
const sectionStore = useSectionStore()
const fetchError = ref('')
const loading = ref(false)
const posts = ref([])
const currentPage = ref(1)
const totalCount = ref(0)
const sentinel = ref(null)
let observer = null
const PAGE_SIZE = 20

const hasMore = computed(() => posts.value.length < totalCount.value)
const pinnedPosts = computed(() => posts.value.filter(p => p.pinned))

const groupedPosts = computed(() => {
  const unpinned = posts.value.filter(p => !p.pinned)
  const groups = {}
  unpinned.forEach(p => {
    const date = formatDate(p.createdAt)
    if (!groups[date]) groups[date] = []
    groups[date].push(p)
  })
  return groups
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now - d
  if (diff < 86400000 && d.getDate() === now.getDate()) return '今天'
  if (diff < 172800000) return '昨天'
  const m = d.getMonth() + 1
  const day = d.getDate()
  if (d.getFullYear() === now.getFullYear()) return `${m}月${day}日`
  return `${d.getFullYear()}年${m}月${day}日`
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function fetchAnnouncements(page = 1) {
  loading.value = true
  try {
    const sectionId = sectionStore.getSectionId('announce')
    if (!sectionId) { loading.value = false; return }
    const res = await getPosts({ section_id: sectionId, page, page_size: PAGE_SIZE })
    const data = res?.data || {}
    totalCount.value = data.count || 0
    const results = (data.results || []).map(p => ({
      id: p.id,
      title: p.title,
      content: p.content_preview || p.content || '',
      author: p.author?.nickname || `管理员`,
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
  fetchAnnouncements(currentPage.value + 1)
}

function goPost(post) { router.push(`/announcements/${post.id}`) }

onMounted(async () => {
  await sectionStore.fetchSections()
  fetchAnnouncements(1)
  observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => { observer?.disconnect() })
</script>

<style scoped>
/* ---- Header ---- */
.ann-header {
  display: flex; align-items: center; gap: var(--s-base);
  padding: var(--s-lg); margin-bottom: var(--s-lg);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
}
.ann-header-icon {
  width: 48px; height: 48px; border-radius: var(--r-md); flex-shrink: 0;
  background: rgba(25,118,210,0.08); color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(25,118,210,0.15);
}
.ann-header-title { font-size: 22px; font-weight: 700; letter-spacing: -0.3px; margin-bottom: 2px; }
.ann-header-desc { font-size: 14px; color: var(--text-secondary); }

/* ---- Pinned ---- */
.ann-pinned {
  display: flex; align-items: center; gap: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  margin-bottom: var(--s-base); cursor: pointer; overflow: hidden;
  transition: all var(--t-fast);
}
.ann-pinned:hover { border-color: var(--primary); box-shadow: 0 4px 16px rgba(25,118,210,0.1); }
.ann-pinned-stripe {
  width: 4px; align-self: stretch; flex-shrink: 0;
  background: linear-gradient(180deg, var(--primary), var(--primary-light));
}
.ann-pinned-body { flex: 1; padding: var(--s-base) 0; min-width: 0; }
.ann-pinned-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 600; color: var(--primary);
  background: var(--primary-bg); padding: 2px 8px; border-radius: 999px;
  margin-bottom: var(--s-sm);
}
.ann-pinned-title { font-size: 16px; font-weight: 600; margin-bottom: var(--s-xs); line-height: 1.4; }
.ann-pinned-preview {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: var(--s-sm);
}
.ann-pinned-meta { font-size: 12px; color: var(--text-disabled); display: flex; align-items: center; gap: var(--s-xs); }
.ann-dot { color: var(--text-disabled); }
.ann-pinned-arrow { color: var(--text-disabled); padding-right: var(--s-base); transition: transform var(--t-fast); flex-shrink: 0; }
.ann-pinned:hover .ann-pinned-arrow { transform: translateX(4px); color: var(--primary); }

/* ---- Timeline ---- */
.ann-timeline { position: relative; padding-left: 28px; }

.ann-date-marker {
  position: relative; padding: var(--s-sm) 0;
  margin-left: -28px;
}
.ann-date-marker::before {
  content: ''; position: absolute; left: 5px; top: 50%;
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--primary); transform: translateY(-50%);
}
.ann-date-text {
  margin-left: 24px; font-size: 13px; font-weight: 600;
  color: var(--text-primary); background: var(--bg-secondary);
  padding: 2px 10px; border-radius: 999px;
}

.ann-item {
  position: relative; padding: var(--s-base) 0;
  cursor: pointer; animation: annFadeIn 350ms ease-out both;
}
.ann-item-dot {
  position: absolute; left: -24px; top: calc(var(--s-base) + 6px);
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--divider); border: 2px solid var(--bg-secondary);
  transition: all var(--t-fast);
}
.ann-item:hover .ann-item-dot { background: var(--primary); transform: scale(1.3); }
.ann-item-line {
  position: absolute; left: -22px; top: calc(var(--s-base) + 14px);
  width: 2px; bottom: 0; background: var(--divider);
}

.ann-item-content {
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  padding: var(--s-base) var(--s-lg); transition: all var(--t-fast);
}
.ann-item:hover .ann-item-content {
  border-color: var(--primary); background: #F8FBFF;
  box-shadow: 0 2px 8px rgba(25,118,210,0.06);
}
.ann-item-header { display: flex; align-items: baseline; justify-content: space-between; gap: var(--s-sm); margin-bottom: var(--s-xs); }
.ann-item-title { font-size: 15px; font-weight: 500; line-height: 1.4; }
.ann-item-time { font-size: 12px; color: var(--text-disabled); font-variant-numeric: tabular-nums; flex-shrink: 0; }
.ann-item-preview {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: var(--s-sm);
}
.ann-item-footer { display: flex; align-items: center; gap: var(--s-base); }
.ann-item-author {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--text-disabled);
}

/* ---- States ---- */
.ann-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.ann-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-secondary); }
.ann-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
.scroll-sentinel { height: 1px; }

/* ---- Animation ---- */
@keyframes annFadeIn {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}

/* ---- Responsive ---- */
@media (max-width: 599px) {
  .ann-timeline { padding-left: 20px; }
  .ann-date-marker { margin-left: -20px; }
  .ann-item-dot { left: -16px; }
  .ann-item-line { left: -14px; }
  .ann-item-content { padding: var(--s-sm) var(--s-base); }
  .ann-pinned { flex-direction: column; align-items: stretch; }
  .ann-pinned-stripe { width: 100%; height: 4px; }
  .ann-pinned-arrow { display: none; }
}
</style>
