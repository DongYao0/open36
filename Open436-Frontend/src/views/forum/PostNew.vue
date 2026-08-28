<template>
  <!-- Back nav -->
  <div class="pn-shell" :class="isResource ? 'pn-shell--resource' : 'pn-shell--tech'">
  <div class="pn-nav">
    <router-link :to="targetPath" class="pn-back">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="15 18 9 12 15 6"/></svg>
      返回{{ isResource ? '资源分享' : '技术交流' }}
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
        <h2 class="pn-title">{{ isResource ? '收录一份可用资源' : '写一篇工程笔记' }}</h2>
        <p class="pn-desc">{{ isResource ? '把链接、用途和上手方法交给下一位使用者' : '记录问题、方案、代码与可复现的实践结论' }}</p>
      </div>
    </div>

    <div class="pn-body">
      <div class="pn-field">
        <label class="pn-label">{{ isResource ? '资源名称' : '文章标题' }}</label>
        <input v-model="form.title" class="pn-input" :placeholder="isResource ? '例如：一个值得收藏的 Agent 上下文压缩项目' : '例如：如何为 Agent 设计可靠的 Memory'" maxlength="100" />
        <div class="pn-counter">{{ form.title.length }}/100</div>
      </div>

      <div class="pn-field">
        <label class="pn-label">{{ isResource ? '推荐理由' : '文章摘要' }}</label>
        <textarea v-model="form.summary" class="pn-textarea-simple" :placeholder="isResource ? '它能解决什么问题、适合谁使用、为什么值得收藏' : '用两三句话说清问题、结论与读者能获得什么'" rows="3" maxlength="300"></textarea>
        <div class="pn-counter">{{ form.summary.length }}/300</div>
      </div>

      <div v-if="isResource" class="pn-field">
        <label class="pn-label">资源链接</label>
        <input v-model="form.resourceUrl" class="pn-input" placeholder="官网、GitHub 仓库、下载地址或网盘链接" inputmode="url" />
        <p class="pn-field-hint">该链接会成为资源详情页顶部的“获取资源”入口。</p>
      </div>

      <div class="pn-mode-note">
        <b>{{ isResource ? 'RESOURCE DIRECTORY' : 'ENGINEERING NOTE' }}</b>
        <span>{{ isResource ? '将发布到资源分享，详情页会展示获取入口和资源信息。' : '将发布到技术交流，详情页会生成摘要和文章目录。' }}</span>
      </div>

      <div class="pn-field">
        <label class="pn-label">{{ isResource ? '使用说明与补充信息' : '技术正文' }}</label>
        <div class="pn-editor">
          <div class="pn-toolbar">
            <button v-for="t in toolbar" :key="t.label" class="pn-tool" @click="t.action ? t.action() : insertMarkdown(t.syntax)" :title="t.label" :disabled="imageUploading" v-html="t.icon"></button>
            <span v-if="imageUploading" class="pn-uploading-hint">上传中...</span>
          </div>
          <input ref="imageFileInput" type="file" accept="image/jpeg,image/png,image/gif,image/svg+xml" style="display:none" @change="handleImageUpload" />
          <div class="pn-split">
            <textarea v-model="form.content" class="pn-textarea" :placeholder="isResource ? '建议写明：适用场景、使用步骤、注意事项与替代方案。支持 Markdown。' : '建议写明：问题背景、方案取舍、关键实现、踩坑和结论。支持 Markdown。'" rows="16"></textarea>
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
          {{ submitting ? '发布中...' : (isResource ? '发布资源' : '发布文章') }}
        </button>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { markdownToHtml } from '@/utils/format'
import { createPost } from '@/api/post'
import { uploadFile } from '@/api/file'

const router = useRouter()
const route = useRoute()
const sectionStore = useSectionStore()
const ui = useUIStore()
const auth = useAuthStore()
const submitting = ref(false)
const imageUploading = ref(false)
const imageFileInput = ref(null)
const form = ref({ title: '', summary: '', section: 'tech', resourceUrl: '', content: '' })
const isResource = computed(() => route.query.type === 'share')
const targetPath = computed(() => isResource.value ? '/forum/share' : '/forum/tech')

