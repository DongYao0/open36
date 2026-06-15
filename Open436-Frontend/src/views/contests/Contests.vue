<template>
  <div class="contests-page">
    <!-- 标题 -->
    <div class="contests-header">
      <h1>赛事日历</h1>
      <p>点击月份查看该月相关赛事</p>
    </div>

    <!-- 月份时间线 -->
    <div class="timeline">
      <div
        v-for="m in months"
        :key="m"
        class="timeline-month"
        :class="{ active: selectedMonth === m, 'has-data': monthContests[m]?.length }"
        @click="selectedMonth = selectedMonth === m ? null : m"
      >
        <span class="month-num">{{ m }}</span>
        <span class="month-label">月</span>
        <span v-if="monthContests[m]?.length" class="month-dot"></span>
      </div>
    </div>

    <!-- 赛事列表 -->
    <div class="contests-list" v-if="selectedMonth && monthContests[selectedMonth]?.length">
      <div
        v-for="(c, i) in monthContests[selectedMonth]"
        :key="c.id"
        class="contest-card"
        :style="{ animationDelay: `${i * 60}ms` }"
        @click="router.push(`/contests/${c.id}`)"
      >
        <div class="contest-cover">
          <img :src="c.cover" :alt="c.name" />
        </div>
        <div class="contest-info">
          <h3 class="contest-name">{{ c.name }}</h3>
          <p class="contest-desc">{{ c.description }}</p>
          <div class="contest-meta">
            <div class="meta-item">
              <span class="meta-label">主办方</span>
              <span>{{ c.organizer }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">级别</span>
              <span class="meta-tag" :class="c.level">{{ c.levelText }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">时间</span>
              <span>{{ c.date }}</span>
            </div>
          </div>
          <a v-if="c.url" :href="c.url" target="_blank" rel="noopener" class="contest-link">
            官网
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
          </a>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="selectedMonth" class="contests-empty">
      <p>{{ selectedMonth }} 月暂无已收录赛事</p>
    </div>
    <div v-else class="contests-empty">
      <p>选择上方月份查看赛事</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const selectedMonth = ref(new Date().getMonth() + 1)
const months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

// 赛事数据，按月份分组
const monthContests = {
  1: [
    { id: 1, name: 'LeetCode 周赛', description: '每周举办的在线编程比赛，3-4道算法题，适合日常练习和提升。', organizer: 'LeetCode', level: 'platform', levelText: '平台赛', date: '每周日上午', cover: 'https://img.icons8.com/color/200/source-code.png', url: 'https://leetcode.cn/contest/' },
    { id: 2, name: 'Codeforces Round', description: 'Codeforces 定期举办的 Rated 比赛，题目涵盖多种难度。', organizer: 'Codeforces', level: 'platform', levelText: '平台赛', date: '不定期', cover: 'https://img.icons8.com/color/200/programming.png', url: 'https://codeforces.com/contests' },
  ],
  2: [
    { id: 3, name: '蓝桥杯省赛报名', description: '蓝桥杯全国软件和信息技术专业人才大赛省赛报名阶段。', organizer: '工信部人才交流中心', level: 'national', levelText: '国家级', date: '2月-3月', cover: 'https://img.icons8.com/color/200/code.png', url: 'https://dasai.lanqiao.cn/' },
  ],
  3: [
    { id: 4, name: '蓝桥杯省赛', description: '蓝桥杯全国软件和信息技术专业人才大赛省赛阶段。', organizer: '工信部人才交流中心', level: 'national', levelText: '国家级', date: '3月-4月', cover: 'https://img.icons8.com/color/200/code.png', url: 'https://dasai.lanqiao.cn/' },
    { id: 5, name: '天梯赛（GPLT）', description: '全国高校计算机能力挑战赛，考察数据结构与算法能力。', organizer: '全国高校计算机能力挑战赛组委会', level: 'national', levelText: '国家级', date: '3月-5月', cover: 'https://img.icons8.com/color/200/prize.png' },
  ],
  4: [
    { id: 6, name: '蓝桥杯国赛', description: '蓝桥杯全国总决赛，省赛晋级选手参加。', organizer: '工信部人才交流中心', level: 'national', levelText: '国家级', date: '4月-5月', cover: 'https://img.icons8.com/color/200/code.png', url: 'https://dasai.lanqiao.cn/' },
    { id: 7, name: 'Google Code Jam', description: 'Google 举办的全球编程竞赛，题目难度较高。', organizer: 'Google', level: 'international', levelText: '国际级', date: '4月-5月', cover: 'https://img.icons8.com/color/200/google-logo.png', url: 'https://codingcompetitions.withgoogle.com/' },
  ],
  5: [
    { id: 8, name: 'CCPC 中国大学生程序设计竞赛', description: '国内规模最大的大学生程序设计竞赛之一。', organizer: 'CCPC组委会', level: 'national', levelText: '国家级', date: '5月-10月', cover: 'https://img.icons8.com/color/200/medal.png', url: 'https://ccpc.io/' },
  ],
  6: [
    { id: 9, name: 'AtCoder Beginner Contest', description: 'AtCoder 新手赛，题目从入门到中等难度。', organizer: 'AtCoder', level: 'platform', levelText: '平台赛', date: '每周六晚', cover: 'https://img.icons8.com/color/200/algorithm.png', url: 'https://atcoder.jp/contests/' },
  ],
  7: [
    { id: 10, name: '牛客暑期多校训练营', description: '牛客网暑期举办的多校联合训练，模拟真实竞赛环境。', organizer: '牛客网', level: 'platform', levelText: '平台赛', date: '7月-8月', cover: 'https://img.icons8.com/color/200/classroom.png', url: 'https://ac.nowcoder.com/' },
  ],
  8: [
    { id: 11, name: 'ACM-ICPC 网络赛', description: 'ICPC 区域赛前的网络预选赛。', organizer: 'ACM', level: 'international', levelText: '国际级', date: '8月-9月', cover: 'https://img.icons8.com/color/200/trophy.png', url: 'https://icpc.global/' },
  ],
  9: [
    { id: 12, name: 'ACM-ICPC 区域赛', description: '国际大学生程序设计竞赛亚洲区域赛。', organizer: 'ACM', level: 'international', levelText: '国际级', date: '9月-11月', cover: 'https://img.icons8.com/color/200/trophy.png', url: 'https://icpc.global/' },
    { id: 13, name: 'CCPC 区域赛', description: '中国大学生程序设计竞赛区域赛。', organizer: 'CCPC组委会', level: 'national', levelText: '国家级', date: '9月-10月', cover: 'https://img.icons8.com/color/200/medal.png', url: 'https://ccpc.io/' },
  ],
  10: [
    { id: 14, name: '百度之星程序设计大赛', description: '百度举办的年度程序设计竞赛。', organizer: '百度', level: 'enterprise', levelText: '企业赛', date: '10月-11月', cover: 'https://img.icons8.com/color/200/search.png' },
  ],
  11: [
    { id: 15, name: '蓝桥杯新一届报名', description: '新一届蓝桥杯报名阶段。', organizer: '工信部人才交流中心', level: 'national', levelText: '国家级', date: '11月-12月', cover: 'https://img.icons8.com/color/200/code.png', url: 'https://dasai.lanqiao.cn/' },
  ],
  12: [
    { id: 16, name: 'LeetCode 年度大赛', description: 'LeetCode 年终总决赛。', organizer: 'LeetCode', level: 'platform', levelText: '平台赛', date: '12月', cover: 'https://img.icons8.com/color/200/source-code.png', url: 'https://leetcode.cn/contest/' },
  ],
}
</script>

<style scoped>
.contests-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 var(--s-lg) 40px;
}

.contests-header {
  text-align: center;
  padding: 32px 0 24px;
}
.contests-header h1 {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.contests-header p {
  font-size: 14px;
  color: var(--text-secondary);
}

/* ---- 月份时间线 ---- */
.timeline {
  display: flex;
  justify-content: center;
  gap: 6px;
  padding: 16px 0 28px;
  flex-wrap: wrap;
}
.timeline-month {
  display: flex;
  align-items: baseline;
  gap: 2px;
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  user-select: none;
}
.timeline-month:hover {
  background: var(--bg-secondary, #f5f7fa);
}
.timeline-month.active {
  background: #EEF2FF;
}
.month-num {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-secondary);
  transition: color 0.2s;
}
.month-label {
  font-size: 12px;
  color: var(--text-disabled);
}
.timeline-month.active .month-num {
  color: #4F46E5;
}
.timeline-month.has-data .month-num {
  color: var(--text-primary);
}
.month-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6366F1;
}

/* ---- 赛事卡片 ---- */
.contests-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.contest-card {
  display: flex;
  gap: 18px;
  background: var(--bg);
  border: 1px solid var(--divider);
  border-radius: 14px;
  overflow: hidden;
  transition: all 0.25s ease;
  animation: fadeUp 300ms ease both;
  cursor: pointer;
}
.contest-card:hover {
  border-color: #C7D2FE;
  box-shadow: 0 6px 18px rgba(99,102,241,0.08);
  transform: translateY(-2px);
}

.contest-cover {
  width: 180px;
  min-height: 160px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #EEF2FF, #E0E7FF);
  display: flex;
  align-items: center;
  justify-content: center;
}
.contest-cover img {
  width: 90px;
  height: 90px;
  object-fit: contain;
  opacity: 0.85;
}

.contest-info {
  flex: 1;
  padding: 16px 20px 16px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}
.contest-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}
.contest-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.contest-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 20px;
  margin-top: auto;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}
.meta-label {
  color: var(--text-disabled);
  flex-shrink: 0;
}
.meta-tag {
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.meta-tag.national { background: #FEF3C7; color: #D97706; }
.meta-tag.international { background: #DBEAFE; color: #2563EB; }
.meta-tag.platform { background: #F3F4F6; color: #6B7280; }
.meta-tag.enterprise { background: #ECFDF5; color: #059669; }

.contest-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6366F1;
  text-decoration: none;
  width: fit-content;
}
.contest-link:hover { text-decoration: underline; }

/* ---- 空状态 ---- */
.contests-empty {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-disabled);
  font-size: 14px;
}

/* ---- Animations ---- */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- Responsive ---- */
@media (max-width: 640px) {
  .contest-card { flex-direction: column; }
  .contest-cover { width: 100%; min-height: 100px; }
  .contest-info { padding: 12px 16px; }
  .timeline-month { padding: 8px 10px; }
  .month-num { font-size: 16px; }
}
</style>
