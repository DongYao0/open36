<template>
  <!-- Search Bar -->
  <div class="fm-search">
    <div class="fm-search-inner">
      <svg class="fm-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        v-model="searchQuery"
        class="fm-search-input"
        type="text"
        placeholder="搜索帖子..."
        @keyup.enter="doSearch"
      />
      <button v-if="searchQuery" class="fm-search-clear" @click="searchQuery = ''">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <div class="fm-search-meta">
      <span>{{ totalCount }} 篇帖子</span>
      <span>·</span>
      <span>{{ sectionStore.forumSections.filter(s => s.key !== 'all').length }} 个板块</span>
    </div>
  </div>

  <!-- Section Chips -->
  <div class="fm-chips">
    <button
      v-for="s in sectionStore.forumSections"
      :key="s.key"
      class="fm-chip"
      :class="{ active: sectionStore.activeSection === s.key }"
      :style="sectionStore.activeSection === s.key ? { background: s.color, borderColor: s.color } : {}"
      @click="selectSection(s.key)"
    >
      {{ s.name }}
      <span v-if="s.key !== 'all' && s.count" class="fm-chip-count">{{ s.count }}</span>
    </button>
  </div>

  <!-- Posts Grid -->
  <div class="fm-grid">
    <div
      v-for="(post, i) in posts"
      :key="post.id"
      class="fm-card"
      :class="{ 'fm-card-pinned': post.pinned }"
      :style="{ animationDelay: `${i * 40}ms` }"
      @click="goPost(post)"
    >
      <div class="fm-card-top">
        <span class="fm-card-section" :style="{ color: getSectionColor(post.section), background: getSectionBg(post.section) }">
          {{ getSectionName(post.section) }}
        </span>
        <span v-if="post.pinned" class="fm-card-pin">置顶</span>
      </div>
      <h3 class="fm-card-title">{{ post.title }}</h3>
      <p class="fm-card-preview">{{ post.content }}</p>
      <div class="fm-card-footer">
        <span class="fm-card-author">{{ post.author }}</span>
        <span class="fm-card-time">{{ formatDate(post.createdAt) }}</span>
        <span class="fm-card-stats">
          <span class="fm-card-stat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
            {{ post.votes }}
          </span>
          <span class="fm-card-stat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            {{ post.replyCount }}
          </span>
        </span>
      </div>
    </div>
  </div>

  <div v-if="loading" class="fm-loading"><span class="spinner"></span></div>
  <div v-if="!loading && posts.length === 0" class="fm-empty">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
    <p>{{ fetchError || '暂无帖子' }}</p>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'
import { getPosts } from '@/api/post'
import { formatDate } from '@/utils/format'

const router = useRouter()
const sectionStore = useSectionStore()
const auth = useAuthStore()

const searchQuery = ref('')
const fetchError = ref('')
const loading = ref(false)
const posts = ref([])
const currentPage = ref(1)
const totalCount = ref(0)
const sentinel = ref(null)
let observer = null
const PAGE_SIZE = 10

const activeSectionId = computed(() => {
  const key = sectionStore.activeSection
  if (key === 'all') return null
  return sectionStore.getSectionId(key)
})
const hasMore = computed(() => posts.value.length < totalCount.value)

function getSectionName(key) { return sectionStore.getSection(key)?.name || '' }
function getSectionColor(key) { return sectionStore.getSection(key)?.color || '#1976D2' }
function getSectionBg(key) { return (sectionStore.getSection(key)?.color || '#1976D2') + '14' }

function selectSection(key) {
  sectionStore.setActive(key)
  currentPage.value = 1
  fetchPosts(1)
}

function doSearch() {
  currentPage.value = 1
  fetchPosts(1)
}

