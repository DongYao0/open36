const PREFIX = 'open436_admin_'

export const storage = {
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(PREFIX + key)
      if (!item) return defaultValue
      try {
        return JSON.parse(item)
      } catch {
        // 兼容裸字符串格式（旧版直接 setItem 写入的值）
        return item
      }
    } catch {
      return defaultValue
    }
  },
  set(key, value) {
    localStorage.setItem(PREFIX + key, JSON.stringify(value))
  },
  remove(key) {
    localStorage.removeItem(PREFIX + key)
  },
  clear() {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX))
    keys.forEach(k => localStorage.removeItem(k))
  }
}
