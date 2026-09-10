<template>
  <header class="app-navbar">
    <nav class="navbar-inner" aria-label="主导航">
      <a class="navbar-brand" href="/" aria-label="Open436 首页">
        <img src="@/assets/logo.svg" alt="Open436" />
        <span>OPEN436</span><em>技术社区</em>
      </a>
      <div class="navbar-tabs">
        <router-link v-for="tab in tabs" :key="tab.path" :to="tab.path" class="nav-tab" :class="{ active: isTabActive(tab) }">{{ tab.label }}</router-link>
      </div>
      <router-link v-if="!auth.isLoggedIn" to="/login" class="login-link">登录</router-link>
      <div v-else class="navbar-user" @click.stop="dropdownOpen = !dropdownOpen">
        <img :src="avatar" class="user-avatar" :alt="displayName" />
        <span>{{ displayName }}</span>
        <div class="navbar-dropdown" :class="{ active: dropdownOpen }">
          <router-link to="/mine" class="dropdown-item" @click="dropdownOpen = false">个人中心</router-link>
          <button class="dropdown-item danger" @click="handleLogout">{{ auth.isVisitor ? '退出游客模式' : '退出登录' }}</button>
        </div>
      </div>
      <button class="mobile-toggle" type="button" aria-label="打开侧边栏" @click="ui.toggleSidebar()"><i></i><i></i><i></i></button>
    </nav>
  </header>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const ui = useUIStore()
const dropdownOpen = ref(false)
const tabs = [
  { label: '论坛', path: '/forum' }, { label: '赛事', path: '/contests' },
  { label: '公告', path: '/announcements' }, { label: '算法', path: '/quiz' }
]
const displayName = computed(() => auth.isVisitor ? '游客' : auth.nickname || '个人中心')
const avatar = computed(() => auth.isVisitor
  ? 'https://ui-avatars.com/api/?name=Guest&background=5546d9&color=fff&size=64'
  : auth.avatar || 'https://ui-avatars.com/api/?name=Open436&background=5546d9&color=fff&size=64')
function isTabActive(tab) { return route.path.startsWith(tab.path) }
function handleLogout() { dropdownOpen.value = false; auth.logout(); router.push('/login') }
function closeDropdowns(event) { if (!event.target.closest('.navbar-user')) dropdownOpen.value = false }
onMounted(() => document.addEventListener('click', closeDropdowns))
onUnmounted(() => document.removeEventListener('click', closeDropdowns))
</script>

<style scoped>
.app-navbar{position:fixed;inset:0 0 auto;z-index:100;height:68px;background:linear-gradient(90deg,rgba(14,10,55,.98),rgba(40,30,111,.94));box-shadow:0 10px 28px rgba(7,5,29,.24);color:#fff}
.navbar-inner{display:flex;align-items:center;width:min(1280px,calc(100% - 48px));height:100%;margin:auto;gap:32px}.navbar-brand{display:flex;align-items:center;gap:9px;margin-right:30px;color:#fff;text-decoration:none;font-weight:800;letter-spacing:.07em}.navbar-brand img{width:34px;height:34px;object-fit:contain}.navbar-brand span{font-size:16px}.navbar-brand em{padding-left:9px;border-left:1px solid rgba(255,255,255,.34);color:rgba(255,255,255,.76);font-size:12px;font-style:normal;font-weight:500;letter-spacing:.04em}.navbar-tabs{display:flex;align-items:center;gap:5px}.nav-tab{padding:9px 17px;border-radius:22px;color:rgba(255,255,255,.72);font-size:14px;text-decoration:none;transition:.2s}.nav-tab:hover,.nav-tab.active{color:#fff;background:rgba(255,255,255,.14)}.login-link{margin-left:auto;padding:9px 19px;border:1px solid rgba(255,255,255,.42);border-radius:22px;color:#fff;font-size:14px;text-decoration:none;transition:.2s}.login-link:hover{background:#fff;color:#3a2ba4}.navbar-user{position:relative;display:flex;align-items:center;gap:8px;margin-left:auto;cursor:pointer;font-size:14px}.user-avatar{width:34px;height:34px;border:2px solid rgba(255,255,255,.55);border-radius:50%;object-fit:cover}.navbar-dropdown{position:absolute;top:47px;right:0;display:grid;min-width:142px;padding:6px;border:1px solid rgba(255,255,255,.13);border-radius:12px;background:#17113f;box-shadow:0 16px 34px rgba(0,0,0,.28);opacity:0;visibility:hidden;transform:translateY(-5px);transition:.18s}.navbar-dropdown.active{opacity:1;visibility:visible;transform:translateY(0)}.dropdown-item{padding:10px 12px;border:0;border-radius:7px;background:none;color:#f4f2ff;font:inherit;font-size:13px;text-align:left;text-decoration:none;cursor:pointer}.dropdown-item:hover{background:rgba(255,255,255,.1)}.dropdown-item.danger{color:#ffb8c2}.mobile-toggle{display:none;margin-left:auto;width:35px;height:35px;border:0;border-radius:8px;background:rgba(255,255,255,.12)}.mobile-toggle i{display:block;width:17px;height:2px;margin:4px auto;background:#fff}
@media(max-width:760px){.app-navbar{height:60px}.navbar-inner{width:calc(100% - 28px);gap:14px}.navbar-brand{margin-right:auto}.navbar-brand em,.navbar-tabs,.navbar-user span,.login-link{display:none}.navbar-brand img{width:31px;height:31px}.mobile-toggle{display:block}.navbar-user{margin-left:0}.navbar-dropdown{right:0}.login-link{margin:0}}
</style>
