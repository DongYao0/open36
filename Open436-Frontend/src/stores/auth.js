import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'
import { storage } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(storage.get('user', null))
  const token = ref(storage.get('token', ''))
  const guestMode = ref(storage.get('guest_mode', false))

  const isLoggedIn = computed(() => !!user.value || guestMode.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isGuest = computed(() => user.value?.status === 'pending')
  const isVisitor = computed(() => guestMode.value)
  const isReadOnly = computed(() => user.value?.status === 'pending' || guestMode.value || !user.value)
  const canPost = computed(() => !!user.value && user.value.status === 'active')
  const avatar = computed(() => user.value?.avatar || '')
  const nickname = computed(() => user.value?.nickname || '')

  function setUser(u) {
    user.value = u
    storage.set('user', u)
  }

  function setToken(t) {
    token.value = t
    storage.set('token', t)
  }

  async function register({ username, password, nickname, studentId, realName, phone, major }) {
    try {
      const res = await request.post('/api/enrollment/apply', {
        username,
        password,
        studentId,
        realName,
        phone,
        major,
        selfIntro: '',
        skills: ''
      })
      if (res.code !== 200) {
        return { success: false, message: res.message || '注册失败' }
      }
      // 报名成功，自动以 pending 身份登录
      const loginRes = await login(username, password)
      if (loginRes.success) {
        return { success: true, message: '报名成功，已自动登录' }
      }
      return { success: true, message: res.message || '报名成功，请登录' }
    } catch (e) {
      const msg = e?.response?.data?.message
      return { success: false, message: msg || e?.message || '注册失败' }
    }
  }

  async function syncToHoj() {
    try {
      const res = await request.post('/api/auth/algo-sync', {})
      if (res.code === 200 && res.data) {
        localStorage.setItem('token', res.data)
        // 同步 HOJ 所需的 userInfo（含 roleList，用于登录态判定）
        const hojUserInfo = {
          username: user.value?.username || '',
          nickname: user.value?.nickname || user.value?.username || '',
          avatar: user.value?.avatar || '',
          roleList: user.value?.role === 'admin' ? ['admin'] : ['user']
        }
        localStorage.setItem('userInfo', JSON.stringify(hojUserInfo))
        // open436_token 由 setToken() 统一管理（JSON 编码），此处不再覆盖
      }
    } catch (e) {
      console.error('HOJ 同步失败:', e)
    }
  }

  async function login(username, password) {
    try {
      const res = await request.post('/api/auth/login', { username, password })
      if (res.code !== 200 || !res.data?.token) {
        return { success: false, message: res.message || '登录失败' }
      }
      setToken(res.data.token)
      setUser(res.data.user)
      await syncToHoj()
      return { success: true }
    } catch (e) {
      const msg = e?.response?.data?.message
      return { success: false, message: msg || e?.message || '登录失败' }
    }
  }

  async function fetchUser() {
    if (!token.value) return false
    try {
      const res = await request.get('/api/auth/current')
      if (res.code === 200 && res.data?.user) {
        setUser(res.data.user)
        await syncToHoj()
        return true
      }
      return false
    } catch {
      return false
    }
  }

  function enterGuestMode() {
    guestMode.value = true
    storage.set('guest_mode', true)
  }

  function exitGuestMode() {
    guestMode.value = false
    storage.remove('guest_mode')
  }

  function logout() {
    user.value = null
    token.value = ''
    guestMode.value = false
    storage.remove('user')
    storage.remove('token')
    storage.remove('guest_mode')
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('open436_token')
  }

  return { user, token, guestMode, isLoggedIn, isAdmin, isGuest, isVisitor, isReadOnly, canPost, avatar, nickname, login, register, fetchUser, logout, enterGuestMode, exitGuestMode, setUser, setToken, syncToHoj }
})
