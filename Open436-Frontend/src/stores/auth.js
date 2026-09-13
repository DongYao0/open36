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
  const avatar = computed(() => user.value?.avatarUrl || user.value?.avatar || '/app/user.jpg')
  const nickname = computed(() => user.value?.nickname || '')
  const displayName = computed(() => user.value?.realName || user.value?.username || user.value?.nickname || '')

  function setUser(u) {
    user.value = u
    storage.set('user', u)
  }

  function mergeUserProfile(profile) {
    if (!user.value || !profile) return
    setUser({
      ...user.value,
      nickname: profile.nickname ?? user.value.nickname,
      avatarUrl: profile.avatarUrl ?? user.value.avatarUrl,
      bio: profile.bio ?? user.value.bio
    })
  }

  function setToken(t) {
    token.value = t
    storage.set('token', t)
  }

  /**
   * 报名提交（阶段5.1 幂等）：
   * idempotencyKey 由调用方（登录页报名表单会话）维护——
   * 同一次报名的所有重试复用同一个 Key，服务端保证只建一个账号。
   */
  async function register({ username, password, nickname, studentId, realName, phone, major, idempotencyKey }) {
    try {
      const headers = idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {}
      const res = await request.post('/api/enrollment/apply', {
        username,
        password,
        studentId,
        realName,
        phone,
        major,
        selfIntro: '',
        skills: ''
      }, { headers })
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
      // status 透传给调用方：503=可重试保留幂等键；4xx=冲突需换键重填
      return { success: false, message: msg || e?.message || '注册失败', status: e?.response?.status }
    }
  }

  async function syncToHoj() {
    // 待审核报名用户只能浏览平台，后端会拒绝其 HOJ 同步请求。
    if (user.value?.status !== 'active') return

    try {
      const res = await request.post('/api/auth/algo-sync', {})
      if (res.code === 200 && res.data) {
        localStorage.setItem('token', res.data)
        // 同步 HOJ 所需的 userInfo（含 roleList，用于登录态判定）
        const hojUserInfo = {
          username: user.value?.username || '',
          nickname: displayName.value,
          avatar: avatar.value || '',
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
      if (res.code === 200 && res.data) {
        // /current 提供真实姓名等权威账号字段；保留登录响应中的头像、昵称和简介。
        setUser({ ...(user.value || {}), ...res.data })
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

  return { user, token, guestMode, isLoggedIn, isAdmin, isGuest, isVisitor, isReadOnly, canPost, avatar, nickname, displayName, login, register, fetchUser, logout, enterGuestMode, exitGuestMode, setUser, mergeUserProfile, setToken, syncToHoj }
})
