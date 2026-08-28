<template>
  <ForumHeader />
  <div class="forum-layout">
    <div class="forum-main" :style="{ '--tech-forum-universe': `url(${techForumUniverse})` }" :class="{ 'forum-main--resource': route.meta.forumSection === 'share', 'forum-main--tech': route.meta.forumSection === 'tech' }">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'
import techForumUniverse from '@/assets/tech-forum-universe.png'

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
.forum-main--tech { position: relative; isolation: isolate; min-height: calc(100vh - var(--navbar-h, 56px)); }
.forum-main--tech::before { position: fixed; z-index: -2; inset: var(--navbar-h, 56px) 0 0; background: var(--tech-forum-universe) center top / cover fixed; content: ''; }
.forum-main--tech::after { position: fixed; z-index: -1; inset: var(--navbar-h, 56px) 0 0; background: linear-gradient(180deg, rgba(5,11,37,.30), rgba(6,12,38,.62) 56%, rgba(4,8,28,.78)); content: ''; }
</style>