const toolbar = [
  { label: '加粗', syntax: '**粗体文本**', icon: '<b>B</b>' },
  { label: '斜体', syntax: '*斜体文本*', icon: '<i>I</i>' },
  { label: '标题', syntax: '\n## 标题\n', icon: 'H' },
  { label: '代码', syntax: '`代码`', icon: '&lt;/&gt;' },
  { label: '链接', syntax: '[链接文本](https://)', icon: '🔗' },
  { label: '图片', icon: '🖼', action: () => imageFileInput.value?.click() },
  { label: '列表', syntax: '\n- 列表项\n', icon: '&#8226;' },
  { label: '引用', syntax: '\n> 引用内容\n', icon: '❝' }
]

const previewHtml = computed(() => markdownToHtml(form.value.content))
const canSubmit = computed(() => form.value.title.trim() && form.value.content.trim() && form.value.section && (!isResource.value || form.value.resourceUrl.trim()))

onMounted(() => {
  if (!auth.canPost) { ui.showToast('请先登录后再发帖', 'warning'); router.push('/login'); return }
  form.value.section = isResource.value ? 'share' : 'tech'
  sectionStore.fetchSections()
})

function insertMarkdown(syntax) { form.value.content += syntax }

async function handleImageUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  // 重置 input 以便重复选择同一文件
  e.target.value = ''

  // 客户端校验
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) { ui.showToast('图片大小不能超过 5MB', 'warning'); return }
  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/svg+xml']
  if (!allowed.includes(file.type)) { ui.showToast('仅支持 JPG / PNG / GIF / SVG 格式', 'warning'); return }

  imageUploading.value = true
  try {
    const res = await uploadFile(file, 'post')
    // 响应拦截器已解包 {code, message, data}，res 即 data 部分
    const url = res.data?.url || res.url
    const filename = res.data?.filename || file.name
    if (!url) { ui.showToast('上传成功但未获取到图片地址', 'error'); return }
    insertMarkdown(`\n![${filename}](${url})\n`)
    ui.showToast('图片上传成功', 'success')
  } catch (err) {
    const msg = err?.response?.data?.message || '图片上传失败，请稍后重试'
    ui.showToast(msg, 'error')
  } finally {
    imageUploading.value = false
  }
}

async function submitPost() {
  if (!canSubmit.value) { ui.showToast('请填写完整内容', 'warning'); return }
  if (submitting.value) return
  if (isResource.value) {
    try {
      const url = new URL(form.value.resourceUrl.trim())
      if (!['http:', 'https:'].includes(url.protocol)) throw new Error('unsupported protocol')
    }
    catch { ui.showToast('请填写有效的资源链接（需以 http:// 或 https:// 开头）', 'warning'); return }
  }
  submitting.value = true
  try {
    let sectionId = sectionStore.getSectionId(form.value.section)
    if (!sectionId) { await sectionStore.fetchSections(); sectionId = sectionStore.getSectionId(form.value.section) }
    if (!sectionId) { ui.showToast('板块信息异常，请刷新重试', 'error'); return }
    const content = isResource.value
      ? `## 获取资源\n\n[访问资源](${form.value.resourceUrl.trim()})\n\n${form.value.content.trim()}`
      : form.value.content.trim()
    await createPost({ title: form.value.title.trim(), summary: form.value.summary.trim(), content, section_id: sectionId })
    ui.showToast('发布成功！', 'success')
    router.push('/forum/' + (form.value.section || 'tech'))
  } catch (e) {
    const errData = e?.response?.data
    const msg = errData?.message || '发布失败，请稍后重试'
    const details = errData?.errors ? Object.values(errData.errors).flat().join('; ') : ''
    ui.showToast(details ? `${msg}: ${details}` : msg, 'error')
  } finally { submitting.value = false }
}
</script>

