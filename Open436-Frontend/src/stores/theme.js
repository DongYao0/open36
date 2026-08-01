/**
 * 主题状态（浅色 / 深色）
 * 与 main.js 中的预应用逻辑保持一致：data-theme 驱动 CSS 变量切换，
 * 主题值持久化在 localStorage 的 open436_theme 中。
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

const THEME_KEY = 'open436_theme'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(false)

  function apply() {
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  }

  function init() {
    try {
      const raw = localStorage.getItem(THEME_KEY)
      const t = raw ? JSON.parse(raw) : 'light'
      isDark.value = t === 'dark'
    } catch {
      isDark.value = false
    }
    apply()
  }

  function toggle() {
    isDark.value = !isDark.value
    try {
      localStorage.setItem(THEME_KEY, JSON.stringify(isDark.value ? 'dark' : 'light'))
    } catch { /* 忽略 localStorage 不可用 */ }
    apply()
  }

  function setDark(value) {
    isDark.value = !!value
    try {
      localStorage.setItem(THEME_KEY, JSON.stringify(isDark.value ? 'dark' : 'light'))
    } catch { /* 忽略 localStorage 不可用 */ }
    apply()
  }

  return { isDark, init, toggle, setDark, apply }
})
