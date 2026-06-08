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
          :key="conv.id"
          class="conv-item"
          :class="{ active: currentConvId === conv.id }"
          @click="selectConversation(conv.id)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="conv-title">{{ conv.title || '新对话' }}</span>
          <el-icon class="delete-btn" @click.stop="removeConversation(conv.id)"><Delete /></el-icon>
        </div>
        <el-empty v-if="conversations.length === 0" description="暂无会话" :image-size="60" />
      </div>
    </div>

    <!-- 右侧聊天区 -->
    <div class="chat-main">
      <div class="chat-header">
        <span>AI 智能助手</span>
        <el-tag v-if="currentConvId" size="small" type="info">会话 #{{ currentConvId }}</el-tag>
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
          <div class="bubble">
            <div class="content" v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>
        <div v-if="loading" class="message-row assistant">
          <div class="avatar"><el-icon><Monitor /></el-icon></div>
          <div class="bubble"><span class="typing">思考中...</span></div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
          @keydown="handleKeydown"
          :disabled="loading"
        />
        <el-button
          type="primary"
          :loading="loading"
          @click="send"
          :disabled="!input.trim()"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Plus, Delete, ChatDotRound, User, Monitor } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { sendChat, getConversations, getConversationDetail, deleteConversation } from '@/api/ai'

const input = ref('')
const loading = ref(false)
const messages = ref([])
const conversations = ref([])
const currentConvId = ref(null)
const messagesRef = ref(null)

// 简单 markdown 渲染（粗体、代码块、行内代码）
function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function loadConversations() {
  try {
    const res = await getConversations({ page: 1, page_size: 50 })
    conversations.value = res.data?.items || res.data || []
  } catch (e) {
    // AI 服务未启动时静默处理
  }
}

async function selectConversation(id) {
  currentConvId.value = id
  try {
    const res = await getConversationDetail(id)
    messages.value = res.data?.messages || []
    scrollToBottom()
  } catch (e) {
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
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (currentConvId.value === id) {
      currentConvId.value = null
      messages.value = []
    }
    ElMessage.success('已删除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return

  input.value = ''
  messages.value.push({ role: 'user', content: text })
  scrollToBottom()
  loading.value = true

  try {
    const res = await sendChat(text, currentConvId.value)
    const data = res.data
    messages.value.push({ role: 'assistant', content: data?.reply || data?.message || '无响应' })
    if (data?.conversation_id && !currentConvId.value) {
      currentConvId.value = data.conversation_id
      loadConversations()
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `错误: ${e.message}` })
  } finally {
    loading.value = false
    scrollToBottom()
  }
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

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  &.user {
    flex-direction: row-reverse;
    .bubble { background: #ecf5ff; color: #303133; }
    .avatar { background: #409eff; }
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
.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  :deep(pre) {
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    margin: 8px 0;
  }
  :deep(code) {
    background: #e8e8e8;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 13px;
  }
  :deep(pre code) {
    background: none;
    padding: 0;
  }
}
.typing {
  color: #909399;
  animation: blink 1s infinite;
}
@keyframes blink {
  50% { opacity: 0.4; }
}

.chat-input {
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 10px;
  align-items: flex-end;
  .el-input { flex: 1; }
}
</style>
