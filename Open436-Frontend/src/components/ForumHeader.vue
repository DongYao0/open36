<template>
  <header class="forum-header">
    <div class="fh-left">
      <router-link to="/" class="fh-back" title="返回首页">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        <span>首页</span>
      </router-link>
      <span class="fh-sep"></span>
      <div class="fh-brand">
        <div class="fh-mark">O</div>
        <span class="fh-brand-text">论坛</span>
      </div>
    </div>

    <div class="fh-search">
      <input v-model="searchQuery" placeholder="搜索帖子..." @keypress.enter="doSearch" />
      <svg class="fh-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
    </div>

    <div class="fh-right">
      <button class="fh-menu-btn" @click="ui.toggleSidebar()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="15" y2="12"/><line x1="3" y1="18" x2="18" y2="18"/>
        </svg>
      </button>

      <div v-if="auth.isLoggedIn" class="fh-user">
        <div class="fh-trigger" @click="dropdownOpen = !dropdownOpen">
          <img :src="auth.isVisitor ? 'https://ui-avatars.com/api/?name=Guest&background=9E9E9E&color=fff&size=40' : auth.avatar"
               class="avatar avatar-sm" :alt="auth.isVisitor ? '游客' : auth.nickname" />
          <svg class="fh-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
        <div class="fh-dropdown" :class="{ active: dropdownOpen }">
          <router-link to="/mine" class="fh-dd-item" @click="dropdownOpen = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            个人中心
          </router-link>
          <router-link to="/forum/favorites" class="fh-dd-item" @click="dropdownOpen = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
            我的收藏
          </router-link>
          <div class="fh-dd-divider"></div>
          <button class="fh-dd-item danger" @click="handleLogout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            {{ auth.isVisitor ? '退出游客模式' : '退出登录' }}
          </button>
        </div>
      </div>

      <router-link v-else to="/login" class="btn btn-primary btn-sm">登录</router-link>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const auth = useAuthStore()
const ui = useUIStore()

const searchQuery = ref('')
const dropdownOpen = ref(false)

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

function closeDropdown(e) {
  if (!e.target.closest('.fh-user')) dropdownOpen.value = false
}

onMounted(() => { document.addEventListener('click', closeDropdown) })
onUnmounted(() => { document.removeEventListener('click', closeDropdown) })
</script>

<style scoped>
.forum-header {
  position: fixed; top: 0; left: 0; right: 0; height: var(--navbar-h);
  background: var(--bg); border-bottom: 1px solid var(--divider);
  display: flex; align-items: center; padding: 0 var(--s-lg);
  z-index: 100; gap: var(--s-lg);
}
.fh-left { display: flex; align-items: center; gap: var(--s-sm); flex-shrink: 0; }
.fh-back {
  display: inline-flex; align-items: center; gap: 6px;
  color: var(--text-secondary); font-size: 13px; font-weight: 500;
  text-decoration: none; padding: 6px 10px; border-radius: var(--r-sm);
  transition: all var(--t-fast);
}
.fh-back:hover { color: var(--primary); background: var(--primary-bg); }
.fh-sep { width: 1px; height: 24px; background: var(--divider); }
.fh-brand { display: flex; align-items: center; gap: 8px; }
.fh-mark {
  width: 30px; height: 30px; border-radius: 6px;
  background: var(--primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800;
}
.fh-brand-text { font-size: 16px; font-weight: 700; color: var(--text-primary); letter-spacing: 0.5px; }

.fh-search {
  position: relative; flex: 1; max-width: 420px; margin: 0 auto;
}
.fh-search input {
  width: 100%; height: 36px; padding: 0 12px 0 36px;
  border: 1px solid var(--divider); border-radius: 18px;
  background: var(--bg-secondary); font-size: 14px; transition: all var(--t-fast);
}
.fh-search input:focus { border-color: var(--primary); background: var(--bg); box-shadow: 0 0 0 3px rgba(25,118,210,0.08); }
.fh-search input::placeholder { color: var(--text-disabled); }
.fh-search-icon {
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; color: var(--text-disabled);
}

.fh-right { display: flex; align-items: center; gap: var(--s-sm); flex-shrink: 0; }
.fh-menu-btn {
  display: none; width: 36px; height: 36px; border-radius: var(--r-sm);
  align-items: center; justify-content: center; color: var(--text-secondary);
  transition: all var(--t-fast);
}
.fh-menu-btn svg { width: 20px; height: 20px; }
.fh-menu-btn:hover { background: var(--bg-dark); color: var(--text-primary); }

.fh-user { position: relative; }
.fh-trigger {
  display: flex; align-items: center; gap: 6px; cursor: pointer;
  padding: 4px 8px; border-radius: var(--r-md); transition: background var(--t-fast);
}
.fh-trigger:hover { background: var(--bg-dark); }
.fh-chevron { width: 14px; height: 14px; color: var(--text-secondary); transition: transform var(--t-fast); }
.fh-dropdown.active .fh-chevron { transform: rotate(180deg); }

.fh-dropdown {
  position: absolute; top: 100%; right: 0; margin-top: var(--s-sm);
  background: var(--bg); border-radius: var(--r-md); box-shadow: var(--sh-lg);
  min-width: 200px; padding: var(--s-sm); opacity: 0; visibility: hidden;
  transform: translateY(-8px); transition: all var(--t-fast); z-index: 101;
}
.fh-dropdown.active { opacity: 1; visibility: visible; transform: translateY(0); }

.fh-dd-item {
  display: flex; align-items: center; gap: var(--s-sm); padding: 10px 12px;
  color: var(--text-primary); font-size: 14px; border-radius: var(--r-sm);
  transition: background var(--t-fast); cursor: pointer; width: 100%;
  text-decoration: none;
}
.fh-dd-item:hover { background: var(--bg-dark); }
.fh-dd-item.danger { color: var(--error); }
.fh-dd-label {
  padding: 8px 12px 4px; font-size: 11px; font-weight: 600;
  color: var(--text-disabled); text-transform: uppercase; letter-spacing: 0.5px;
}
.fh-dd-divider { height: 1px; background: var(--divider); margin: var(--s-xs) 0; }

@media (max-width: 768px) {
  .fh-search { display: none; }
  .fh-menu-btn { display: flex; }
  .fh-brand-text { display: none; }
}
</style>
