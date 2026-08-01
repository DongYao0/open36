<template>
  <div class="ann-page">
    <!-- 标题 -->
    <div class="ann-hero">
      <h1>公告通知</h1>
      <p>平台重要通知、赛事安排与系统更新会发布在这里</p>
    </div>

    <!-- 搜索 -->
    <div class="ann-search">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
      <input v-model="keyword" placeholder="搜索公告..." />
    </div>

    <!-- 置顶公告 -->
    <section v-if="pinnedPosts.length" class="ann-section">
      <h2 class="ann-section-title">置顶公告</h2>
      <article v-for="p in pinnedPosts" :key="p.id" class="ann-card pinned" @click="goPost(p)">
        <h3 class="ann-card-title">{{ p.title }}</h3>
        <p class="ann-card-desc">{{ p.content }}</p>
        <div class="ann-card-foot">
          <span class="ann-meta">{{ formatDate(p.createdAt) }} · {{ p.author }}</span>
          <span class="ann-link">查看详情 →</span>
        </div>
      </article>
    </section>

    <!-- 全部公告 / 搜索结果 -->
    <section class="ann-section">
      <h2 class="ann-section-title">{{ hasKeyword ? '搜索结果' : '全部公告' }}</h2>
      <article v-for="p in normalPosts" :key="p.id" class="ann-card" :class="{ pinned: p.pinned }" @click="goPost(p)">
        <span v-if="p.pinned" class="ann-badge">置顶</span>
        <h3 class="ann-card-title">{{ p.title }}</h3>
        <p class="ann-card-desc">{{ p.content }}</p>
        <div class="ann-card-foot">
          <span class="ann-meta">{{ formatDate(p.createdAt) }} · {{ p.author }}</span>
          <span class="ann-link">查看详情 →</span>
        </div>
      </article>
      <div v-if="loading" class="ann-loading"><span class="spinner" /></div>
      <div v-if="!loading && normalPosts.length === 0" class="ann-empty">
        {{ hasKeyword ? '未找到相关公告' : '暂无公告' }}
      </div>
    </section>

    <div ref="sentinel" class="scroll-sentinel" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { getPosts } from '@/api/post'

const router = useRouter()
const sectionStore = useSectionStore()
const keyword = ref('')
const loading = ref(false)
const posts = ref([])
const currentPage = ref(1)
const totalCount = ref(0)
const sentinel = ref(null)
let observer = null
const PAGE_SIZE = 20

const hasKeyword = computed(() => keyword.value.trim().length > 0)
const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return posts.value
  return posts.value.filter(p =>
    (p.title || '').toLowerCase().includes(kw) ||
    (p.content || '').toLowerCase().includes(kw) ||
    (p.author || '').toLowerCase().includes(kw))
})
const pinnedPosts = computed(() => hasKeyword.value ? [] : filtered.value.filter(p => p.pinned))
const normalPosts = computed(() => hasKeyword.value ? filtered.value : filtered.value.filter(p => !p.pinned))
const hasMore = computed(() => posts.value.length < totalCount.value)

function formatDate(s) {
  if (!s) return ''
  const d = new Date(s), now = new Date(), pad = n => String(n).padStart(2, '0')
  if (now - d < 86400000 && d.getDate() === now.getDate()) return '今天'
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
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
      id: p.id, title: p.title,
      content: p.content_preview || p.content || '',
      author: p.author?.nickname || '管理员',
      pinned: p.is_pinned, createdAt: p.created_at
    }))
    if (page === 1) posts.value = results
    else posts.value.push(...results)
    currentPage.value = page
  } catch (e) {
    console.warn('fetch announcements failed', e)
  } finally { loading.value = false }
}

function loadMore() { if (!loading.value && hasMore.value) fetchAnnouncements(currentPage.value + 1) }
function goPost(p) { router.push(`/announcements/${p.id}`) }

onMounted(async () => {
  await sectionStore.fetchSections()
  fetchAnnouncements(1)
  observer = new IntersectionObserver(([e]) => { if (e.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<style scoped>
.ann-page { padding: var(--s-lg) 0 80px; }
.ann-hero { margin-bottom: var(--s-lg); }
.ann-hero h1 { font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }
.ann-hero p { font-size: 14px; color: var(--text-secondary); margin-top: 6px; }
.ann-search {
  display: flex; align-items: center; gap: var(--s-sm); padding: 0 14px;
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  margin-bottom: var(--s-xl); color: var(--text-disabled); transition: border-color var(--t-fast);
}
.ann-search:focus-within { border-color: var(--primary); }
.ann-search input { flex: 1; height: 42px; border: none; outline: none; background: transparent; font-size: 14px; color: var(--text-primary); }
.ann-search input::placeholder { color: var(--text-disabled); }
.ann-section { margin-bottom: var(--s-xl); }
.ann-section-title { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: var(--s-base); letter-spacing: 0.5px; }
.ann-badge { display: inline-block; font-size: 11px; font-weight: 600; color: var(--primary); background: var(--primary-bg); padding: 2px 8px; border-radius: 999px; margin-bottom: 6px; }
.ann-card {
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  padding: var(--s-base) var(--s-lg); margin-bottom: var(--s-sm); cursor: pointer;
  transition: all var(--t-fast); position: relative;
}
.ann-card:hover { border-color: var(--primary); box-shadow: 0 4px 16px rgba(25,118,210,0.08); transform: translateY(-1px); }
.ann-card.pinned { border-left: 3px solid var(--primary); }
.ann-card-title { font-size: 16px; font-weight: 600; line-height: 1.4; margin-bottom: 6px; }
.ann-card-desc {
  font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-bottom: var(--s-sm);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.ann-card-foot { display: flex; align-items: center; justify-content: space-between; }
.ann-meta { font-size: 12px; color: var(--text-disabled); }
.ann-link { font-size: 13px; color: var(--primary); font-weight: 500; transition: transform var(--t-fast); }
.ann-card:hover .ann-link { transform: translateX(3px); }
.ann-loading { display: flex; justify-content: center; padding: var(--s-lg); }
.ann-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-disabled); font-size: 14px; }
.scroll-sentinel { height: 1px; }
@media (max-width: 599px) {
  .ann-hero h1 { font-size: 22px; }
  .ann-card { padding: var(--s-sm) var(--s-base); }
}
</style>
