<template>
  <article class="tech-detail">
    <header class="tech-head">
      <p>ENGINEERING NOTE / {{ post.section || '技术交流' }}</p>
      <h1>{{ post.title }}</h1>
      <div class="tech-meta"><span>u/{{ post.author }}</span><span>{{ formatDate(post.createdAt) }}</span><span>{{ headings.length }} 个章节</span></div>
      <div class="tech-abstract"><b>摘要</b><span>{{ summary }}</span></div>
    </header>
    <div class="tech-layout">
      <main class="tech-article"><div v-html="postHtml"></div></main>
      <aside class="tech-aside">
        <p>本文目录</p>
        <a v-for="(heading, index) in headings" :key="`${heading}-${index}`" :href="`#tech-section-${index}`">{{ heading }}</a>
        <div class="tech-note"><b>讨论原则</b><span>补充推理、实践结果与可复现的代码，帮助下一位读者少走弯路。</span></div>
      </aside>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { formatDate, markdownToHtml } from '@/utils/format'

const props = defineProps({ post: { type: Object, required: true } })
const headings = computed(() => [...(props.post.content || '').matchAll(/^#{2,3}\s+(.+)$/gm)].map(match => match[1].trim()).slice(0, 8))
const summary = computed(() => (props.post.content || '').replace(/^#{1,3}\s+.*$/gm, '').replace(/[`*_>#-]/g, '').replace(/\s+/g, ' ').trim().slice(0, 180) || '围绕一个真实工程问题，记录方案、取舍与实践结果。')
const postHtml = computed(() => {
  let index = 0
  return markdownToHtml(props.post.content || '').replace(/<h([23])>(.*?)<\/h\1>/g, (_, level, text) => `<h${level} id="tech-section-${index++}">${text}</h${level}>`)
})
</script>

<style scoped>
.tech-detail{max-width:1180px;margin:0 auto;color:#eaf0ff}.tech-head{padding:44px 48px 35px;border:1px solid rgba(146,186,255,.27);border-radius:22px;background:linear-gradient(120deg,rgba(12,22,63,.9),rgba(38,23,84,.78));box-shadow:0 25px 70px rgba(0,0,0,.3)}
.tech-head>p{margin:0;color:#86ddff;font:800 11px/1 var(--font-mono,var(--font-body));letter-spacing:.15em}.tech-head h1{max-width:none;margin:13px 0 18px;color:#fff;font:700 clamp(31px,4.6vw,59px)/1.12 var(--font-display);letter-spacing:-.045em}.tech-meta{display:flex;flex-wrap:wrap;gap:14px;color:rgba(225,235,255,.68);font-size:13px}.tech-meta span+span:before{margin-right:14px;color:#6c82bd;content:'/'}.tech-abstract{display:grid;grid-template-columns:50px 1fr;gap:14px;max-width:none;margin-top:28px;padding:17px 19px;border-left:2px solid #67d7ff;background:rgba(8,15,47,.3);color:#cbd8fa;line-height:1.75}.tech-abstract b{color:#9ae5ff;font-size:12px;letter-spacing:.12em}
.tech-layout{display:grid;grid-template-columns:minmax(0,1fr) 210px;gap:20px;align-items:start;margin-top:24px}.tech-article{padding:45px 50px;border:1px solid rgba(146,186,255,.18);border-radius:20px;background:rgba(8,15,43,.72);box-shadow:0 17px 45px rgba(0,0,0,.2);font-size:15px;line-height:1.95}.tech-article :deep(h2){margin:36px 0 13px;color:#fff;font:700 28px/1.25 var(--font-display)}.tech-article :deep(h3){margin:26px 0 10px;color:#8de4ff;font-size:18px}.tech-article :deep(p){color:#d2dcf5}.tech-article :deep(strong){color:#fff}.tech-article :deep(a){color:#7bd7ff}.tech-article :deep(code){padding:2px 6px;border-radius:4px;background:rgba(137,91,255,.22);color:#e9d9ff}.tech-article :deep(pre){overflow:auto;padding:20px;border:1px solid rgba(130,167,255,.2);border-radius:13px;background:#090e22;color:#dbeaff}.tech-article :deep(img){max-width:100%;border-radius:12px}.tech-article :deep(blockquote){margin:22px 0;padding-left:17px;border-left:2px solid #6be1ff;color:#aebfe5}
.tech-aside{position:sticky;top:76px;display:grid;gap:3px;padding:20px;border:1px solid rgba(146,186,255,.18);border-radius:16px;background:rgba(11,19,54,.74)}.tech-aside>p{margin:0 0 9px;color:#8ee0ff;font-size:11px;font-weight:800;letter-spacing:.13em}.tech-aside>a{padding:7px 8px;border-radius:7px;color:#cbd7f5;font-size:13px;line-height:1.4;text-decoration:none}.tech-aside>a:hover{background:rgba(104,209,255,.12);color:#fff}.tech-note{display:grid;gap:8px;margin-top:16px;padding-top:16px;border-top:1px solid rgba(146,186,255,.17);color:#aebcdc;font-size:12px;line-height:1.65}.tech-note b{color:#fff}
@media(max-width:840px){.tech-head{padding:30px 26px}.tech-layout{grid-template-columns:1fr}.tech-aside{position:static;grid-template-columns:repeat(2,minmax(0,1fr))}.tech-aside>p,.tech-note{grid-column:1/-1}.tech-article{padding:32px 25px}}@media(max-width:560px){.tech-head h1{font-size:34px}.tech-aside{grid-template-columns:1fr}.tech-article{padding:26px 20px}}
</style>
