import request from './request'

export function getUserList(params) {
  return request.get('/api/auth/users', { params })
}

export function createUser(data) {
  return request.post('/api/auth/users', data)
}

export function updateUserStatus(id, data) {
  return request.put(`/api/auth/users/${id}/status`, data)
}

export function updateUserRole(id, data) {
  return request.put(`/api/auth/users/${id}/role`, data)
}

export function resetPassword(id, data) {
  return request.put(`/api/auth/users/${id}/password`, data)
}

export function deleteUser(id) {
  return request.delete(`/api/auth/users/${id}`)
}

export function batchDeleteUsers(ids) {
  return request.delete('/api/auth/users/batch', { data: ids })
}

export function batchUpdateUserStatus(ids, data) {
  return request.put('/api/auth/users/batch/status', { ids, ...data })
}

export function updateUserPermission(id, data) {
  return request.put(`/api/auth/users/${id}/permission`, data)
}
