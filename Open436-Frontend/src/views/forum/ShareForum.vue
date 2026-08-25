<template>
  <div class="sf-banner">
    <span class="sf-banner-dot"></span>
    <h2 class="sf-banner-title">资源分享</h2>
    <span class="sf-banner-count">{{ totalCount }} 个资源</span>
  </div>

  <div class="sf-grid">
    <article
      v-for="(p, i) in posts"
      :key="p.id"
      class="sf-card"
      :style="{ animationDelay: `${i * 70}ms` }"
      @click="goPost(p)"
    >
      <div class="sf-cover">
        <svg class="sf-cover-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
        <span v-if="p.pinned" class="sf-cover-tag">置顶</span>
        <div class="sf-cover-glow"></div>
      </div>
      <div class="sf-body">
        <h3 class="sf-title">{{ p.title }}</h3>
        <p class="sf-summary">{{ p.summary || p.preview }}</p>
        <div class="sf-meta">
          <span class="sf-author"><span class="sf-avatar">{{ (p.author || 'U').charAt(0) }}</span>{{ p.author }}</span>
          <span class="sf-time">{{ formatDate(p.createdAt) }}</span>
        </div>
        <div class="sf-stats">
          <span class="sf-stat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19V5M5 12l7-7 7 7"/></svg>{{ p.votes }}</span>
          <span class="sf-stat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>{{ p.replyCount }}</span>
          <span class="sf-stat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>{{ p.favorites }}</span>
          <span class="sf-stat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>{{ p.shares }}</span>
        </div>
      </div>
    </article>
  </div>

  <div v-if="loading" class="sf-loading"><span class="spinner"></span></div>
  <div v-if="!loading && posts.length === 0" class="sf-empty">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
    <p>{{ fetchError || '还没有资源，来分享第一个吧' }}</p>
  </div>
  <div ref="sentinel" class="scroll-sentinel"></div>

  <router-link v-if="auth.canPost" to="/forum/post/new" class="sf-fab" title="分享资源">
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

const SECTION = 'share'
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
const PAGE_SIZE = 12

const activeSectionId = computed(() => sectionStore.getSectionId(SECTION))
const hasMore = computed(() => posts.value.length < totalCount.value)

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
        summary: p.summary || '',
        preview: p.content_preview || p.content || '',
        author: p.author?.nickname || `用户${p.author?.user_id || ''}`,
        section: sec?.key || SECTION,
        votes: p.likes_count || 0, replyCount: p.replies_count || 0,
        favorites: p.favorites_count || p.collects_count || 0,
        shares: p.shares_count || 0,
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
function goPost(p) { router.push(`/forum/post/${p.id}`) }

onMounted(async () => {
  await sectionStore.fetchSections()
  await fetchPosts(1)
  observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => { observer?.disconnect() })
</script>

<style scoped>
.sf-banner { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-xl); }
.sf-banner-dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, var(--cosmic-cyan), var(--cosmic-violet)); box-shadow: 0 0 12px rgba(0,188,212,0.6); }
.sf-banner-title { font-family: var(--font-display); font-size: 22px; font-weight: 700; color: var(--text-primary); }
.sf-banner-count { font-size: 13px; color: var(--text-disabled); margin-left: auto; font-variant-numeric: tabular-nums; }
.sf-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 28px; }
@media (max-width: 900px) { .sf-grid { grid-template-columns: 1fr; } }
.sf-card { position: relative; background: var(--bg); border-radius: 22px; overflow: hidden; border: 1px solid rgba(33,30,53,0.06); box-shadow: var(--sh-cosmic-card); cursor: pointer; transition: transform .45s cubic-bezier(0.2,0.8,0.2,1), box-shadow .45s; animation: sfRise .7s cubic-bezier(0.2,0.8,0.2,1) both; }
.sf-card:hover { transform: translateY(-8px); box-shadow: 0 50px 140px -20px rgba(145,94,255,0.4), 0 0 0 1px rgba(145,94,255,0.2); }
.sf-card:hover .sf-cover-glow { opacity: 1; }
.sf-cover { position: relative; height: 150px; background: linear-gradient(135deg, var(--cosmic-cyan) 0%, #0a4a78 60%, var(--cosmic-bg) 100%); display: flex; align-items: center; justify-content: center; overflow: hidden; }
.sf-cover-icon { width: 64px; height: 64px; color: rgba(255,255,255,0.92); filter: drop-shadow(0 6px 20px rgba(0,188,212,0.6)); position: relative; z-index: 1; }
.sf-cover-glow { position: absolute; inset: 0; opacity: 0; transition: opacity .45s; background: radial-gradient(400px 200px at 30% 0%, rgba(145,94,255,0.5), transparent 70%); }
.sf-cover-tag { position: absolute; top: 14px; right: 14px; background: rgba(255,255,255,0.18); backdrop-filter: blur(6px); color: #fff; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.25); z-index: 2; }
.sf-body { padding: 22px 24px 20px; display: flex; flex-direction: column; gap: 12px; }
.sf-title { font-family: var(--font-display); font-size: 20px; font-weight: 700; line-height: 1.35; color: var(--text-primary); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.sf-summary { font-size: 14px; line-height: 1.7; color: var(--text-secondary); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; min-height: 48px; }
.sf-meta { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-disabled); }
.sf-author { display: flex; align-items: center; gap: 6px; font-weight: 500; color: var(--text-secondary); }
.sf-avatar { width: 22px; height: 22px; border-radius: 50%; background: linear-gradient(135deg, var(--cosmic-violet), var(--cosmic-cyan)); color: #fff; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; font-family: var(--font-display); }
.sf-time { margin-left: auto; }
.sf-stats { display: flex; gap: 18px; padding-top: 14px; margin-top: 2px; border-top: 1px solid var(--divider); font-size: 13px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
.sf-stat { display: flex; align-items: center; gap: 5px; }
.sf-stat svg { width: 14px; height: 14px; }
.sf-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.sf-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-disabled); }
.sf-empty svg { opacity: 0.3; margin-bottom: var(--s-base); }
.scroll-sentinel { height: 1px; }
.sf-fab { position: fixed; bottom: var(--s-xl); right: var(--s-xl); width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, var(--cosmic-violet), var(--cosmic-cyan)); color: #fff; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 24px rgba(145,94,255,0.35); transition: all var(--t-fast); z-index: 40; }
.sf-fab:hover { transform: scale(1.1) rotate(90deg); }
@keyframes sfRise { from { opacity: 0; transform: translateY(28px) scale(0.98); } to { opacity: 1; transform: none; } }
</style>