async function fetchPosts(page = 1) {
  loading.value = true
  fetchError.value = ''
  try {
    const params = { page, page_size: PAGE_SIZE }
    if (activeSectionId.value) params.section_id = activeSectionId.value
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
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
/* ---- Search ---- */
.fm-search {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: var(--s-base); gap: var(--s-base); flex-wrap: wrap;
}
.fm-search-inner {
  position: relative; flex: 1; min-width: 240px; max-width: 480px;
}
.fm-search-icon {
  position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
  color: var(--text-disabled); pointer-events: none;
}
.fm-search-input {
  width: 100%; height: 42px; padding: 0 36px 0 40px;
  border: 1px solid var(--divider); border-radius: 999px;
  background: var(--bg); font-size: 14px; color: var(--text-primary);
  outline: none; transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.fm-search-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(25,118,210,0.1);
}
.fm-search-input::placeholder { color: var(--text-disabled); }
.fm-search-clear {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; color: var(--text-disabled);
  padding: 4px; border-radius: 50%; display: flex;
}
.fm-search-clear:hover { color: var(--text-primary); background: var(--divider); }
.fm-search-meta {
  display: flex; align-items: center; gap: var(--s-xs);
  font-size: 13px; color: var(--text-disabled); white-space: nowrap;
}

/* ---- Section Chips ---- */
.fm-chips {
  display: flex; gap: var(--s-sm); margin-bottom: var(--s-lg);
  flex-wrap: wrap;
}
.fm-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 16px; border-radius: 999px; font-size: 13px; font-weight: 500;
  border: 1px solid var(--divider); background: var(--bg); color: var(--text-secondary);
  cursor: pointer; transition: all var(--t-fast); white-space: nowrap;
}
.fm-chip:hover { border-color: var(--primary); color: var(--primary); }
.fm-chip.active { color: #fff; border-color: transparent; }
.fm-chip-count {
  font-size: 11px; background: rgba(0,0,0,0.1); padding: 1px 6px;
  border-radius: 999px;
}
.fm-chip.active .fm-chip-count { background: rgba(255,255,255,0.25); }

/* ---- Card Grid ---- */
.fm-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--s-base);
}
@media (max-width: 768px) {
  .fm-grid { grid-template-columns: 1fr; }
}

/* ---- Card ---- */
.fm-card {
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  padding: var(--s-lg); cursor: pointer; overflow: hidden;
  transition: all var(--t-fast); animation: fmFadeUp 350ms ease-out both;
  display: flex; flex-direction: column;
}
.fm-card:hover {
  border-color: var(--primary); box-shadow: 0 6px 20px rgba(25,118,210,0.1);
  transform: translateY(-2px);
}
.fm-card-pinned { border-top: 3px solid var(--warning); }
.fm-card-top { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-sm); }
.fm-card-section {
  font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 999px;
}
.fm-card-pin {
  font-size: 11px; font-weight: 600; color: var(--warning);
  background: rgba(255,152,0,0.08); padding: 2px 8px; border-radius: 999px;
}
.fm-card-title {
  font-size: 15px; font-weight: 600; line-height: 1.5;
  margin-bottom: var(--s-xs);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.fm-card-preview {
  font-size: 13px; color: var(--text-secondary); line-height: 1.6;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: var(--s-base); flex: 1;
}
.fm-card-footer {
  display: flex; align-items: center; gap: var(--s-sm);
  font-size: 12px; color: var(--text-disabled); margin-top: auto;
  padding-top: var(--s-sm); border-top: 1px solid var(--divider);
}
.fm-card-author { font-weight: 500; color: var(--text-secondary); }
.fm-card-stats { margin-left: auto; display: flex; gap: var(--s-sm); }
.fm-card-stat { display: flex; align-items: center; gap: 3px; }

/* ---- States ---- */
.fm-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.fm-empty {
  text-align: center; padding: var(--s-3xl) var(--s-lg);
  color: var(--text-disabled);
}
.fm-empty svg { opacity: 0.3; margin-bottom: var(--s-base); }
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
.fm-fab:hover { transform: scale(1.1) rotate(90deg); }

@keyframes fmFadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
