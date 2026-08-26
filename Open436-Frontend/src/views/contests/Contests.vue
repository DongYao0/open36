<template>
  <main class="contests-page" :class="{ ready }">
    <header class="contest-hero">
      <p class="eyebrow hero-kicker">核心优势</p>
      <h1>赛事<br>功能<span>.</span></h1>
      <div class="hero-bottom"><p>从每周训练到区域赛场，把值得投入的每一场编程赛事整理成清晰、可追踪的成长路线。</p><b>{{ contests.length }} 个月度节点</b></div>
    </header>

    <section class="timeline" aria-label="赛事时间线">
      <article v-for="(contest, index) in contests" :key="contest.name" class="entry" :class="[{ open: contest.open }, index % 2 === 0 ? 'entry-right' : 'entry-left']" :style="{ '--delay': `${index * 130}ms` }">
        <div class="marker"><small>0{{ index + 1 }}</small><strong>{{ contest.month }}</strong></div>
        <div class="contest-card lab-card">
          <h2>{{ contest.name }}</h2><p>{{ contest.level }}</p>
          <div class="details"><ul><li v-for="detail in contest.details" :key="detail">{{ detail }}</li></ul></div>
          <button type="button" :aria-expanded="contest.open" @click="contest.open = !contest.open">赛事信息 <span>+</span></button>
        </div>
        <time>{{ contest.period }}</time>
      </article>
    </section>
    <footer>赛事档案 / 点击赛事条目查看准备建议</footer>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const ready = ref(false)

const contests = ref([
  { month: '01', name: '寒假集训', level: '基础算法专项训练', period: '一月', open: true, details: ['梳理本学期错题，确定假期训练专题。', '每天完成一道基础题与一次代码复盘。', '建立个人模板库和题解归档。'] },
  { month: '02', name: '开学热身赛', level: '线上模拟与状态恢复', period: '二月', open: false, details: ['用两场短时赛恢复读题和编码节奏。', '检查本地开发环境与常用模板。', '为春季赛事确定本月训练目标。'] },
  { month: '03', name: '蓝桥杯省赛', level: '全国高校软件与算法挑战', period: '三月', open: false, details: ['完成报名与组别确认，建立个人备赛清单。', '从基础题型开始训练时间分配与边界处理。', '赛前一周集中复盘错题和常用模板。'] },
  { month: '04', name: '春季校赛', level: '校内程序设计选拔', period: '四月', open: false, details: ['按专题进行组队模拟，观察协作节奏。', '记录每道题的首思路与最终解法。', '根据赛后数据调整薄弱专题。'] },
  { month: '05', name: '天梯赛 · GPLT', level: '团队程序设计赛事', period: '五月', open: false, details: ['按团队角色分配练习主题，建立共用题库。', '模拟比赛环境，练习沟通与题目交接。', '赛后归档题解，沉淀协作方法。'] },
  { month: '06', name: '期末冲刺赛', level: '综合题型模拟训练', period: '六月', open: false, details: ['以限时训练检验本学期专题掌握度。', '整理常用数据结构与图论模板。', '输出一份个人阶段复盘。'] },
  { month: '07', name: '暑期算法营', level: '进阶专题集训', period: '七月', open: false, details: ['围绕动态规划和图论安排密集训练。', '每周进行一次五小时完整模拟赛。', '复盘罚时来源和决策失误。'] },
  { month: '08', name: 'CCPC 区域赛', level: '中国大学生程序设计竞赛', period: '八月', open: false, details: ['以三人一队进行多轮五小时模拟赛。', '围绕比赛分工优化题目交接流程。', '记录每场比赛的罚时、决策与结论。'] },
  { month: '09', name: '秋季选拔赛', level: '区域赛队伍选拔', period: '九月', open: false, details: ['结合暑期数据制定个人能力雷达图。', '完成队内角色定位与沟通演练。', '针对短板安排两周强化训练。'] },
  { month: '10', name: '区域赛模拟赛', level: '长赛制团队演练', period: '十月', open: false, details: ['按正式赛程完成多轮封闭模拟。', '统一代码规范，降低协作调试成本。', '复盘选题顺序与信息同步效率。'] },
  { month: '11', name: 'ICPC 网络赛', level: '国际大学生程序设计竞赛', period: '十一月', open: false, details: ['根据网络赛节奏打磨选题与首题策略。', '保持代码规范统一，降低调试成本。', '用赛后讲评补齐薄弱专题。'] },
  { month: '12', name: '年度复盘赛', level: '全年成长档案总结', period: '十二月', open: false, details: ['回顾全年参赛记录与题目完成情况。', '归档有效模板、题解与团队经验。', '据此制定下一年度赛事计划。'] }
])

