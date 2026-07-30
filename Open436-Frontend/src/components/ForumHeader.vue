<template>
  <header class="fh">
    <!-- 左：返回首页 + 品牌 -->
    <div class="fh-left">
      <router-link to="/" class="fh-back" title="返回首页">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        <span>首页</span>
      </router-link>
      <span class="fh-sep"></span>
      <div class="fh-brand">
        <div class="fh-mark">O</div>
        <span class="fh-brand-text">Open436 论坛</span>
      </div>
    </div>

    <!-- 中：两大板块路由 Tab + 滑动 pill -->
    <nav class="fh-tabs">
      <div class="fh-pill" :style="pillStyle"></div>
      <router-link
        v-for="t in sections"
        :key="t.key"
        :to="t.to"
        class="fh-tab"
        :class="{ active: route.meta.forumSection === t.key }"
        :ref="el => { if (el) tabRefs[t.key] = el }"
      >{{ t.label }}</router-link>
    </nav>

    <!-- 中右：搜索框 -->
    <div class="fh-search">
      <svg class="fh-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input v-model="searchQuery" placeholder="搜索论坛…" @keyup.enter="doSearch" />
    </div>
    <router-link to="/forum/search" class="fh-search-mobile" title="搜索">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    </router-link>

    <!-- 最右：主题切换 + 用户下拉 / 登录 -->
    <div class="fh-right">
      <ThemeToggle class="fh-theme" />
      <div v-if="auth.isLoggedIn" class="fh-user">
        <div class="fh-trigger" @click="dropdownOpen = !dropdownOpen">
          <img :src="auth.isVisitor ? 'https://ui-avatars.com/api/?name=Guest&background=9E9E9E&color=fff&size=40' : auth.avatar" class="avatar avatar-sm" :alt="auth.isVisitor ? '游客' : auth.nickname" />
          <svg class="fh-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <div class="fh-dropdown" :class="{ active: dropdownOpen }">
          <router-link to="/mine" class="fh-dd-item" @click="dropdownOpen = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>个人中心
          </router-link>
          <router-link to="/forum/favorites" class="fh-dd-item" @click="dropdownOpen = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>我的收藏
          </router-link>
          <div class="fh-dd-divider"></div>
          <button class="fh-dd-item danger" @click="handleLogout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            {{ auth.isVisitor ? '退出游客模式' : '退出登录' }}
          </button>
        </div>
      </div>
      <router-link v-else to="/login" class="fh-login">登录</router-link>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const searchQuery = ref('')
const dropdownOpen = ref(false)
const tabRefs = ref({})
const pillTick = ref(0) // toggle 以在字体加载后强制重算 pill 位置

const sections = [
  { key: 'tech', label: '技术交流', to: '/forum/tech' },
  { key: 'share', label: '资源分享', to: '/forum/share' },
]

const pillStyle = computed(() => {
  pillTick.value // 依赖触发
  const el = tabRefs.value[route.meta.forumSection]
  if (!el) return { opacity: 0 }
  const node = el.$el || el
  const rect = node.getBoundingClientRect()
  const parent = node.parentElement.getBoundingClientRect()
  return { opacity: 1, width: `${rect.width + 8}px`, transform: `translateX(${rect.left - parent.left - 4}px)` }
})

function doSearch() {
  if (searchQuery.value.trim()) {
    router.push({ path: '/forum/search', query: { q: searchQuery.value.trim() } })
    searchQuery.value = ''
  }
}
function handleLogout() {
  dropdownOpen.value = false
  auth.logout()
  router.push('/login')
}
function closeDropdown(e) { if (!e.target.closest('.fh-user')) dropdownOpen.value = false }

onMounted(() => {
  document.addEventListener('click', closeDropdown)
  nextTick(() => requestAnimationFrame(() => { pillTick.value++ }))
  if (document.fonts?.ready) document.fonts.ready.then(() => { pillTick.value++ })
})
onUnmounted(() => document.removeEventListener('click', closeDropdown))
watch(() => route.meta.forumSection, () => nextTick(() => requestAnimationFrame(() => { pillTick.value++ })))
</script>

