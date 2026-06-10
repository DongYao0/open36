<template>
  <nav class="navbar" :class="{ 'sidebar-visible': showSidebar }">
    <router-link to="/" class="navbar-brand">
      <div class="brand-logo">O</div>
      <span class="brand-text">OPEN436</span>
    </router-link>

    <div class="navbar-tabs">
      <router-link
        v-for="tab in tabs"
        :key="tab.path"
        :to="tab.path"
        class="nav-tab"
        :class="{ active: isTabActive(tab) }"
      >
        {{ tab.label }}
      </router-link>
      <a href="javascript:void(0)" class="nav-tab" :class="{ active: route.path.startsWith('/algo') }" @click="goToAlgo">
        算法
      </a>
      <router-link to="/mine" class="nav-tab" :class="{ active: route.path === '/mine' }">我的</router-link>
    </div>

    <div class="navbar-search">
      <input
        v-model="searchQuery"
        placeholder="搜索帖子..."
        @keypress.enter="doSearch"
      />
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
    </div>

    <div class="navbar-user" v-if="auth.isLoggedIn">
      <div class="user-trigger" @click="dropdownOpen = !dropdownOpen">
        <img :src="auth.isVisitor ? 'https://ui-avatars.com/api/?name=Guest&background=9E9E9E&color=fff&size=40' : auth.avatar" class="avatar avatar-sm" :alt="auth.isVisitor ? '游客' : auth.nickname" />
        <span class="user-name">{{ auth.isVisitor ? '游客' : auth.nickname }}</span>
        <span v-if="auth.isReadOnly" class="guest-badge">游客</span>
        <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
      <div class="navbar-dropdown" :class="{ active: dropdownOpen }">
        <button class="dropdown-item danger" @click="handleLogout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          {{ auth.isVisitor ? '退出游客模式' : '退出登录' }}
        </button>
      </div>
    </div>

    <div v-else class="navbar-auth">
      <router-link to="/login" class="btn btn-primary btn-sm">登录</router-link>
    </div>

    <button class="mobile-toggle" @click="ui.toggleSidebar()">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
    </button>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const ui = useUIStore()

const searchQuery = ref('')
const dropdownOpen = ref(false)
const showSidebar = ref(true)

const tabs = [
  { key: 'home', label: '首页', path: '/' },
  { key: 'forum', label: '论坛', path: '/forum' },
  { key: 'resources', label: '资源', path: '/resources' },
  { key: 'announcements', label: '公告', path: '/announcements' }
]

function isTabActive(tab) {
  if (tab.path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(tab.path)
}

async function goToAlgo() {
  if (auth.isGuest) {
    ui.showToast('审核通过后方可进入算法平台', 'warning')
    return
  }
  if (auth.isLoggedIn && !auth.isVisitor) {
    await auth.syncToHoj()
  }
  window.location.href = '/algo/'
}

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

function closeDropdowns(e) {
  if (!e.target.closest('.navbar-user')) dropdownOpen.value = false
}

onMounted(() => { document.addEventListener('click', closeDropdowns) })
onUnmounted(() => { document.removeEventListener('click', closeDropdowns) })
</script>

<style scoped>
.navbar {
  position: fixed; top: 0; left: 0; right: 0; height: var(--navbar-h);
  background: var(--primary); color: #fff; display: flex; align-items: center;
  padding: 0 var(--s-lg); z-index: 100; box-shadow: var(--sh-md);
}
.navbar-brand {
  display: flex; align-items: center; gap: var(--s-sm);
  color: #fff; text-decoration: none; margin-right: var(--s-xl);
}
.brand-logo {
  width: 36px; height: 36px; background: rgba(255,255,255,0.2);
  border-radius: var(--r-sm); display: flex; align-items: center;
  justify-content: center; font-size: 18px; font-weight: 700;
}
.brand-text { font-size: 18px; font-weight: 700; letter-spacing: 1px; }
.navbar-tabs {
  display: flex; align-items: center; gap: 4px;
}
.nav-tab {
  padding: 6px 16px;
  border-radius: 20px;
  color: rgba(255,255,255,0.7);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all var(--t-fast);
}
.nav-tab:hover {
  color: #fff;
  background: rgba(255,255,255,0.1);
}
.nav-tab.active {
  color: #fff;
  background: rgba(255,255,255,0.18);
  font-weight: 600;
}
.navbar-search {
  position: relative; margin-left: auto; margin-right: var(--s-lg);
}
.navbar-search input {
  width: 280px; max-width: 400px; height: 36px; padding: 0 12px 0 36px;
  border: none; border-radius: 18px; background: rgba(255,255,255,0.2);
  color: #fff; font-size: 14px; transition: all var(--t-fast);
}
.navbar-search input::placeholder { color: rgba(255,255,255,0.6); }
.navbar-search input:focus { background: rgba(255,255,255,0.3); width: 320px; }
.search-icon {
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; color: rgba(255,255,255,0.6);
}
.navbar-user { position: relative; }
.user-trigger {
  display: flex; align-items: center; gap: var(--s-sm); cursor: pointer;
  padding: 4px 8px; border-radius: var(--r-md); transition: background var(--t-fast);
}
.user-trigger:hover { background: rgba(255,255,255,0.1); }
.user-name { font-size: 14px; }
.guest-badge { font-size: 11px; background: rgba(255,152,0,0.2); color: var(--warning); padding: 1px 6px; border-radius: 10px; margin-left: 2px; font-weight: 500; }
.chevron { width: 14px; height: 14px; transition: transform var(--t-fast); }
.navbar-dropdown.active .chevron { transform: rotate(180deg); }
.navbar-dropdown {
  position: absolute; top: 100%; right: 0; margin-top: var(--s-sm);
  background: var(--bg); border-radius: var(--r-md); box-shadow: var(--sh-lg);
  min-width: 200px; padding: var(--s-sm); opacity: 0; visibility: hidden;
  transform: translateY(-8px); transition: all var(--t-fast); z-index: 101;
}
.navbar-dropdown.active { opacity: 1; visibility: visible; transform: translateY(0); }
.dropdown-item {
  display: flex; align-items: center; gap: var(--s-sm); padding: 10px 12px;
  color: var(--text-primary); font-size: 14px; border-radius: var(--r-sm);
  transition: background var(--t-fast); cursor: pointer; width: 100%;
}
.dropdown-item:hover { background: var(--bg-dark); }
.dropdown-item.danger { color: var(--error); }
.dropdown-divider { height: 1px; background: var(--divider); margin: var(--s-xs) 0; }
.mobile-toggle { display: none; color: #fff; }
.navbar-auth { margin-left: auto; }

@media (max-width: 768px) {
  .navbar-search { display: none; }
  .mobile-toggle { display: flex; align-items: center; }
  .navbar-auth { margin-left: auto; margin-right: var(--s-sm); }
}
</style>
