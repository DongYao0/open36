<template>
  <header class="res-header">
    <div class="rh-left">
      <router-link to="/" class="rh-back" title="返回首页">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        <span>首页</span>
      </router-link>
      <span class="rh-sep"></span>
      <div class="rh-brand">
        <div class="rh-mark">R</div>
        <span class="rh-brand-text">资源分享</span>
      </div>
    </div>

    <div class="rh-right">
      <div v-if="auth.isLoggedIn" class="rh-user">
        <div class="rh-trigger" @click="dropdownOpen = !dropdownOpen">
          <img :src="auth.isVisitor ? 'https://ui-avatars.com/api/?name=Guest&background=9E9E9E&color=fff&size=40' : auth.avatar"
               class="avatar avatar-sm" :alt="auth.isVisitor ? '游客' : auth.nickname" />
          <svg class="rh-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
        <div class="rh-dropdown" :class="{ active: dropdownOpen }">
          <router-link to="/mine" class="rh-dd-item" @click="dropdownOpen = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            个人中心
          </router-link>
          <div class="rh-dd-divider"></div>
          <button class="rh-dd-item danger" @click="handleLogout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            {{ auth.isVisitor ? '退出游客模式' : '退出登录' }}
          </button>
        </div>
      </div>
      <router-link v-else to="/login" class="btn btn-primary btn-sm">登录</router-link>
    </div>
  </header>
  <div class="res-layout">
    <div class="res-main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const dropdownOpen = ref(false)

function handleLogout() {
  dropdownOpen.value = false
  auth.logout()
  router.push('/login')
}

function closeDropdown(e) {
  if (!e.target.closest('.rh-user')) dropdownOpen.value = false
}

onMounted(() => { document.addEventListener('click', closeDropdown) })
onUnmounted(() => { document.removeEventListener('click', closeDropdown) })
</script>

<style scoped>
.res-header {
  position: fixed; top: 0; left: 0; right: 0; height: var(--navbar-h);
  background: var(--bg); border-bottom: 1px solid var(--divider);
  display: flex; align-items: center; padding: 0 var(--s-lg);
  z-index: 100; gap: var(--s-lg);
}
.rh-left { display: flex; align-items: center; gap: var(--s-sm); flex-shrink: 0; }
.rh-back {
  display: inline-flex; align-items: center; gap: 6px;
  color: var(--text-secondary); font-size: 13px; font-weight: 500;
  text-decoration: none; padding: 6px 10px; border-radius: var(--r-sm);
  transition: all var(--t-fast);
}
.rh-back:hover { color: #D97706; background: rgba(245,158,11,0.08); }
.rh-sep { width: 1px; height: 24px; background: var(--divider); }
.rh-brand { display: flex; align-items: center; gap: 8px; }
.rh-mark {
  width: 30px; height: 30px; border-radius: 6px;
  background: linear-gradient(135deg, #F59E0B, #F97316); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800;
}
.rh-brand-text { font-size: 16px; font-weight: 700; color: var(--text-primary); letter-spacing: 0.5px; }

.rh-right { display: flex; align-items: center; gap: var(--s-sm); margin-left: auto; }
.rh-user { position: relative; }
.rh-trigger {
  display: flex; align-items: center; gap: 6px; cursor: pointer;
  padding: 4px 8px; border-radius: var(--r-md); transition: background var(--t-fast);
}
.rh-trigger:hover { background: var(--bg-dark); }
.rh-chevron { width: 14px; height: 14px; color: var(--text-secondary); transition: transform var(--t-fast); }
.rh-dropdown.active .rh-chevron { transform: rotate(180deg); }

.rh-dropdown {
  position: absolute; top: 100%; right: 0; margin-top: var(--s-sm);
  background: var(--bg); border-radius: var(--r-md); box-shadow: var(--sh-lg);
  min-width: 200px; padding: var(--s-sm); opacity: 0; visibility: hidden;
  transform: translateY(-8px); transition: all var(--t-fast); z-index: 101;
}
.rh-dropdown.active { opacity: 1; visibility: visible; transform: translateY(0); }

.rh-dd-item {
  display: flex; align-items: center; gap: var(--s-sm); padding: 10px 12px;
  color: var(--text-primary); font-size: 14px; border-radius: var(--r-sm);
  transition: background var(--t-fast); cursor: pointer; width: 100%;
  text-decoration: none;
}
.rh-dd-item:hover { background: var(--bg-dark); }
.rh-dd-item.danger { color: var(--error); }
.rh-dd-divider { height: 1px; background: var(--divider); margin: var(--s-xs) 0; }

.res-layout { padding-top: var(--navbar-h); }
.res-main { max-width: 1200px; margin: 0 auto; padding: var(--s-lg); }
</style>
