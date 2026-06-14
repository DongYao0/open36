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
