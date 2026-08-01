<template>
  <AppNavbar />
  <div class="page-mount">
    <div class="scene">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>

      <div class="enroll-card">
        <div class="enroll-header">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="8.5" cy="7" r="4"/>
              <line x1="20" y1="8" x2="20" y2="14"/>
              <line x1="23" y1="11" x2="17" y2="11"/>
            </svg>
          </div>
          <h2 class="title">报名加入 Open436</h2>
          <p class="subtitle">填写基本信息，申请成为 0436 正式成员</p>
        </div>

        <form @submit.prevent="onSubmit" class="enroll-form">
          <div class="form-section">
            <div class="section-label">账号信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>用户名 <span class="required">*</span></label>
                <input v-model="form.username" type="text" placeholder="3-20 位字符" maxlength="20" required />
              </div>
              <div class="form-group">
                <label>密码 <span class="required">*</span></label>
                <div class="password-wrap">
                  <input v-model="form.password" :type="showPwd ? 'text' : 'password'" placeholder="至少 6 位" required />
                  <button type="button" class="eye-btn" @click="showPwd = !showPwd">
                    <svg v-if="showPwd" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/><line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>确认密码 <span class="required">*</span></label>
                <input v-model="form.confirmPassword" :type="showPwd ? 'text' : 'password'" placeholder="再次输入密码" required />
              </div>
              <div class="form-group">
                <label>昵称</label>
                <input v-model="form.nickname" type="text" placeholder="显示名称（可选）" />
              </div>
            </div>
          </div>

          <div class="form-divider"></div>

          <div class="form-section">
            <div class="section-label">基本信息</div>
            <div class="form-row">
              <div class="form-group">
                <label>学号 <span class="required">*</span></label>
                <input v-model="form.studentId" type="text" placeholder="请输入学号" maxlength="30" required />
              </div>
              <div class="form-group">
                <label>真实姓名 <span class="required">*</span></label>
                <input v-model="form.realName" type="text" placeholder="请输入真实姓名" maxlength="50" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>电话号码 <span class="required">*</span></label>
                <input v-model="form.phone" type="tel" placeholder="请输入电话号码" maxlength="20" required />
              </div>
              <div class="form-group">
                <label>专业 <span class="required">*</span></label>
                <input v-model="form.major" type="text" placeholder="请输入专业名称" maxlength="50" required />
              </div>
            </div>
          </div>

          <div v-if="error" class="error-msg">{{ error }}</div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="loading" class="spinner-small"></span>
            {{ loading ? '提交中...' : '提交报名申请' }}
          </button>

          <div class="form-footer">
            已有账号？<router-link to="/login">立即登录</router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import request from '@/api/request'
import AppNavbar from '@/components/AppNavbar.vue'

const router = useRouter()
const ui = useUIStore()
const auth = useAuthStore()

const loading = ref(false)
const error = ref('')
const showPwd = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  studentId: '',
  realName: '',
  phone: '',
  major: ''
})

