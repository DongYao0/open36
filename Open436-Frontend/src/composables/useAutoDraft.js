import { isRef, onBeforeUnmount, watch } from 'vue'

const PREFIX = 'open436_draft_v1:'
const DEFAULT_TTL = 30 * 24 * 60 * 60 * 1000

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function targetValue(source) {
  return isRef(source) ? source.value : source
}

function applyValue(source, value) {
  const target = targetValue(source)
  if (target && typeof target === 'object' && value && typeof value === 'object') {
    Object.assign(target, value)
  } else if (isRef(source)) {
    source.value = value
  }
}

export function useAutoDraft(key, source, options = {}) {
  const storageKey = PREFIX + key
  const ttl = options.ttl ?? DEFAULT_TTL
  const debounce = options.debounce ?? 300
  const include = options.include || null
  let started = false
  let timer = null
  let lastSnapshot = null

  function snapshot() {
    const value = targetValue(source)
    if (!include || !value || typeof value !== 'object') return clone(value)
    return Object.fromEntries(include.map(field => [field, clone(value[field])]))
  }

  function saveDraft() {
    if (!started) return
    clearTimeout(timer)
    try {
      const data = snapshot()
      const serialized = JSON.stringify(data)
      if (serialized === lastSnapshot) return
      localStorage.setItem(storageKey, JSON.stringify({
        version: 1,
        updatedAt: Date.now(),
        data
      }))
      lastSnapshot = serialized
    } catch (error) {
      console.warn('自动保存草稿失败', error)
    }
  }

  function scheduleSave() {
    if (!started) return
    clearTimeout(timer)
    timer = setTimeout(saveDraft, debounce)
  }

  function restoreDraft(transform = value => value) {
    try {
      const raw = localStorage.getItem(storageKey)
      if (!raw) { startDraft(); return null }
      const payload = JSON.parse(raw)
      if (!payload?.updatedAt || Date.now() - payload.updatedAt > ttl) {
        localStorage.removeItem(storageKey)
        startDraft()
        return null
      }
      const value = transform(clone(payload.data))
      if (options.apply) options.apply(value)
      else applyValue(source, value)
      startDraft()
      return { updatedAt: payload.updatedAt }
    } catch (error) {
      localStorage.removeItem(storageKey)
      startDraft()
      console.warn('恢复草稿失败', error)
      return null
    }
  }

  function startDraft() {
    lastSnapshot = JSON.stringify(snapshot())
    started = true
  }
  function clearDraft() {
    clearTimeout(timer)
    started = false
    lastSnapshot = null
    localStorage.removeItem(storageKey)
  }
  function flushOnHide() {
    if (document.visibilityState === 'hidden') saveDraft()
  }

  const stop = watch(source, scheduleSave, { deep: true, flush: 'post' })
  window.addEventListener('pagehide', saveDraft)
  document.addEventListener('visibilitychange', flushOnHide)
  onBeforeUnmount(() => {
    saveDraft()
    stop()
    window.removeEventListener('pagehide', saveDraft)
    document.removeEventListener('visibilitychange', flushOnHide)
  })

  return { restoreDraft, startDraft, saveDraft, clearDraft }
}
