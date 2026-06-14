<template>
  <ForumHeader />
  <AppSidebar @select="handleSidebarSelect" />
  <div class="forum-layout with-sidebar">
    <div class="forum-main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { provide } from 'vue'
import ForumHeader from '@/components/ForumHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'

let sidebarCallback = null

function handleSidebarSelect(key) {
  if (sidebarCallback) sidebarCallback(key)
}

function onSidebarSelect(cb) {
  sidebarCallback = cb
}

provide('forumOnSidebarSelect', onSidebarSelect)
</script>
