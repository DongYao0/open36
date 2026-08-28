import request from './request'

/** 前台聚合数据（预览用） */
export function getPublicHomepage() {
  return request.get('/api/users/homepage/public')
}

/** 管理端读取单模块，data 为 null 表示未配置（前台用默认值） */
export function getHomepageModule(module) {
  return request.get(`/api/users/homepage/admin/${module}`)
}

/** 全量保存单模块 */
export function saveHomepageModule(module, content) {
  return request.put(`/api/users/homepage/admin/${module}`, content)
}

/** 重置单模块（删行，前台回默认内容） */
export function resetHomepageModule(module) {
  return request.post(`/api/users/homepage/admin/${module}/reset`)
}
