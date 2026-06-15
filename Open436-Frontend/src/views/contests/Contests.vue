<template>
  <div class="contests-page">
    <!-- 搜索 + 筛选 -->
    <div class="contests-toolbar">
      <div class="contests-search">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input v-model="searchQuery" placeholder="搜索赛事..." />
      </div>
      <div class="contests-filters">
        <button
          v-for="f in filters"
          :key="f.value"
          class="filter-btn"
          :class="{ active: currentFilter === f.value }"
          @click="currentFilter = f.value"
        >{{ f.label }}</button>
      </div>
    </div>

    <!-- 赛事卡片列表 -->
    <div class="contests-list">
      <div
        v-for="(contest, i) in filteredContests"
        :key="contest.id"
        class="contest-card"
        :style="{ animationDelay: `${i * 50}ms` }"
      >
        <!-- 左侧封面图 -->
        <div class="contest-cover">
          <img :src="contest.cover" :alt="contest.name" />
          <div class="contest-status" :class="contest.status">{{ contest.statusText }}</div>
        </div>

        <!-- 右侧信息 -->
        <div class="contest-info">
          <h3 class="contest-name">{{ contest.name }}</h3>
          <p class="contest-desc">{{ contest.description }}</p>
          <div class="contest-meta">
            <div class="meta-row">
              <span class="meta-label">主办方</span>
              <span class="meta-value">{{ contest.organizer }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">级别</span>
              <span class="meta-tag" :class="contest.level">{{ contest.levelText }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">时间</span>
              <span class="meta-value">{{ contest.date }}</span>
            </div>
          </div>
          <a v-if="contest.url" :href="contest.url" target="_blank" rel="noopener" class="contest-link">
            官网链接
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
          </a>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="filteredContests.length === 0" class="contests-empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
        <circle cx="12" cy="12" r="10"/><line x1="8" y1="15" x2="16" y2="15"/>
        <line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
      </svg>
      <p>没有找到相关赛事</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const searchQuery = ref('')
const currentFilter = ref('all')

const filters = [
  { label: '全部', value: 'all' },
  { label: '报名中', value: 'enrolling' },
  { label: '进行中', value: 'ongoing' },
  { label: '即将开始', value: 'upcoming' },
  { label: '已结束', value: 'ended' },
]

// 赛事数据
const contests = [
  {
    id: 1,
    name: '蓝桥杯全国软件和信息技术专业人才大赛',
    description: '由工业和信息化部人才交流中心主办，面向在校大学生的全国性IT学科赛事，涵盖C/C++、Java、Python等编程语言。',
    organizer: '工业和信息化部人才交流中心',
    level: 'national',
    levelText: '国家级',
    date: '省赛：2026年4月 / 国赛：2026年6月',
    status: 'enrolling',
    statusText: '报名中',
    cover: 'https://img.icons8.com/color/200/code.png',
    url: 'https://dasai.lanqiao.cn/',
  },
  {
    id: 2,
    name: 'ACM-ICPC 国际大学生程序设计竞赛',
    description: '由国际计算机学会（ACM）主办的全球最具影响力的大学生程序设计竞赛，三人一组使用一台计算机解题。',
    organizer: '国际计算机学会（ACM）',
    level: 'international',
    levelText: '国际级',
    date: '区域赛：2026年9月-11月',
    status: 'upcoming',
    statusText: '即将开始',
    cover: 'https://img.icons8.com/color/200/trophy.png',
    url: 'https://icpc.global/',
  },
  {
    id: 3,
    name: 'CCPC 中国大学生程序设计竞赛',
    description: '由中国大学生程序设计竞赛组委会主办，是国内规模最大的大学生程序设计竞赛之一。',
    organizer: '中国大学生程序设计竞赛组委会',
    level: 'national',
    levelText: '国家级',
    date: '区域赛：2026年9月-10月 / 总决赛：2026年11月',
    status: 'upcoming',
    statusText: '即将开始',
    cover: 'https://img.icons8.com/color/200/medal.png',
    url: 'https://ccpc.io/',
  },
  {
    id: 4,
    name: 'LeetCode 周赛 / 双周赛',
    description: 'LeetCode 每周和双周举办的在线编程比赛，包含3-4道算法题，适合日常刷题和提升编程能力。',
    organizer: 'LeetCode',
    level: 'platform',
    levelText: '平台赛',
    date: '每周日上午 / 每隔周六晚',
    status: 'ongoing',
    statusText: '进行中',
    cover: 'https://img.icons8.com/color/200/source-code.png',
    url: 'https://leetcode.cn/contest/',
  },
  {
    id: 5,
    name: 'Codeforces Round',
    description: 'Codeforces 定期举办的 Rated 比赛，题目涵盖多种难度，是提升算法能力的绝佳平台。',
    organizer: 'Codeforces',
    level: 'platform',
    levelText: '平台赛',
    date: '不定期举办',
    status: 'ongoing',
    statusText: '进行中',
    cover: 'https://img.icons8.com/color/200/programming.png',
    url: 'https://codeforces.com/contests',
  },
  {
    id: 6,
    name: 'AtCoder Beginner / Regular / Grand Contest',
    description: 'AtCoder 举办的系列编程竞赛，从入门到高级难度递进，题目质量极高。',
    organizer: 'AtCoder',
    level: 'platform',
    levelText: '平台赛',
    date: '每周六晚（ABC）/ 不定期（ARC/AGC）',
    status: 'ongoing',
    statusText: '进行中',
    cover: 'https://img.icons8.com/color/200/algorithm.png',
    url: 'https://atcoder.jp/contests/',
  },
  {
    id: 7,
    name: '百度之星程序设计大赛',
    description: '百度举办的年度程序设计竞赛，面向全国高校在校学生，考察算法和编程能力。',
    organizer: '百度',
    level: 'enterprise',
    levelText: '企业赛',
    date: '2026年10月-11月',
    status: 'upcoming',
    statusText: '即将开始',
    cover: 'https://img.icons8.com/color/200/search.png',
  },
  {
    id: 8,
    name: 'Google Code Jam',
    description: 'Google 举办的全球编程竞赛，题目难度较高，吸引全球顶尖选手参与。',
    organizer: 'Google',
    level: 'international',
    levelText: '国际级',
    date: '2026年4月-5月',
    status: 'ended',
    statusText: '已结束',
    cover: 'https://img.icons8.com/color/200/google-logo.png',
    url: 'https://codingcompetitions.withgoogle.com/',
  },
  {
    id: 9,
    name: '天梯赛（GPLT）',
    description: '全国高校计算机能力挑战赛系列赛事之一，考察数据结构与算法能力，分个人赛和团队赛。',
    organizer: '全国高校计算机能力挑战赛组委会',
    level: 'national',
    levelText: '国家级',
    date: '2026年5月',
    status: 'ended',
    statusText: '已结束',
    cover: 'https://img.icons8.com/color/200/prize.png',
  },
  {
    id: 10,
    name: '牛客暑期多校训练营',
    description: '牛客网暑期举办的多校联合训练，模拟真实竞赛环境，适合备赛 ACM/CCPC。',
    organizer: '牛客网',
    level: 'platform',
    levelText: '平台赛',
    date: '2026年7月-8月',
    status: 'upcoming',
    statusText: '即将开始',
    cover: 'https://img.icons8.com/color/200/classroom.png',
    url: 'https://ac.nowcoder.com/',
  },
]

const filteredContests = computed(() => {
  let list = contests
  if (currentFilter.value !== 'all') {
    list = list.filter(c => c.status === currentFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(c =>
      c.name.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q) ||
      c.organizer.toLowerCase().includes(q)
    )
  }
  return list
})
</script>

<style scoped>
.contests-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 var(--s-lg);
}

/* ---- 搜索 + 筛选 ---- */
.contests-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
  flex-wrap: wrap;
}
.contests-search {
  position: relative;
  flex: 1;
  min-width: 200px;
}
.contests-search .search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-disabled);
}
.contests-search input {
  width: 100%;
  height: 40px;
  padding: 0 12px 0 36px;
  border: 1px solid var(--divider);
  border-radius: 10px;
  font-size: 14px;
  background: var(--bg-secondary, #f5f7fa);
  transition: all 0.2s;
}
.contests-search input:focus {
  border-color: #6366F1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
  background: var(--bg);
}
.contests-filters {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.filter-btn {
  padding: 6px 14px;
  border: 1px solid var(--divider);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg);
  cursor: pointer;
  transition: all 0.2s;
}
.filter-btn:hover {
  border-color: #C7D2FE;
  color: #6366F1;
}
.filter-btn.active {
  background: #6366F1;
  border-color: #6366F1;
  color: #fff;
}

/* ---- 赛事卡片 ---- */
.contests-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 40px;
}
.contest-card {
  display: flex;
  gap: 20px;
  background: var(--bg);
  border: 1px solid var(--divider);
  border-radius: 14px;
  overflow: hidden;
  transition: all 0.25s ease;
  animation: fadeUp 300ms ease both;
}
.contest-card:hover {
  border-color: #C7D2FE;
  box-shadow: 0 6px 20px rgba(99,102,241,0.08);
  transform: translateY(-2px);
}

