<template>
  <!-- Back nav -->
  <div class="pn-nav">
    <router-link to="/forum" class="pn-back">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="15 18 9 12 15 6"/></svg>
      返回论坛
    </router-link>
  </div>

  <div class="pn-card">
    <div class="pn-header">
      <div class="pn-header-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="22" height="22">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </div>
      <div>
        <h2 class="pn-title">发布新帖</h2>
        <p class="pn-desc">分享你的想法与经验</p>
      </div>
    </div>

    <div class="pn-body">
      <div class="pn-field">
        <label class="pn-label">标题</label>
        <input v-model="form.title" class="pn-input" placeholder="请输入帖子标题" maxlength="100" />
        <div class="pn-counter">{{ form.title.length }}/100</div>
      </div>

      <div class="pn-field">
        <label class="pn-label">板块</label>
        <div class="pn-sections">
          <button
            v-for="s in sectionStore.forumSections.filter(s => s.key !== 'all')"
            :key="s.key"
            class="pn-section-btn"
            :class="{ active: form.section === s.key }"
            :style="form.section === s.key ? { background: s.color, borderColor: s.color } : {}"
            @click="form.section = s.key"
          >
            {{ s.name }}
          </button>
        </div>
      </div>

      <div class="pn-field">
        <label class="pn-label">内容</label>
        <div class="pn-editor">
          <div class="pn-toolbar">
            <button v-for="t in toolbar" :key="t.label" class="pn-tool" @click="insertMarkdown(t.syntax)" :title="t.label" v-html="t.icon"></button>
          </div>
          <div class="pn-split">
            <textarea v-model="form.content" class="pn-textarea" placeholder="支持 Markdown 语法..." rows="16"></textarea>
            <div class="pn-preview">
              <div v-if="previewHtml" v-html="previewHtml"></div>
              <span v-else class="pn-preview-placeholder">预览区域...</span>
            </div>
          </div>
        </div>
      </div>

      <div class="pn-actions">
        <button class="btn btn-text" @click="router.back()">取消</button>
        <button class="btn btn-primary" @click="submitPost" :disabled="!canSubmit || submitting">
          <svg v-if="!submitting" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
          {{ submitting ? '发布中...' : '发布帖子' }}
        </button>
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
const form = ref({ title: '', section: 'tech', content: '' })

const toolbar = [
  { label: '加粗', syntax: '**粗体文本**', icon: '<b>B</b>' },
  { label: '斜体', syntax: '*斜体文本*', icon: '<i>I</i>' },
  { label: '标题', syntax: '\n## 标题\n', icon: 'H' },
  { label: '代码', syntax: '`代码`', icon: '&lt;/&gt;' },
  { label: '链接', syntax: '[链接文本](https://)', icon: '🔗' },
  { label: '图片', syntax: '![图片描述](https://)', icon: '🖼' },
  { label: '列表', syntax: '\n- 列表项\n', icon: '&#8226;' },
  { label: '引用', syntax: '\n> 引用内容\n', icon: '❝' }
]

const previewHtml = computed(() => markdownToHtml(form.value.content))
const canSubmit = computed(() => form.value.title.trim() && form.value.content.trim() && form.value.section)

onMounted(() => {
  if (!auth.canPost) { ui.showToast('请先登录后再发帖', 'warning'); router.push('/login'); return }
  sectionStore.fetchSections()
})

function insertMarkdown(syntax) { form.value.content += syntax }

async function submitPost() {
  if (!canSubmit.value) { ui.showToast('请填写完整内容', 'warning'); return }
  if (submitting.value) return
  submitting.value = true
  try {
    let sectionId = sectionStore.getSectionId(form.value.section)
    if (!sectionId) { await sectionStore.fetchSections(); sectionId = sectionStore.getSectionId(form.value.section) }
    if (!sectionId) { ui.showToast('板块信息异常，请刷新重试', 'error'); return }
    await createPost({ title: form.value.title.trim(), content: form.value.content.trim(), section_id: sectionId })
    ui.showToast('发布成功！', 'success')
    router.push('/forum')
  } catch (e) {
    const errData = e?.response?.data
    const msg = errData?.message || '发布失败，请稍后重试'
    const details = errData?.errors ? Object.values(errData.errors).flat().join('; ') : ''
    ui.showToast(details ? `${msg}: ${details}` : msg, 'error')
  } finally { submitting.value = false }
}
</script>

<style scoped>
.pn-nav { margin-bottom: var(--s-base); }
.pn-back {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 13px; color: var(--text-secondary); font-weight: 500;
  padding: 6px 12px; border-radius: var(--r-sm); transition: all var(--t-fast);
}
.pn-back:hover { color: var(--primary); background: var(--primary-bg); }

.pn-card { background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md); overflow: hidden; }
.pn-header {
  display: flex; align-items: center; gap: var(--s-base);
  padding: var(--s-lg); border-bottom: 1px solid var(--divider);
  background: linear-gradient(135deg, #EFF6FF 0%, #F8FBFF 100%);
}
.pn-header-icon {
  width: 44px; height: 44px; border-radius: var(--r-md); flex-shrink: 0;
  background: var(--primary-bg); color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(25,118,210,0.15);
}
.pn-title { font-size: 20px; font-weight: 700; margin-bottom: 2px; }
.pn-desc { font-size: 13px; color: var(--text-secondary); }

.pn-body { padding: var(--s-lg); }
.pn-field { margin-bottom: var(--s-lg); }
.pn-label { display: block; font-size: 14px; font-weight: 600; margin-bottom: var(--s-sm); }
.pn-input {
  width: 100%; padding: 10px 12px; border: 1px solid var(--divider);
  border-radius: var(--r-sm); font-size: 14px; transition: all var(--t-fast);
}
.pn-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(25,118,210,0.1); }
.pn-counter { text-align: right; font-size: 12px; color: var(--text-disabled); margin-top: var(--s-xs); }

.pn-sections { display: flex; gap: var(--s-sm); flex-wrap: wrap; }
.pn-section-btn {
  padding: 6px 16px; border-radius: 999px; font-size: 13px; font-weight: 500;
  border: 1px solid var(--divider); color: var(--text-secondary);
  transition: all var(--t-fast);
}
.pn-section-btn:hover { border-color: var(--primary); color: var(--primary); }
.pn-section-btn.active { color: #fff; border-color: transparent; }

.pn-editor { border: 1px solid var(--divider); border-radius: var(--r-sm); overflow: hidden; }
.pn-toolbar {
  display: flex; gap: 2px; padding: var(--s-sm); background: var(--bg-dark);
  border-bottom: 1px solid var(--divider);
}
.pn-tool {
  width: 32px; height: 32px; border-radius: var(--r-sm); font-size: 13px;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-secondary); transition: all var(--t-fast);
}
.pn-tool:hover { background: var(--bg); color: var(--text-primary); }
.pn-split { display: flex; }
.pn-textarea {
  flex: 1; border: none; resize: none; font-family: var(--mono);
  font-size: 14px; line-height: 1.6; padding: var(--s-base);
}
.pn-textarea:focus { box-shadow: none; outline: none; }
.pn-preview {
  flex: 1; padding: var(--s-base); background: var(--bg); font-size: 14px;
  line-height: 1.8; overflow-y: auto; border-left: 1px solid var(--divider);
  min-height: 300px;
}
.pn-preview-placeholder { color: var(--text-disabled); }

.pn-actions { display: flex; justify-content: flex-end; gap: var(--s-sm); padding-top: var(--s-lg); border-top: 1px solid var(--divider); }

@media (max-width: 959px) { .pn-split { flex-direction: column; } }
</style>