<style scoped>
.pn-shell{--pn-panel:rgba(8,17,47,.88);--pn-panel-soft:rgba(16,26,67,.72);--pn-line:rgba(146,186,255,.24);--pn-text:#edf3ff;--pn-muted:#aab8dc;--pn-accent:#71ddff;max-width:1180px;margin:0 auto;color:var(--pn-text)}.pn-shell--resource{--pn-panel:rgba(39,25,60,.88);--pn-panel-soft:rgba(78,40,70,.76);--pn-line:rgba(246,203,137,.31);--pn-text:#fff5e8;--pn-muted:#e8cfc2;--pn-accent:#f5ae5d}
.pn-nav{margin-bottom:16px}.pn-back{color:var(--pn-muted)}.pn-back:hover{color:var(--pn-accent);background:rgba(255,255,255,.06)}.pn-card{border-color:var(--pn-line);border-radius:22px;background:var(--pn-panel);box-shadow:0 24px 70px rgba(0,0,0,.28);backdrop-filter:blur(14px)}.pn-header{padding:30px 34px;border-color:var(--pn-line);background:linear-gradient(130deg,rgba(91,74,191,.25),transparent 62%)}.pn-shell--resource .pn-header{background:linear-gradient(130deg,rgba(228,111,52,.28),transparent 62%)}.pn-header-icon{border-color:var(--pn-line);background:rgba(112,221,255,.13);color:var(--pn-accent)}.pn-title,.pn-label{color:var(--pn-text)}.pn-desc,.pn-counter,.pn-field-hint{color:var(--pn-muted)}.pn-body{padding:32px 34px}.pn-input,.pn-textarea-simple,.pn-textarea{box-sizing:border-box;border-color:var(--pn-line);background:rgba(3,10,31,.36);color:var(--pn-text)}.pn-input:focus,.pn-textarea-simple:focus{border-color:var(--pn-accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--pn-accent) 15%,transparent)}.pn-field-hint{margin:7px 0 0;font-size:12px}.pn-mode-note{display:grid;grid-template-columns:170px 1fr;gap:16px;margin:0 0 var(--s-lg);padding:15px 17px;border:1px solid var(--pn-line);border-radius:12px;background:var(--pn-panel-soft);font-size:13px;line-height:1.65}.pn-mode-note b{color:var(--pn-accent);font-size:11px;letter-spacing:.11em}.pn-mode-note span{color:var(--pn-muted)}
.pn-editor{border-color:var(--pn-line)}.pn-toolbar{background:rgba(2,8,25,.6);border-color:var(--pn-line)}.pn-tool{color:var(--pn-muted)}.pn-tool:hover{background:rgba(255,255,255,.08);color:var(--pn-text)}.pn-preview{border-color:var(--pn-line);background:rgba(3,10,31,.28);color:var(--pn-text)}.pn-actions{border-color:var(--pn-line)}.pn-actions .btn-primary{background:var(--pn-accent);color:#071225}.pn-actions .btn-text{color:var(--pn-muted)}
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
.pn-textarea-simple {
  width: 100%; padding: 10px 12px; border: 1px solid var(--divider);
  border-radius: var(--r-sm); font-size: 14px; resize: vertical; line-height: 1.6;
  transition: all var(--t-fast);
}
.pn-textarea-simple:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(25,118,210,0.1); outline: none; }

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
.pn-tool:disabled { opacity: 0.5; cursor: not-allowed; }
.pn-uploading-hint { font-size: 12px; color: var(--primary); margin-left: 8px; align-self: center; }
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
.pn-preview :deep(img) { max-width: 100%; border-radius: var(--r-sm); margin: var(--s-sm) 0; }

.pn-actions { display: flex; justify-content: flex-end; gap: var(--s-sm); padding-top: var(--s-lg); border-top: 1px solid var(--divider); }

@media (max-width: 959px) { .pn-split { flex-direction: column; } }
.pn-shell .pn-card{border-color:var(--pn-line);background:var(--pn-panel)}.pn-shell .pn-header{border-color:var(--pn-line);background:linear-gradient(130deg,rgba(91,74,191,.25),transparent 62%)}.pn-shell--resource .pn-header{background:linear-gradient(130deg,rgba(228,111,52,.28),transparent 62%)}.pn-shell .pn-title,.pn-shell .pn-label{color:var(--pn-text)}.pn-shell .pn-desc,.pn-shell .pn-counter,.pn-shell .pn-field-hint{color:var(--pn-muted)}.pn-shell .pn-input,.pn-shell .pn-textarea-simple,.pn-shell .pn-textarea{border-color:var(--pn-line);background:rgba(3,10,31,.36);color:var(--pn-text)}.pn-shell .pn-editor,.pn-shell .pn-toolbar,.pn-shell .pn-preview,.pn-shell .pn-actions{border-color:var(--pn-line)}.pn-shell .pn-toolbar{background:rgba(2,8,25,.6)}.pn-shell .pn-preview{background:rgba(3,10,31,.28);color:var(--pn-text)}.pn-shell .pn-tool{color:var(--pn-muted)}.pn-shell .pn-actions .btn-primary{background:var(--pn-accent);color:#071225}.pn-shell .pn-actions .btn-text{color:var(--pn-muted)}
</style>
