import request from './request'

export function getInterviewList(params) {
  return request.get('/api/interview/', { params })
}

export function recordInterview(data) {
  return request.post('/api/interview/record', data)
}

export function updateInterviewStatus(id, status) {
  return request.put(`/api/interview/${id}/status`, { status })
}

export function getInterviewDetail(enrollmentId) {
  return request.get(`/api/interview/${enrollmentId}`)
}

export function getInterviewStatistics() {
  return request.get('/api/interview/statistics')
}
