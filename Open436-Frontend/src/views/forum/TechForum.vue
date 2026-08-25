<template>
  <!-- 板块标识条 -->
  <div class="tf-banner">
    <span class="tf-banner-dot"></span>
    <h2 class="tf-banner-title">技术交流</h2>
    <span class="tf-banner-count">{{ totalCount }} 篇帖子</span>
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
        <span class="fm-card-section" :style="{ color: getSectionColor(post.section), background: getSectionBg(post.section) }">{{ getSectionName(post.section) }}</span>
        <span v-if="post.pinned" class="fm-card-pin">置顶</span>
      </div>
      <h3 class="fm-card-title">{{ post.title }}</h3>
      <p class="fm-card-preview">{{ post.content }}</p>
      <div class="fm-card-footer">
        <span class="fm-card-author">{{ post.author }}</span>
        <span class="fm-card-time">{{ formatDate(post.createdAt) }}</span>
        <span class="fm-card-stats">
          <span class="fm-card-stat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M12 19V5M5 12l7-7 7 7"/></svg>{{ post.votes }}</span>
          <span class="fm-card-stat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>{{ post.replyCount }}</span>
        </span>
      </div>
    </div>
  </div>

  <div v-if="loading" class="fm-loading"><span class="spinner"></span></div>
  <div v-if="!loading && posts.length === 0" class="fm-empty">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
    <p>{{ fetchError || '暂无帖子，快来发布第一篇吧' }}</p>
  </div>
  <div ref="sentinel" class="scroll-sentinel"></div>

  <router-link v-if="auth.canPost" to="/forum/post/new" class="fm-fab" title="发帖">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="24" height="24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
  </router-link>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'
import { getPosts } from '@/api/post'
import { formatDate } from '@/utils/format'

const SECTION = 'tech'
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

const activeSectionId = computed(() => sectionStore.getSectionId(SECTION))
const hasMore = computed(() => posts.value.length < totalCount.value)

function getSectionName(key) { return sectionStore.getSection(key)?.name || '' }
function getSectionColor(key) { return sectionStore.getSection(key)?.color || '#1976D2' }
function getSectionBg(key) { return (sectionStore.getSection(key)?.color || '#1976D2') + '14' }

async function fetchPosts(page = 1) {
  loading.value = true
  fetchError.value = ''
  try {
    let sectionId = activeSectionId.value
    if (!sectionId) { await sectionStore.fetchSections(); sectionId = activeSectionId.value }
    const params = { page, page_size: PAGE_SIZE }
    if (sectionId) params.section_id = sectionId
    const res = await getPosts(params)
    const data = res?.data || {}
    totalCount.value = data.count || 0
    const results = (data.results || []).map(p => {
      const sec = sectionStore.getSectionById(p.section?.section_id)
      return {
        id: p.id, title: p.title,
        content: p.content_preview || p.content || '',
        author: p.author?.nickname || `用户${p.author?.user_id || ''}`,
        section: sec?.key || SECTION,
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

function loadMore() { if (loading.value || !hasMore.value) return; fetchPosts(currentPage.value + 1) }
function goPost(post) { router.push(`/forum/post/${post.id}`) }

onMounted(async () => {
  await sectionStore.fetchSections()
  await fetchPosts(1)
  observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => { observer?.disconnect() })
</script>

<style scoped>
.tf-banner { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-lg); }
.tf-banner-dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, var(--cosmic-violet), var(--cosmic-cyan)); box-shadow: 0 0 12px rgba(145,94,255,0.6); }
.tf-banner-title { font-family: var(--font-display); font-size: 22px; font-weight: 700; color: var(--text-primary); }
.tf-banner-count { font-size: 13px; color: var(--text-disabled); margin-left: auto; font-variant-numeric: tabular-nums; }
.fm-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--s-base); }
@media (max-width: 768px) { .fm-grid { grid-template-columns: 1fr; } }
.fm-card { background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md); padding: var(--s-lg); cursor: pointer; overflow: hidden; transition: all var(--t-fast); animation: fmFadeUp 350ms ease-out both; display: flex; flex-direction: column; }
.fm-card:hover { border-color: var(--cosmic-violet); box-shadow: 0 6px 24px rgba(145,94,255,0.14); transform: translateY(-2px); }
.fm-card-pinned { border-top: 3px solid var(--warning); }
.fm-card-top { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-sm); }
.fm-card-section { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 999px; }
.fm-card-pin { font-size: 11px; font-weight: 600; color: var(--warning); background: rgba(255,152,0,0.08); padding: 2px 8px; border-radius: 999px; }
.fm-card-title { font-size: 15px; font-weight: 600; line-height: 1.5; margin-bottom: var(--s-xs); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.fm-card-preview { font-size: 13px; color: var(--text-secondary); line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: var(--s-base); flex: 1; }
.fm-card-footer { display: flex; align-items: center; gap: var(--s-sm); font-size: 12px; color: var(--text-disabled); margin-top: auto; padding-top: var(--s-sm); border-top: 1px solid var(--divider); }
.fm-card-author { font-weight: 500; color: var(--text-secondary); }
.fm-card-stats { margin-left: auto; display: flex; gap: var(--s-sm); }
.fm-card-stat { display: flex; align-items: center; gap: 3px; }
.fm-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.fm-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-disabled); }
.fm-empty svg { opacity: 0.3; margin-bottom: var(--s-base); }
.scroll-sentinel { height: 1px; }
.fm-fab { position: fixed; bottom: var(--s-xl); right: var(--s-xl); width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, var(--cosmic-violet), var(--cosmic-cyan)); color: #fff; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 24px rgba(145,94,255,0.35); transition: all var(--t-fast); z-index: 40; }
.fm-fab:hover { transform: scale(1.1) rotate(90deg); }
@keyframes fmFadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
</style>
