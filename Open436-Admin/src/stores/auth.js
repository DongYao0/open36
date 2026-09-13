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
        return true
      }
    } catch (e) {
      console.error('HOJ 同步失败:', e)
    }
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    return false
  }

  async function openHojAdmin() {
    const synced = await syncToHoj()
    const hojToken = localStorage.getItem('token') || ''
    let userInfo = {}
    try {
      userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
    } catch {
      localStorage.removeItem('userInfo')
    }
    if (!synced || !hojToken) {
      throw new Error('HOJ 同步失败，未取得登录凭据')
    }
    const params = new URLSearchParams({
      hoj_token: hojToken,
      username: userInfo.username || '',
      role: userInfo.roleList?.[0] || 'admin'
    })
    const hojVueBase = import.meta.env.VITE_HOJ_VUE_URL || ''
    window.location.assign(`${hojVueBase}/algo/admin/dashboard#${params}`)
  }

  async function loginWithBackend(username, password) {
    const res = await loginApi({ username, password })
    const data = res.data || res
    setToken(data.token)
    setUser(data.user)
    await syncToHoj()
    return data
  }

  async function loginWithDevFallback(username, password) {
    try {
      return await loginWithBackend(username, password)
    } catch (e) {
      const msg = e?.message || ''
      if (msg.includes('管理员') || msg.includes('权限') || msg.includes('403') || msg.includes('401') || msg.includes('未登录') || msg.includes('密码')) {
        throw e
      }
      const isNetworkError = !e.response && (msg.includes('Network Error') || msg.includes('ECONNREFUSED') || msg.includes('timeout') || msg.includes('连接失败'))
      if (username === 'admin' && isNetworkError) {
        const mockToken = 'mock-admin-token-' + Date.now()
        const mockUser = { id: 1, username: 'admin', role: 'admin', status: 'active' }
        setToken(mockToken)
        setUser(mockUser)
        return { token: mockToken, user: mockUser }
      }
      throw e
    }
  }

  // Vite 在生产构建时静态选择真实登录函数，并移除整个 dev fallback。
  const login = import.meta.env.DEV ? loginWithDevFallback : loginWithBackend

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

  return { token, user, isLoggedIn, isAdmin, username, login, logout, fetchUser, syncToHoj, openHojAdmin }
})
