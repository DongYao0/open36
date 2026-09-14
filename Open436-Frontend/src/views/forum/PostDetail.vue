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
    <div v-if="post.canEdit || post.canDelete" class="pd-owner-actions">
      <router-link v-if="post.canEdit" :to="`/forum/post/${post.id}/edit`" class="pd-owner-btn">编辑帖子</router-link>
      <button v-if="post.canDelete" class="pd-owner-btn pd-owner-btn--danger" @click="removePost">删除帖子</button>
    </div>
    <ForumResourceDetail v-if="post.sectionKey === 'share'" :post="post" />
    <ForumTechDetail v-else :post="post" />
    <div class="pd-discussion">
      <div class="pd-actions">
        <InteractionBar
          :post-id="post.id"
          :votes="post.votes"
          :can-post="auth.canPost"
          @update:votes="post.votes = $event"
        />
      </div>
      <CommentSection
        :post-id="post.id"
        :can-post="auth.canPost"
      />
    </div>
  </template>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'
import { deletePost, getPost } from '@/api/post'
import { useUIStore } from '@/stores/ui'
import { resolvePostAuthor } from '@/utils/format'
import ForumResourceDetail from '@/components/ForumResourceDetail.vue'
import ForumTechDetail from '@/components/ForumTechDetail.vue'
import CommentSection from '@/components/forum/CommentSection.vue'
import InteractionBar from '@/components/forum/InteractionBar.vue'

const route = useRoute()
const router = useRouter()
const sectionStore = useSectionStore()
const auth = useAuthStore()
const ui = useUIStore()
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
        author: resolvePostAuthor(raw),
        section: sec?.name || '未知板块',
        sectionKey: sec?.key || '',
        votes: raw.likes_count || 0, createdAt: raw.created_at,
        canEdit: raw.can_edit === true, canDelete: raw.can_delete === true
      }
    } else { post.value = null }
  } catch (e) {
    fetchError.value = `[${e?.response?.status || 'ERR'}] ${e?.response?.data?.message || e?.message || '请求失败'}`
    post.value = null
  } finally { loading.value = false }
}

async function removePost() {
  if (!post.value?.canDelete || !window.confirm('确定删除这篇帖子吗？删除后普通用户将无法查看。')) return
  try {
    await deletePost(post.value.id)
    ui.showToast('帖子已删除', 'success')
    router.push('/mine')
  } catch (e) {
    ui.showToast(e?.response?.data?.message || '删除失败，请稍后重试', 'error')
  }
}

onMounted(async () => {
  await sectionStore.fetchSections()
  const id = route.params.id
  if (id) fetchPost(id)
})
watch(() => route.params.id, (newId) => { if (newId) fetchPost(newId) })
</script>

<style scoped>
.pd-nav { margin-bottom: var(--s-base); }
.pd-owner-actions{display:flex;justify-content:flex-end;gap:8px;width:min(1180px,100%);margin:0 auto 12px}.pd-owner-btn{padding:7px 14px;border:1px solid var(--divider);border-radius:8px;background:var(--bg);color:var(--text-secondary);font-size:13px;cursor:pointer}.pd-owner-btn:hover{border-color:var(--primary);color:var(--primary)}.pd-owner-btn--danger:hover{border-color:var(--error);color:var(--error)}
.pd-back {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--text-secondary); font-weight: 500;
  padding: 6px 12px; border-radius: var(--r-sm); transition: all var(--t-fast);
}
.pd-back:hover { color: var(--primary); background: var(--primary-bg); }
.pd-discussion { width: min(916px, calc(100% - 230px)); margin: var(--s-base) 0 0 max(0px, calc((100% - 1180px) / 2)); }
.pd-actions { padding: 0 var(--s-sm); }
@media (max-width: 840px) { .pd-discussion { width: 100%; } }
.pd-empty { text-align: center; padding: var(--s-3xl); color: var(--text-secondary); }
.pd-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
</style>
