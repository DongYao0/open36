<template>
  <div class="auth-page">
    <div class="auth-left">
      <div class="brand"><div class="brand-icon">O</div><span>Open436</span></div>
      <div class="hero-title">
        <code class="code-line">
          <span class="token-class">System</span><span class="token-dot">.</span><span class="token-method">out</span><span class="token-dot">.</span><span class="token-method">print</span><span class="token-paren">(</span><span class="token-string">"Hello 0436!"</span><span class="token-paren">)</span><span class="token-semicolon">;</span><span class="cursor">|</span>
        </code>
      </div>
      <div class="characters">
        <div class="char-group">
          <div ref="pR" class="char purple" :class="{ stretch: isStretch, shrink: isShrink }" :style="pBody">
            <div class="eyes" :class="{ closed: allEyesClosed }" :style="pEyes">
              <div class="eye" :class="{ blink: pb || allEyesClosed }"><div class="pupil" :style="pPupil"/></div>
              <div class="eye" :class="{ blink: pb || allEyesClosed }"><div class="pupil" :style="pPupil"/></div>
            </div>
          </div>
          <div ref="bR" class="char black" :class="{ stretch: isStretch, shrink: isShrink }" :style="bBody">
            <div class="eyes" :class="{ closed: allEyesClosed }" :style="bEyes">
              <div class="eye" :class="{ blink: bb || allEyesClosed }"><div class="pupil" :style="bPupil"/></div>
              <div class="eye" :class="{ blink: bb || allEyesClosed }"><div class="pupil" :style="bPupil"/></div>
            </div>
          </div>
          <div ref="oR" class="char orange" :class="{ stretch: isStretch, shrink: isShrink }" :style="oBody">
            <div class="eyes" :class="{ closed: allEyesClosed }" :style="oEyes">
              <div class="pupil-wrap"><div class="pupil-only" :style="oPupil"/></div>
              <div class="pupil-wrap"><div class="pupil-only" :style="oPupil"/></div>
            </div>
          </div>
          <div ref="yR" class="char yellow" :class="{ stretch: isStretch, shrink: isShrink }" :style="yBody">
            <div class="eyes" :class="{ closed: allEyesClosed }" :style="yEyes">
              <div class="pupil-wrap"><div class="pupil-only" :style="yPupil"/></div>
              <div class="pupil-wrap"><div class="pupil-only" :style="yPupil"/></div>
            </div>
            <div class="mouth" :style="mS"/>
          </div>
        </div>
      </div>
      <div class="floating-letters">
        <div class="fleaf java">Java</div>
        <div class="fleaf spring">Spring</div>
        <div class="fleaf springboot">SpringBoot</div>
        <div class="fleaf langchain">LangChain</div>
        <div class="fleaf openai_api">OpenAI_API</div>
        <div class="fleaf maven">Maven</div>
        <div class="fleaf mysql">MySQL</div>
        <div class="fleaf redis">Redis</div>
        <div class="fleaf prompt_engineering">Prompt Engineering</div>
        <div class="fleaf vector_database">Vector_Database</div>
        <div class="fleaf embeddings">Embeddings</div>
        <div class="fleaf rag">RAG</div>
        <div class="fleaf git">Git</div>
        <div class="fleaf docker">Docker</div>
        <div class="fleaf restful">RESTful</div>
        <div class="fleaf api">API</div>
        <div class="fleaf service">Service</div>
        <div class="fleaf mapper">Mapper</div>
        <div class="fleaf dto">DTO</div>
        <div class="fleaf linux">Linux</div>
        <div class="fleaf html">HTML</div>
        <div class="fleaf css">CSS</div>
        <div class="fleaf javascript">JavaScript</div>
        <div class="fleaf react">React</div>
        <div class="fleaf vue">Vue</div>
        <div class="fleaf angular">Angular</div>
        <div class="fleaf nodejs">Node.js</div>
        <div class="fleaf llm">LLM</div>
      </div>
      <div class="bg-grid"/><div class="bg-orb o1"/><div class="bg-orb o2"/><div class="bg-orb o3"/>
    </div>
    <div class="auth-right">
      <div class="mobile-brand"><div class="brand-icon">O</div><span>Open436</span></div>
      <div class="form-box">
        <div class="form-tabs">
          <button :class="{ active: !isEnroll }" @click="setMode(false)">登录</button>
          <button :class="{ active: isEnroll }" @click="setMode(true)">报名</button>
        </div>
        <div class="form-header"><h1>{{ isEnroll ? '报名加入 Open436' : '欢迎回来！' }}</h1><p>{{ isEnroll ? '填写信息申请成为 0436 正式成员' : '请输入你的账号信息' }}</p></div>
        <form @submit.prevent="onSubmit" class="auth-form">
          <div class="form-group"><label>{{ isEnroll ? '真实姓名' : '用户名' }}</label><input ref="uRef" v-model="f.u" type="text" :placeholder="isEnroll ? '2-20 位字符，将作为登录账号' : '3-20 位'" maxlength="20" autocomplete="username" required @focus="onTextFocus" @blur="onBlur"/></div>
          <div class="form-group"><label>密码</label><div class="password-wrap"><input ref="pRef" v-model="f.p" :type="showP ? 'text' : 'password'" placeholder="至少 6 位" autocomplete="current-password" required @focus="onPasswordFocus" @blur="onBlur"/><button type="button" class="eye-btn" @click="showP = !showP"><svg v-if="showP" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/><line x1="1" y1="1" x2="23" y2="23"/></svg><svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></button></div></div>

          <template v-if="isEnroll">
            <div class="form-group"><label>确认密码</label><div class="password-wrap"><input v-model="f.cp" :type="showP ? 'text' : 'password'" placeholder="再次输入密码" required @focus="onPasswordFocus" @blur="onBlur"/></div></div>
            <div class="form-group"><label>学号</label><input v-model="f.sid" type="text" placeholder="请输入学号" maxlength="30" required @focus="onTextFocus" @blur="onBlur"/></div>
            <div class="form-group"><label>电话号码</label><input v-model="f.ph" type="tel" placeholder="请输入 11 位手机号" maxlength="11" pattern="[0-9]*" inputmode="numeric" required @focus="onTextFocus" @blur="onBlur"/></div>
          </template>

          <div v-if="!isEnroll" class="form-options"><label class="remember"><input type="checkbox" v-model="f.r"/><span>记住我</span></label><a href="#" class="forgot">忘记密码？</a></div>
          <div v-if="err" class="error-msg">{{ err }}</div>
          <button type="submit" class="submit-btn" :disabled="ld"><span v-if="ld" class="spinner"/>{{ ld ? (isEnroll ? '提交中...' : '登录中...') : (isEnroll ? '提交报名申请' : '登录') }}</button>
        </form>
        <div class="guest-entry">
          <div class="divider"><span>或</span></div>
          <button class="guest-btn" @click="enterAsGuest">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            游客浏览
          </button>
          <p class="guest-tip">不登录，仅浏览内容</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const R = useRoute(), router = useRouter(), auth = useAuthStore(), ui = useUIStore()
