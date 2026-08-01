<template>
  <div class="card">
    <div class="post-detail">
      <div class="post-meta">
        <img :src="`https://ui-avatars.com/api/?name=${post.author}&background=1976D2&color=fff&size=40`" class="avatar" />
        <div>
          <div class="author-name">u/{{ post.author }}</div>
          <div class="post-time">{{ formatDate(post.createdAt) }} · {{ post.section }}</div>
        </div>
      </div>
      <h1 class="post-title">{{ post.title }}</h1>
      <div class="post-content" v-html="postHtml"></div>
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDate, markdownToHtml } from '@/utils/format'

const props = defineProps({
  post: { type: Object, required: true }
})

const postHtml = computed(() => markdownToHtml(props.post?.content || ''))
</script>

<style scoped>
.post-detail { padding: var(--s-lg); }
.post-meta { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-base); }
.author-name { font-weight: 500; font-size: 14px; }
.post-time { font-size: 12px; color: var(--text-secondary); }
.post-title { font-size: 24px; font-weight: 600; margin-bottom: var(--s-base); line-height: 1.4; }
.post-content { line-height: 1.8; color: var(--text-primary); margin-bottom: var(--s-lg); }
.post-content :deep(h2) { font-size: 20px; margin: var(--s-base) 0 var(--s-sm); }
.post-content :deep(h3) { font-size: 16px; margin: var(--s-base) 0 var(--s-xs); }
.post-content :deep(code) { background: var(--bg-dark); padding: 2px 6px; border-radius: 3px; font-family: var(--mono); font-size: 13px; }
.post-content :deep(pre) { background: #1e1e1e; color: #d4d4d4; padding: var(--s-base); border-radius: var(--r-md); overflow-x: auto; margin: var(--s-base) 0; }
.post-content :deep(pre code) { background: none; padding: 0; color: inherit; }
.post-content :deep(blockquote) { border-left: 3px solid var(--primary); padding-left: var(--s-base); color: var(--text-secondary); margin: var(--s-base) 0; }
.post-content :deep(img) { max-width: 100%; border-radius: var(--r-sm); margin: var(--s-sm) 0; }
</style>
