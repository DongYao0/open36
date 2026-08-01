import request from './request'

// ==================== 作业 CRUD ====================

export function getAssignmentList(params) {
  return request.get('/api/assignment/', { params })
}

export function getAssignmentStats() {
  return request.get('/api/assignment/statistics')
}

export function createAssignment(data) {
  return request.post('/api/assignment/', data)
}

export function deleteAssignment(id) {
  return request.delete(`/api/assignment/${id}`)
}

// ==================== 人员分配 ====================

export function getAssignmentMembers(id, params) {
  return request.get(`/api/assignment/${id}/members`, { params })
}

export function allocateStudents(id, data) {
  return request.post(`/api/assignment/${id}/allocate`, data)
}

export function removeAllocation(id, studentId) {
  return request.delete(`/api/assignment/${id}/allocate/${studentId}`)
}

export function batchRemoveAllocations(id, data) {
  return request.post(`/api/assignment/${id}/allocate/batch-remove`, data)
}

export function getStudentPool(id, params) {
  return request.get(`/api/assignment/${id}/students`, { params })
}

// ==================== 提交管理 ====================

export function getSubmissions(id, params) {
  return request.get(`/api/assignment/${id}/submissions`, { params })
}

export function getSubmissionDetail(submissionId) {
  return request.get(`/api/assignment/submissions/${submissionId}`)
}

export function sendReminder(submissionId) {
  return request.post(`/api/assignment/submissions/${submissionId}/remind`)
}
