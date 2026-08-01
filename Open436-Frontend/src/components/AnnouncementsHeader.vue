<template>
  <header class="ah">
    <!-- 左：返回首页 + 品牌 -->
    <div class="ah-left">
      <router-link to="/" class="ah-back" title="返回首页">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        <span>首页</span>
      </router-link>
      <span class="ah-sep"></span>
      <div class="ah-brand">
        <div class="ah-mark">O</div>
        <span class="ah-brand-text">公告通知</span>
      </div>
    </div>

    <!-- 中：回到论坛入口 -->
    <nav class="ah-nav">
      <router-link to="/forum/tech" class="ah-link">返回论坛</router-link>
    </nav>

    <!-- 右：主题切换 + 用户下拉 / 登录 -->
    <div class="ah-right">
      <ThemeToggle class="ah-theme" />
      <div v-if="auth.isLoggedIn" class="ah-user">
        <div class="ah-trigger" @click="dropdownOpen = !dropdownOpen">
          <img :src="auth.isVisitor ? 'https://ui-avatars.com/api/?name=Guest&background=9E9E9E&color=fff&size=40' : auth.avatar" class="avatar avatar-sm" :alt="auth.isVisitor ? '游客' : auth.nickname" />
          <span class="ah-name">{{ auth.isVisitor ? '游客' : auth.nickname }}</span>
          <svg class="ah-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <div class="ah-dropdown" :class="{ active: dropdownOpen }">
          <router-link to="/mine" class="ah-dd-item" @click="dropdownOpen = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>个人中心
          </router-link>
          <router-link to="/forum/favorites" class="ah-dd-item" @click="dropdownOpen = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>我的收藏
          </router-link>
          <div class="ah-dd-divider"></div>
          <button class="ah-dd-item danger" @click="handleLogout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            {{ auth.isVisitor ? '退出游客模式' : '退出登录' }}
          </button>
        </div>
      </div>
      <router-link v-else to="/login" class="ah-login">登录</router-link>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const auth = useAuthStore()
const dropdownOpen = ref(false)

function handleLogout() {
  dropdownOpen.value = false
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.ah {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: var(--navbar-h, 56px);
  display: flex;
  align-items: center;
  gap: var(--s-lg);
  padding: 0 var(--s-xl);
  background: var(--bg);
  border-bottom: 1px solid var(--divider);
  backdrop-filter: blur(8px);
}
.ah-left { display: flex; align-items: center; gap: var(--s-base); min-width: 0; }
.ah-back {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 13px; color: var(--text-secondary);
  transition: color var(--t-fast); white-space: nowrap;
}
.ah-back:hover { color: var(--primary); }
.ah-sep { width: 1px; height: 18px; background: var(--divider); flex-shrink: 0; }
.ah-brand { display: flex; align-items: center; gap: var(--s-sm); }
.ah-mark {
  width: 28px; height: 28px; border-radius: var(--r-sm); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--primary), #7c4dff);
  color: #fff; font-weight: 800; font-size: 14px;
}
.ah-brand-text { font-size: 15px; font-weight: 600; white-space: nowrap; }

.ah-nav { flex: 1; display: flex; align-items: center; }
.ah-link {
  font-size: 14px; color: var(--text-secondary);
  padding: 6px 12px; border-radius: var(--r-sm);
  transition: all var(--t-fast); white-space: nowrap;
}
.ah-link:hover { color: var(--primary); background: var(--bg-dark); }

.ah-right { display: flex; align-items: center; gap: var(--s-base); margin-left: auto; }
.ah-theme { display: inline-flex; align-items: center; justify-content: center; }
.ah-user { position: relative; }
.ah-trigger {
  display: flex; align-items: center; gap: var(--s-xs);
  padding: 4px 8px; border-radius: 999px; cursor: pointer;
  transition: background var(--t-fast);
}
.ah-trigger:hover { background: var(--bg-dark); }
.ah-name { font-size: 13px; color: var(--text-primary); max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ah-chevron { width: 14px; height: 14px; color: var(--text-secondary); transition: transform var(--t-fast); }
.ah-trigger:hover .ah-chevron { transform: rotate(180deg); }

.ah-dropdown {
  position: absolute; top: calc(100% + 8px); right: 0; min-width: 180px;
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  box-shadow: var(--shadow-md); padding: var(--s-xs); opacity: 0; visibility: hidden;
  transform: translateY(-6px); transition: all var(--t-fast); z-index: 110;
}
.ah-dropdown.active { opacity: 1; visibility: visible; transform: translateY(0); }
.ah-dd-item {
  display: flex; align-items: center; gap: var(--s-sm);
  width: 100%; padding: 10px var(--s-base); border-radius: var(--r-sm);
  font-size: 14px; color: var(--text-primary); cursor: pointer;
  background: none; border: none; text-align: left; transition: background var(--t-fast);
}
.ah-dd-item:hover { background: var(--bg-dark); }
.ah-dd-item.danger { color: var(--error); }
.ah-dd-divider { height: 1px; background: var(--divider); margin: var(--s-xs) 0; }
.ah-login {
  font-size: 14px; font-weight: 500; color: var(--primary);
  padding: 6px 14px; border: 1px solid var(--primary); border-radius: 999px;
  transition: all var(--t-fast); white-space: nowrap;
}
.ah-login:hover { background: var(--primary); color: #fff; }
</style>
