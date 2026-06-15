import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSections } from '@/api/section'

// 图标 fallback（API 没返回 icon 时用）
const ICON_MAP = {
  tech: 'mdi:code-tags',
  discuss: 'mdi:forum',
  question: 'mdi:help-circle',
  share: 'mdi:share-variant',
  announce: 'mdi:bullhorn',
}

export const useSectionStore = defineStore('section', () => {
  // 'all' 是虚拟的"全部"筛选项，不在数据库中
  const sections = ref([
    { key: 'all', name: '全部', icon: 'mdi:apps', color: '#757575', count: 0 }
  ])
  const activeSection = ref('all')
  const sectionIdMap = ref({})
  const idToSlugMap = ref({})

  function setActive(key) { activeSection.value = key }
  function getSection(key) { return sections.value.find(s => s.key === key) }
  function getSectionId(slug) { return sectionIdMap.value[slug] || null }
  function getSectionById(id) {
    const slug = idToSlugMap.value[id]
    return slug ? getSection(slug) : null
  }

  async function fetchSections() {
    try {
      const res = await getSections()
      const data = res?.results || res?.data?.results || res?.data || []

      // 保留 'all'，其余从 API 动态构建
      const allEntry = sections.value.find(s => s.key === 'all')
      const dynamicSections = data
        .filter(s => s.is_enabled !== false)
        .sort((a, b) => (a.sort_order || 999) - (b.sort_order || 999))
        .map(s => {
          sectionIdMap.value[s.slug] = s.id
          idToSlugMap.value[s.id] = s.slug
          return {
            key: s.slug,
            name: s.name,
            icon: ICON_MAP[s.slug] || 'mdi:tag',
            color: s.color || '#757575',
            count: s.posts_count || 0,
          }
        })

      sections.value = [allEntry, ...dynamicSections]
    } catch (e) {
      console.warn('Failed to fetch sections:', e)
    }
  }

  // 论坛板块 = 所有板块（含 'all'）
  const forumSections = computed(() => sections.value)

  return { sections, forumSections, activeSection, sectionIdMap, idToSlugMap, setActive, getSection, getSectionId, getSectionById, fetchSections }
})
