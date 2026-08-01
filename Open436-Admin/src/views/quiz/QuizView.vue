<template>
  <div class="algo-iframe-wrap">
    <div v-if="loading" class="algo-loading">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p>正在同步算法系统登录态...</p>
    </div>
    <iframe
      v-show="!loading"
      ref="iframeRef"
      :src="iframeSrc"
      class="algo-iframe"
      frameborder="0"
      sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"
    ></iframe>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(true)
const iframeSrc = ref('')
const iframeRef = ref(null)

onMounted(async () => {
  // 重新同步 HOJ token，防止过期导致二次登录
  try {
    await authStore.syncToHoj()
  } catch (e) {
    console.error('HOJ 同步失败:', e)
  }
  iframeSrc.value = '/algo/admin/'
  loading.value = false
})
</script>

<style scoped lang="scss">
.algo-iframe-wrap {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 100px);
  margin: -20px;
  padding: 0;
  position: relative;
}
.algo-iframe {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 100px);
  border: none;
  display: block;
}
.algo-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 100px);
  color: #909399;
  gap: 12px;
}
</style>