async function onSubmit() {
  error.value = ''

  if (form.username.length < 3 || form.username.length > 20) {
    error.value = '用户名长度必须为 3-20 位'
    return
  }
  if (form.password.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  if (form.password !== form.confirmPassword) {
    error.value = '两次密码输入不一致'
    return
  }
  if (!form.studentId.trim()) {
    error.value = '请填写学号'
    return
  }
  if (!form.realName.trim()) {
    error.value = '请填写真实姓名'
    return
  }
  if (!form.phone.trim()) {
    error.value = '请填写电话号码'
    return
  }
  if (!form.major.trim()) {
    error.value = '请填写专业'
    return
  }

  loading.value = true
  try {
    const res = await request.post('/api/enrollment/apply', {
      username: form.username.trim(),
      password: form.password,
      realName: form.realName.trim(),
      studentId: form.studentId.trim(),
      phone: form.phone.trim(),
      major: form.major.trim(),
      selfIntro: '',
      skills: ''
    })
    if (res.code === 200) {
      ui.showToast(res.message || '报名成功，已自动登录', 'success')
      // 自动以 pending 身份登录
      try {
        await auth.login(form.username.trim(), form.password)
        router.push('/')
      } catch (e) {
        ui.showToast('报名成功，请手动登录', 'success')
        router.push('/login')
      }
    } else {
      error.value = res.message || '报名失败'
    }
  } catch (e) {
    const msg = e?.response?.data?.message
    error.value = msg || e?.message || '报名失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page-mount {
  padding-top: var(--navbar-h);
  min-height: 100vh;
  background: var(--bg-secondary);
}
.scene {
  min-height: calc(100vh - var(--navbar-h));
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: var(--s-xl) var(--s-base);
}
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
  pointer-events: none;
}
.orb-1 {
  width: 380px; height: 380px;
  background: radial-gradient(circle, rgba(25,118,210,0.22), transparent 70%);
  top: -8%; left: -4%;
  animation: drift 16s ease-in-out infinite alternate;
}
.orb-2 {
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(66,165,245,0.18), transparent 70%);
  bottom: -6%; right: -2%;
  animation: drift 13s ease-in-out infinite alternate-reverse;
}
@keyframes drift {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(-20px, 15px) scale(1.08); }
}

.enroll-card {
  background: var(--bg);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-lg);
  width: 100%;
  max-width: 640px;
  position: relative;
  z-index: 1;
  animation: fadeUp 600ms cubic-bezier(0.4, 0, 0.2, 1) both;
  overflow: hidden;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.enroll-header {
  text-align: center;
  padding: var(--s-2xl) var(--s-xl) var(--s-lg);
  background: linear-gradient(135deg, rgba(25,118,210,0.04) 0%, rgba(66,165,245,0.06) 100%);
  border-bottom: 1px solid var(--divider);
}
.header-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto var(--s-md);
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(25,118,210,0.25);
}
.header-icon svg { width: 28px; height: 28px; }
.title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--s-xs);
  letter-spacing: -0.3px;
}
.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

.enroll-form {
  padding: var(--s-xl) var(--s-2xl) var(--s-2xl);
}
.form-section {
  margin-bottom: var(--s-lg);
}
.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: var(--s-md);
  padding-left: var(--s-sm);
  border-left: 3px solid var(--primary);
}
.form-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--s-lg);
  margin-bottom: var(--s-md);
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--s-xs);
  min-width: 0;
}
.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}
.required { color: var(--error); }
.form-group input {
  width: 100%;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--divider);
  border-radius: var(--r-sm);
  font-size: 14px;
  transition: all var(--t-fast);
  background: var(--bg);
  color: var(--text-primary);
  box-sizing: border-box;
}
.form-group input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(25,118,210,0.1);
}
.password-wrap {
  position: relative;
}
.password-wrap input { padding-right: 38px; }
.eye-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.eye-btn:hover { color: var(--text-primary); }

.form-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--divider), transparent);
  margin: var(--s-lg) 0;
}

.error-msg {
  background: rgba(244,67,54,0.08);
  color: var(--error);
  padding: var(--s-sm) var(--s-base);
  border-radius: var(--r-sm);
  font-size: 13px;
  margin-bottom: var(--s-lg);
  border-left: 3px solid var(--error);
}

.submit-btn {
  width: 100%;
  height: 44px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  border: none;
  border-radius: var(--r-sm);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--t-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--s-sm);
  box-shadow: 0 4px 12px rgba(25,118,210,0.25);
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(25,118,210,0.35);
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.spinner-small {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.form-footer {
  text-align: center;
  margin-top: var(--s-lg);
  font-size: 13px;
  color: var(--text-secondary);
}
.form-footer a {
  color: var(--primary);
  font-weight: 500;
}
.form-footer a:hover {
  text-decoration: underline;
}

@media (max-width: 599px) {
  .enroll-form { padding: var(--s-lg) var(--s-base) var(--s-xl); }
  .form-row { grid-template-columns: 1fr; gap: var(--s-md); }
  .title { font-size: 20px; }
  .enroll-header { padding: var(--s-xl) var(--s-lg) var(--s-base); }
}
</style>
