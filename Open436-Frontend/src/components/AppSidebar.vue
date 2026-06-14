<template>
  <aside class="sidebar" :class="{ active: ui.sidebarOpen }">
    <div class="sidebar-header">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
      </svg>
      板块分类
    </div>
    <nav class="sidebar-menu">
      <a
        v-for="s in sectionStore.forumSections"
        :key="s.key"
        class="sidebar-link"
        :class="{ active: sectionStore.activeSection === s.key, 'sidebar-link-all': s.key === 'all' }"
        @click="selectSection(s.key)"
      >
        <div class="sidebar-icon" :style="{ background: s.color + '12', color: s.color }">
          <img
            :src="`https://api.iconify.design/${s.icon}.svg?color=%23${s.color.slice(1)}&width=20`"
            :alt="s.name"
            width="20" height="20"
          />
        </div>
        <span class="sidebar-name">{{ s.name }}</span>
        <span v-if="s.count && s.key !== 'all'" class="sidebar-count">{{ s.count }}</span>
      </a>
    </nav>
  </aside>
  <div v-if="ui.sidebarOpen" class="sidebar-overlay" @click="ui.toggleSidebar()"></div>
</template>

<script setup>
import { useSectionStore } from '@/stores/section'
import { useUIStore } from '@/stores/ui'

const sectionStore = useSectionStore()
const ui = useUIStore()
const emit = defineEmits(['select'])

function selectSection(key) {
  sectionStore.setActive(key)
  emit('select', key)
  if (window.innerWidth < 960) ui.sidebarOpen = false
}
</script>

<style scoped>
.sidebar {
  position: fixed; left: 0; top: var(--navbar-h); bottom: 0;
  width: var(--sidebar-w); background: var(--bg); border-right: 1px solid var(--divider);
  padding: var(--s-lg) 0; overflow-y: auto; z-index: 50;
}
.sidebar-header {
  display: flex; align-items: center; gap: var(--s-sm);
  padding: 0 var(--s-lg) var(--s-base); font-size: 12px; font-weight: 600;
  color: var(--text-disabled); text-transform: uppercase; letter-spacing: 0.8px;
}
.sidebar-menu { display: flex; flex-direction: column; gap: 2px; padding: 0 var(--s-sm); }
.sidebar-link-all { margin-bottom: var(--s-sm); border-bottom: 1px solid var(--divider); padding-bottom: var(--s-sm); border-radius: 0; }
.sidebar-link {
  display: flex; align-items: center; gap: var(--s-md);
  padding: 10px var(--s-base); border-radius: var(--r-md);
  color: var(--text-primary); font-size: 14px; cursor: pointer;
  transition: all var(--t-fast);
}
.sidebar-link:hover { background: var(--bg-dark); }
.sidebar-link.active {
  background: var(--primary-bg); color: var(--primary); font-weight: 600;
}
.sidebar-link.active .sidebar-icon { transform: scale(1.05); }
.sidebar-icon {
  width: 32px; height: 32px; border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  transition: transform var(--t-fast);
}
.sidebar-name { flex: 1; }
.sidebar-count {
  font-size: 12px; font-weight: 500; color: var(--text-secondary);
  background: var(--bg-dark); padding: 2px 8px; border-radius: 999px;
  font-variant-numeric: tabular-nums;
}
.sidebar-link.active .sidebar-count { background: var(--primary); color: #fff; }
.sidebar-overlay { display: none; }

@media (max-width: 959px) {
  .sidebar {
    transform: translateX(-100%); transition: transform var(--t-base);
    box-shadow: var(--sh-lg);
  }
  .sidebar.active { transform: translateX(0); }
  .sidebar-overlay {
    display: block; position: fixed; inset: 0; background: rgba(0,0,0,0.3);
    z-index: 49;
  }
}
</style>
