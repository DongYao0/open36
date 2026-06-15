<template>
  <div class="card">
    <div class="card-header">分享资源</div>
    <div class="card-body">
      <div class="form-group">
        <label class="form-label">标题</label>
        <input v-model="form.title" class="form-input" placeholder="请输入资源标题" maxlength="100" />
      </div>
      <div class="form-group">
        <label class="form-label">简介 <span class="form-hint">（卡片展示用，不超过300字）</span></label>
        <textarea v-model="form.summary" class="form-textarea" placeholder="简要描述这个资源的用途和亮点..." rows="3" maxlength="300"></textarea>
      </div>
      <div class="form-group">
        <label class="form-label">正文内容</label>
        <div class="editor-toolbar">
          <button v-for="t in toolbar" :key="t.label" class="toolbar-btn" @click="insertMarkdown(t.syntax)" :title="t.label" v-html="t.icon"></button>
        </div>
        <div class="editor-split">
          <textarea v-model="form.content" class="form-textarea editor-pane" placeholder="描述资源内容、使用方式、下载链接等..." rows="16"></textarea>
          <div class="preview-pane" v-html="previewHtml"></div>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn btn-text" @click="router.back()">取消</button>
        <button class="btn btn-primary" @click="submitPost" :disabled="!canSubmit || submitting">{{ submitting ? '发布中...' : '发布资源' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { markdownToHtml } from '@/utils/format'
import { createPost } from '@/api/post'

const router = useRouter()
const sectionStore = useSectionStore()
const ui = useUIStore()
const auth = useAuthStore()
const submitting = ref(false)
const form = ref({ title: '', summary: '', content: '' })

const toolbar = [
  { label: '加粗', syntax: '**粗体文本**', icon: '<b>B</b>' },
  { label: '斜体', syntax: '*斜体文本*', icon: '<i>I</i>' },
  { label: '标题', syntax: '\n## 标题\n', icon: 'H' },
  { label: '代码', syntax: '`代码`', icon: '&lt;/&gt;' },
  { label: '链接', syntax: '[链接文本](https://)', icon: '🔗' },
  { label: '列表', syntax: '\n- 列表项\n', icon: '&#8226;' },
  { label: '引用', syntax: '\n> 引用内容\n', icon: '❝' }
]

const previewHtml = computed(() => markdownToHtml(form.value.content))
const canSubmit = computed(() => form.value.title.trim() && form.value.content.trim())

onMounted(() => {
  if (!auth.canPost) {
    ui.showToast('请先登录后再发布', 'warning')
    router.push('/login')
    return
  }
  sectionStore.fetchSections()
})

function insertMarkdown(syntax) {
  form.value.content += syntax
}

async function submitPost() {
  if (!canSubmit.value) { ui.showToast('请填写完整内容', 'warning'); return }
  if (submitting.value) return
  submitting.value = true
  try {
    const sectionId = sectionStore.getSectionId('share')
    if (!sectionId) {
      await sectionStore.fetchSections()
    }
    const sid = sectionStore.getSectionId('share')
    if (!sid) {
      ui.showToast('板块信息异常，请刷新重试', 'error')
      return
    }
    const payload = {
      title: form.value.title.trim(),
      summary: form.value.summary.trim(),
      content: form.value.content.trim(),
      section_id: sid
    }
    await createPost(payload)
    ui.showToast('发布成功！', 'success')
    router.push('/resources')
  } catch (e) {
    const errData = e?.response?.data
    const msg = errData?.message || '发布失败，请稍后重试'
    const details = errData?.errors ? Object.values(errData.errors).flat().join('; ') : ''
    ui.showToast(details ? `${msg}: ${details}` : msg, 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.editor-toolbar {
  display: flex; gap: 2px; padding: var(--s-sm); background: var(--bg-dark);
  border: 1px solid var(--divider); border-bottom: none; border-radius: var(--r-sm) var(--r-sm) 0 0;
}
.toolbar-btn {
  width: 32px; height: 32px; border-radius: var(--r-sm); font-size: 13px;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-secondary); transition: all var(--t-fast);
}
.toolbar-btn:hover { background: var(--bg); color: var(--text-primary); }
.editor-split { display: flex; gap: 0; border: 1px solid var(--divider); border-radius: 0 0 var(--r-sm) var(--r-sm); overflow: hidden; }
.editor-pane {
  flex: 1; border: none; border-radius: 0; resize: none; font-family: var(--mono);
  font-size: 14px; line-height: 1.6; padding: var(--s-base);
}
.editor-pane:focus { box-shadow: none; }
.preview-pane {
  flex: 1; padding: var(--s-base); background: var(--bg); font-size: 14px;
  line-height: 1.8; overflow-y: auto; border-left: 1px solid var(--divider);
  min-height: 300px;
}
.preview-pane:empty::before { content: '预览区域...'; color: var(--text-disabled); }
.form-actions { display: flex; justify-content: flex-end; gap: var(--s-sm); margin-top: var(--s-lg); }
@media (max-width: 959px) { .editor-split { flex-direction: column; } }
</style>
