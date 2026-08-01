import request from './request'

export function getPosts(params) {
  return request.get('/api/posts/', { params })
}

export function deletePost(id) {
  return request.delete(`/api/posts/${id}/`)
}

export function restorePost(id) {
  return request.post(`/api/posts/${id}/restore/`)
}

export function pinPost(id, data) {
  return request.post(`/api/posts/${id}/pin/`, data)
}

export function unpinPost(id) {
  return request.post(`/api/posts/${id}/unpin/`)
}
