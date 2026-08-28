<template>
  <ForumHeader />
  <div class="forum-layout">
    <div class="forum-main" :style="{ '--tech-forum-universe': `url(${techForumUniverse})`, '--tech-detail-blueprint': `url(${techDetailBlueprint})` }" :class="{ 'forum-main--resource': route.meta.forumSection === 'share', 'forum-main--tech': route.meta.forumSection === 'tech', 'forum-main--detail': route.name === 'PostDetail', 'forum-main--composer': route.name === 'PostNew' }">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'
import techForumUniverse from '@/assets/tech-forum-universe.png'
import techDetailBlueprint from '@/assets/tech-detail-blueprint.png'

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
.forum-main--detail { position: relative; isolation: isolate; max-width: none; min-height: calc(100vh - var(--navbar-h, 56px)); padding: 34px clamp(18px, 5vw, 84px) 88px; background: #071224; }
.forum-main--detail::before { position: fixed; z-index: -2; inset: var(--navbar-h, 56px) 0 0; background: var(--tech-detail-blueprint) center top / cover fixed; content: ''; }
.forum-main--detail::after { position: fixed; z-index: -1; inset: var(--navbar-h, 56px) 0 0; background: linear-gradient(180deg, rgba(3,11,27,.46), rgba(7,16,39,.76)); content: ''; }
.forum-main--composer { position: relative; isolation: isolate; max-width: none; min-height: calc(100vh - var(--navbar-h, 56px)); padding: 34px clamp(18px, 5vw, 84px) 88px; background: #071224; }
.forum-main--composer::before { position: fixed; z-index: -2; inset: var(--navbar-h, 56px) 0 0; background: var(--tech-detail-blueprint) center / cover fixed; content: ''; }
.forum-main--composer::after { position: fixed; z-index: -1; inset: var(--navbar-h, 56px) 0 0; background: rgba(4,12,31,.68); content: ''; }
</style>
