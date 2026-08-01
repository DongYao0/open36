<template>
  <AppNavbar />
  <div class="page-mount">
    <div class="submit-container">
      <!-- 顶栏 -->
      <div class="page-header">
        <router-link to="/mine" class="back-link">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        </router-link>
        <h1>作业提交</h1>
        <span class="status-badge" :class="assignment.submissionStatus">
          {{ assignment.submissionStatus === 'submitted' ? '已提交' : '待提交' }}
        </span>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-state">加载中...</div>

      <!-- 作业内容 -->
      <template v-else>
        <!-- 作业信息卡 -->
        <div class="info-card">
          <h2 class="assignment-title">{{ assignment.title }}</h2>
          <div class="assignment-desc" v-if="assignment.description">{{ assignment.description }}</div>
          <div class="meta-row">
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              分配时间: {{ formatDate(assignment.assignedAt) }}
            </span>
            <span class="meta-item" v-if="assignment.deadline">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              截止时间: {{ formatDate(assignment.deadline) }}
            </span>
            <span class="meta-item" v-if="isExpired" style="color: var(--error)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              已截止
            </span>
          </div>
        </div>

        <!-- 已提交内容（只读） -->
        <div v-if="assignment.submissionStatus === 'submitted'" class="submitted-card">
          <div class="submitted-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <span>已于 {{ formatDate(assignment.submittedAt) }} 提交</span>
          </div>
          <div class="submitted-content" v-if="assignment.content">
            <label>提交内容</label>
            <div class="content-text">{{ assignment.content }}</div>
          </div>
          <div class="submitted-files" v-if="assignment.files?.length">
            <label>提交文件</label>
            <div class="file-list">
              <div v-for="(file, idx) in assignment.files" :key="idx" class="file-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span>{{ file.name || file }}</span>
              </div>
            </div>
          </div>
          <button v-if="!isExpired" class="btn btn-primary" @click="editMode = true">
            重新提交
          </button>
        </div>

        <!-- 提交表单 -->
        <div v-if="assignment.submissionStatus !== 'submitted' || editMode" class="submit-form">
          <h3>{{ editMode ? '重新提交' : '提交作业' }}</h3>

          <div class="form-group">
            <label>作业内容</label>
            <textarea
              v-model="form.content"
              placeholder="请输入作业内容..."
              rows="8"
              :disabled="isExpired"
            ></textarea>
          </div>

          <div class="form-actions">
            <router-link to="/mine" class="btn btn-secondary">取消</router-link>
            <button
              class="btn btn-primary"
              @click="handleSubmit"
              :disabled="submitting || isExpired"
            >
              {{ submitting ? '提交中...' : '提交作业' }}
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppNavbar from '@/components/AppNavbar.vue'
import { useUIStore } from '@/stores/ui'
import { getMyAssignmentDetail, submitAssignment } from '@/api/user'

const router = useRouter()
const route = useRoute()
const ui = useUIStore()

const assignmentId = route.params.id
const loading = ref(true)
const submitting = ref(false)
const editMode = ref(false)
const assignment = ref({})

const form = reactive({
  content: ''
})

const isExpired = computed(() => {
  if (!assignment.value.deadline) return false
  return new Date(assignment.value.deadline) < new Date()
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function loadAssignment() {
  loading.value = true
  try {
    const res = await getMyAssignmentDetail(assignmentId)
    assignment.value = res.data || {}
    form.content = assignment.value.content || ''
  } catch (e) {
    console.error('加载作业失败:', e)
    ui.showToast('加载作业失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!form.content.trim()) {
    ui.showToast('请输入作业内容', 'warning')
    return
  }

  submitting.value = true
  try {
    await submitAssignment(assignmentId, {
      content: form.content.trim()
    })
    ui.showToast('作业提交成功', 'success')
    editMode.value = false
    await loadAssignment() // 重新加载
  } catch (e) {
    const msg = e?.response?.data?.message || e?.message || '提交失败'
    ui.showToast(msg, 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadAssignment()
})
</script>

<style scoped>
.page-mount {
  padding-top: var(--navbar-h);
  min-height: 100vh;
  background: var(--bg-secondary);
}
.submit-container {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--s-xl) var(--s-base);
}

/* 顶栏 */
.page-header {
  display: flex;
  align-items: center;
  gap: var(--s-base);
  margin-bottom: var(--s-xl);
}
.page-header h1 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
}
.back-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--r-md);
  background: var(--bg);
  color: var(--text-primary);
  text-decoration: none;
  transition: all 200ms;
}
.back-link:hover { background: var(--primary-bg); color: var(--primary); }
.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.status-badge.submitted {
  background: var(--success-bg, #e8f5e9);
  color: var(--success, #4caf50);
}
.status-badge.unsubmitted {
  background: var(--warning-bg, #fff3e0);
  color: var(--warning, #ff9800);
}

/* 作业信息卡 */
.info-card {
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  padding: var(--s-lg);
  margin-bottom: var(--s-lg);
}
.assignment-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--s-sm);
}
.assignment-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: var(--s-base);
}
.meta-row {
  display: flex;
  gap: var(--s-lg);
  flex-wrap: wrap;
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}
.meta-item svg { opacity: 0.6; }

/* 已提交内容 */
.submitted-card {
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  padding: var(--s-lg);
  margin-bottom: var(--s-lg);
}
.submitted-header {
  display: flex;
  align-items: center;
  gap: var(--s-sm);
  padding-bottom: var(--s-base);
  border-bottom: 1px solid var(--divider);
  margin-bottom: var(--s-base);
  font-size: 14px;
  color: var(--success);
  font-weight: 500;
}
.submitted-content,
.submitted-files {
  margin-bottom: var(--s-base);
}
.submitted-content label,
.submitted-files label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.content-text {
  padding: var(--s-base);
  background: var(--bg-secondary);
  border-radius: var(--r-md);
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
}
.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--r-md);
  font-size: 13px;
  color: var(--text-primary);
}
.file-item svg { color: var(--primary); opacity: 0.6; }

/* 提交表单 */
.submit-form {
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  padding: var(--s-lg);
}
.submit-form h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--s-base);
}
.form-group {
  margin-bottom: var(--s-lg);
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--divider);
  border-radius: var(--r-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  min-height: 150px;
  transition: all 200ms;
}
.form-group textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}
.form-group textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 按钮 */
.form-actions {
  display: flex;
  gap: var(--s-base);
  justify-content: flex-end;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: var(--r-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 200ms;
}
.btn-primary {
  background: var(--primary);
  color: #fff;
}
.btn-primary:hover { background: var(--primary-dark); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary {
  background: var(--bg);
  color: var(--text-primary);
  border: 1px solid var(--divider);
  text-decoration: none;
}
.btn-secondary:hover { background: var(--bg-secondary); }

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--s-3xl);
  color: var(--text-tertiary);
}

/* 响应式 */
@media (max-width: 600px) {
  .meta-row { flex-direction: column; gap: var(--s-sm); }
  .form-actions { flex-direction: column-reverse; }
  .form-actions .btn { width: 100%; justify-content: center; }
}
</style>
