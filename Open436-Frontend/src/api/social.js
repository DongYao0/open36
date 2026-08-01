/**
 * 社交 API（关注/话题）
 */
import request from './request'

// 用户关注
export function toggleFollow(userId) {
  return request.post(`/api/comments/follows/users/${userId}/toggle/`)
}

export function getFollowStatus(userId) {
  return request.get(`/api/comments/follows/users/${userId}/status/`)
}

export function getMyFollowing(params) {
  return request.get('/api/comments/follows/my-following/', { params })
}

export function getMyFollowers(params) {
  return request.get('/api/comments/follows/my-followers/', { params })
}

// 话题
export function getTopics(params) {
  return request.get('/api/comments/topics/', { params })
}

export function toggleTopicFollow(topicId) {
  return request.post(`/api/comments/topics/${topicId}/follow/`)
}

export function getTopicFollowStatus(topicId) {
  return request.get(`/api/comments/topics/${topicId}/follow-status/`)
}

export function getMyTopics() {
  return request.get('/api/comments/topics/my-topics/')
}
