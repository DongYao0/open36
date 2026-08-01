<template>
  <!-- Back nav -->
  <div class="pd-nav">
    <router-link :to="post && post.sectionKey ? `/forum/${post.sectionKey}` : '/forum/tech'" class="pd-back">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="15 18 9 12 15 6"/></svg>
      返回论坛
    </router-link>
  </div>

  <div v-if="!post && !loading" class="card">
    <div class="pd-empty">
      <div class="pd-empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <p>帖子不存在或已被删除</p>
      <p v-if="fetchError" style="color: var(--error); font-size: 12px; margin-top: var(--s-sm)">{{ fetchError }}</p>
      <p style="color: var(--text-disabled); font-size: 12px; margin-top: var(--s-xs)">ID: {{ route.params.id }}</p>
    </div>
  </div>
  <template v-if="post">
    <div class="pd-accent"></div>
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
        id: raw.id, title: raw.title || '', content: raw.content || '',
        author: raw.author?.nickname || `用户${raw.author?.user_id || ''}`,
        section: sec?.name || '未知板块',
        sectionKey: sec?.key || '',
        votes: raw.likes_count || 0, createdAt: raw.created_at
      }
    } else { post.value = null }
  } catch (e) {
    fetchError.value = `[${e?.response?.status || 'ERR'}] ${e?.response?.data?.message || e?.message || '请求失败'}`
    post.value = null
  } finally { loading.value = false }
}

onMounted(() => { sectionStore.fetchSections(); const id = route.params.id; if (id) fetchPost(id) })
watch(() => route.params.id, (newId) => { if (newId) fetchPost(newId) })
</script>

<style scoped>
.pd-nav { margin-bottom: var(--s-base); }
.pd-back {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--text-secondary); font-weight: 500;
  padding: 6px 12px; border-radius: var(--r-sm); transition: all var(--t-fast);
}
.pd-back:hover { color: var(--primary); background: var(--primary-bg); }
.pd-accent {
  height: 3px; border-radius: 2px; margin-bottom: var(--s-base);
  background: linear-gradient(90deg, var(--primary), var(--primary-light), #64B5F6);
}
.pd-empty { text-align: center; padding: var(--s-3xl); color: var(--text-secondary); }
.pd-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
</style>
