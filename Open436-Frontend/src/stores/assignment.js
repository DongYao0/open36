import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAssignmentUnreadCount } from '@/api/user'

export const useAssignmentStore = defineStore('assignmentNotifications', () => {
  const unreadCount = ref(0)
  const lastFetchedAt = ref(0)
  let pending = null

  async function refresh(force = false) {
    if (!force && Date.now() - lastFetchedAt.value < 30000) return unreadCount.value
    if (pending) return pending
    pending = getAssignmentUnreadCount()
      .then((res) => {
        unreadCount.value = Math.max(0, Number(res?.data?.count ?? res?.count ?? 0))
        lastFetchedAt.value = Date.now()
        return unreadCount.value
      })
      .catch(() => unreadCount.value)
      .finally(() => { pending = null })
    return pending
  }

  function setFromAssignments(assignments) {
    unreadCount.value = (assignments || []).filter(item => !item.read).length
    lastFetchedAt.value = Date.now()
  }

  function markOneRead() {
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  function clear() {
    unreadCount.value = 0
    lastFetchedAt.value = 0
  }

  return { unreadCount, refresh, setFromAssignments, markOneRead, clear }
})
