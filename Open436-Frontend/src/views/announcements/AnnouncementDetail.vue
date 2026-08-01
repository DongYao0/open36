<template>
  <!-- Back nav -->
  <div class="ad-nav">
    <router-link to="/announcements" class="ad-back">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="15 18 9 12 15 6"/></svg>
      返回系统通知
    </router-link>
  </div>

  <div v-if="!post && !loading" class="card">
    <div class="ad-empty">
      <div class="ad-empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
      </div>
      <p>公告不存在或已被删除</p>
      <p v-if="fetchError" style="color: var(--error); font-size: 12px; margin-top: var(--s-sm)">{{ fetchError }}</p>
    </div>
  </div>
  <template v-if="post">
    <!-- Pinned banner -->
    <div v-if="post.pinned" class="ad-pinned-banner">
      <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
      <span>置顶公告</span>
    </div>
    <PostDetailContent :post="post">
      <template #actions>
        <InteractionBar
          :post-id="post.id"
          :votes="post.votes"
          :can-post="auth.canPost"
          @update:votes="post.votes = $event"
        />
      </template>
    </PostDetailContent>
    <CommentSection
      :post-id="post.id"
      :can-post="auth.canPost"
      style="margin-top: var(--s-base)"
    />
  </template>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'
import { getPost } from '@/api/post'
import PostDetailContent from '@/components/PostDetailContent.vue'
import CommentSection from '@/components/forum/CommentSection.vue'
import InteractionBar from '@/components/forum/InteractionBar.vue'

const route = useRoute()
const sectionStore = useSectionStore()
const auth = useAuthStore()
const loading = ref(false)
const post = ref(null)
const fetchError = ref('')

async function fetchPost(id) {
  loading.value = true
  fetchError.value = ''
  try {
    const res = await getPost(id)
    const raw = res?.data || res
    if (raw && raw.id) {
      const sec = sectionStore.getSectionById(raw.section?.section_id)
      post.value = {
        id: raw.id,
        title: raw.title || '',
        content: raw.content || '',
        author: raw.author?.nickname || `管理员`,
        section: sec?.name || '公告通知',
        votes: raw.likes_count || 0,
        createdAt: raw.created_at,
        pinned: raw.is_pinned
      }
    } else {
      post.value = null
    }
  } catch (e) {
    const status = e?.response?.status
    const msg = e?.response?.data?.message || e?.message || '请求失败'
    fetchError.value = `[${status || 'ERR'}] ${msg}`
    post.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  sectionStore.fetchSections()
  const id = route.params.id
  if (id) fetchPost(id)
})

watch(() => route.params.id, (newId) => {
  if (newId) fetchPost(newId)
})
</script>

<style scoped>
.ad-nav { margin-bottom: var(--s-base); }
.ad-back {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--text-secondary); font-weight: 500;
  padding: 6px 12px; border-radius: var(--r-sm);
  transition: all var(--t-fast);
}
.ad-back:hover { color: var(--primary); background: var(--primary-bg); }
.ad-pinned-banner {
  display: flex; align-items: center; gap: var(--s-sm);
  padding: var(--s-sm) var(--s-base); margin-bottom: var(--s-sm);
  background: var(--primary-bg); border-radius: var(--r-sm);
  color: var(--primary); font-size: 13px; font-weight: 500;
  border-left: 3px solid var(--primary);
}
.ad-empty { text-align: center; padding: var(--s-3xl); color: var(--text-secondary); }
.ad-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
</style>