const isEnroll = ref(R.query.mode === 'register')
const ld = ref(false), err = ref(''), showP = ref(false)
const f = reactive({ u: '', p: '', cp: '', sid: '', ph: '', r: false })

const focusedType = ref(null)
const mx = ref(0), my = ref(0)
const uRef = ref(null), pRef = ref(null)
const pR = ref(null), bR = ref(null), oR = ref(null), yR = ref(null)
const pb = ref(false), bb = ref(false)

function onMove(e) { mx.value = e.clientX; my.value = e.clientY }
onMounted(() => window.addEventListener('mousemove', onMove))
onUnmounted(() => window.removeEventListener('mousemove', onMove))

const targetPt = computed(() => {
  const ae = document.activeElement
  if (ae && (ae.type === 'text' || ae.type === 'username' || ae.type === 'tel')) {
    const r = ae.getBoundingClientRect()
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 }
  }
  return null
})

function bodyOf(ref, maxSkew, sCfg, kCfg) {
  if (!ref.value) return {}
  const r = ref.value.getBoundingClientRect()
  const cx = r.left + r.width / 2
  if (focusedType.value === 'text' && sCfg) {
    return { transform: `skewX(${sCfg.skew}deg) translateX(${sCfg.x}px) translateY(${sCfg.y}px) scale(${sCfg.s}) !important` }
  }
  if (focusedType.value === 'password' && kCfg) {
    return { transform: `skewX(${kCfg.skew}deg) translateX(${kCfg.x}px) translateY(${kCfg.y}px) scale(${kCfg.s}) !important` }
  }
  const dx = mx.value - cx
  const baseSk = Math.max(-maxSkew, Math.min(maxSkew, -dx / 120))
  return { transform: `skewX(${baseSk}deg) !important` }
}

