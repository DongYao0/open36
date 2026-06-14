<template>
  <div class="ai-chat">
    <!-- 左侧会话列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <span>会话列表</span>
        <el-button type="primary" size="small" @click="newConversation">
          <el-icon><Plus /></el-icon> 新会话
        </el-button>
      </div>
      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.conversation_id"
          class="conv-item"
          :class="{ active: currentConvId === conv.conversation_id }"
          @click="selectConversation(conv.conversation_id)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="conv-title">{{ conv.title || '新对话' }}</span>
          <el-icon class="delete-btn" @click.stop="removeConversation(conv.conversation_id)"><Delete /></el-icon>
        </div>
        <el-empty v-if="conversations.length === 0" description="暂无会话" :image-size="60" />
      </div>
    </div>

    <!-- 右侧聊天区 -->
    <div class="chat-main">
      <div class="chat-header">
        <span>AI 智能助手</span>
        <el-tag v-if="currentConvId" size="small" type="info">会话 #{{ currentConvId.slice(0, 8) }}</el-tag>
      </div>

      <div class="chat-messages" ref="messagesRef">
        <div v-if="messages.length === 0" class="empty-chat">
          <el-icon :size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
          <p>发送消息开始与 AI 对话</p>
        </div>
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="message-row"
          :class="msg.role"
        >
          <div class="avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><Monitor /></el-icon>
          </div>
          <div class="bubble-wrapper">
            <div class="bubble">
              <div class="content md-body" v-html="renderMarkdown(msg.content)"></div>
            </div>
            <!-- 操作按钮 -->
            <div class="msg-actions">
              <el-button text size="small" @click="copyMessage(msg)" title="复制">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
              <el-button
                v-if="msg.role === 'user'"
                text size="small"
                @click="retryMessage(msg)"
                title="重试"
              >
                <el-icon><RefreshRight /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        <!-- 流式输出中的消息 -->
        <div v-if="streaming" class="message-row assistant">
          <div class="avatar"><el-icon><Monitor /></el-icon></div>
          <div class="bubble-wrapper">
            <div class="bubble">
              <div class="content md-body" v-html="renderMarkdown(streamContent)"></div>
              <span class="typing-cursor"></span>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <div class="input-toolbar">
          <el-upload
            :show-file-list="false"
            :before-upload="handleFileSelect"
            accept=".pdf,.txt,.md,.csv,.json,.py,.js,.java,.c,.cpp"
          >
            <el-button text size="small" :disabled="streaming">
              <el-icon><Paperclip /></el-icon>
            </el-button>
          </el-upload>
          <span v-if="pendingFile" class="file-tag">
            {{ pendingFile.name }}
            <el-icon @click="pendingFile = null" class="file-remove"><Close /></el-icon>
          </span>
        </div>
        <div class="input-row">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
            @keydown="handleKeydown"
            :disabled="streaming"
          />
          <div class="input-buttons">
            <el-button
              v-if="streaming"
              type="danger"
              @click="handleStop"
            >
              <el-icon><VideoPause /></el-icon> 停止
            </el-button>
            <el-button
              v-else
              type="primary"
              @click="send"
              :disabled="!input.trim() && !pendingFile"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Plus, Delete, ChatDotRound, User, Monitor, CopyDocument, RefreshRight, Paperclip, Close, VideoPause } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import { sendChatStream, stopChat, getConversations, getConversationDetail, deleteConversation, uploadFile } from '@/api/ai'

// ============== Markdown 配置 ==============
marked.setOptions({
  breaks: true,
  gfm: true,
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(code, { language: lang }).value } catch {}
    }
    try { return hljs.highlightAuto(code).value } catch {}
    return code
  },
})

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

// ============== 状态 ==============
const input = ref('')
const streaming = ref(false)
const streamContent = ref('')
const messages = ref([])
const conversations = ref([])
const currentConvId = ref(null)
const messagesRef = ref(null)
const pendingFile = ref(null)
let abortController = null

