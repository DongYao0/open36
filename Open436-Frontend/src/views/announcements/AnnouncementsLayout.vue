<template>
  <AnnouncementsHeader />
  <div class="forum-layout">
    <div class="forum-main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import AnnouncementsHeader from '@/components/AnnouncementsHeader.vue'
</script>
