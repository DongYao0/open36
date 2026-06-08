import request from './request'
import { storage } from '@/utils/storage'

// AI 服务需要 X-User-Id / X-User-Role 头（Kong 网关注入格式）
function aiHeaders() {
  const user = storage.get('user') || {}
  return {
    'X-User-Id': String(user.id || ''),
    'X-User-Role': user.role || '',
  }
}

// 发送聊天消息（AI 处理较慢，超时设为 120 秒）
export function sendChat(message, conversationId) {
  return request.post('/api/ai/chat', { message, conversation_id: conversationId }, { headers: aiHeaders(), timeout: 120000 })
}

// 获取会话列表
export function getConversations(params) {
  return request.get('/api/ai/conversations', { params, headers: aiHeaders() })
}

// 获取会话详情（含消息历史）
export function getConversationDetail(conversationId) {
  return request.get(`/api/ai/conversations/${conversationId}`, { headers: aiHeaders() })
}

// 删除会话
export function deleteConversation(conversationId) {
  return request.delete(`/api/ai/conversations/${conversationId}`, { headers: aiHeaders() })
}
