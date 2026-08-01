import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { storage } from '@/utils/storage'
import { loginApi, logoutApi, getCurrentUser, syncToHojApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const rawToken = storage.get('token', '')
  const rawUser = storage.get('user', null)
  // 清除无效的 mock token，强制重新登录
  const isMockToken = rawToken && rawToken.startsWith('mock-')
  const token = ref(isMockToken ? '' : rawToken)
  const user = ref(isMockToken ? null : rawUser)
  if (isMockToken) {
    storage.remove('token')
    storage.remove('user')
  }

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const username = computed(() => user.value?.username || '')

  function setToken(val) {
    token.value = val
    storage.set('token', val)
  }

  function setUser(u) {
    user.value = u
    storage.set('user', u)
  }

  async function syncToHoj() {
    try {
      const res = await syncToHojApi()
      if (res.code === 200 && res.data) {
        localStorage.setItem('token', res.data)
        // 同步 HOJ 所需的 userInfo（包含 roleList，用于管理端路由权限判定）
        const hojUserInfo = {
          username: user.value?.username || '',
          nickname: user.value?.realName || user.value?.username || '',
          avatar: user.value?.avatar || '',
          roleList: user.value?.role === 'admin' ? ['root', 'admin'] : ['user']
        }
        localStorage.setItem('userInfo', JSON.stringify(hojUserInfo))
        // 写入 open436_token，供 HOJ 统一登出检测使用
        if (token.value) {
          localStorage.setItem('open436_token', token.value)
        }
      }
    } catch (e) {
      console.error('HOJ 同步失败:', e)
    }
  }

  async function login(username, password) {
    try {
      const res = await loginApi({ username, password })
      const data = res.data || res
      setToken(data.token)
      setUser(data.user)
      await syncToHoj()
      console.log('[DEBUG login] token set:', data.token)
      return data
    } catch (e) {
      const msg = e?.message || ''
      // 后端明确拒绝（403/401/鉴权相关）则直接抛出
      if (msg.includes('管理员') || msg.includes('权限') || msg.includes('403') || msg.includes('401') || msg.includes('未登录') || msg.includes('密码')) {
        throw e
      }
      // Mock fallback：仅在后端完全不可达（网络错误）时允许 admin 账号登录
      const isNetworkError = !e.response && (msg.includes('Network Error') || msg.includes('ECONNREFUSED') || msg.includes('timeout') || msg.includes('连接失败'))
      if (username === 'admin' && isNetworkError) {
        console.warn('[DEV] 后端不可达，使用 mock 登录')
        const mockToken = 'mock-admin-token-' + Date.now()
        const mockUser = { id: 1, username: 'admin', role: 'admin', status: 'active' }
        setToken(mockToken)
        setUser(mockUser)
        return { token: mockToken, user: mockUser }
      }
      throw e
    }
  }

  async function logout() {
    try { await logoutApi() } catch {}
    token.value = ''
    user.value = null
    storage.remove('token')
    storage.remove('user')
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('open436_token')
  }

  async function fetchUser() {
    const res = await getCurrentUser()
    const data = res.data || res
    setUser(data)
    await syncToHoj()
    return data
  }

  return { token, user, isLoggedIn, isAdmin, username, login, logout, fetchUser, syncToHoj }
})
