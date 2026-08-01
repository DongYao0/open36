/**
 * 帖子互动 API（点赞/收藏/分享）
 */
import request from './request'

export function toggleLike(postId) {
  return request.post(`/api/comments/posts/${postId}/like/`)
}

export function toggleFavorite(postId) {
  return request.post(`/api/comments/posts/${postId}/favorite/`)
}

export function getInteractionStatus(postId) {
  return request.get(`/api/comments/posts/${postId}/interaction-status/`)
}

export function getMyFavorites(params) {
  return request.get('/api/comments/favorites/', { params })
}

export function recordShare(postId, shareType) {
  return request.post(`/api/comments/posts/${postId}/share/`, { share_type: shareType })
}

export function getShareCount(postId) {
  return request.get(`/api/comments/posts/${postId}/share-count/`)
}
