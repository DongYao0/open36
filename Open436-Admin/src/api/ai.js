import request from './request'
import { storage } from '@/utils/storage'

// AI service needs X-User-Id / X-User-Role headers (Kong gateway injection format)
function aiHeaders() {
  const user = storage.get('user') || {}
  return {
    'X-User-Id': String(user.id || ''),
    'X-User-Role': user.role || '',
  }
}

// Send chat message (synchronous - wait for full response)
export function sendChat(message, conversationId) {
  return request.post('/api/ai/chat', { message, conversation_id: conversationId }, { headers: aiHeaders(), timeout: 300000 })
}

// Send chat message (streaming - SSE)
// Returns an AbortController for cancellation
export function sendChatStream(message, conversationId, { onChunk, onDone, onError }) {
  const headers = {
    ...aiHeaders(),
    'Content-Type': 'application/json',
  }
  const token = storage.get('token')
  if (token) headers['token'] = token

  const controller = new AbortController()

  fetch('/api/ai/chat/stream', {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, conversation_id: conversationId }),
    signal: controller.signal,
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            onDone()
            return
          }
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() // 保留不完整的行
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') {
                onDone()
                return
              }
              try {
                const parsed = JSON.parse(data)
                onChunk(parsed)
              } catch {
                // 忽略解析错误
              }
            }
          }
          read()
        }).catch(err => {
          if (err.name !== 'AbortError') {
            onError(err)
          }
        })
      }
      read()
    })
    .catch(err => {
      if (err.name !== 'AbortError') {
        onError(err)
      }
    })

  return controller
}

// Stop streaming generation
export function stopChat(conversationId) {
  return request.post('/api/ai/chat/stop', { conversation_id: conversationId }, { headers: aiHeaders() })
}

// Upload file
export function uploadFile(file) {
  const headers = aiHeaders()
  const token = storage.get('token')
  if (token) headers['token'] = token

  const formData = new FormData()
  formData.append('file', file)

  return request.post('/api/ai/upload', formData, {
    headers: { ...headers, 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

// Get conversation list
export function getConversations(params) {
  return request.get('/api/ai/conversations', { params, headers: aiHeaders() })
}

// Get conversation detail (with message history)
export function getConversationDetail(conversationId) {
  return request.get(`/api/ai/conversations/${conversationId}`, { headers: aiHeaders() })
}

// Delete conversation
export function deleteConversation(conversationId) {
  return request.delete(`/api/ai/conversations/${conversationId}`, { headers: aiHeaders() })
}
