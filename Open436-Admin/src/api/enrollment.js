import request from './request'

export function getApplicationList(params) {
  return request.get('/api/enrollment/', { params })
}

export function reviewApplication(id, data) {
  return request.put(`/api/enrollment/${id}/review`, data)
}

export function batchReview(data) {
  return request.post('/api/enrollment/batch-review', data)
}

export function getEnrollmentStatistics() {
  return request.get('/api/enrollment/statistics')
}
