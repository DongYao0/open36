import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSections } from '@/api/section'

const SECTION_DEFAULTS = [
  { key: 'all', name: '全部', icon: 'mdi:apps', color: '#757575', count: 0 },
  { key: 'tech', name: '技术交流', icon: 'mdi:code-tags', color: '#1976D2', count: 0 },
  { key: 'design', name: '设计分享', icon: 'mdi:palette', color: '#FF6F00', count: 0 },
  { key: 'share', name: '资源分享', icon: 'mdi:share-variant', color: '#FF9800', count: 0 },
  { key: 'announce', name: '公告通知', icon: 'mdi:bullhorn', color: '#F44336', count: 0 }
]

export const useSectionStore = defineStore('section', () => {
  const sections = ref(SECTION_DEFAULTS)
  const activeSection = ref('all')
  // slug → 数据库 section_id
  const sectionIdMap = ref({})
  // section_id → slug 反向映射
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
      data.forEach(s => {
        sectionIdMap.value[s.slug] = s.id
        idToSlugMap.value[s.id] = s.slug
        const local = sections.value.find(ls => ls.key === s.slug)
        if (local) {
          local.count = s.posts_count || 0
          local.name = s.name || local.name
        }
      })
    } catch (e) {
      console.warn('Failed to fetch sections:', e)
    }
  }

  const forumSections = computed(() => sections.value.filter(s => ['all', 'tech', 'design'].includes(s.key)))

  return { sections, forumSections, activeSection, sectionIdMap, idToSlugMap, setActive, getSection, getSectionId, getSectionById, fetchSections }
})
