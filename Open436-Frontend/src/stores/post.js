import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePostStore = defineStore('post', () => {
  // 帖子缓存：id → mapped post object
  const cache = ref(new Map())

  function getCachedPost(id) {
    return cache.value.get(String(id)) || null
  }

  function setCachedPost(id, post) {
    cache.value.set(String(id), post)
  }

  function removeCachedPost(id) {
    cache.value.delete(String(id))
  }

  function clearCache() {
    cache.value.clear()
  }

  return { cache, getCachedPost, setCachedPost, removeCachedPost, clearCache }
})
