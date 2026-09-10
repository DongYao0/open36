<template>
  <AppNavbar />
  <div class="forum-layout">
    <div class="forum-main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import AppNavbar from '@/components/AppNavbar.vue'
</script>
