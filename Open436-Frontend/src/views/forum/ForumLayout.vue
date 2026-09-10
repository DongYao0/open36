<template>
  <AppNavbar />
  <div class="forum-layout">
    <div class="forum-main" :style="{ '--tech-forum-universe': `url(${techForumUniverse})`, '--tech-detail-blueprint': `url(${techDetailBlueprint})` }" :class="{ 'forum-main--resource': route.meta.forumSection === 'share', 'forum-main--tech': route.meta.forumSection === 'tech', 'forum-main--detail': route.name === 'PostDetail', 'forum-main--composer': route.name === 'PostNew' }">
      <div v-if="isForumIndex" class="forum-toolbar">
        <nav class="forum-switcher" aria-label="论坛分区">
          <router-link to="/forum/tech" :class="{ active: route.meta.forumSection === 'tech' }">技术交流</router-link>
          <router-link to="/forum/share" :class="{ active: route.meta.forumSection === 'share' }">资源分享</router-link>
        </nav>
        <form class="forum-search" @submit.prevent="doSearch">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>
          <input v-model="searchQuery" placeholder="搜索技术文章与可用资源" aria-label="搜索论坛" />
          <button type="submit">搜索</button>
        </form>
      </div>
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNavbar from '@/components/AppNavbar.vue'
import techForumUniverse from '@/assets/tech-forum-universe.png'
import techDetailBlueprint from '@/assets/tech-detail-blueprint.png'

const route = useRoute()
const router = useRouter()
const searchQuery = ref('')
const isForumIndex = computed(() => route.name === 'ForumTech' || route.name === 'ForumShare')
function doSearch() {
  const query = searchQuery.value.trim()
  if (query) router.push({ path: '/forum/search', query: { q: query } })
}
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
.forum-main--resource { max-width: none; padding: 0 0 80px; background: #100561; }
.forum-main--tech { position: relative; isolation: isolate; min-height: calc(100vh - var(--navbar-h, 56px)); }
.forum-main--tech::before { position: fixed; z-index: -2; inset: var(--navbar-h, 56px) 0 0; background: var(--tech-forum-universe) center top / cover fixed; content: ''; }
.forum-main--tech::after { position: fixed; z-index: -1; inset: var(--navbar-h, 56px) 0 0; background: linear-gradient(180deg, rgba(5,11,37,.30), rgba(6,12,38,.62) 56%, rgba(4,8,28,.78)); content: ''; }
.forum-main--detail { position: relative; isolation: isolate; max-width: none; min-height: calc(100vh - var(--navbar-h, 56px)); padding: 34px clamp(18px, 5vw, 84px) 88px; background: #071224; }
.forum-main--detail::before { position: fixed; z-index: -2; inset: var(--navbar-h, 56px) 0 0; background: var(--tech-detail-blueprint) center top / cover fixed; content: ''; }
.forum-main--detail::after { position: fixed; z-index: -1; inset: var(--navbar-h, 56px) 0 0; background: linear-gradient(180deg, rgba(3,11,27,.46), rgba(7,16,39,.76)); content: ''; }
.forum-main--composer { position: relative; isolation: isolate; max-width: none; min-height: calc(100vh - var(--navbar-h, 56px)); padding: 34px clamp(18px, 5vw, 84px) 88px; background: #071224; }
.forum-main--composer::before { position: fixed; z-index: -2; inset: var(--navbar-h, 56px) 0 0; background: var(--tech-detail-blueprint) center / cover fixed; content: ''; }
.forum-main--composer::after { position: fixed; z-index: -1; inset: var(--navbar-h, 56px) 0 0; background: rgba(4,12,31,.68); content: ''; }
.forum-toolbar { position: relative; z-index: 2; display: flex; align-items: center; gap: 22px; max-width: 1364px; margin: 0 auto 22px; }
.forum-switcher { display: flex; gap: 4px; flex: 0 0 auto; padding: 4px; border: 1px solid rgba(173,197,255,.18); border-radius: 12px; background: rgba(4,13,42,.62); backdrop-filter: blur(12px); }
.forum-switcher a { padding: 9px 14px; border-radius: 8px; color: rgba(225,233,255,.72); font-size: 14px; font-weight: 700; text-decoration: none; transition: .2s; white-space: nowrap; }
.forum-switcher a:hover { color: #fff; background: rgba(255,255,255,.08); }.forum-switcher a.active { color: #07112d; background: linear-gradient(135deg, #8be8ff, #a99cff); box-shadow: 0 7px 17px rgba(86,148,255,.22); }
.forum-search { display: flex; align-items: center; gap: 9px; min-width: 0; width: min(470px, 100%); margin-left: auto; padding: 5px 6px 5px 13px; border: 1px solid rgba(173,197,255,.2); border-radius: 12px; background: rgba(5,14,43,.66); box-shadow: 0 10px 26px rgba(0,0,0,.16); backdrop-filter: blur(12px); }
.forum-search svg { flex: 0 0 auto; width: 17px; color: #8ddffb; }.forum-search input { min-width: 0; flex: 1; border: 0; outline: 0; background: transparent; color: #f4f7ff; font: inherit; font-size: 14px; }.forum-search input::placeholder { color: rgba(218,230,255,.54); }.forum-search button { padding: 8px 14px; border: 0; border-radius: 8px; background: #786fe9; color: #fff; font: inherit; font-size: 13px; font-weight: 700; cursor: pointer; }
@media (max-width: 720px) { .forum-toolbar { display: grid; gap: 12px; margin-bottom: 16px; }.forum-search { width: 100%; margin: 0; }.forum-switcher { justify-self: start; }.forum-switcher a { padding: 8px 12px; } }
</style>
