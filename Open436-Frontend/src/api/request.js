/**
 * Axios 请求封装
 * 统一配置请求拦截器和响应拦截器
 */
import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    let token = localStorage.getItem('open436_token')
    if (token) {
      // 兼容 storage.js 的 JSON 序列化（如 "\"xxx\""）和原始字符串
      try {
        const parsed = JSON.parse(token)
        if (typeof parsed === 'string') token = parsed
      } catch (e) {
        // 不是 JSON，保持原值
      }
      config.headers['token'] = token
    }

    // 注入用户身份 headers（供微服务 UserInfoMiddleware 读取）
    const userStr = localStorage.getItem('open436_user')
    if (userStr) {
      try {
        let user = JSON.parse(userStr)
        // storage.js 可能二次序列化
        if (typeof user === 'string') user = JSON.parse(user)
        if (user?.id) config.headers['X-User-Id'] = String(user.id)
        if (user?.username) config.headers['X-Username'] = user.username
        if (user?.role) config.headers['X-User-Role'] = user.role
        if (user?.status) config.headers['X-User-Status'] = user.status
      } catch (e) {
        // 解析失败忽略
      }
    }

    return config
  },
  (error) => {
    console.error('请求错误：', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端统一返回 {code, message, data} 格式，200/201 视为成功
    if (res && typeof res.code === 'number' && res.code !== 200 && res.code !== 201) {
      return Promise.reject({ response: { data: res, status: res.code } })
    }
    return res
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('open436_token')
      localStorage.removeItem('open436_user')
    }
    return Promise.reject(error)
  }
)

export default request
