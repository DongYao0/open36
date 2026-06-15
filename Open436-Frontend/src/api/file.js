/**
 * 文件服务 API
 */
import request from './request'

/**
 * 上传文件
 * @param {File} file - 文件对象
 * @param {string} fileType - 文件类型: avatar | post | reply | section_icon
 * @returns {Promise<{file_id: string, url: string, filename: string}>}
 */
export function uploadFile(file, fileType) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('file_type', fileType)
  return request.post('/api/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000
  })
}
