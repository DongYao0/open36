<template>
  <div class="contests-page">
    <!-- 顶部标题 -->
    <div class="contests-hero">
      <div class="contests-hero-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="28" height="28">
          <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
          <path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20 7 22"/>
          <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20 17 22"/>
          <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>
        </svg>
      </div>
      <h1 class="contests-hero-title">赛事日历</h1>
      <p class="contests-hero-desc">了解全年各类编程竞赛与技术赛事，提前规划备赛节奏</p>
    </div>

    <!-- 月份时间线 -->
    <div class="timeline">
      <div
        v-for="month in months"
        :key="month.num"
        class="timeline-item"
        :class="{ active: selectedMonth === month.num, 'has-contests': getContests(month.num).length > 0 }"
        @click="selectMonth(month.num)"
      >
        <div class="timeline-dot">
          <span class="timeline-dot-inner"></span>
        </div>
        <div class="timeline-label">{{ month.label }}</div>
        <div class="timeline-count" v-if="getContests(month.num).length > 0">
          {{ getContests(month.num).length }}
        </div>
      </div>
    </div>

    <!-- 选中月份的赛事列表 -->
    <div class="contests-content" v-if="selectedMonth">
      <div class="contests-month-header">
        <h2>{{ selectedMonth }} 月赛事</h2>
        <span class="contests-month-count">共 {{ getContests(selectedMonth).length }} 场赛事</span>
      </div>

      <div class="contests-list" v-if="getContests(selectedMonth).length > 0">
        <div
          v-for="(contest, i) in getContests(selectedMonth)"
          :key="i"
          class="contest-card"
          :style="{ animationDelay: `${i * 60}ms` }"
        >
          <div class="contest-badge" :class="contest.level">
            {{ contest.levelText }}
          </div>
          <div class="contest-info">
            <h3 class="contest-name">{{ contest.name }}</h3>
            <p class="contest-desc">{{ contest.description }}</p>
            <div class="contest-meta">
              <span class="contest-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                {{ contest.date }}
              </span>
              <span class="contest-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                </svg>
                {{ contest.format }}
              </span>
              <span class="contest-meta-item" v-if="contest.url">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
                <a :href="contest.url" target="_blank" rel="noopener">官网链接</a>
              </span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="contests-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
          <circle cx="12" cy="12" r="10"/><line x1="8" y1="15" x2="16" y2="15"/>
          <line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
        </svg>
        <p>本月暂无已收录的赛事</p>
      </div>
    </div>

    <!-- 未选择月份时的提示 -->
    <div v-else class="contests-hint">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
      <p>点击上方月份查看该月赛事</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selectedMonth = ref(null)

const months = [
  { num: 1, label: '1月' },
  { num: 2, label: '2月' },
  { num: 3, label: '3月' },
  { num: 4, label: '4月' },
  { num: 5, label: '5月' },
  { num: 6, label: '6月' },
  { num: 7, label: '7月' },
  { num: 8, label: '8月' },
  { num: 9, label: '9月' },
  { num: 10, label: '10月' },
  { num: 11, label: '11月' },
  { num: 12, label: '12月' },
]

