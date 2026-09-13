import request from './request'

export function uploadFile(formData) {
  return request.post('/api/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000  // 10MB 大文件上传预留
  })
}

export function getFileInfo(id) {
  return request.get(`/api/files/${id}`)
}

export function deleteFile(id) {
  return request.delete(`/api/files/${id}`)
}
