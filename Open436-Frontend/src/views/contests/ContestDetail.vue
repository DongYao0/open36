<template>
  <div class="contest-detail" v-if="contest">
    <!-- 返回 -->
    <div class="detail-back">
      <router-link to="/contests" class="back-link">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回赛事日历
      </router-link>
    </div>

    <!-- 头部 -->
    <div class="detail-header">
      <div class="detail-cover">
        <img :src="contest.cover" :alt="contest.name" />
      </div>
      <div class="detail-title-area">
        <span class="detail-tag" :class="contest.level">{{ contest.levelText }}</span>
        <h1>{{ contest.name }}</h1>
      </div>
    </div>

    <!-- 信息卡片 -->
    <div class="detail-info-grid">
      <div class="info-card">
        <div class="info-label">主办方</div>
        <div class="info-value">{{ contest.organizer }}</div>
      </div>
      <div class="info-card">
        <div class="info-label">竞赛级别</div>
        <div class="info-value">{{ contest.levelText }}</div>
      </div>
      <div class="info-card">
        <div class="info-label">比赛时间</div>
        <div class="info-value">{{ contest.date }}</div>
      </div>
      <div class="info-card" v-if="contest.url">
        <div class="info-label">官网</div>
        <a :href="contest.url" target="_blank" rel="noopener" class="info-link">{{ contest.url }}</a>
      </div>
    </div>

    <!-- 详细介绍 -->
    <div class="detail-section">
      <h2>赛事简介</h2>
      <div class="detail-content">
        <p>{{ contest.description }}</p>
        <p v-if="contest.detail">{{ contest.detail }}</p>
      </div>
    </div>

    <!-- 备赛建议 -->
    <div class="detail-section" v-if="contest.tips">
      <h2>备赛建议</h2>
      <div class="detail-content">
        <p>{{ contest.tips }}</p>
      </div>
    </div>

    <!-- 评论区 -->
    <div class="detail-section">
      <h2>评论 ({{ comments.length }})</h2>
      <!-- 发表评论 -->
      <div class="comment-form" v-if="auth.isLoggedIn">
        <textarea
          v-model="newComment"
          class="comment-textarea"
          placeholder="写下你的评论..."
          rows="3"
        ></textarea>
        <button class="comment-submit" @click="submitComment" :disabled="!newComment.trim()">
          发表评论
        </button>
      </div>
      <div v-else class="comment-login-tip">
        <router-link to="/login">登录</router-link>后可发表评论
      </div>

      <!-- 评论列表 -->
      <div class="comments-list">
        <div v-for="c in comments" :key="c.id" class="comment-item">
          <div class="comment-header">
            <img :src="`https://ui-avatars.com/api/?name=${encodeURIComponent(c.author)}&background=6366F1&color=fff&size=32`" class="comment-avatar" />
            <div class="comment-meta">
              <span class="comment-author">{{ c.author }}</span>
              <span class="comment-time">{{ c.time }}</span>
            </div>
          </div>
          <div class="comment-body">{{ c.content }}</div>
        </div>
        <div v-if="comments.length === 0" class="comment-empty">
          暂无评论，快来抢沙发吧
        </div>
      </div>
    </div>
  </div>

  <!-- 未找到 -->
  <div v-else class="contest-empty">
    <p>未找到该赛事信息</p>
    <router-link to="/contests" class="back-link">返回赛事日历</router-link>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const newComment = ref('')
const comments = ref([])

// 从 localStorage 加载评论
function loadComments() {
  const key = `contest_comments_${route.params.id}`
  try {
    comments.value = JSON.parse(localStorage.getItem(key) || '[]')
  } catch {
    comments.value = []
  }
}

// 发表评论
function submitComment() {
  if (!newComment.value.trim()) return
  const comment = {
    id: Date.now(),
    author: auth.nickname || '匿名用户',
    content: newComment.value.trim(),
    time: new Date().toLocaleString('zh-CN'),
  }
  comments.value.unshift(comment)
  const key = `contest_comments_${route.params.id}`
  localStorage.setItem(key, JSON.stringify(comments.value))
  newComment.value = ''
}

onMounted(loadComments)

