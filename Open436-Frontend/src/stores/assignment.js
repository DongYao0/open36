import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAssignmentUnreadCount } from '@/api/user'

export function isAssignmentPending(item) {
  if (!item || item.submissionStatus === 'submitted' || item.status !== 'active') return false
  if (item.pendingActionable === false || item.expired === true) return false
  if (!item.deadline) return true
  const deadline = new Date(item.deadline).getTime()
  return Number.isNaN(deadline) || deadline > Date.now()
}

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
    unreadCount.value = (assignments || []).filter(isAssignmentPending).length
    lastFetchedAt.value = Date.now()
  }

  function clear() {
    unreadCount.value = 0
    lastFetchedAt.value = 0
  }

  return { unreadCount, refresh, setFromAssignments, clear }
})
