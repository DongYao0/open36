<template>
  <section class="search-page">
  <div class="sr-header">
    <div class="sr-header-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="22" height="22">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
    </div>
    <div class="sr-header-text">
      <span class="sr-kicker">OPEN436 KNOWLEDGE RADAR</span>
      <h1 class="sr-header-title">搜索论坛知识库</h1>
      <p class="sr-header-query">在技术交流与资源分享中定位真正有用的内容</p>
    </div>
  </div>

  <form class="sr-searchbox" @submit.prevent="submitSearch">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <input v-model="searchInput" placeholder="输入关键词，例如 Vue、算法、开源项目" aria-label="搜索论坛" />
    <button type="submit">开始搜索</button>
  </form>

  <!-- Section filter -->
  <div class="sr-filters">
    <button v-for="s in categoryFilters" :key="s.key" class="sr-chip" :class="{ active: activeSection === s.key }" @click="selectSection(s.key)">{{ s.name }}</button>
  </div>

  <!-- Results -->
  <div class="sr-list">
    <div
      v-for="(post, i) in results"
      :key="post.id"
      class="sr-item"
      :style="{ animationDelay: `${i * 50}ms` }"
      @click="router.push({ name: 'PostDetail', params: { id: post.id } })"
    >
      <div class="sr-item-icon" :style="{ background: getSectionColor(post.section) + '12', color: getSectionColor(post.section) }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="18" height="18">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      </div>
      <div class="sr-item-body">
        <div class="sr-item-meta">
          <span class="sr-item-section" :style="{ color: getSectionColor(post.section), background: getSectionColor(post.section) + '12' }">{{ getSectionName(post.section) }}</span>
          <span class="sr-item-author">u/{{ post.author }}</span>
          <span class="sr-dot">·</span>
          <span class="sr-item-time">{{ formatPostTime(post.createdAt) }}</span>
        </div>
        <h4 class="sr-item-title" v-html="highlight(post.title)"></h4>
        <p class="sr-item-preview" v-html="highlight(post.content)"></p>
      </div>
      <div class="sr-item-arrow">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="9 18 15 12 9 6"/></svg>
      </div>
    </div>
  </div>

  <div v-if="loading" class="sr-loading"><span class="spinner"></span></div>
  <div v-if="!loading && results.length === 0" class="sr-empty">
    <div class="sr-empty-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
    </div>
    <p>未找到相关结果</p>
    <div class="sr-suggestions">
      <span class="sr-suggest-label">试试搜索：</span>
      <button v-for="tag in suggestions" :key="tag" class="sr-suggest-tag" @click="router.push({ path: '/forum/search', query: { q: tag } })">{{ tag }}</button>
    </div>
  </div>
  <div v-if="!loading && total > 0" class="sr-pager">
    <span>共 {{ total }} 条结果</span>
    <Pagination v-model="page" :total-pages="totalPages" />
    <label>每页
      <select :value="pageSize" @change="changePageSize">
        <option v-for="size in pageSizes" :key="size" :value="size">{{ size }} 条</option>
      </select>
    </label>
  </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { formatPostTime, resolvePostAuthor } from '@/utils/format'
import { getPosts } from '@/api/post'
import Pagination from '@/components/Pagination.vue'

const route = useRoute()
const router = useRouter()
const sectionStore = useSectionStore()
const query = computed(() => route.query.q || '')
const activeSection = ref('all')
const loading = ref(false)
const searchInput = ref(query.value)
const page = ref(1)
const pageSize = ref(15)
const pageSizes = [15, 30, 45]
const total = ref(0)
const ready = ref(false)
const suggestions = ['Vue 3', 'TypeScript', '性能优化', 'Docker', 'CSS']
const results = ref([])
const categoryFilters = [
  { key: 'all', name: '全部' },
  { key: 'tech', name: '技术交流' },
  { key: 'share', name: '资源分享' },
]
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

