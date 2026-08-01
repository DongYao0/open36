/**
 * 应用入口文件
 */
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './stores'

// 导入全局样式
import '@/assets/styles/main.css'

// 提前应用主题，避免刷新闪烁（data-theme 驱动 CSS 变量切换）
;(() => {
  try {
    const raw = localStorage.getItem('open436_theme')
    const t = raw ? JSON.parse(raw) : 'light'
    document.documentElement.setAttribute('data-theme', t === 'dark' ? 'dark' : 'light')
  } catch {
    document.documentElement.setAttribute('data-theme', 'light')
  }
})()

// 创建应用实例
const app = createApp(App)

// 使用插件
app.use(router)
app.use(pinia)

// 挂载应用
app.mount('#app')
