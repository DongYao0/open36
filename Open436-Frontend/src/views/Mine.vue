<template>
  <AppNavbar />
  <div class="page-mount">
    <!-- 未登录 -->
    <div v-if="!auth.isLoggedIn" class="guest-scene">
      <div class="guest-content">
        <div class="guest-icon">
          <svg viewBox="0 0 200 200" fill="none">
            <circle cx="100" cy="100" r="85" fill="rgba(25,118,210,0.04)"/>
            <circle cx="100" cy="78" r="28" fill="rgba(25,118,210,0.08)" stroke="var(--primary)" stroke-width="1.5" stroke-dasharray="4 3"/>
            <circle cx="100" cy="78" r="14" fill="var(--primary-bg)"/>
            <path d="M60 156a40 40 0 0 1 80 0" fill="rgba(25,118,210,0.06)" stroke="var(--primary)" stroke-width="1.5" stroke-dasharray="4 3"/>
          </svg>
        </div>
        <h2>个人中心</h2>
        <p>登录后查看个人信息、学习记录与更多内容</p>
        <router-link to="/login" class="btn-login">立即登录</router-link>
      </div>
    </div>

    <!-- 已登录 -->
    <div v-else class="mine-container">
      <!-- 顶部个人信息卡 -->
      <div class="profile-card">
        <div class="profile-header">
          <div class="avatar-section">
            <img :src="profile.avatarUrl || defaultAvatar" class="avatar-large" />
            <div class="avatar-badge" :class="auth.user?.status">
              {{ statusText }}
            </div>
          </div>
          <div class="info-section">
            <h1 class="nickname">{{ profile.nickname || auth.user?.username }}</h1>
            <p class="username">@{{ auth.user?.username }}</p>
            <p class="bio" v-if="profile.bio">{{ profile.bio }}</p>
            <p class="bio placeholder" v-else>这个人很懒，什么都没有留下...</p>
            <div class="meta-row">
              <span class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                加入于 {{ formatDate(profile.createdAt) }}
              </span>
              <span class="meta-item" v-if="auth.user?.major">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
                {{ auth.user.major }}
              </span>
            </div>
          </div>
          <div class="action-section">
            <router-link to="/mine/edit" class="btn-edit">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              编辑资料
            </router-link>
          </div>
        </div>

        <!-- 统计数据 -->
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-value">{{ stats.postsCount || 0 }}</span>
            <span class="stat-label">帖子</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.repliesCount || 0 }}</span>
            <span class="stat-label">回复</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.likesReceived || 0 }}</span>
            <span class="stat-label">获赞</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.favoritesReceived || 0 }}</span>
            <span class="stat-label">收藏</span>
          </div>
        </div>
      </div>

      <!-- 审核状态提示 -->
      <div v-if="auth.user?.status === 'pending'" class="pending-banner">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>你的报名正在审核中，审核通过后可解锁更多功能</span>
      </div>

      <!-- 作业提醒 -->
      <div v-if="assignments.length > 0" class="section-card assignments-section">
        <div class="section-header">
          <h3>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            作业提醒
          </h3>
          <span class="badge">{{ assignments.length }}</span>
        </div>
        <div class="assignment-list">
          <div
            v-for="item in assignments"
            :key="item.id"
            class="assignment-item"
            :class="{ unread: !item.read }"
            @click="readAssignment(item)"
          >
            <div class="assignment-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
            </div>
            <div class="assignment-content">
              <div class="assignment-title">{{ item.title }}</div>
              <div class="assignment-desc">{{ item.description }}</div>
              <div class="assignment-meta">
                <span class="assignment-time">{{ formatDate(item.assignedAt) }}</span>
                <span v-if="item.deadline" class="assignment-deadline">截止: {{ formatDate(item.deadline) }}</span>
                <span v-if="item.submissionStatus === 'submitted'" class="assignment-status submitted">已提交</span>
                <span v-else class="assignment-status pending">待提交</span>
              </div>
            </div>
            <div v-if="item.submissionStatus !== 'submitted'" class="unread-dot"></div>
          </div>
        </div>
      </div>

      <!-- 内容Tab区 -->
      <div class="section-card content-section">
        <div class="tabs-header">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-btn"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
        <div class="tabs-content">
          <!-- 我的帖子 -->
          <div v-if="activeTab === 'posts'" class="tab-pane">
            <div v-if="loading.posts" class="loading-state">加载中...</div>
            <div v-else-if="posts.length === 0" class="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <p>还没有发布过帖子</p>
              <router-link to="/forum/post/new" class="link-btn">去发帖</router-link>
            </div>
            <div v-else class="post-list">
              <div v-for="post in posts" :key="post.id" class="post-item" @click="$router.push(`/forum/post/${post.id}`)">
                <div class="post-title">{{ post.title }}</div>
                <div class="post-meta">
                  <span>{{ formatDate(post.createdAt) }}</span>
                  <span>浏览 {{ post.viewCount || 0 }}</span>
                  <span>回复 {{ post.commentCount || 0 }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 我的回复 -->
          <div v-if="activeTab === 'replies'" class="tab-pane">
            <div v-if="loading.replies" class="loading-state">加载中...</div>
            <div v-else-if="replies.length === 0" class="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              <p>还没有发表过回复</p>
              <router-link to="/forum/tech" class="link-btn">去看看</router-link>
            </div>
            <div v-else class="post-list">
              <div v-for="reply in replies" :key="reply.id" class="post-item" @click="$router.push(`/forum/post/${reply.postId}`)">
                <div class="post-title">回复: {{ reply.postTitle }}</div>
                <div class="reply-content">{{ reply.content }}</div>
                <div class="post-meta">
                  <span>{{ formatDate(reply.createdAt) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 我的资源 -->
          <div v-if="activeTab === 'resources'" class="tab-pane">
            <div v-if="loading.resources" class="loading-state">加载中...</div>
            <div v-else-if="resources.length === 0" class="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              <p>还没有分享过资源</p>
              <router-link to="/resources/new" class="link-btn">去分享</router-link>
            </div>
            <div v-else class="post-list">
              <div v-for="res in resources" :key="res.id" class="post-item" @click="$router.push(`/resources/${res.id}`)">
                <div class="post-title">{{ res.title }}</div>
                <div class="post-meta">
                  <span>{{ formatDate(res.createdAt) }}</span>
                  <span>下载 {{ res.downloadCount || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="quick-links">
        <router-link to="/forum/favorites" class="quick-link-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
          <span>我的收藏</span>
        </router-link>
        <router-link to="/mine/edit" class="quick-link-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <span>账号设置</span>
        </router-link>
        <a href="javascript:void(0)" @click="goToAlgo" class="quick-link-item">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
          <span>算法平台</span>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppNavbar from '@/components/AppNavbar.vue'
import { useAuthStore } from '@/stores/auth'
import { getUserProfile, getUserStatistics, getUserPosts, getUserReplies, getUserResources, getMyAssignments } from '@/api/user'

const router = useRouter()
const auth = useAuthStore()

const defaultAvatar = 'https://ui-avatars.com/api/?name=User&background=1976D2&color=fff&size=120'

const profile = ref({})
const stats = ref({})
const posts = ref([])
const replies = ref([])
const resources = ref([])
const assignments = ref([])
const activeTab = ref('posts')

const loading = reactive({
  profile: false,
  posts: false,
  replies: false,
  resources: false,
  assignments: false
})

const tabs = [
  { key: 'posts', label: '我的帖子' },
  { key: 'replies', label: '我的回复' },
  { key: 'resources', label: '我的资源' }
]

const statusText = computed(() => {
  const map = { active: '正式成员', pending: '待审核', admin: '管理员' }
  return map[auth.user?.status] || '成员'
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function loadProfile() {
  if (!auth.user?.id) return
  loading.profile = true
  try {
    const [profileRes, statsRes] = await Promise.all([
      getUserProfile(auth.user.id),
      getUserStatistics(auth.user.id)
    ])
    if (profileRes.code === 200) profile.value = profileRes.data || {}
    if (statsRes.code === 200) stats.value = statsRes.data || {}
  } catch (e) {
    console.error('加载资料失败:', e)
  } finally {
    loading.profile = false
  }
}

async function loadPosts() {
  if (!auth.user?.id) return
  loading.posts = true
  try {
    const res = await getUserPosts(auth.user.id, { page: 1, size: 20 })
    const data = res.data
    // 确保是数组
    if (Array.isArray(data)) {
      posts.value = data
    } else if (data && Array.isArray(data.list)) {
      posts.value = data.list
    } else {
      posts.value = []
    }
  } catch (e) {
    console.error('加载帖子失败:', e)
    posts.value = []
  } finally {
    loading.posts = false
  }
}

async function loadReplies() {
  if (!auth.user?.id) return
  loading.replies = true
  try {
    const res = await getUserReplies(auth.user.id, { page: 1, size: 20 })
    const data = res.data
    if (Array.isArray(data)) {
      replies.value = data
    } else if (data && Array.isArray(data.list)) {
      replies.value = data.list
    } else {
      replies.value = []
    }
  } catch (e) {
    console.error('加载回复失败:', e)
    replies.value = []
  } finally {
    loading.replies = false
  }
}

async function loadResources() {
  if (!auth.user?.id) return
  loading.resources = true
  try {
    const res = await getUserResources(auth.user.id, { page: 1, size: 20 })
    const data = res.data
    if (Array.isArray(data)) {
      resources.value = data
    } else if (data && Array.isArray(data.list)) {
      resources.value = data.list
    } else {
      resources.value = []
    }
  } catch (e) {
    console.error('加载资源失败:', e)
    resources.value = []
  } finally {
    loading.resources = false
  }
}

async function loadAssignments() {
  loading.assignments = true
  try {
    console.log('开始加载作业提醒...')
    const res = await getMyAssignments()
    console.log('作业提醒API返回:', res)
    assignments.value = res.data || []
    console.log('作业提醒数据:', assignments.value)
  } catch (e) {
    console.error('加载作业提醒失败:', e)
    console.error('错误详情:', e.response?.data || e.message)
  } finally {
    loading.assignments = false
  }
}

function readAssignment(item) {
  // 跳转到作业提交页面
  router.push(`/assignment/${item.assignmentId}`)
}

async function goToAlgo() {
  // 游客/待审核用户亦可进入算法平台浏览，提交与交互限制由 HOJ 自身处理
  if (auth.isLoggedIn) {
    await auth.syncToHoj()
  }
  window.location.href = '/algo/'
}

onMounted(() => {
  if (auth.isLoggedIn) {
    loadProfile()
    loadPosts()
    loadAssignments()
  }
})

// 监听Tab切换加载数据
import { watch } from 'vue'
watch(activeTab, (tab) => {
  if (tab === 'replies' && replies.value.length === 0) loadReplies()
  if (tab === 'resources' && resources.value.length === 0) loadResources()
})
</script>

<style scoped>
.page-mount {
  padding-top: var(--navbar-h);
  min-height: 100vh;
  background: var(--bg-secondary);
}

/* 未登录状态 */
.guest-scene {
  min-height: calc(100vh - var(--navbar-h));
  display: flex;
  align-items: center;
  justify-content: center;
}
.guest-content {
  text-align: center;
  padding: var(--s-3xl);
}
.guest-icon {
  width: 160px;
  height: 160px;
  margin: 0 auto var(--s-xl);
}
.guest-icon svg { width: 100%; height: 100%; }
.guest-content h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--s-md);
}
.guest-content p {
  color: var(--text-secondary);
  margin-bottom: var(--s-xl);
}
.btn-login {
  display: inline-flex;
  align-items: center;
  padding: 12px 32px;
  border-radius: 24px;
  background: var(--primary);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  box-shadow: 0 4px 14px rgba(25,118,210,0.3);
  transition: all 250ms;
}
.btn-login:hover {
  background: var(--primary-dark);
  transform: translateY(-2px);
}

/* 已登录容器 */
.mine-container {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--s-xl) var(--s-base);
}

/* 个人资料卡 */
.profile-card {
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  overflow: hidden;
  margin-bottom: var(--s-lg);
}
.profile-header {
  display: flex;
  gap: var(--s-xl);
  padding: var(--s-xl);
  align-items: flex-start;
}
.avatar-section {
  position: relative;
  flex-shrink: 0;
}
.avatar-large {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--bg-secondary);
}
.avatar-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
.avatar-badge.active {
  background: var(--success-bg, #e8f5e9);
  color: var(--success, #4caf50);
}
.avatar-badge.pending {
  background: var(--warning-bg, #fff3e0);
  color: var(--warning, #ff9800);
}
.avatar-badge.admin {
  background: var(--primary-bg);
  color: var(--primary);
}
.info-section {
  flex: 1;
  min-width: 0;
}
.nickname {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2px;
}
.username {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--s-sm);
}
.bio {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: var(--s-sm);
}
.bio.placeholder {
  color: var(--text-tertiary);
  font-style: italic;
}
.meta-row {
  display: flex;
  gap: var(--s-lg);
  flex-wrap: wrap;
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}
.meta-item svg { opacity: 0.6; }
.action-section {
  flex-shrink: 0;
}
.btn-edit {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--r-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  transition: all 200ms;
}
.btn-edit:hover {
  background: var(--primary-bg);
  color: var(--primary);
}

/* 统计行 */
.stats-row {
  display: flex;
  border-top: 1px solid var(--divider);
}
.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--s-base);
  border-right: 1px solid var(--divider);
}
.stat-item:last-child { border-right: none; }
.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}
.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* 审核提示 */
.pending-banner {
  display: flex;
  align-items: center;
  gap: var(--s-sm);
  padding: var(--s-base) var(--s-lg);
  background: var(--warning-bg, #fff3e0);
  border-radius: var(--r-md);
  color: var(--warning, #e65100);
  font-size: 14px;
  margin-bottom: var(--s-lg);
}

/* 作业提醒 */
.section-card {
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  margin-bottom: var(--s-lg);
  overflow: hidden;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--s-base) var(--s-lg);
  border-bottom: 1px solid var(--divider);
}
.section-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.badge {
  background: var(--primary);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}
.assignment-list {
  max-height: 300px;
  overflow-y: auto;
}
.assignment-item {
  display: flex;
  align-items: flex-start;
  gap: var(--s-base);
  padding: var(--s-base) var(--s-lg);
  cursor: pointer;
  transition: background 200ms;
  position: relative;
}
.assignment-item:hover {
  background: var(--bg-secondary);
}
.assignment-item.unread {
  background: var(--primary-bg-light, rgba(25,118,210,0.03));
}
.assignment-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: var(--r-md);
  background: var(--primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}
.assignment-content {
  flex: 1;
  min-width: 0;
}
.assignment-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.assignment-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.assignment-meta {
  display: flex;
  align-items: center;
  gap: var(--s-sm);
  flex-wrap: wrap;
}
.assignment-time {
  font-size: 12px;
  color: var(--text-tertiary);
}
.assignment-deadline {
  font-size: 12px;
  color: var(--text-tertiary);
}
.assignment-status {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
}
.assignment-status.submitted {
  background: var(--success-bg, #e8f5e9);
  color: var(--success, #4caf50);
}
.assignment-status.pending {
  background: var(--warning-bg, #fff3e0);
  color: var(--warning, #ff9800);
}
.unread-dot {
  position: absolute;
  top: 50%;
  right: var(--s-lg);
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
}

/* Tab区 */
.content-section { margin-bottom: var(--s-lg); }
.tabs-header {
  display: flex;
  border-bottom: 1px solid var(--divider);
}
.tab-btn {
  flex: 1;
  padding: var(--s-base);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 200ms;
}
.tab-btn:hover { color: var(--text-primary); background: var(--bg-secondary); }
.tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}
.tabs-content {
  padding: var(--s-base);
}
.tab-pane { min-height: 200px; }

/* 帖子列表 */
.post-list {
  display: flex;
  flex-direction: column;
}
.post-item {
  padding: var(--s-base);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: background 200ms;
}
.post-item:hover { background: var(--bg-secondary); }
.post-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.reply-content {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.post-meta {
  display: flex;
  gap: var(--s-base);
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 空状态 */
.empty-state, .loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--s-3xl);
  color: var(--text-tertiary);
}
.empty-state p { margin: var(--s-base) 0; }
.link-btn {
  color: var(--primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}
.link-btn:hover { text-decoration: underline; }

/* 快捷入口 */
.quick-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--s-base);
}
.quick-link-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: var(--s-lg);
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  color: var(--text-primary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 200ms;
}
.quick-link-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--sh-md);
  color: var(--primary);
}
.quick-link-item svg { color: var(--primary); opacity: 0.7; }

/* 响应式 */
@media (max-width: 600px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .meta-row { justify-content: center; }
  .action-section { width: 100%; }
  .btn-edit { width: 100%; justify-content: center; }
  .stats-row { flex-wrap: wrap; }
  .stat-item { min-width: 25%; }
  .quick-links { grid-template-columns: 1fr; }
}
</style>
