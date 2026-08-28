<template>
  <ResourceShareLanding
    :posts="posts"
    :total-count="totalCount"
    :loading="loading"
    :error="fetchError"
    @open="goPost"
  />
  <router-link v-if="auth.canPost" to="/forum/post/new?type=share" class="sf-fab" title="收录资源">＋</router-link>
  <div ref="sentinel" class="scroll-sentinel"></div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getPosts } from '@/api/post'
import ResourceShareLanding from '@/components/ResourceShareLanding.vue'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'

const SECTION = 'share'
const PAGE_SIZE = 12
const router = useRouter()
const sectionStore = useSectionStore()
const auth = useAuthStore()
const fetchError = ref('')
const loading = ref(false)
const posts = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const sentinel = ref(null)
let observer = null

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
    const data = (await getPosts(params))?.data || {}
    totalCount.value = data.count || 0
    const results = (data.results || []).map((post) => ({
      id: post.id,
      title: post.title,
      summary: post.summary || '',
      preview: post.content_preview || post.content || '',
      author: post.author?.nickname || `用户${post.author?.user_id || ''}`,
      votes: post.likes_count || 0,
      pinned: post.is_pinned
    }))
    if (page === 1) posts.value = results
    else posts.value.push(...results)
    currentPage.value = page
  } catch (error) {
    fetchError.value = error?.response?.data?.message || error?.message || '加载失败'
  } finally { loading.value = false }
}

function loadMore() { if (!loading.value && hasMore.value) fetchPosts(currentPage.value + 1) }
function goPost(post) { router.push(`/forum/post/${post.id}`) }

onMounted(async () => {
  await sectionStore.fetchSections()
  await fetchPosts()
  observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<style scoped>
.scroll-sentinel { height: 1px; }
.sf-fab { position: fixed; right: var(--s-xl); bottom: var(--s-xl); z-index: 40; display: grid; place-items: center; width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, #f6a34d, #e55b39); box-shadow: 0 12px 28px rgba(95,25,61,.42); color: #fffaf0; font-size: 32px; line-height: 1; text-decoration: none; transition: transform var(--t-fast); }
.sf-fab:hover { transform: scale(1.08) rotate(90deg); }
</style>
