<template>
  <div class="algo-blocked" v-if="blockReason">
    <div class="blocked-card">
      <div class="blocked-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="48" height="48">
          <circle cx="12" cy="12" r="10"/>
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
        </svg>
      </div>
      <h2>无法进入算法平台</h2>
      <p>{{ blockReason }}</p>
      <router-link to="/" class="back-btn">返回首页</router-link>
    </div>
  </div>
  <div class="algo-loading" v-else>
    <p>正在进入算法系统...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const blockReason = ref('')

onMounted(async () => {
  // 游客/待审核用户不可进入算法平台
  if (auth.isVisitor) {
    blockReason.value = '游客模式不可进行算法答题，请先报名成为正式成员后再进入算法平台'
    return
  }
  if (auth.user?.status === 'pending') {
    blockReason.value = '您的报名正在审核中，审核通过后即可进入算法平台进行答题'
    return
  }

  if (auth.isLoggedIn) {
    await auth.syncToHoj()
  }
  window.location.href = '/algo/'
})
</script>

<style scoped>
.algo-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: #909399;
  font-size: 14px;
}
.algo-blocked {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-secondary);
  padding: var(--s-base);
}
.blocked-card {
  text-align: center;
  background: var(--bg);
  padding: 48px 40px;
  border-radius: var(--r-lg);
  box-shadow: var(--sh-lg);
  max-width: 420px;
  width: 100%;
}
.blocked-icon {
  color: var(--warning, #e6a23c);
  margin-bottom: var(--s-lg);
}
.blocked-card h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--s-md);
}
.blocked-card p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: var(--s-xl);
}
.back-btn {
  display: inline-block;
  padding: 10px 28px;
  background: var(--primary, #1976d2);
  color: #fff;
  border-radius: var(--r-sm);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: opacity var(--t-fast);
}
.back-btn:hover {
  opacity: 0.85;
}
</style>