// 所有赛事数据（与 Contests.vue 保持一致）
const allContests = [
  { id: 1, name: 'LeetCode 周赛', description: '每周举办的在线编程比赛，3-4道算法题，适合日常练习和提升。', detail: 'LeetCode 周赛是 LeetCode 平台每周日上午举办的在线编程竞赛，通常包含4道题目，难度从易到难递增。比赛时长1.5小时，根据解题速度和正确率进行排名。双周赛每隔一周周六晚上举办，题目难度略高。', organizer: 'LeetCode', level: 'platform', levelText: '平台赛', date: '每周日上午', cover: 'https://img.icons8.com/color/200/source-code.png', url: 'https://leetcode.cn/contest/', tips: '建议先刷完 LeetCode 热题 100，熟悉常见算法模板。比赛时先做前两道保分，再挑战后两道。' },
  { id: 2, name: 'Codeforces Round', description: 'Codeforces 定期举办的 Rated 比赛，题目涵盖多种难度。', detail: 'Codeforces 是全球最知名的在线算法竞赛平台，定期举办 Rated 比赛（Div.1/Div.2/Div.3/Div.4）。比赛通常5-6道题，时长2-2.5小时。Rating 系统是衡量选手水平的重要指标。', organizer: 'Codeforces', level: 'platform', levelText: '平台赛', date: '不定期', cover: 'https://img.icons8.com/color/200/programming.png', url: 'https://codeforces.com/contests', tips: '建议从 Div.3 开始，逐步提升到 Div.2。多做 Educational Round 的题目，学习标准算法。' },
  { id: 3, name: '蓝桥杯省赛报名', description: '蓝桥杯全国软件和信息技术专业人才大赛省赛报名阶段。', detail: '蓝桥杯是由工业和信息化部人才交流中心主办的全国性IT学科赛事，已连续举办多届。比赛分C/C++、Java、Python等语言组别，设研究生组、本科A组、本科B组、高职高专组等。', organizer: '工信部人才交流中心', level: 'national', levelText: '国家级', date: '2月-3月', cover: 'https://img.icons8.com/color/200/code.png', url: 'https://dasai.lanqiao.cn/', tips: '省赛题目偏基础，重点复习枚举、排序、二分、DP等常见算法。注意填空题的答题技巧。' },
  { id: 4, name: '蓝桥杯省赛', description: '蓝桥杯全国软件和信息技术专业人才大赛省赛阶段。', detail: '省赛通常在3-4月举行，比赛时长4小时，包含填空题和编程题。省赛一等奖选手可晋级全国总决赛。', organizer: '工信部人才交流中心', level: 'national', levelText: '国家级', date: '3月-4月', cover: 'https://img.icons8.com/color/200/code.png', url: 'https://dasai.lanqiao.cn/', tips: '填空题可以用暴力枚举，编程题注意边界条件。时间分配：填空题1小时，编程题3小时。' },
  { id: 5, name: '天梯赛（GPLT）', description: '全国高校计算机能力挑战赛，考察数据结构与算法能力。', detail: '天梯赛分为个人赛和团队赛，个人赛考察基础编程、数据结构、算法设计等能力。团队赛需要3人协作完成。', organizer: '全国高校计算机能力挑战赛组委会', level: 'national', levelText: '国家级', date: '3月-5月', cover: 'https://img.icons8.com/color/200/prize.png', tips: '重点复习图论、动态规划、字符串处理等高级算法。团队赛需要良好的分工协作。' },
  { id: 6, name: '蓝桥杯国赛', description: '蓝桥杯全国总决赛，省赛晋级选手参加。', detail: '全国总决赛通常在4-5月举行，比赛形式与省赛类似但难度更高。国赛一等奖含金量很高，对保研和就业都有帮助。', organizer: '工信部人才交流中心', level: 'national', levelText: '国家级', date: '4月-5月', cover: 'https://img.icons8.com/color/200/code.png', url: 'https://dasai.lanqiao.cn/', tips: '国赛难度高于省赛，需要掌握更高级的算法。建议多做历年国赛真题。' },
  { id: 7, name: 'Google Code Jam', description: 'Google 举办的全球编程竞赛，题目难度较高。', detail: 'Google Code Jam 是 Google 举办的全球性编程竞赛，吸引了来自世界各地的顶尖选手。比赛分为资格赛、Round 1、Round 2、Round 3 和总决赛。', organizer: 'Google', level: 'international', levelText: '国际级', date: '4月-5月', cover: 'https://img.icons8.com/color/200/google-logo.png', url: 'https://codingcompetitions.withgoogle.com/', tips: '题目偏向数学和算法设计，需要较强的抽象思维能力。建议多做 Google Kick Start 的题目。' },
  { id: 8, name: 'CCPC 中国大学生程序设计竞赛', description: '国内规模最大的大学生程序设计竞赛之一。', detail: 'CCPC 是中国大学生程序设计竞赛的简称，与 ICPC 类似，3人一组使用一台计算机解题。比赛设多个赛区，优秀队伍可参加全国总决赛。', organizer: 'CCPC组委会', level: 'national', levelText: '国家级', date: '5月-10月', cover: 'https://img.icons8.com/color/200/medal.png', url: 'https://ccpc.io/', tips: '团队配合非常重要，建议明确分工：一人主写代码，一人主想算法，一人查错。' },
  { id: 9, name: 'AtCoder Beginner Contest', description: 'AtCoder 新手赛，题目从入门到中等难度。', detail: 'AtCoder 是日本知名的在线算法竞赛平台，ABC 每周六晚举办，题目质量极高。比赛包含6-8道题，时长100分钟。', organizer: 'AtCoder', level: 'platform', levelText: '平台赛', date: '每周六晚', cover: 'https://img.icons8.com/color/200/algorithm.png', url: 'https://atcoder.jp/contests/', tips: 'ABC 前4题适合入门选手，后几题难度较高。建议从 ABC 的 A-D 题开始练习。' },
  { id: 10, name: '牛客暑期多校训练营', description: '牛客网暑期举办的多校联合训练，模拟真实竞赛环境。', detail: '牛客暑期多校是模拟 ICPC/CCPC 赛制的在线训练赛，每周举办多场，题目来自各高校命题组。适合备赛 ACM 的选手。', organizer: '牛客网', level: 'platform', levelText: '平台赛', date: '7月-8月', cover: 'https://img.icons8.com/color/200/classroom.png', url: 'https://ac.nowcoder.com/', tips: '建议组队参加，模拟真实比赛环境。赛后认真补题，学习解题思路。' },
  { id: 11, name: 'ACM-ICPC 网络赛', description: 'ICPC 区域赛前的网络预选赛。', detail: 'ICPC 网络赛是区域赛的预选阶段，通过网络赛确定区域赛参赛名额。比赛形式与区域赛一致，3人一队。', organizer: 'ACM', level: 'international', levelText: '国际级', date: '8月-9月', cover: 'https://img.icons8.com/color/200/trophy.png', url: 'https://icpc.global/', tips: '网络赛竞争激烈，建议提前组建队伍并进行密集训练。' },
  { id: 12, name: 'ACM-ICPC 区域赛', description: '国际大学生程序设计竞赛亚洲区域赛。', detail: 'ICPC 区域赛是全球最具影响力的大学生程序设计竞赛，3人一队使用一台计算机，在5小时内解决10-13道题目。金奖队伍可参加世界总决赛。', organizer: 'ACM', level: 'international', levelText: '国际级', date: '9月-11月', cover: 'https://img.icons8.com/color/200/trophy.png', url: 'https://icpc.global/', tips: '这是含金量最高的编程竞赛之一。建议从大一就开始训练，积累算法知识和比赛经验。' },
  { id: 13, name: 'CCPC 区域赛', description: '中国大学生程序设计竞赛区域赛。', detail: 'CCPC 区域赛赛制与 ICPC 类似，是国内最重要的程序设计竞赛之一。设多个赛区，优秀队伍可参加全国总决赛。', organizer: 'CCPC组委会', level: 'national', levelText: '国家级', date: '9月-10月', cover: 'https://img.icons8.com/color/200/medal.png', url: 'https://ccpc.io/', tips: '与 ICPC 备赛同步进行，重点提升团队配合和解题速度。' },
  { id: 14, name: '百度之星程序设计大赛', description: '百度举办的年度程序设计竞赛。', detail: '百度之星是百度举办的面向全国高校在校学生的程序设计竞赛，考察算法和编程能力。比赛设初赛和决赛。', organizer: '百度', level: 'enterprise', levelText: '企业赛', date: '10月-11月', cover: 'https://img.icons8.com/color/200/search.png', tips: '题目偏向实际应用场景，建议多做百度之星历年真题。' },
  { id: 15, name: '蓝桥杯新一届报名', description: '新一届蓝桥杯报名阶段。', detail: '新一届蓝桥杯开始报名，建议尽早报名并开始备赛。', organizer: '工信部人才交流中心', level: 'national', levelText: '国家级', date: '11月-12月', cover: 'https://img.icons8.com/color/200/code.png', url: 'https://dasai.lanqiao.cn/', tips: '利用寒假时间集中训练，重点突破薄弱算法模块。' },
  { id: 16, name: 'LeetCode 年度大赛', description: 'LeetCode 年终总决赛。', detail: 'LeetCode 年度大赛是 LeetCode 平台每年年底举办的顶级赛事，邀请年度表现最优秀的选手参加。', organizer: 'LeetCode', level: 'platform', levelText: '平台赛', date: '12月', cover: 'https://img.icons8.com/color/200/source-code.png', url: 'https://leetcode.cn/contest/', tips: '平时多参加周赛积累 Rating，争取获得年度大赛参赛资格。' },
]

