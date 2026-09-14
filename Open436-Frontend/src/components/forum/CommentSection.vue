<template>
  <div class="card">
    <div class="card-header">评论 ({{ flatComments.length }})</div>
    <div v-if="canPost" class="comment-form">
      <div v-if="replyTo" class="reply-to-bar">
        回复 #{{ replyTo.floor }} {{ replyTo.author }}
        <button class="cancel-reply" @click="cancelReply">取消</button>
      </div>
      <textarea v-model="newComment" class="form-textarea" :placeholder="replyTo ? `回复 #${replyTo.floor}...` : '写下你的评论...'" rows="3"></textarea>
      <button class="btn btn-primary btn-sm" style="margin-top: var(--s-sm)" @click="submitComment" :disabled="commentLoading">
        {{ commentLoading ? '发送中...' : (replyTo ? '回复' : '发表评论') }}
      </button>
    </div>
    <div v-else class="guest-comment-tip">
      <span>登录后可发表评论</span>
    </div>
    <div class="comments-list">
      <template v-for="c in commentTree" :key="c.id">
        <div class="comment-item">
          <div class="comment-header">
            <img :src="c.avatar" :alt="c.author" class="avatar avatar-sm" />
            <span class="comment-author">{{ c.author }}</span>
            <span class="comment-floor">#{{ c.floor }}</span>
            <span class="comment-time">{{ formatDate(c.createdAt) }}</span>
          </div>
          <div class="comment-body">{{ c.content }}</div>
          <div class="comment-actions">
            <button v-if="canPost" class="comment-action-btn" :class="{ active: c.isLiked }" @click="handleReplyLike(c)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
              {{ c.likesCount || '' }}
            </button>
            <button v-if="canPost" class="comment-action-btn" @click="startReply(c)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              回复
            </button>
            <button v-if="c.canDelete" class="comment-action-btn danger" @click="handleDelete(c)">
              删除
            </button>
          </div>
        </div>
        <div v-for="child in c.threadReplies" :key="child.id" class="comment-item nested">
          <div class="comment-header">
            <img :src="child.avatar" :alt="child.author" class="avatar avatar-xs" />
            <span class="comment-author">{{ child.author }}</span>
            <span class="comment-time">{{ formatDate(child.createdAt) }}</span>
            <span v-if="child.replyToAuthor" class="reply-indicator">回复 @{{ child.replyToAuthor }}</span>
          </div>
          <div class="comment-body">{{ child.content }}</div>
          <div class="comment-actions">
            <button v-if="canPost" class="comment-action-btn" :class="{ active: child.isLiked }" @click="handleReplyLike(child)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
              {{ child.likesCount || '' }}
            </button>
            <button v-if="canPost" class="comment-action-btn" @click="startReply(child)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              回复
            </button>
            <button v-if="child.canDelete" class="comment-action-btn danger" @click="handleDelete(child)">
              删除
            </button>
          </div>
        </div>
      </template>
      <div v-if="flatComments.length === 0 && !commentLoading" class="empty-state" style="padding: var(--s-xl)">
        <p style="font-size: 13px">暂无评论，快来抢沙发吧</p>
      </div>
      <button v-if="hasMore" class="load-more-comments" :disabled="loadingMore" @click="loadMoreReplies">
        {{ loadingMore ? '加载中...' : '展开更多评论' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/format'
import { getReplies, createReply, deleteReply, toggleReplyLike } from '@/api/comment'

const props = defineProps({
  postId: { type: [String, Number], required: true },
  canPost: { type: Boolean, default: false }
})

const emit = defineEmits(['count-change'])

const ui = useUIStore()
const auth = useAuthStore()
const newComment = ref('')
const flatComments = ref([])
const commentTree = ref([])
const replyTo = ref(null)
const commentLoading = ref(false)
const loadingMore = ref(false)
const replyPage = ref(1)
const hasMore = ref(false)

async function fetchReplies(postId, page = 1, append = false) {
  try {
    const res = await getReplies(postId, { page, page_size: 50 })
    const data = res?.data || res || {}
    const results = data.results || []
    const mapped = results.map(r => ({
      id: r.id,
      parentId: r.parent_id,
      author: r.author?.real_name || r.author?.nickname || `用户${r.author?.user_id || ''}`,
      avatar: r.author?.avatar_url || '/app/user.jpg',
      content: r.content,
      floor: r.floor_number,
      createdAt: r.created_at,
      likesCount: r.likes_count || 0,
      isLiked: !!r.is_liked,
      canDelete: r.can_delete === true,
      threadReplies: []
    }))
    const combined = append ? [...flatComments.value, ...mapped] : mapped
    flatComments.value = combined
    replyPage.value = page
    hasMore.value = !!data.next
    buildCommentTree(combined)
    emit('count-change', Number(data.count ?? combined.length))
  } catch (e) {
    console.warn('Failed to fetch replies:', e)
    if (!append) {
      flatComments.value = []
      commentTree.value = []
    }
  }
}

function buildCommentTree(flat) {
  const map = {}
  const roots = []
  flat.forEach(c => {
    c.threadReplies = []
    c.replyToAuthor = ''
    map[c.id] = c
  })
  flat.forEach(comment => {
    const parent = map[comment.parentId]
    if (!parent) {
      roots.push(comment)
      return
    }
    comment.replyToAuthor = parent.author
    let root = parent
    const visited = new Set([comment.id])
    while (root.parentId && map[root.parentId] && !visited.has(root.parentId)) {
      visited.add(root.id)
      root = map[root.parentId]
    }
    root.threadReplies.push(comment)
  })
  commentTree.value = roots
}

async function loadMoreReplies() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  try {
    await fetchReplies(props.postId, replyPage.value + 1, true)
  } finally {
    loadingMore.value = false
  }
}

function startReply(comment) {
  replyTo.value = { id: comment.id, floor: comment.floor, author: comment.author }
}

function cancelReply() {
  replyTo.value = null
}

async function handleReplyLike(comment) {
  if (!auth.canPost) return
  try {
    const res = await toggleReplyLike(comment.id)
    const data = res?.data || {}
    if (data.is_liked !== undefined) comment.isLiked = data.is_liked
    if (data.likes_count !== undefined) comment.likesCount = data.likes_count
  } catch (e) {
    console.warn('Reply like failed:', e)
  }
}

async function handleDelete(comment) {
  if (!comment.canDelete || !window.confirm('确定删除这条评论吗？')) return
  try {
    await deleteReply(comment.id)
    ui.showToast('评论已删除', 'success')
    await fetchReplies(props.postId)
  } catch (e) {
    ui.showToast(e?.response?.data?.message || '删除评论失败', 'error')
  }
}

async function submitComment() {
  if (!newComment.value.trim()) { ui.showToast('请输入评论内容', 'warning'); return }
  commentLoading.value = true
  try {
    const isReply = !!replyTo.value
    const payload = { post_id: props.postId, content: newComment.value.trim() }
    if (replyTo.value) payload.parent_id = replyTo.value.id
    await createReply(payload)
    newComment.value = ''
    replyTo.value = null
    ui.showToast(isReply ? '回复成功' : '评论成功', 'success')
    await fetchReplies(props.postId)
  } catch (e) {
    const msg = e?.response?.data?.message || '评论失败'
    ui.showToast(msg, 'error')
  } finally {
    commentLoading.value = false
  }
}

onMounted(() => {
  if (props.postId) fetchReplies(props.postId)
})

watch(() => props.postId, (newId) => {
  if (newId) fetchReplies(newId)
})
</script>

<style scoped>
.comment-form { padding: var(--s-lg); border-bottom: 1px solid var(--divider); }
.comment-form .form-textarea {
  color: var(--text-primary);
  caret-color: var(--primary);
  font-size: 15px;
  font-weight: 500;
  line-height: 1.65;
  background: var(--bg);
  border-color: color-mix(in srgb, var(--text-secondary) 38%, transparent);
}
.comment-form .form-textarea::placeholder {
  color: var(--text-secondary);
  opacity: 0.9;
  font-weight: 400;
}
.comment-form .form-textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 16%, transparent);
}
.guest-comment-tip { padding: var(--s-lg); border-bottom: 1px solid var(--divider); text-align: center; color: var(--text-secondary); font-size: 13px; background: var(--bg-secondary); }
.comments-list { padding: var(--s-base) var(--s-lg); }
.comment-item { padding: var(--s-base) 0; border-bottom: 1px solid var(--divider); }
.comment-header { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-xs); }
.comment-author { font-size: 13px; font-weight: 500; }
.comment-floor { font-size: 11px; color: var(--primary); background: var(--primary-bg); padding: 1px 6px; border-radius: 999px; }
.comment-time { font-size: 12px; color: var(--text-secondary); }
.comment-body { font-size: 14px; line-height: 1.6; padding-left: 40px; }
.comment-item.nested { padding-left: 48px; background: var(--bg-secondary); border-radius: 0; }
.comment-item.nested .comment-body { padding-left: 36px; }
.comment-actions { display: flex; gap: var(--s-sm); padding-left: 40px; margin-top: var(--s-xs); }
.comment-item.nested .comment-actions { padding-left: 36px; }
.comment-action-btn {
  display: inline-flex; align-items: center; gap: 3px; font-size: 12px;
  color: var(--text-disabled); transition: color var(--t-fast);
}
.comment-action-btn:hover { color: var(--text-secondary); }
.comment-action-btn.active { color: var(--primary); }
.comment-action-btn.danger:hover { color: var(--error); }
.reply-indicator { font-size: 11px; color: var(--primary); opacity: 0.7; }
.reply-to-bar {
  display: flex; align-items: center; gap: var(--s-sm); font-size: 13px;
  color: var(--primary); margin-bottom: var(--s-sm); padding: var(--s-xs) var(--s-sm);
  background: var(--primary-bg); border-radius: var(--r-sm);
}
.cancel-reply { margin-left: auto; font-size: 12px; color: var(--text-secondary); cursor: pointer; }
.cancel-reply:hover { color: var(--error); }
.avatar-xs { width: 24px; height: 24px; border-radius: 50%; }
.empty-state { text-align: center; padding: var(--s-3xl); color: var(--text-secondary); }
.load-more-comments {
  display: block; margin: var(--s-base) auto 0; padding: 8px 18px;
  border-radius: 999px; color: var(--primary); background: var(--primary-bg);
  font-size: 13px; font-weight: 500;
}
.load-more-comments:disabled { opacity: .55; cursor: wait; }
</style>
