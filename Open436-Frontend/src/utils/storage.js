/**
 * localStorage 封装
 * 提供统一的本地存储接口，支持 JSON 序列化
 */

const PREFIX = 'open436_'

export const storage = {
  /**
   * 设置存储
   * @param {string} key - 键名
   * @param {any} value - 值（支持对象，自动序列化）
   */
  set(key, value) {
    try {
      const serializedValue = JSON.stringify(value)
      localStorage.setItem(PREFIX + key, serializedValue)
    } catch (error) {
      console.error('存储失败：', error)
    }
  },

  /**
   * 获取存储
   * @param {string} key - 键名
   * @param {any} defaultValue - 默认值
   * @returns {any} 解析后的值
   */
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(PREFIX + key)
      if (item === null) return defaultValue
      try {
        return JSON.parse(item)
      } catch {
        // 非 JSON 格式（如旧版直接写入的原始字符串），返回原始值
        return item
      }
    } catch (error) {
      console.error('读取失败：', error)
      return defaultValue
    }
  },

  /**
   * 移除存储
   * @param {string} key - 键名
   */
  remove(key) {
    localStorage.removeItem(PREFIX + key)
  },

  /**
   * 清空所有存储
   */
  clear() {
    localStorage.clear()
  },

  /**
   * 检查是否存在
   * @param {string} key - 键名
   * @returns {boolean}
   */
  has(key) {
    return localStorage.getItem(PREFIX + key) !== null
  }
}

export default storage

