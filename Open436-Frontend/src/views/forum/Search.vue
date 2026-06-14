<template>
  <!-- Search Header -->
  <div class="sr-header">
    <div class="sr-header-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="22" height="22">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
    </div>
    <div class="sr-header-text">
      <h1 class="sr-header-title">搜索结果</h1>
      <p class="sr-header-query" v-if="query">关键词：<strong>{{ query }}</strong></p>
    </div>
  </div>

  <!-- Section filter -->
  <div class="sr-filters">
    <button class="sr-chip" :class="{ active: activeSection === 'all' }" @click="activeSection = 'all'">全部</button>
    <button v-for="s in sectionStore.forumSections.filter(s => s.key !== 'all')" :key="s.key" class="sr-chip" :class="{ active: activeSection === s.key }" @click="activeSection = s.key">{{ s.name }}</button>
  </div>

  <!-- Results -->
  <div class="sr-list">
    <div
      v-for="(post, i) in filteredResults"
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
          <span class="sr-item-time">{{ formatDate(post.createdAt) }}</span>
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
  <div v-if="!loading && filteredResults.length === 0" class="sr-empty">
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
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { formatDate } from '@/utils/format'
import { getPosts } from '@/api/post'

const route = useRoute()
const router = useRouter()
const sectionStore = useSectionStore()
const query = computed(() => route.query.q || '')
const activeSection = ref('all')
const loading = ref(false)
const suggestions = ['Vue 3', 'TypeScript', '性能优化', 'Docker', 'CSS']
const results = ref([])

const filteredResults = computed(() => {
  if (activeSection.value === 'all') return results.value
  return results.value.filter(p => p.section === activeSection.value)
})

async function doSearch(q) {
  if (!q) { results.value = []; return }
  loading.value = true
  try {
    const res = await getPosts({ search: q, page_size: 20 })
    const data = res?.data || {}
    results.value = (data.results || []).map(p => {
      const sec = sectionStore.getSectionById(p.section?.section_id)
      return {
        id: p.id, title: p.title || '', content: p.content_preview || p.content || '',
        author: p.author?.nickname || `用户${p.author?.user_id || ''}`,
        section: sec?.key || '', createdAt: p.created_at
      }
    })
  } catch (e) { results.value = [] }
  finally { loading.value = false }
}

function getSectionName(key) { return sectionStore.getSection(key)?.name || '' }
function getSectionColor(key) { return sectionStore.getSection(key)?.color || '#757575' }

function highlight(text) {
  if (!query.value || !text) return text
  const escaped = query.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark>$1</mark>')
}

onMounted(() => { sectionStore.fetchSections(); if (query.value) doSearch(query.value) })
watch(query, (newQ) => { if (newQ) doSearch(newQ) })
</script>

<style scoped>
.sr-header {
  display: flex; align-items: center; gap: var(--s-base);
  padding: var(--s-lg); margin-bottom: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
}
.sr-header-icon {
  width: 44px; height: 44px; border-radius: var(--r-md); flex-shrink: 0;
  background: var(--primary-bg); color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(25,118,210,0.15);
}
.sr-header-title { font-size: 20px; font-weight: 700; margin-bottom: 2px; }
.sr-header-query { font-size: 13px; color: var(--text-secondary); }
.sr-header-query strong { color: var(--primary); }

.sr-filters { display: flex; gap: var(--s-sm); flex-wrap: wrap; margin-bottom: var(--s-lg); }
.sr-chip {
  padding: 5px 14px; border-radius: 999px; font-size: 13px; font-weight: 500;
  border: 1px solid var(--divider); color: var(--text-secondary); transition: all var(--t-fast);
}
.sr-chip:hover { border-color: var(--primary); color: var(--primary); }
.sr-chip.active { background: var(--primary); color: #fff; border-color: var(--primary); }

.sr-list { display: flex; flex-direction: column; }
.sr-item {
  display: flex; align-items: center; gap: var(--s-base);
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  padding: var(--s-base) var(--s-lg); margin-bottom: var(--s-sm);
  cursor: pointer; transition: all var(--t-fast); animation: srFadeUp 350ms ease-out both;
}
.sr-item:hover { border-color: var(--primary); box-shadow: 0 4px 16px rgba(25,118,210,0.08); transform: translateY(-1px); }
.sr-item-icon {
  width: 40px; height: 40px; border-radius: var(--r-sm); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.sr-item-body { flex: 1; min-width: 0; }
.sr-item-meta { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-xs); }
.sr-item-section { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.sr-item-author { font-size: 12px; color: var(--text-secondary); }
.sr-dot { color: var(--text-disabled); font-size: 12px; }
.sr-item-time { font-size: 12px; color: var(--text-disabled); }
.sr-item-title { font-size: 15px; font-weight: 600; margin-bottom: var(--s-xs); line-height: 1.4; }
.sr-item-preview {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
:deep(mark) { background: #FFF176; padding: 0 2px; border-radius: 2px; }
.sr-item-arrow { color: var(--text-disabled); transition: transform var(--t-fast); flex-shrink: 0; }
.sr-item:hover .sr-item-arrow { transform: translateX(4px); color: var(--primary); }

.sr-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.sr-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-secondary); }
.sr-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
.sr-suggestions { margin-top: var(--s-base); }
.sr-suggest-label { font-size: 13px; color: var(--text-secondary); }
.sr-suggest-tag {
  display: inline-block; padding: 4px 12px; margin: var(--s-xs); border-radius: 999px;
  border: 1px solid var(--divider); font-size: 13px; color: var(--primary); transition: all var(--t-fast);
}
.sr-suggest-tag:hover { background: var(--primary-bg); border-color: var(--primary); }

@keyframes srFadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
