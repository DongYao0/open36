<template>
  <div class="post-actions">
    <button v-if="canPost" class="action-btn" :class="{ active: liked }" :disabled="actionLoading.like" @click="handleLike">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
      {{ votes }}
    </button>
    <button v-if="canPost" class="action-btn" :class="{ active: favorited }" :disabled="actionLoading.favorite" @click="handleFavorite">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
      {{ favorited ? '已收藏' : '收藏' }}
    </button>
    <button class="action-btn" @click="shareRef.open(null, postId)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
      分享
    </button>
    <span v-if="!canPost" class="guest-tip">登录后可互动</span>
  </div>
  <ShareModal ref="shareRef" />
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { toggleLike, toggleFavorite, getInteractionStatus } from '@/api/interaction'
import ShareModal from '@/components/ShareModal.vue'

const props = defineProps({
  postId: { type: [String, Number], required: true },
  votes: { type: Number, default: 0 },
  canPost: { type: Boolean, default: false }
})

const emit = defineEmits(['update:votes'])

const ui = useUIStore()
const auth = useAuthStore()
const shareRef = ref(null)
const liked = ref(false)
const favorited = ref(false)
const actionLoading = ref({ like: false, favorite: false })

async function fetchInteractionStatus(postId) {
  try {
    const res = await getInteractionStatus(postId)
    const data = res?.data || res || {}
    liked.value = !!data.is_liked
    favorited.value = !!data.is_favorited
    if (data.likes_count !== undefined) {
      emit('update:votes', data.likes_count)
    }
  } catch (e) {
    console.warn('Failed to fetch interaction status:', e)
  }
}

async function handleLike() {
  if (!auth.canPost || actionLoading.value.like) return
  actionLoading.value.like = true
  try {
    const res = await toggleLike(props.postId)
    const data = res?.data || {}
    const msg = res?.message || ''
    if (data.is_liked !== undefined) {
      liked.value = data.is_liked
    }
    if (data.likes_count !== undefined) {
      emit('update:votes', data.likes_count)
    }
    ui.showToast(msg, liked.value ? 'success' : 'info')
  } catch (e) {
    const msg = e?.response?.data?.message || '操作失败'
    ui.showToast(msg, 'error')
  } finally {
    actionLoading.value.like = false
  }
}

async function handleFavorite() {
  if (!auth.canPost || actionLoading.value.favorite) return
  actionLoading.value.favorite = true
  try {
    const res = await toggleFavorite(props.postId)
    const data = res?.data || {}
    const msg = res?.message || ''
    if (data.is_favorited !== undefined) {
      favorited.value = data.is_favorited
    }
    ui.showToast(msg, favorited.value ? 'success' : 'info')
  } catch (e) {
    const msg = e?.response?.data?.message || '操作失败'
    ui.showToast(msg, 'error')
  } finally {
    actionLoading.value.favorite = false
  }
}

onMounted(() => {
  if (props.postId && props.canPost) fetchInteractionStatus(props.postId)
})

watch(() => props.postId, (newId) => {
  if (newId && props.canPost) fetchInteractionStatus(newId)
})
</script>

<style scoped>
.post-actions { display: flex; gap: var(--s-sm); border-top: 1px solid var(--divider); padding-top: var(--s-base); }
.action-btn {
  display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px;
  border-radius: var(--r-sm); font-size: 13px; color: var(--text-secondary);
  transition: all var(--t-fast);
}
.action-btn:hover { background: var(--bg-dark); }
.action-btn.active { color: var(--primary); font-weight: 500; }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.guest-tip { font-size: 12px; color: var(--warning); margin-left: auto; }
</style>
