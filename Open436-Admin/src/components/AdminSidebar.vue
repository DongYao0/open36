<template>
  <div class="sidebar">
    <div class="sidebar-logo">
      <span class="logo-icon">O</span>
      <span v-show="!collapsed" class="logo-text">Open436</span>
    </div>
    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      background-color="#001529"
      text-color="#ffffffa6"
      active-text-color="#fff"
      router
      :collapse-transition="false"
    >
      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <template #title>仪表盘</template>
      </el-menu-item>
      <el-menu-item index="/users">
        <el-icon><User /></el-icon>
        <template #title>用户管理</template>
      </el-menu-item>
      <el-menu-item index="/forum">
        <el-icon><ChatDotRound /></el-icon>
        <template #title>论坛管理</template>
      </el-menu-item>
      <el-menu-item @click="openHojAdmin">
        <el-icon><EditPen /></el-icon>
        <template #title>算法管理</template>
      </el-menu-item>
      <el-menu-item index="/ai-chat">
        <el-icon><MagicStick /></el-icon>
        <template #title>AI 助手</template>
      </el-menu-item>
      <el-sub-menu index="enrollment">
        <template #title>
          <el-icon><UserFilled /></el-icon>
          <span>纳新管理</span>
        </template>
        <el-menu-item index="/enrollment/application">
          <el-icon><DocumentChecked /></el-icon>
          <template #title>报名管理</template>
        </el-menu-item>
        <el-menu-item index="/enrollment/interview">
          <el-icon><ChatLineRound /></el-icon>
          <template #title>面试管理</template>
        </el-menu-item>
        <el-menu-item index="/enrollment/assignment">
          <el-icon><Promotion /></el-icon>
          <template #title>作业分发</template>
        </el-menu-item>
        <el-menu-item index="/enrollment/collection">
          <el-icon><FolderChecked /></el-icon>
          <template #title>作业收集</template>
        </el-menu-item>
      </el-sub-menu>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const appStore = useAppStore()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const collapsed = computed(() => appStore.sidebarCollapsed)

const openHojAdmin = async () => {
  await authStore.syncToHoj()
  // 跨端口 localStorage 不共享，通过 URL 参数将 HOJ token 传递给目标页
  const hojToken = localStorage.getItem('token') || ''
  let username = ''
  let role = ''
  const userInfoStr = localStorage.getItem('userInfo')
  if (userInfoStr) {
    try {
      const ui = JSON.parse(userInfoStr)
      username = ui.username || ''
      role = (ui.roleList && ui.roleList[0]) || ''
    } catch (e) {}
  }
  // 在当前页面跳转，直接进入 HOJ 管理后台 dashboard，不再经过 login 页
  const hojVueBase = import.meta.env.VITE_HOJ_VUE_URL || `${window.location.protocol}//${window.location.hostname}:8066`
  const url = `${hojVueBase}/algo/admin/dashboard?hoj_token=${encodeURIComponent(hojToken)}&username=${encodeURIComponent(username)}&role=${encodeURIComponent(role)}`
  window.location.href = url
}

</script>

<style lang="scss" scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #ffffff1a;
}
.logo-icon {
  width: 36px;
  height: 36px;
  background: #1976D2;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}
.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}
.el-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}
</style>