// ============== 工具函数 ==============
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// ============== 会话管理 ==============
async function loadConversations() {
  try {
    const res = await getConversations({ page: 1, page_size: 50 })
    conversations.value = res.data?.results || res.data?.items || res.data || []
  } catch {}
}

async function selectConversation(id) {
  currentConvId.value = id
  try {
    const res = await getConversationDetail(id)
    messages.value = res.data?.messages || []
    scrollToBottom()
  } catch {
    messages.value = []
  }
}

function newConversation() {
  currentConvId.value = null
  messages.value = []
}

async function removeConversation(id) {
  try {
    await ElMessageBox.confirm('确定删除此会话？', '提示', { type: 'warning' })
    await deleteConversation(id)
    conversations.value = conversations.value.filter(c => c.conversation_id !== id)
    if (currentConvId.value === id) {
      currentConvId.value = null
      messages.value = []
    }
    ElMessage.success('已删除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// ============== 文件上传 ==============
function handleFileSelect(file) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过 10MB')
    return false
  }
  pendingFile.value = file
  return false // 阻止自动上传
}

// ============== 发送消息 ==============
function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

async function send() {
  const text = input.value.trim()
  if ((!text && !pendingFile.value) || streaming.value) return

  let fileContext = ''
  if (pendingFile.value) {
    try {
      const res = await uploadFile(pendingFile.value)
      fileContext = `\n\n[已上传文件: ${pendingFile.value.name}]\n${res.data?.text || ''}`
    } catch (e) {
      ElMessage.error('文件上传失败: ' + e.message)
    }
    pendingFile.value = null
  }

  const fullMessage = text + fileContext
  input.value = ''

  messages.value.push({ role: 'user', content: text || `[文件] ${pendingFile?.value?.name || '上传文件'}` })
  scrollToBottom()

  // 开始流式输出
  streaming.value = true
  streamContent.value = ''

  abortController = sendChatStream(fullMessage, currentConvId.value, {
    onChunk(chunk) {
      if (chunk.type === 'content') {
        streamContent.value += chunk.content
        scrollToBottom()
      } else if (chunk.type === 'meta') {
        // 保存 conversation_id，停止生成时需要
        if (chunk.conversation_id && !currentConvId.value) {
          currentConvId.value = chunk.conversation_id
        }
      } else if (chunk.type === 'done') {
        // 流结束，保存结果
        messages.value.push({ role: 'assistant', content: streamContent.value })
        if (chunk.conversation_id && !currentConvId.value) {
          currentConvId.value = chunk.conversation_id
          loadConversations()
        }
        streamContent.value = ''
        streaming.value = false
        scrollToBottom()
      } else if (chunk.type === 'stopped') {
        // 用户手动停止
        const stoppedContent = streamContent.value + (streamContent.value ? '\n\n_[已停止生成]_' : '_[已停止]_')
        messages.value.push({ role: 'assistant', content: stoppedContent })
        streamContent.value = ''
        streaming.value = false
        scrollToBottom()
      } else if (chunk.type === 'error') {
        messages.value.push({ role: 'assistant', content: `错误: ${chunk.message}` })
        streamContent.value = ''
        streaming.value = false
        scrollToBottom()
      }
    },
    onDone() {
      // 如果还没通过 chunk.type === 'done' 处理过
      if (streaming.value && streamContent.value) {
        messages.value.push({ role: 'assistant', content: streamContent.value })
        streamContent.value = ''
        streaming.value = false
        scrollToBottom()
      }
    },
    onError(err) {
      messages.value.push({ role: 'assistant', content: `请求失败: ${err.message}` })
      streamContent.value = ''
      streaming.value = false
      scrollToBottom()
    },
  })
}

// ============== 停止生成 ==============
async function handleStop() {
  console.log('[stop] clicked, currentConvId:', currentConvId.value, 'abortController:', abortController)
  // 先通知后端停止任务
  if (currentConvId.value) {
    try {
      const res = await stopChat(currentConvId.value)
      console.log('[stop] backend response:', res)
    } catch (e) {
      console.error('[stop] backend error:', e)
    }
  } else {
    console.warn('[stop] no conversation_id')
  }
  // 再中止前端 fetch 连接
  if (abortController) {
    abortController.abort()
    abortController = null
    console.log('[stop] fetch aborted')
  } else {
    console.warn('[stop] no abortController')
  }
  // 强制停止 streaming 状态
  streaming.value = false
  if (streamContent.value) {
    messages.value.push({ role: 'assistant', content: streamContent.value + '\n\n_[已停止生成]_' })
    streamContent.value = ''
  }
}

// ============== 复制/重试 ==============
function copyMessage(msg) {
  navigator.clipboard.writeText(msg.content).then(
    () => ElMessage.success('已复制'),
    () => ElMessage.error('复制失败')
  )
}

function retryMessage(msg) {
  input.value = msg.content
  send()
}

onMounted(loadConversations)
</script>

<style lang="scss" scoped>
.ai-chat {
  display: flex;
  height: calc(100vh - 60px);
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

// 左侧栏
.chat-sidebar {
  width: 260px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
}
.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background .2s;
  &:hover { background: #f5f7fa; }
  &.active { background: #ecf5ff; color: #409eff; }
}
.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}
.delete-btn {
  opacity: 0;
  transition: opacity .2s;
  color: #f56c6c;
  .conv-item:hover & { opacity: 1; }
}

// 右侧聊天区
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.empty-chat {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  p { margin-top: 12px; font-size: 14px; }
}

// 消息行
.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  &.user {
    flex-direction: row-reverse;
    .bubble { background: #ecf5ff; color: #303133; }
    .avatar { background: #409eff; }
    .msg-actions { justify-content: flex-start; }
  }
  &.assistant {
    .bubble { background: #f4f4f5; }
    .avatar { background: #909399; }
  }
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.bubble-wrapper {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}
.bubble {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  position: relative;
}
.msg-actions {
  display: flex;
  gap: 4px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity .2s;
  .message-row:hover & { opacity: 1; }
}

// 打字光标
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #409eff;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 1s infinite;
}
@keyframes cursor-blink {
  50% { opacity: 0; }
}

// 输入区
.chat-input {
  padding: 12px 20px;
  border-top: 1px solid #e4e7ed;
}
.input-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.file-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}
.file-remove {
  cursor: pointer;
  &:hover { color: #f56c6c; }
}
.input-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  .el-input { flex: 1; }
}
.input-buttons {
  display: flex;
  gap: 8px;
}

// Markdown 渲染样式
.md-body {
  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    margin: 12px 0 6px;
    font-weight: 600;
  }
  :deep(h1) { font-size: 1.4em; }
  :deep(h2) { font-size: 1.2em; }
  :deep(h3) { font-size: 1.1em; }
  :deep(p) { margin: 6px 0; }
  :deep(ul), :deep(ol) {
    padding-left: 20px;
    margin: 6px 0;
  }
  :deep(li) { margin: 2px 0; }
  :deep(blockquote) {
    border-left: 3px solid #dcdfe6;
    padding-left: 12px;
    color: #909399;
    margin: 8px 0;
  }
  :deep(table) {
    border-collapse: collapse;
    margin: 8px 0;
    th, td {
      border: 1px solid #e4e7ed;
      padding: 6px 10px;
      font-size: 13px;
    }
    th { background: #f5f7fa; }
  }
  :deep(pre) {
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 8px 0;
    position: relative;
  }
  :deep(code) {
    background: #e8e8e8;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 13px;
    font-family: 'Consolas', 'Monaco', monospace;
  }
  :deep(pre code) {
    background: none;
    padding: 0;
    color: inherit;
  }
  :deep(a) {
    color: #409eff;
    text-decoration: none;
    &:hover { text-decoration: underline; }
  }
  :deep(hr) {
    border: none;
    border-top: 1px solid #e4e7ed;
    margin: 12px 0;
  }
  :deep(img) {
    max-width: 100%;
    border-radius: 4px;
  }
}
</style>