onMounted(() => {
  requestAnimationFrame(() => {
    ready.value = true
  })
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap');
.contests-page{--ink:#111622;--panel:#1a2232;--muted:#9ca8bb;--paper:#f1ede4;--lime:#d5ff45;--line:rgba(214,255,69,.32);--border:rgba(241,237,228,.14);min-height:100vh;margin:-16px;padding:92px clamp(24px,7vw,110px) 80px;overflow:hidden;color:var(--paper);font-family:Manrope,"Noto Sans SC",sans-serif;background:radial-gradient(circle at 94% 9%,#344a43 0,transparent 25rem),var(--ink)}
.contests-page::before{position:fixed;inset:0;pointer-events:none;opacity:.2;background-image:radial-gradient(rgba(255,255,255,.28) .7px,transparent .7px);background-size:5px 5px;content:""}.contest-hero,.timeline,footer{position:relative;z-index:1;max-width:1040px;margin-inline:auto}.contest-hero{margin-bottom:86px}.eyebrow,.marker small,time,footer,.hero-bottom b{font-family:"DM Mono",monospace;letter-spacing:.08em;text-transform:uppercase}.eyebrow{margin:0 0 17px;color:var(--lime);font-size:.74rem}.contest-hero h1{max-width:760px;margin:0;font-family:Fraunces,serif;font-size:clamp(3.2rem,8vw,7.6rem);letter-spacing:-.075em;line-height:.9}.contest-hero h1 span{color:var(--lime)}.hero-bottom{display:flex;justify-content:space-between;gap:28px;margin-top:42px;padding-top:18px;border-top:1px solid var(--border)}.hero-bottom p{max-width:470px;margin:0;color:var(--muted);font-size:.96rem;line-height:1.65}.hero-bottom b{color:var(--muted);font-size:.72rem;white-space:nowrap}.timeline{position:relative}.timeline::before{position:absolute;top:68px;bottom:135px;left:38px;width:1px;background:linear-gradient(var(--line),rgba(213,255,69,.08));content:""}.entry{position:relative;display:grid;grid-template-columns:78px minmax(0,1fr) auto;gap:20px;padding-bottom:52px}.marker{position:relative;z-index:1;display:grid;place-items:center;width:78px;height:78px;border:1px solid var(--border);border-radius:50%;background:var(--panel);transition:.25s}.marker small{position:absolute;top:-21px;left:-7px;color:var(--lime);font-size:.72rem}.marker strong{font:600 1rem "DM Mono",monospace;color:var(--paper)}.contest-card{position:relative;padding:28px 30px 26px;border:1px solid var(--border);border-radius:4px;background:rgba(26,34,50,.78);transition:.25s}.contest-card::after{position:absolute;top:0;left:0;width:100%;height:1px;background:var(--lime);content:"";transform:scaleX(0);transform-origin:left;transition:.35s}.entry:hover .marker{border-color:var(--lime);transform:rotate(-7deg) scale(1.05)}.entry:hover .contest-card{border-color:rgba(213,255,69,.42);background:#202b3d;transform:translateX(7px)}.entry:hover .contest-card::after{transform:scaleX(1)}.contest-card h2{margin:0 0 7px;font-size:clamp(1.25rem,2.6vw,1.7rem);letter-spacing:-.045em;line-height:1.1}.contest-card>p{margin:0;color:var(--lime);font-family:Fraunces,serif;font-size:1.13rem}.details{max-height:0;overflow:hidden;opacity:0;transition:.35s}.open .details{max-height:250px;margin-top:21px;opacity:1}.details ul{display:grid;gap:10px;margin:0;padding-left:19px;color:#c8d0dd;font-size:.88rem;line-height:1.55}.details li::marker{color:var(--lime)}.contest-card button{margin-top:20px;padding:0;border:0;background:none;color:var(--muted);font:500 .7rem "DM Mono",monospace;letter-spacing:.06em;text-transform:uppercase}.contest-card button:hover{color:var(--lime)}.contest-card button span{display:inline-block;margin-left:5px;font-size:1rem;transition:.25s}.open button span{transform:rotate(45deg)}time{padding-top:29px;color:var(--muted);font-size:.72rem;white-space:nowrap}footer{margin-top:32px;padding-top:16px;border-top:1px solid var(--border);color:var(--muted);font-size:.7rem}
@media(max-width:680px){.contests-page{margin:-16px;padding:56px 20px 44px}.contest-hero{margin-bottom:56px}.hero-bottom{flex-direction:column}.timeline::before{top:53px;bottom:112px;left:25px}.entry{grid-template-columns:52px minmax(0,1fr);gap:14px;padding-bottom:34px}.marker{width:52px;height:52px}.contest-card{padding:22px 20px}.entry time{grid-column:2;padding:0;text-align:left}.open .details{max-height:390px}}

/* 与落地页“实验室功能”保持一致的居中标题与时间线入场节奏 */
.contest-hero{text-align:center}.contest-hero h1{margin-inline:auto}.hero-bottom{text-align:left}
.hero-kicker{opacity:0;transform:translateY(14px)}
.contest-hero h1,.hero-bottom{opacity:0;transform:translateY(26px)}
.ready .hero-kicker{animation:lab-rise .42s ease-out .08s both}
.ready .contest-hero h1{animation:lab-rise .6s cubic-bezier(.2,.8,.2,1) .18s both}
.ready .hero-bottom{animation:lab-rise .55s ease-out .38s both}
.ready .timeline::before{animation:lab-track .78s cubic-bezier(.4,0,.2,1) .45s both}
.ready .entry{animation:lab-rise .54s cubic-bezier(.2,.8,.2,1) calc(.56s + var(--delay)) both}
.lab-card{box-shadow:0 14px 42px rgba(0,0,0,.14)}
.lab-card::before{position:absolute;top:28px;left:-8px;width:15px;height:15px;border:3px solid var(--lime);border-radius:50%;background:var(--ink);content:"";transform:translateX(-100%)}
@keyframes lab-rise{from{opacity:0;transform:translateY(26px)}to{opacity:1;transform:translateY(0)}}
@keyframes lab-track{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@media(prefers-reduced-motion:reduce){.ready .hero-kicker,.ready .contest-hero h1,.ready .hero-bottom,.ready .timeline::before,.ready .entry{animation:none}.hero-kicker,.contest-hero h1,.hero-bottom,.entry{opacity:1;transform:none}}

/* 全年节点围绕中轴左右交错，复用实验室功能的纵向时间线语义。 */
@media(min-width:681px){
  .timeline::before{left:calc(50% - .5px)}
  .entry{grid-template-columns:minmax(0,1fr) 78px minmax(0,1fr);align-items:start}
  .marker{grid-column:2;grid-row:1}
  .contest-card{grid-column:3;grid-row:1}
  .entry time{grid-column:1;grid-row:1;padding-top:29px;text-align:right}
  .entry-left .contest-card{grid-column:1}
  .entry-left time{grid-column:3;text-align:left}
  .entry-left .lab-card::before{right:-8px;left:auto;transform:translateX(100%)}
  .entry-left:hover .contest-card{transform:translateX(-7px)}
}
@media(max-width:680px){
  .lab-card::before{left:-8px;right:auto;transform:translateX(-100%)}
}
</style>