<style scoped>
.fh {
  position: fixed; top: 0; left: 0; right: 0; height: var(--navbar-h);
  display: flex; align-items: center; gap: var(--s-md);
  padding: 0 var(--s-lg); z-index: 100;
  background:
    radial-gradient(900px 280px at 12% -40%, rgba(145,94,255,0.35), transparent 60%),
    radial-gradient(700px 240px at 88% -60%, rgba(0,188,212,0.30), transparent 60%),
    linear-gradient(180deg, var(--cosmic-bg-2) 0%, var(--cosmic-bg) 100%);
  border-bottom: 1px solid var(--cosmic-border);
  box-shadow: 0 8px 40px -10px rgba(5,8,22,0.6);
}
.fh-left { display: flex; align-items: center; gap: var(--s-sm); flex-shrink: 0; }
.fh-back {
  display: inline-flex; align-items: center; gap: 6px; color: var(--cosmic-text);
  font-size: 13px; font-weight: 500; text-decoration: none; padding: 6px 10px;
  border-radius: var(--r-sm); transition: all var(--t-fast);
}
.fh-back:hover { color: #fff; background: rgba(255,255,255,0.08); }
.fh-sep { width: 1px; height: 22px; background: rgba(255,255,255,0.12); }
.fh-brand { display: flex; align-items: center; gap: 8px; }
.fh-mark {
  width: 30px; height: 30px; border-radius: 8px;
  background: linear-gradient(135deg, var(--cosmic-violet), var(--cosmic-cyan));
  color: #fff; font-family: var(--font-display); font-size: 14px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 18px rgba(145,94,255,0.55);
}
.fh-brand-text { font-size: 15px; font-weight: 700; color: #fff; font-family: var(--font-display); letter-spacing: 0.3px; }
.fh-tabs {
  position: relative; display: flex; gap: 4px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 999px; padding: 4px;
}
.fh-tab {
  position: relative; z-index: 1; padding: 7px 18px; border-radius: 999px;
  color: #9aa3d4; font-size: 13.5px; font-weight: 500; text-decoration: none;
  white-space: nowrap; transition: color 250ms ease;
}
.fh-tab:hover { color: #fff; }
.fh-tab.active { color: #fff; font-weight: 600; }
.fh-pill {
  position: absolute; top: 4px; bottom: 4px; left: 0; z-index: 0;
  background: linear-gradient(135deg, rgba(145,94,255,0.9), rgba(0,188,212,0.8));
  border-radius: 999px; box-shadow: 0 6px 18px -4px rgba(145,94,255,0.6);
  transition: all 380ms cubic-bezier(0.4,0,0.1,1); pointer-events: none;
}
.fh-search { position: relative; width: 260px; max-width: 30vw; margin-left: var(--s-sm); }
.fh-search-icon {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; color: var(--cosmic-text-dim); pointer-events: none;
}
.fh-search input {
  width: 100%; height: 38px; padding: 0 14px 0 36px; border-radius: 999px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
  color: #e8ebff; font-size: 13px; transition: all var(--t-fast);
}
.fh-search input::placeholder { color: var(--cosmic-text-dim); }
.fh-search input:focus {
  border-color: rgba(0,188,212,0.6); background: rgba(255,255,255,0.1);
  box-shadow: 0 0 0 3px rgba(0,188,212,0.15); outline: none;
}
.fh-search-mobile { display: none; color: var(--cosmic-text); margin-left: var(--s-sm); }
.fh-right { margin-left: auto; display: flex; align-items: center; gap: var(--s-sm); color: var(--cosmic-text); flex-shrink: 0; }
.fh-user { position: relative; }
.fh-trigger { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 4px 8px; border-radius: var(--r-md); transition: background var(--t-fast); }
.fh-trigger:hover { background: rgba(255,255,255,0.08); }
.fh-chevron { width: 14px; height: 14px; color: var(--cosmic-text); transition: transform var(--t-fast); }
.fh-dropdown.active .fh-chevron { transform: rotate(180deg); }
.fh-dropdown {
  position: absolute; top: 100%; right: 0; margin-top: var(--s-sm);
  background: var(--bg); border-radius: var(--r-md); box-shadow: var(--sh-lg);
  min-width: 200px; padding: var(--s-sm); opacity: 0; visibility: hidden;
  transform: translateY(-8px); transition: all var(--t-fast); z-index: 101;
}
.fh-dropdown.active { opacity: 1; visibility: visible; transform: translateY(0); }
.fh-dd-item { display: flex; align-items: center; gap: var(--s-sm); padding: 10px 12px; color: var(--text-primary); font-size: 14px; border-radius: var(--r-sm); transition: background var(--t-fast); cursor: pointer; width: 100%; text-decoration: none; }
.fh-dd-item:hover { background: var(--bg-dark); }
.fh-dd-item.danger { color: var(--error); }
.fh-dd-divider { height: 1px; background: var(--divider); margin: var(--s-xs) 0; }
.fh-login {
  background: linear-gradient(135deg, var(--cosmic-violet), var(--cosmic-cyan));
  color: #fff; padding: 8px 22px; border-radius: 999px; font-size: 14px;
  font-weight: 600; font-family: var(--font-display);
  box-shadow: 0 0 18px rgba(145,94,255,0.5); text-decoration: none;
  transition: all var(--t-fast); white-space: nowrap;
}
.fh-login:hover { transform: translateY(-1px); box-shadow: 0 0 26px rgba(145,94,255,0.7); color: #fff; }
@media (max-width: 768px) {
  .fh-search { display: none; }
  .fh-search-mobile { display: flex; align-items: center; }
  .fh-brand-text { display: none; }
  .fh-back span { display: none; }
  .fh-tab { padding: 7px 12px; font-size: 12.5px; }
}
</style>
