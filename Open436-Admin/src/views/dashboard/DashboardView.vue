<template>
  <div class="dashboard">
    <el-card shadow="hover" class="client-address-card">
      <div class="client-address-row">
        <div class="client-address-info">
          <div class="client-address-title">
            <el-icon><Link /></el-icon>
            客户端访问地址
            <el-tag v-if="clientUrl" size="small" type="success">在线</el-tag>
            <el-tag v-else size="small" type="warning">等待隧道</el-tag>
          </div>
          <a v-if="clientUrl" :href="clientUrl" target="_blank" rel="noopener noreferrer">
            {{ clientUrl }}
          </a>
          <span v-else class="client-address-empty">正在获取 Cloudflare 随机地址…</span>
          <div class="client-address-time">{{ clientAddressHint }}</div>
        </div>
        <div class="client-address-actions">
          <el-button :loading="clientUrlLoading" @click="loadClientUrl">刷新</el-button>
          <el-button :disabled="!clientUrl" @click="copyClientUrl">复制</el-button>
          <el-button type="primary" :disabled="!clientUrl" @click="openClient">打开客户端</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <StatCard label="用户总数" :value="1248" icon="User" icon-bg="#e3f2fd" icon-color="#1976D2" :change="12" />
      </el-col>
      <el-col :span="6">
        <StatCard label="帖子总数" :value="3456" icon="Document" icon-bg="#e8f5e9" icon-color="#4caf50" :change="8" />
      </el-col>
      <el-col :span="6">
        <StatCard label="今日活跃" :value="342" icon="TrendCharts" icon-bg="#fff3e0" icon-color="#ff9800" :change="5" />
      </el-col>
      <el-col :span="6">
        <StatCard label="今日新增" :value="28" icon="Plus" icon-bg="#f3e5f5" icon-color="#9c27b0" :change="15" />
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header><span class="card-title">最近帖子</span></template>
          <el-table :data="recentPosts" stripe size="small">
            <el-table-column prop="title" label="标题" min-width="200" />
            <el-table-column prop="author" label="作者" width="120" />
            <el-table-column prop="time" label="时间" width="140" />
            <el-table-column label="操作" width="80">
              <template #default>
                <el-button type="primary" link size="small">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span class="card-title">快捷操作</span></template>
          <div class="quick-actions">
            <el-button @click="$router.push('/users')" class="action-btn">
              <el-icon><User /></el-icon>用户管理
            </el-button>
            <el-button @click="openHojAdmin" class="action-btn">
              <el-icon><EditPen /></el-icon>算法管理
            </el-button>
            <el-button @click="$router.push('/forum')" class="action-btn">
              <el-icon><ChatDotRound /></el-icon>论坛管理
            </el-button>
            <el-button @click="$router.push('/enrollment')" class="action-btn">
              <el-icon><UserFilled /></el-icon>纳新管理
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import StatCard from '@/components/StatCard.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const openHojAdmin = () => authStore.openHojAdmin()

const clientUrl = ref('')
const clientUrlLoading = ref(false)
const clientAddressHint = ref('地址会在隧道启动后自动更新')
let clientUrlTimer

async function loadClientUrl() {
  clientUrlLoading.value = true
  try {
    const response = await fetch(`/runtime/client-url.json?t=${Date.now()}`, { cache: 'no-store' })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    const parsed = data.url ? new URL(data.url) : null
    if (parsed && !['http:', 'https:'].includes(parsed.protocol)) throw new Error('invalid protocol')
    clientUrl.value = parsed ? parsed.href.replace(/\/$/, '') : ''
    clientAddressHint.value = data.status === 'starting'
      ? '隧道正在启动，页面将每 15 秒自动刷新'
      : `更新于 ${data.updatedAt ? new Date(data.updatedAt).toLocaleString() : '刚刚'}`
  } catch (_error) {
    clientAddressHint.value = clientUrl.value
      ? '自动刷新暂时失败，当前仍显示上一次可用地址'
      : '尚未检测到地址，请确认 Cloudflare Tunnel 已启动'
  } finally {
    clientUrlLoading.value = false
  }
}

async function copyClientUrl() {
  if (!clientUrl.value) return
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(clientUrl.value)
    } else {
      const input = document.createElement('textarea')
      input.value = clientUrl.value
      input.style.position = 'fixed'
      input.style.opacity = '0'
      document.body.appendChild(input)
      input.select()
      document.execCommand('copy')
      input.remove()
    }
    ElMessage.success('客户端地址已复制')
  } catch (_error) {
    ElMessage.error('复制失败，请手动选择地址')
  }
}

function openClient() {
  if (clientUrl.value) window.open(clientUrl.value, '_blank', 'noopener,noreferrer')
}

onMounted(() => {
  loadClientUrl()
  clientUrlTimer = window.setInterval(loadClientUrl, 15000)
})

onBeforeUnmount(() => window.clearInterval(clientUrlTimer))

const recentPosts = ref([
  { title: 'Vue 3 Composition API 最佳实践', author: '张三', time: '5 分钟前' },
  { title: 'Spring Boot 微服务架构分享', author: '李四', time: '12 分钟前' },
  { title: 'Docker 容器化部署指南', author: '王五', time: '30 分钟前' },
  { title: 'Rust 所有权系统详解', author: '赵六', time: '1 小时前' },
  { title: 'PostgreSQL 性能优化技巧', author: '孙七', time: '2 小时前' }
])
</script>

<style lang="scss" scoped>
.client-address-card { margin-bottom: 20px; }
.client-address-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.client-address-info { min-width: 0; }
.client-address-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 600;
}
.client-address-info a {
  color: var(--el-color-primary);
  font-size: 16px;
  overflow-wrap: anywhere;
}
.client-address-empty, .client-address-time { color: var(--el-text-color-secondary); }
.client-address-time { margin-top: 7px; font-size: 12px; }
.client-address-actions { display: flex; flex-shrink: 0; }
.stat-row { margin-bottom: 20px; }
.card-title { font-weight: 600; font-size: 16px; }
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.action-btn {
  width: 100%;
  justify-content: flex-start;
  height: 44px;
}
@media (max-width: 900px) {
  .client-address-row { align-items: flex-start; flex-direction: column; }
  .client-address-actions { width: 100%; }
}
</style>
