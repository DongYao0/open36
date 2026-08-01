<template>
  <router-view />
  <ToastNotification />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import ToastNotification from '@/components/ToastNotification.vue'

const auth = useAuthStore()
const theme = useThemeStore()

onMounted(() => {
  // 应用主题（跨应用同步监听在此注册）
  theme.init()
  // 页面刷新时尝试恢复登录态
  if (auth.token && !auth.user) {
    auth.fetchUser()
  }
})
</script>
