import request from './request'

export function getComments(params) {
  return request.get('/api/replies/', { params })
}

export function deleteComment(id) {
  return request.delete(`/api/replies/${id}/`)
}
