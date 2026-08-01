/**
 * 用户相关 API
 */
import request from './request'

/**
 * 获取当前登录用户信息
 */
export function getCurrentUser() {
  return request.get('/api/auth/current')
}

/**
 * 获取用户资料（公开）
 */
export function getUserProfile(userId) {
  return request.get(`/api/users/${userId}`)
}

/**
 * 更新用户资料
 */
export function updateUserProfile(userId, data) {
  return request.put(`/api/users/${userId}/profile`, data)
}

/**
 * 上传头像
 */
export function uploadAvatar(userId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/api/users/${userId}/avatar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 获取用户统计
 */
export function getUserStatistics(userId) {
  return request.get(`/api/users/${userId}/statistics`)
}

/**
 * 获取用户帖子列表
 */
export function getUserPosts(userId, params = {}) {
  return request.get(`/api/posts/`, { params: { ...params, author_id: userId } })
}

/**
 * 获取用户回复列表
 */
export function getUserReplies(userId, params = {}) {
  return request.get(`/api/comments/replies/`, { params: { ...params, user_id: userId } })
}

/**
 * 获取用户分享的资源
 */
export function getUserResources(userId, params = {}) {
  return request.get(`/api/resources/`, { params: { ...params, author_id: userId } })
}

/**
 * 获取当前用户被分配的作业列表
 */
export function getMyAssignments() {
  return request.get('/api/assignment/my')
}

/**
 * 获取作业详情
 */
export function getMyAssignmentDetail(assignmentId) {
  return request.get(`/api/assignment/my/${assignmentId}`)
}

/**
 * 提交作业
 */
export function submitAssignment(assignmentId, data) {
  return request.post(`/api/assignment/my/${assignmentId}/submit`, data)
}

/**
 * 修改密码
 */
export function changePassword(data) {
  return request.post('/api/auth/change-password', data)
}