/* 封面图 */
.contest-cover {
  width: 200px;
  min-height: 180px;
  flex-shrink: 0;
  position: relative;
  background: linear-gradient(135deg, #EEF2FF, #E0E7FF);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.contest-cover img {
  width: 100px;
  height: 100px;
  object-fit: contain;
  opacity: 0.85;
}
.contest-status {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}
.contest-status.enrolling {
  background: #ECFDF5;
  color: #059669;
}
.contest-status.ongoing {
  background: #DBEAFE;
  color: #2563EB;
}
.contest-status.upcoming {
  background: #FEF3C7;
  color: #D97706;
}
.contest-status.ended {
  background: #F3F4F6;
  color: #6B7280;
}

/* 右侧信息 */
.contest-info {
  flex: 1;
  padding: 18px 20px 18px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}
.contest-name {
  font-size: 17px;
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
  gap: 12px 24px;
  margin-top: auto;
}
.meta-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.meta-label {
  color: var(--text-disabled);
  flex-shrink: 0;
}
.meta-value {
  color: var(--text-secondary);
}
.meta-tag {
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.meta-tag.national {
  background: #FEF3C7;
  color: #D97706;
}
.meta-tag.international {
  background: #DBEAFE;
  color: #2563EB;
}
.meta-tag.platform {
  background: #F3F4F6;
  color: #6B7280;
}
.meta-tag.enterprise {
  background: #ECFDF5;
  color: #059669;
}
.contest-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6366F1;
  text-decoration: none;
  margin-top: 4px;
  width: fit-content;
}
.contest-link:hover {
  text-decoration: underline;
}

/* ---- 空状态 ---- */
.contests-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-disabled);
}
.contests-empty svg { opacity: 0.4; margin-bottom: 12px; }
.contests-empty p { font-size: 14px; }

/* ---- Animations ---- */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- Responsive ---- */
@media (max-width: 640px) {
  .contest-card {
    flex-direction: column;
  }
  .contest-cover {
    width: 100%;
    min-height: 120px;
  }
  .contest-info {
    padding: 14px 16px;
  }
  .contests-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