const contest = computed(() => {
  const id = parseInt(route.params.id)
  return allContests.find(c => c.id === id)
})
</script>

<style scoped>
.contest-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 var(--s-lg) 40px;
}

.detail-back {
  padding: 20px 0;
}
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s;
}
.back-link:hover { color: #6366F1; }

/* ---- 头部 ---- */
.detail-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 28px;
}
.detail-cover {
  width: 100px;
  height: 100px;
  border-radius: 16px;
  background: linear-gradient(135deg, #EEF2FF, #E0E7FF);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.detail-cover img {
  width: 60px;
  height: 60px;
  object-fit: contain;
}
.detail-title-area {
  flex: 1;
}
.detail-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}
.detail-tag.national { background: #FEF3C7; color: #D97706; }
.detail-tag.international { background: #DBEAFE; color: #2563EB; }
.detail-tag.platform { background: #F3F4F6; color: #6B7280; }
.detail-tag.enterprise { background: #ECFDF5; color: #059669; }
.detail-title-area h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}

/* ---- 信息网格 ---- */
.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 28px;
}
.info-card {
  background: var(--bg-secondary, #f5f7fa);
  border-radius: 10px;
  padding: 14px 16px;
}
.info-label {
  font-size: 12px;
  color: var(--text-disabled);
  margin-bottom: 6px;
}
.info-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.info-link {
  font-size: 14px;
  color: #6366F1;
  text-decoration: none;
  word-break: break-all;
}
.info-link:hover { text-decoration: underline; }

/* ---- 内容区块 ---- */
.detail-section {
  margin-bottom: 28px;
}
.detail-section h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--divider);
}
.detail-content p {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin-bottom: 12px;
}

/* ---- 空状态 ---- */
.contest-empty {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-secondary);
}
.contest-empty p { margin-bottom: 16px; }