// 赛事数据（可后续接入后端 API）
const contests = {
  1: [
    { name: 'LeetCode 周赛', description: 'LeetCode 每周举办的比赛，包含算法题 3-4 道，适合日常练习。', date: '每周日上午', format: '线上', level: 'easy', levelText: '入门', url: 'https://leetcode.cn/contest/' },
    { name: 'Codeforces Round', description: 'Codeforces 定期举办的 Rated 比赛，题目涵盖多种难度。', date: '不定期', format: '线上', level: 'medium', levelText: '进阶', url: 'https://codeforces.com/contests' },
  ],
  2: [
    { name: '蓝桥杯省赛报名', description: '蓝桥杯软件类省赛报名阶段，面向在校大学生。', date: '2月-3月', format: '线上/线下', level: 'easy', levelText: '入门', url: 'https://dasai.lanqiao.cn/' },
  ],
  3: [
    { name: '蓝桥杯省赛', description: '蓝桥杯全国软件和信息技术专业人才大赛省赛阶段。', date: '3月-4月', format: '线下', level: 'easy', levelText: '入门', url: 'https://dasai.lanqiao.cn/' },
    { name: 'Codeforces Round', description: 'Codeforces 定期举办的 Rated 比赛。', date: '不定期', format: '线上', level: 'medium', levelText: '进阶', url: 'https://codeforces.com/contests' },
  ],
  4: [
    { name: '蓝桥杯国赛', description: '蓝桥杯全国总决赛，省赛晋级选手参加。', date: '4月-5月', format: '线下', level: 'medium', levelText: '进阶', url: 'https://dasai.lanqiao.cn/' },
    { name: 'ACM-ICPC 区域赛报名', description: '国际大学生程序设计竞赛区域赛报名。', date: '4月-5月', format: '线上', level: 'hard', levelText: '高级', url: 'https://icpc.global/' },
  ],
  5: [
    { name: 'Google Code Jam', description: 'Google 举办的全球编程竞赛，题目难度较高。', date: '4月-5月', format: '线上', level: 'hard', levelText: '高级', url: 'https://codingcompetitions.withgoogle.com/' },
    { name: 'CCPC 中国大学生程序设计竞赛', description: '中国大学生程序设计竞赛，含多个赛区。', date: '5月-10月', format: '线下', level: 'hard', levelText: '高级', url: 'https://ccpc.io/' },
  ],
  6: [
    { name: 'LeetCode 周赛/双周赛', description: 'LeetCode 每周/双周举办的比赛。', date: '固定赛程', format: '线上', level: 'easy', levelText: '入门', url: 'https://leetcode.cn/contest/' },
    { name: 'Codeforces Global Round', description: 'Codeforces 全球赛，面向所有 Rating 选手。', date: '不定期', format: '线上', level: 'hard', levelText: '高级', url: 'https://codeforces.com/contests' },
  ],
  7: [
    { name: 'AtCoder Beginner Contest', description: 'AtCoder 新手赛，题目从入门到中等难度。', date: '每周六晚', format: '线上', level: 'easy', levelText: '入门', url: 'https://atcoder.jp/contests/' },
    { name: 'AtCoder Regular Contest', description: 'AtCoder 常规赛，题目难度较高。', date: '不定期', format: '线上', level: 'hard', levelText: '高级', url: 'https://atcoder.jp/contests/' },
  ],
  8: [
    { name: 'ACM-ICPC 网络赛', description: 'ICPC 区域赛前的网络预选赛。', date: '8月-9月', format: '线上', level: 'hard', levelText: '高级', url: 'https://icpc.global/' },
    { name: '牛客暑期多校训练营', description: '牛客网举办的暑期多校联合训练。', date: '7月-8月', format: '线上', level: 'medium', levelText: '进阶', url: 'https://ac.nowcoder.com/' },
  ],
  9: [
    { name: 'ACM-ICPC 区域赛', description: '国际大学生程序设计竞赛亚洲区域赛。', date: '9月-11月', format: '线下', level: 'hard', levelText: '高级', url: 'https://icpc.global/' },
    { name: 'CCPC 区域赛', description: '中国大学生程序设计竞赛区域赛。', date: '9月-10月', format: '线下', level: 'hard', levelText: '高级', url: 'https://ccpc.io/' },
  ],
  10: [
    { name: 'Codeforces Round', description: 'Codeforces 定期举办的 Rated 比赛。', date: '不定期', format: '线上', level: 'medium', levelText: '进阶', url: 'https://codeforces.com/contests' },
    { name: '百度之星程序设计大赛', description: '百度举办的程序设计竞赛。', date: '10月-11月', format: '线上/线下', level: 'medium', levelText: '进阶' },
  ],
  11: [
    { name: 'ACM-ICPC 区域赛（续）', description: 'ICPC 亚洲区域赛后续场次。', date: '11月', format: '线下', level: 'hard', levelText: '高级', url: 'https://icpc.global/' },
    { name: '蓝桥杯报名', description: '新一届蓝桥杯报名阶段。', date: '11月-12月', format: '线上', level: 'easy', levelText: '入门', url: 'https://dasai.lanqiao.cn/' },
  ],
  12: [
    { name: 'LeetCode 年度大赛', description: 'LeetCode 年终总决赛。', date: '12月', format: '线上', level: 'hard', levelText: '高级', url: 'https://leetcode.cn/contest/' },
    { name: 'Codeforces Global Round', description: 'Codeforces 年终全球赛。', date: '12月', format: '线上', level: 'hard', levelText: '高级', url: 'https://codeforces.com/contests' },
  ],
}

