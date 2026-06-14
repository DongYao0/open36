/**
 * 评论/回复 API
 */
import request from './request'

export function getReplies(postId) {
  return request.get('/api/comments/replies/', { params: { post_id: postId } })
}

export function createReply(data) {
  return request.post('/api/comments/replies/', data)
}

export function toggleReplyLike(replyId) {
  return request.post(`/api/comments/replies/${replyId}/like/`)
}