function eyesOf(ref, maxX, maxY) {
  if (!ref.value) return {}
  if (focusedType.value === 'password') {
    return { transform: `translate(-${maxX}px, 0px)` }
  }
  const r = ref.value.getBoundingClientRect()
  const cx = r.left + r.width / 2, cy = r.top + r.height / 3
  const t = targetPt.value || { x: mx.value, y: my.value }
  const dx = t.x - cx, dy = t.y - cy
  return { transform: `translate(${Math.max(-maxX, Math.min(maxX, dx / 20))}px, ${Math.max(-maxY, Math.min(maxY, dy / 30))}px)` }
}

function pupilOf(ref, maxD) {
  if (!ref.value) return {}
  if (focusedType.value === 'password') {
    return { transform: `translate(-${maxD}px, 0px)` }
  }
  const r = ref.value.getBoundingClientRect()
  const cx = r.left + r.width / 2, cy = r.top + r.height / 3
  const t = targetPt.value || { x: mx.value, y: my.value }
  const dx = t.x - cx, dy = t.y - cy
  const d = Math.min(Math.sqrt(dx * dx + dy * dy), maxD)
  const a = Math.atan2(dy, dx)
  return { transform: `translate(${Math.cos(a) * d}px, ${Math.sin(a) * d}px)` }
}

const isStretch = computed(() => focusedType.value !== 'password')
const isShrink = computed(() => focusedType.value === 'password')
const allEyesClosed = computed(() => false)

const pBody = computed(() => bodyOf(pR, 8, { skew: -12, x: 40, y: -15, s: 1.03 }, { skew: 10, x: -12, y: 8, s: 0.97 }))
const bBody = computed(() => bodyOf(bR, 6, { skew: -10, x: 25, y: -8, s: 1.03 }, { skew: 8, x: -10, y: 6, s: 0.97 }))
const oBody = computed(() => bodyOf(oR, 5, { skew: -8, x: 30, y: -30, s: 1.08 }, { skew: 6, x: -12, y: 15, s: 0.92 }))
const yBody = computed(() => bodyOf(yR, 6, { skew: -8, x: 22, y: -25, s: 1.1 }, { skew: 6, x: -10, y: 12, s: 0.9 }))

const pEyes = computed(() => eyesOf(pR, 15, 10))
const bEyes = computed(() => eyesOf(bR, 12, 8))
const oEyes = computed(() => eyesOf(oR, 18, 12))
const yEyes = computed(() => eyesOf(yR, 14, 9))

const pPupil = computed(() => pupilOf(pR, 6))
const bPupil = computed(() => pupilOf(bR, 5))
const oPupil = computed(() => pupilOf(oR, 5))
const yPupil = computed(() => pupilOf(yR, 5))
const mS = computed(() => pupilOf(yR, 5))

