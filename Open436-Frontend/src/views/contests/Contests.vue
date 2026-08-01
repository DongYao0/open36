<template>
  <div class="forum-layout">
    <div class="coming-soon">
      <div class="cs-emoji">🏆</div>
      <h1 class="cs-title">赛事功能开发中</h1>
      <p class="cs-desc">赛事历程功能正在开发中，敬请期待。</p>
      <div class="cs-features">
        <span>赛事历程</span>
      </div>
      <p class="cs-hint">Coming Soon</p>
    </div>
  </div>
</template>

<script setup>
// 赛事功能待开发 —— 当前为占位页
</script>

<style scoped>
.coming-soon {
  min-height: calc(100vh - var(--navbar-h));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
  gap: 0.5rem;
}
.cs-emoji {
  font-size: 4rem;
  margin-bottom: 0.5rem;
  animation: cs-bounce 2s ease-in-out infinite;
}
.cs-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.cs-desc {
  color: var(--text-secondary);
  font-size: 0.9375rem;
  margin: 0;
}
.cs-features {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
  margin: 1rem 0 0.5rem;
}
.cs-features span {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  background: var(--primary-bg);
  color: var(--primary);
  font-weight: 500;
}
.cs-hint {
  color: var(--text-disabled);
  font-size: 0.75rem;
  letter-spacing: 2px;
  margin: 0.5rem 0 0;
  text-transform: uppercase;
}
@keyframes cs-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
</style>
