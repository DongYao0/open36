<template>
  <AppNavbar />
  <div class="page-mount">
    <div class="edit-container">
      <!-- 顶栏 -->
      <div class="edit-header">
        <router-link to="/mine" class="back-link">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        </router-link>
        <h1>编辑资料</h1>
      </div>

      <!-- 头像区 -->
      <div class="avatar-section">
        <div class="avatar-preview">
          <img :src="form.avatarUrl || defaultAvatar" />
        </div>
        <div class="avatar-info">
          <h3>头像</h3>
          <p>支持 JPG、PNG 格式，文件大小不超过 2MB</p>
          <div class="avatar-actions">
            <button class="btn btn-primary btn-sm" @click="triggerUpload">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              上传头像
            </button>
            <button class="btn btn-text btn-sm" @click="removeAvatar">删除</button>
          </div>
          <input ref="fileInput" type="file" accept="image/jpeg,image/png" style="display:none" @change="handleFileChange" />
        </div>
      </div>

      <!-- 基本信息 -->
      <div class="form-section">
        <h2 class="section-title">基本信息</h2>
        <div class="form-group">
          <label>昵称</label>
          <div class="input-wrapper">
            <input v-model="form.nickname" type="text" placeholder="请输入昵称" maxlength="20" @input="updateCount('nickname')" />
            <span class="char-count">{{ counts.nickname }}/20</span>
          </div>
        </div>
        <div class="form-group">
          <label>用户名</label>
          <input :value="auth.user?.username" type="text" disabled />
          <p class="form-hint">用户名不可修改</p>
        </div>
      </div>

      <!-- 个人简介 -->
      <div class="form-section">
        <h2 class="section-title">个人简介</h2>
        <div class="form-group">
          <label>简介</label>
          <div class="input-wrapper">
            <textarea v-model="form.bio" placeholder="介绍一下你自己..." rows="4" maxlength="200" @input="updateCount('bio')"></textarea>
            <span class="char-count">{{ counts.bio }}/200</span>
          </div>
        </div>
      </div>

      <!-- 报名信息（只读） -->
      <div class="form-section" v-if="hasEnrollInfo">
        <h2 class="section-title">报名信息</h2>
        <div class="readonly-grid">
          <div class="readonly-item" v-if="auth.user?.realName">
            <label>姓名</label>
            <span>{{ auth.user.realName }}</span>
          </div>
          <div class="readonly-item" v-if="auth.user?.studentId">
            <label>学号</label>
            <span>{{ auth.user.studentId }}</span>
          </div>
          <div class="readonly-item" v-if="auth.user?.major">
            <label>专业</label>
            <span>{{ auth.user.major }}</span>
          </div>
          <div class="readonly-item" v-if="auth.user?.phone">
            <label>电话</label>
            <span>{{ auth.user.phone }}</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <router-link to="/mine" class="btn btn-secondary">取消</router-link>
        <button class="btn btn-primary" @click="saveProfile" :disabled="saving">
          {{ saving ? '保存中...' : '保存更改' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppNavbar from '@/components/AppNavbar.vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { getUserProfile, updateUserProfile, uploadAvatar as uploadAvatarApi } from '@/api/user'

const router = useRouter()
const auth = useAuthStore()
const ui = useUIStore()

const defaultAvatar = 'https://ui-avatars.com/api/?name=User&background=1976D2&color=fff&size=120'
const fileInput = ref(null)
const saving = ref(false)

const form = reactive({
  nickname: '',
  bio: '',
  avatarUrl: ''
})

const counts = reactive({
  nickname: 0,
  bio: 0
})

const hasEnrollInfo = computed(() => {
  const u = auth.user
  return u?.realName || u?.studentId || u?.major || u?.phone
})

function updateCount(field) {
  counts[field] = form[field]?.length || 0
}

async function loadProfile() {
  if (!auth.user?.id) return
  try {
    const res = await getUserProfile(auth.user.id)
    if (res.code === 200 && res.data) {
      form.nickname = res.data.nickname || ''
      form.bio = res.data.bio || ''
      form.avatarUrl = res.data.avatarUrl || ''
      updateCount('nickname')
      updateCount('bio')
    }
  } catch (e) {
    console.error('加载资料失败:', e)
  }
}

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileChange(e) {
  const file = e.target.files[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    ui.showToast('文件大小不能超过 2MB', 'warning')
    return
  }

  try {
    const res = await uploadAvatarApi(auth.user.id, file)
    if (res.code === 200 && res.data?.avatar_url) {
      form.avatarUrl = res.data.avatar_url
      // 更新本地用户信息
      auth.setUser({ ...auth.user, avatarUrl: res.data.avatar_url })
      ui.showToast('头像上传成功', 'success')
    }
  } catch (e) {
    ui.showToast('头像上传失败', 'error')
  }

  // 清空input
  e.target.value = ''
}

function removeAvatar() {
  form.avatarUrl = ''
  ui.showToast('头像已删除', 'success')
}

async function saveProfile() {
  if (!form.nickname.trim()) {
    ui.showToast('请输入昵称', 'warning')
    return
  }

  saving.value = true
  try {
    const res = await updateUserProfile(auth.user.id, {
      nickname: form.nickname.trim(),
      bio: form.bio.trim()
    })
    if (res.code === 200) {
      // 更新本地用户信息
      auth.setUser({
        ...auth.user,
        nickname: form.nickname.trim(),
        bio: form.bio.trim()
      })
      ui.showToast('资料更新成功', 'success')
      setTimeout(() => router.push('/mine'), 500)
    }
  } catch (e) {
    ui.showToast('更新失败，请重试', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.page-mount {
  padding-top: var(--navbar-h);
  min-height: 100vh;
  background: var(--bg-secondary);
}
.edit-container {
  max-width: 640px;
  margin: 0 auto;
  padding: var(--s-xl) var(--s-base);
}

/* 顶栏 */
.edit-header {
  display: flex;
  align-items: center;
  gap: var(--s-base);
  margin-bottom: var(--s-xl);
}
.edit-header h1 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
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

/* 头像区 */
.avatar-section {
  display: flex;
  align-items: center;
  gap: var(--s-lg);
  padding: var(--s-lg);
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  margin-bottom: var(--s-lg);
}
.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  border: 3px solid var(--bg-secondary);
}
.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-info {
  flex: 1;
}
.avatar-info h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.avatar-info p {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: var(--s-sm);
}
.avatar-actions {
  display: flex;
  gap: var(--s-sm);
}

/* 表单区 */
.form-section {
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  padding: var(--s-lg);
  margin-bottom: var(--s-lg);
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--s-base);
  padding-bottom: var(--s-sm);
  border-bottom: 1px solid var(--divider);
}
.form-group {
  margin-bottom: var(--s-base);
}
.form-group:last-child { margin-bottom: 0; }
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--divider);
  border-radius: var(--r-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  transition: all 200ms;
}
.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}
.form-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.form-group textarea {
  resize: vertical;
  min-height: 80px;
}
.form-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}
.input-wrapper {
  position: relative;
}
.input-wrapper input,
.input-wrapper textarea {
  padding-right: 60px;
}
.char-count {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 只读信息 */
.readonly-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--s-base);
}
.readonly-item label {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}
.readonly-item span {
  font-size: 14px;
  color: var(--text-primary);
}

/* 操作按钮 */
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
.btn-text {
  background: transparent;
  color: var(--text-secondary);
}
.btn-text:hover { color: var(--primary); }
.btn-sm { padding: 6px 12px; font-size: 13px; }

/* 响应式 */
@media (max-width: 600px) {
  .avatar-section {
    flex-direction: column;
    text-align: center;
  }
  .avatar-actions { justify-content: center; }
  .readonly-grid { grid-template-columns: 1fr; }
  .form-actions { flex-direction: column-reverse; }
  .form-actions .btn { width: 100%; justify-content: center; }
}
</style>