function getContests(month) {
  return contests[month] || []
}

function selectMonth(month) {
  selectedMonth.value = selectedMonth.value === month ? null : month
}
</script>

<style scoped>
.contests-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 var(--s-lg);
}

/* ---- Hero ---- */
.contests-hero {
  text-align: center;
  padding: 40px 20px 32px;
}
.contests-hero-icon {
  width: 56px; height: 56px; border-radius: 14px;
  background: linear-gradient(135deg, #EEF2FF, #E0E7FF);
  color: #6366F1;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
}
.contests-hero-title {
  font-size: 28px; font-weight: 700; color: var(--text-primary);
  margin-bottom: 8px;
}
.contests-hero-desc {
  font-size: 15px; color: var(--text-secondary); max-width: 480px; margin: 0 auto;
}

/* ---- 时间线 ---- */
.timeline {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 24px 0;
  flex-wrap: wrap;
}
.timeline-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 60px;
  position: relative;
}
.timeline-item:hover {
  background: var(--bg-secondary, #f5f7fa);
}
.timeline-item.active {
  background: #EEF2FF;
}
.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--divider);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.timeline-item.has-contests .timeline-dot {
  background: #6366F1;
}
.timeline-item.active .timeline-dot {
  background: #4F46E5;
  box-shadow: 0 0 0 4px rgba(99,102,241,0.2);
}
.timeline-dot-inner {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #fff;
}
.timeline-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}
.timeline-item.active .timeline-label {
  color: #4F46E5;
  font-weight: 600;
}
.timeline-count {
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  background: #6366F1;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: 4px;
  right: 4px;
}

/* ---- 赛事内容 ---- */
.contests-content {
  animation: fadeIn 300ms ease;
}
.contests-month-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--divider);
}
.contests-month-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}
.contests-month-count {
  font-size: 13px;
  color: var(--text-disabled);
}

/* ---- 赛事卡片 ---- */
.contests-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.contest-card {
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  background: var(--bg);
  border: 1px solid var(--divider);
  border-radius: 12px;
  transition: all 0.2s ease;
  animation: fadeUp 300ms ease both;
}
.contest-card:hover {
  border-color: #C7D2FE;
  box-shadow: 0 4px 12px rgba(99,102,241,0.08);
}
.contest-badge {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  height: fit-content;
  margin-top: 2px;
}
.contest-badge.easy {
  background: #ECFDF5;
  color: #059669;
}
.contest-badge.medium {
  background: #FEF3C7;
  color: #D97706;
}
.contest-badge.hard {
  background: #FEE2E2;
  color: #DC2626;
}
.contest-info {
  flex: 1;
  min-width: 0;
}
.contest-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.contest-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 10px;
}
.contest-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.contest-meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-disabled);
}
.contest-meta-item a {
  color: #6366F1;
  text-decoration: none;
}
.contest-meta-item a:hover {
  text-decoration: underline;
}

/* ---- 空状态 ---- */
.contests-empty,
.contests-hint {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-disabled);
}
.contests-empty svg,
.contests-hint svg {
  opacity: 0.4;
  margin-bottom: 12px;
}
.contests-empty p,
.contests-hint p {
  font-size: 14px;
}

/* ---- Animations ---- */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .contests-hero { padding: 24px 16px; }
  .contests-hero-title { font-size: 22px; }
  .timeline { gap: 4px; }
  .timeline-item { min-width: 48px; padding: 8px 6px; }
  .timeline-label { font-size: 12px; }
  .contest-card { flex-direction: column; gap: 8px; }
}
</style>
