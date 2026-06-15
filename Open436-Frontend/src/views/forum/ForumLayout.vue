<template>
  <ForumHeader />
  <div class="forum-layout">
    <div class="forum-main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import ForumHeader from '@/components/ForumHeader.vue'
</script>

<style scoped>
.forum-layout {
  min-height: 100vh;
  padding-top: var(--navbar-h, 56px);
  background: var(--bg-page, #f5f7fa);
}
.forum-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--s-lg) var(--s-lg) 80px;
}
</style>