function blink(tgt, dur = 150) {
  const dl = Math.random() * 4000 + 3000
  return setTimeout(() => { tgt.value = true; setTimeout(() => { tgt.value = false; blink(tgt, dur) }, dur) }, dl)
}
let pt, bt
onMounted(() => { pt = blink(pb); bt = blink(bb) })
onUnmounted(() => { clearTimeout(pt); clearTimeout(bt) })

function onTextFocus() { focusedType.value = 'text' }
function onPasswordFocus() { focusedType.value = 'password' }
function onBlur() {
  setTimeout(() => {
    const ae = document.activeElement
    if (ae?.type === 'password') focusedType.value = 'password'
    else if (ae?.tagName === 'INPUT' || ae?.tagName === 'TEXTAREA') focusedType.value = 'text'
    else focusedType.value = null
  }, 50)
}

function setMode(enroll) {
  isEnroll.value = enroll
  err.value = ''
  if (!enroll) {
    Object.assign(f, { cp: '', sid: '', ph: '' })
  }
}

async function onSubmit() {
  err.value = ''
  const username = uRef.value?.value || f.u
  const password = pRef.value?.value || f.p

  if (isEnroll.value) {
    if (f.u.trim().length < 2 || f.u.trim().length > 20) { err.value = '真实姓名长度必须为 2-20 位'; return }
    if (f.p.length < 6) { err.value = '密码至少 6 位'; return }
    if (f.p !== f.cp) { err.value = '两次密码输入不一致'; return }
    if (!f.sid.trim()) { err.value = '请填写学号'; return }
    if (!/^1\d{10}$/.test(f.ph.trim())) { err.value = '请输入正确的 11 位手机号'; return }
  }

  ld.value = true
  try {
    if (isEnroll.value) {
      const res = await auth.register({
        username: f.u.trim(),
        password: f.p,
        realName: f.u.trim(),
        studentId: f.sid.trim(),
        phone: f.ph.trim(),
        major: ''
      })
      if (res.success) {
        ui.showToast(res.message || '报名成功', 'success')
        router.push('/')
      } else {
        err.value = res.message || '报名失败'
      }
    } else {
      const r = await auth.login(username, password)
      if (r.success) {
        ui.showToast('登录成功！', 'success')
        try {
          await router.push(R.query.redirect || '/')
        } catch (navErr) {
          console.error('登录跳转失败:', navErr)
          // 兜底：强制跳首页
          window.location.href = '/'
        }
      } else err.value = r.message || '登录失败'
    }
  } catch (e) {
    const serverMsg = e?.response?.data?.message
    err.value = serverMsg || e?.message || (isEnroll.value ? '报名失败' : '登录失败')
  } finally { ld.value = false }
}

function enterAsGuest() {
  auth.enterGuestMode()
  ui.showToast('已进入游客浏览模式', 'success')
  router.push('/')
}
</script>

<style scoped>
@import url('@/styles/login-page.css');

.form-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--surface-border);
  padding-bottom: 4px;
}
.form-tabs button {
  flex: 1;
  padding: 10px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  transition: all .2s;
  font-family: inherit;
}
.form-tabs button.active {
  color: var(--accent);
  background: rgba(99,102,241,0.12);
}
.form-tabs button:hover:not(.active) {
  color: var(--text-primary);
  background: rgba(255,255,255,0.05);
}

.form-box { max-width: 520px; }

.form-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 10px;
}
@media (max-width: 480px) {
  .form-row { grid-template-columns: 1fr; }
}

.guest-entry { margin-top: 20px; }
.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  color: var(--text-secondary);
  font-size: 13px;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--surface-border);
}
.guest-btn {
  width: 100%;
  height: 44px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--surface-border);
  border-radius: 14px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: inherit;
}
.guest-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(99,102,241,0.06);
}
.guest-tip {
  text-align: center;
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.7;
}
</style>
