/**
 * 板块 API
 */
import request from './request'

export function getSections() {
  return request.get('/api/sections/')
}

export function getSection(idOrSlug) {
  return request.get(`/api/sections/${idOrSlug}/`)
}