/* ---- 评论区 ---- */
.comment-form {
  margin-bottom: 20px;
}
.comment-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--divider);
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.2s;
}
.comment-textarea:focus {
  border-color: #6366F1;
  outline: none;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}
.comment-submit {
  margin-top: 8px;
  padding: 8px 20px;
  background: #6366F1;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.comment-submit:hover { background: #4F46E5; }
.comment-submit:disabled { background: #C7D2FE; cursor: not-allowed; }
.comment-login-tip {
  padding: 16px;
  background: var(--bg-secondary, #f5f7fa);
  border-radius: 10px;
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}
.comment-login-tip a { color: #6366F1; text-decoration: none; font-weight: 500; }

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.comment-item {
  padding: 16px;
  background: var(--bg-secondary, #f5f7fa);
  border-radius: 10px;
}
.comment-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.comment-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}
.comment-meta {
  display: flex;
  flex-direction: column;
}
.comment-author {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.comment-time {
  font-size: 12px;
  color: var(--text-disabled);
}
.comment-body {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  padding-left: 42px;
}
.comment-empty {
  text-align: center;
  padding: 32px;
  color: var(--text-disabled);
  font-size: 14px;
}

@media (max-width: 640px) {
  .detail-header { flex-direction: column; text-align: center; }
  .detail-title-area h1 { font-size: 20px; }
  .detail-info-grid { grid-template-columns: 1fr; }
}
</style>
