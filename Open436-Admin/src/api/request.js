import axios from 'axios'
import { ElMessage } from 'element-plus'
import { storage } from '@/utils/storage'
import router from '@/router'

const request = axios.create({
  baseURL: '',
  timeout: 15000
})

request.interceptors.request.use(config => {
  const token = storage.get('token')
  if (token) {
    config.headers['token'] = token
  }
  return config
})

request.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code && res.code !== 200) {
      // Sa-Token 业务层未登录错误码（401xxxxx），跳转登录
      const codeStr = String(res.code)
      if (codeStr.startsWith('401')) {
        storage.clear()
        router.push('/login')
        ElMessage.error(res.message || '登录已过期，请重新登录')
        return Promise.reject(new Error(res.message || '未登录'))
      }
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }
    return res
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      const msg = data?.message || '请求失败'
      if (status === 401) {
        storage.clear()
        router.push('/login')
      }
      return Promise.reject(new Error(msg))
    }
    return Promise.reject(new Error('网络连接失败'))
  }
)

export default request