async function doSearch(q) {
  if (!q) { results.value = []; total.value = 0; return }
  loading.value = true
  try {
    const params = { search: q, page: page.value, page_size: pageSize.value }
    const sectionId = sectionStore.getSectionId(activeSection.value)
    if (activeSection.value !== 'all' && sectionId) params.section_id = sectionId
    if (activeSection.value === 'all') {
      const sectionIds = ['tech', 'share'].map(key => sectionStore.getSectionId(key)).filter(Boolean)
      if (sectionIds.length) params.section_ids = sectionIds.join(',')
    }
    const res = await getPosts(params)
    const data = res?.data || {}
    total.value = data.count || 0
    results.value = (data.results || []).map(p => {
      const sec = sectionStore.getSectionById(p.section?.section_id)
      return {
        id: p.id, title: p.title || '', content: p.content_preview || p.content || '',
        author: resolvePostAuthor(p),
        section: sec?.key || '', createdAt: p.created_at
      }
    })
  } catch (e) { results.value = []; total.value = 0 }
  finally { loading.value = false }
}

function submitSearch() {
  const value = searchInput.value.trim()
  if (!value) return
  page.value = 1
  if (value === query.value) doSearch(value)
  else router.push({ path: '/forum/search', query: { q: value } })
}

function selectSection(key) { activeSection.value = key; page.value = 1 }
function changePageSize(event) { pageSize.value = Number(event.target.value); page.value = 1 }

function getSectionName(key) { return categoryFilters.find(section => section.key === key)?.name || '' }
function getSectionColor(key) { return key === 'share' ? '#f7c86b' : '#79e2f2' }

