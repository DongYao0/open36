<script setup>
// 已废弃：论坛已拆分为 /forum/tech（技术交流）与 /forum/share（资源分享）两个独立页面。
// 路由表已将 /forum 直接 redirect 到 /forum/tech，本文件仅作兜底转发。
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
onMounted(() => router.replace('/forum/tech'))
</script>

<template>
  <div class="fm-loading"><span class="spinner"></span></div>
</template>
