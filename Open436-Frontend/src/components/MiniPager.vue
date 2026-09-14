<template>
  <nav v-if="totalPages > 1" class="mini-pager" aria-label="分页">
    <button :disabled="page <= 1" @click="$emit('change', page - 1)">上一页</button>
    <span>第 {{ page }} / {{ totalPages }} 页</span>
    <button :disabled="!canGoNext" @click="$emit('change', page + 1)">下一页</button>
  </nav>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, required: true },
  total: { type: Number, default: 0 },
  pageSize: { type: Number, required: true },
  hasNext: { type: Boolean, default: false }
})

defineEmits(['change'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const canGoNext = computed(() => props.hasNext || props.page < totalPages.value)
</script>

<style scoped>
.mini-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 14px 0 4px;
  color: var(--text-secondary);
  font-size: 12px;
}
.mini-pager button {
  min-width: 70px;
  padding: 7px 12px;
  border: 1px solid var(--divider);
  border-radius: 8px;
  color: var(--primary);
  background: var(--bg);
}
.mini-pager button:hover:not(:disabled) { border-color: var(--primary); background: var(--primary-bg); }
.mini-pager button:disabled { color: var(--text-disabled); cursor: not-allowed; opacity: .65; }
</style>