function highlight(text) {
  if (!text) return ''
  const safeText = String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  if (!query.value) return safeText
  const safeQuery = String(query.value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const escaped = safeQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return safeText.replace(new RegExp(`(${escaped})`, 'gi'), '<mark>$1</mark>')
}

onMounted(async () => {
  await sectionStore.fetchSections()
  ready.value = true
  if (query.value) doSearch(query.value)
})
watch(query, newQ => { searchInput.value = newQ; page.value = 1 })
watch([query, activeSection, page, pageSize], () => { if (ready.value) doSearch(query.value) })
</script>

<style scoped>
.search-page { min-height: calc(100vh - var(--navbar-h, 56px)); padding: clamp(34px, 6vw, 84px) clamp(18px, 7vw, 110px) 90px; color: #eef4ff; background: radial-gradient(circle at 12% 8%, rgba(38, 198, 218, .18), transparent 28%), radial-gradient(circle at 86% 4%, rgba(139, 92, 246, .22), transparent 32%), linear-gradient(145deg, #071126 0%, #0a1733 48%, #100d32 100%); }
.sr-header {
  display: flex; align-items: center; gap: var(--s-base);
  max-width: 1040px; padding: 0; margin: 0 auto 22px;
  background: transparent; border: 0;
}
.sr-header-icon {
  width: 58px; height: 58px; border-radius: 18px; flex-shrink: 0;
  background: linear-gradient(135deg, #6f63ed, #25c2d4); color: #fff;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255,255,255,.25); box-shadow: 0 12px 34px rgba(67,112,232,.28);
}
.sr-kicker { color: #79e2f2; font-size: 10px; font-weight: 800; letter-spacing: .16em; }
.sr-header-title { margin: 4px 0; color: #fff; font: 700 clamp(28px, 4vw, 48px)/1.1 var(--font-display); letter-spacing: -.035em; }
.sr-header-query { font-size: 13px; color: rgba(218,229,255,.62); }
.sr-searchbox { display: flex; align-items: center; gap: 12px; max-width: 1040px; margin: 0 auto 18px; padding: 8px 8px 8px 18px; border: 1px solid rgba(160,190,255,.25); border-radius: 16px; background: rgba(8,18,48,.72); box-shadow: 0 22px 60px rgba(0,0,0,.24); backdrop-filter: blur(16px); }
.sr-searchbox svg { width: 20px; flex: 0 0 auto; color: #7de3f2; }.sr-searchbox input { min-width: 0; flex: 1; border: 0; outline: 0; background: transparent; color: #fff; font: inherit; }.sr-searchbox input::placeholder { color: rgba(210,224,255,.42); }.sr-searchbox button { padding: 11px 19px; border: 0; border-radius: 10px; background: linear-gradient(135deg, #7667ec, #278fc2); color: #fff; font-weight: 700; cursor: pointer; }

.sr-filters { display: flex; gap: var(--s-sm); max-width: 1040px; flex-wrap: wrap; margin: 0 auto var(--s-lg); }
.sr-chip {
  padding: 7px 16px; border-radius: 999px; font-size: 13px; font-weight: 600;
  border: 1px solid rgba(160,190,255,.2); color: rgba(222,232,255,.72); background: rgba(255,255,255,.035); transition: all var(--t-fast);
}
.sr-chip:hover { border-color: #72dceb; color: #fff; }
.sr-chip.active { background: linear-gradient(135deg, #715edb, #237fae); color: #fff; border-color: #80ddeb; box-shadow: 0 8px 22px rgba(53,103,218,.22); }

.sr-list { display: flex; max-width: 1040px; margin: 0 auto; flex-direction: column; }
.sr-item {
  display: flex; align-items: center; gap: var(--s-base);
  background: linear-gradient(120deg, rgba(14,30,67,.88), rgba(23,23,67,.76)); border: 1px solid rgba(154,188,255,.17); border-radius: 15px;
  padding: var(--s-base) var(--s-lg); margin-bottom: var(--s-sm);
  cursor: pointer; transition: all var(--t-fast); animation: srFadeUp 350ms ease-out both;
}
.sr-item:hover { border-color: rgba(111,220,238,.68); box-shadow: 0 14px 34px rgba(0,0,0,.24); transform: translateY(-2px); }
.sr-item-icon {
  width: 40px; height: 40px; border-radius: var(--r-sm); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.sr-item-body { flex: 1; min-width: 0; }
.sr-item-meta { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-xs); }
.sr-item-section { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.sr-item-author { font-size: 12px; color: rgba(210,224,255,.72); }
.sr-dot { color: rgba(190,207,245,.38); font-size: 12px; }
.sr-item-time { font-size: 12px; color: rgba(190,207,245,.52); }
.sr-item-title { color: #f7f9ff; font-size: 16px; font-weight: 650; margin-bottom: var(--s-xs); line-height: 1.4; }
.sr-item-preview {
  font-size: 13px; color: rgba(207,220,250,.64); line-height: 1.6;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
:deep(mark) { background: rgba(253,211,92,.9); color: #18213b; padding: 0 2px; border-radius: 2px; }
.sr-item-arrow { color: rgba(190,207,245,.4); transition: transform var(--t-fast); flex-shrink: 0; }
.sr-item:hover .sr-item-arrow { transform: translateX(4px); color: var(--primary); }

.sr-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.sr-empty { max-width: 1040px; margin: 0 auto; text-align: center; padding: var(--s-3xl) var(--s-lg); color: rgba(211,224,255,.7); border: 1px dashed rgba(155,188,255,.22); border-radius: 18px; background: rgba(9,20,49,.48); }
.sr-empty-icon { color: #75dce9; margin-bottom: var(--s-base); opacity: 0.55; }
.sr-suggestions { margin-top: var(--s-base); }
.sr-suggest-label { font-size: 13px; color: rgba(211,224,255,.6); }
.sr-suggest-tag {
  display: inline-block; padding: 4px 12px; margin: var(--s-xs); border-radius: 999px;
  border: 1px solid var(--divider); font-size: 13px; color: var(--primary); transition: all var(--t-fast);
}
.sr-suggest-tag:hover { background: rgba(111,99,237,.18); border-color: #77dce9; }
.sr-pager { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 18px; max-width: 1040px; margin: 22px auto 0; padding: 12px 16px; border: 1px solid rgba(154,188,255,.18); border-radius: 14px; background: rgba(9,20,49,.68); color: rgba(211,224,255,.62); font-size: 12px; }
.sr-pager :deep(.pagination) { padding: 0; }.sr-pager :deep(.page-btn) { border-color: rgba(154,188,255,.25); background: #101e45; color: #dbe6ff; }.sr-pager :deep(.page-btn.active) { border-color: #77dce9; background: linear-gradient(135deg,#705eda,#258ab9); }.sr-pager label { justify-self: end; }.sr-pager select { margin-left: 8px; padding: 7px 9px; border: 1px solid rgba(154,188,255,.25); border-radius: 8px; background: #101e45; color: #fff; }
@media (max-width: 680px) { .search-page { padding: 28px 16px 70px; }.sr-header-icon { display: none; }.sr-searchbox button { padding-inline: 12px; }.sr-item-icon,.sr-item-arrow { display: none; }.sr-pager { grid-template-columns: 1fr auto; }.sr-pager :deep(.pagination) { grid-column: 1/-1; }.sr-item { padding: 15px; } }

@keyframes srFadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
