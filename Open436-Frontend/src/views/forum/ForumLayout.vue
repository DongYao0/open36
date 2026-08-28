<template>
  <ForumHeader />
  <div class="forum-layout">
    <div class="forum-main" :class="{ 'forum-main--resource': route.meta.forumSection === 'share' }">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'

const route = useRoute()
</script>

<style scoped>
.forum-layout {
  min-height: 100vh;
  padding-top: var(--navbar-h, 56px);
  background: var(--bg-page, #f5f7fa);
}
.forum-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--s-lg) var(--s-lg) 80px;
}
.forum-main--resource { max-width: none; padding: 0 0 80px; }
</style>
