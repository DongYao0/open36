<template>
  <article class="resource-detail">
    <header class="resource-hero">
      <div class="resource-emblem">↗</div>
      <div class="resource-heading">
        <p class="eyebrow">RESOURCE DIRECTORY · {{ category }}</p>
        <h1>{{ post.title }}</h1>
        <p class="summary">{{ summary }}</p>
        <div class="resource-tags"><span>{{ category }}</span><span>资源分享</span><span>Open436 精选</span></div>
      </div>
      <div class="resource-actions">
        <a v-for="link in links" :key="link.url" :href="link.url" target="_blank" rel="noopener">{{ link.label }} <b>↗</b></a>
        <a v-if="!links.length" href="#resource-guide">阅读使用说明 <b>↓</b></a>
        <small>发布者 · {{ post.author }}<br>更新于 {{ formatDate(post.createdAt) }}</small>
      </div>
    </header>

    <div class="resource-layout">
      <main class="resource-article">
        <section class="resource-intro"><p>为什么值得收藏</p><h2>把可用的资源，变成可复用的效率。</h2><span>{{ summary }}</span></section>
        <section id="resource-guide" class="resource-body"><div v-html="postHtml"></div></section>
      </main>
      <aside class="resource-aside">
        <section><p>资源信息</p><dl><dt>类型</dt><dd>{{ category }}</dd><dt>提供方式</dt><dd>{{ links.length ? '外部链接' : '正文说明' }}</dd><dt>访问入口</dt><dd>{{ links.length }} 个</dd></dl></section>
        <section class="resource-tip"><p>使用提醒</p><span>打开外部链接前，请自行确认版本、权限与来源安全性。</span></section>
      </aside>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { formatDate, markdownToHtml } from '@/utils/format'

const props = defineProps({ post: { type: Object, required: true } })
const plain = computed(() => (props.post.content || '').replace(/!?(\[[^\]]*\]\([^)]*\)|[`#*_>-])/g, '').replace(/https?:\/\/\S+/g, '').replace(/\s+/g, ' ').trim())
const summary = computed(() => plain.value.slice(0, 158) || '一份值得保存、可以直接上手使用的资源。')
const category = computed(() => /agent|ai|模型|claude|gpt/i.test(`${props.post.title} ${props.post.content}`) ? 'AI / Agent 工具' : /github|开源|项目|仓库/i.test(`${props.post.title} ${props.post.content}`) ? '开源项目' : '效率工具')
const links = computed(() => {
  const matches = [...(props.post.content || '').matchAll(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|\b(https?:\/\/[^\s)]+)/g)]
  const seen = new Set()
  return matches.map(match => ({ label: match[1] || '访问资源', url: match[2] || match[3] })).filter(link => !seen.has(link.url) && seen.add(link.url)).slice(0, 3)
})
const postHtml = computed(() => markdownToHtml(props.post.content || ''))
</script>

<style scoped>
.resource-detail{--ink:#17213f;--paper:#f7f3e9;--orange:#e86f31;max-width:1180px;margin:0 auto;color:var(--ink)}
.resource-hero{display:grid;grid-template-columns:72px minmax(0,1fr) 184px;gap:22px;align-items:start;padding:42px;border:1px solid #d9cfba;border-radius:22px;background:linear-gradient(132deg,#fffdf6,#ece3d0);box-shadow:0 24px 60px rgba(29,42,83,.14)}
.resource-emblem{display:grid;place-items:center;width:78px;height:78px;border-radius:22px;background:var(--ink);color:#fff5da;font:700 42px/1 Georgia,serif;transform:rotate(-7deg)}
.eyebrow,.resource-intro>p,.resource-aside p{margin:0;color:#a74d21;font-size:11px;font-weight:800;letter-spacing:.13em}.resource-heading h1{margin:8px 0 12px;font:700 clamp(30px,4vw,54px)/1.08 var(--font-display);letter-spacing:-.05em}.summary{max-width:none;margin:0;color:#596276;font-size:16px;line-height:1.8}.resource-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.resource-tags span{padding:5px 9px;border:1px solid #d7c7ae;border-radius:999px;color:#6b5847;font-size:12px}
.resource-actions{display:grid;gap:9px}.resource-actions a{display:flex;justify-content:space-between;padding:11px 13px;border-radius:9px;background:var(--ink);color:#fff;text-decoration:none;font-size:13px;font-weight:700}.resource-actions a:first-child{background:var(--orange)}.resource-actions small{margin-top:8px;color:#7b756e;font-size:11px;line-height:1.7}
.resource-layout{display:grid;grid-template-columns:minmax(0,1fr) 215px;gap:20px;margin-top:24px}.resource-article{padding:42px 48px;border-radius:20px;background:#fffdf7;box-shadow:0 16px 38px rgba(29,42,83,.09)}.resource-intro{padding-bottom:32px;border-bottom:1px solid #e5dccb}.resource-intro h2{max-width:none;margin:10px 0;color:#253151;font:700 28px/1.25 var(--font-display)}.resource-intro span{color:#6c737f;line-height:1.8}.resource-body{padding-top:30px;font-size:15px;line-height:1.95}.resource-body :deep(h2){margin:32px 0 12px;color:#253151;font-size:23px}.resource-body :deep(h3){margin:26px 0 10px;color:#a74d21;font-size:17px}.resource-body :deep(a){color:#c25224;font-weight:700}.resource-body :deep(pre){overflow:auto;padding:18px;border-radius:12px;background:#18213b;color:#f5eddb}.resource-body :deep(img){max-width:100%;border-radius:12px}
.resource-aside{display:grid;align-content:start;gap:16px}.resource-aside section{padding:22px;border:1px solid #d9cfba;border-radius:16px;background:rgba(255,253,247,.78)}.resource-aside dl{display:grid;gap:7px;margin:17px 0 0}.resource-aside dt{color:#82796e;font-size:11px}.resource-aside dd{margin:0;color:#2d3855;font-size:14px;font-weight:700}.resource-tip{background:#253151!important;color:#f7f0df}.resource-tip p{color:#f0b266}.resource-tip span{display:block;margin-top:12px;font-size:13px;line-height:1.7}
@media(max-width:820px){.resource-detail{margin:0 4px}.resource-hero{grid-template-columns:64px 1fr;padding:25px;gap:18px}.resource-emblem{width:58px;height:58px;font-size:31px}.resource-actions{grid-column:1/-1}.resource-layout{grid-template-columns:1fr}.resource-aside{grid-template-columns:1fr 1fr}.resource-article{padding:30px 24px}}@media(max-width:560px){.resource-aside{grid-template-columns:1fr}.resource-heading h1{font-size:32px}}
</style>
