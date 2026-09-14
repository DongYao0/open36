/**
 * 评论/回复 API
 */
import request from './request'

export function getReplies(postId, params = {}) {
  return request.get('/api/comments/replies/', { params: { ...params, post_id: postId } })
}

export function createReply(data) {
  return request.post('/api/comments/replies/', data)
}

export function toggleReplyLike(replyId) {
  return request.post(`/api/comments/replies/${replyId}/like/`)
}

export function deleteReply(replyId) {
  return request.delete(`/api/comments/replies/${replyId}/`)
}
