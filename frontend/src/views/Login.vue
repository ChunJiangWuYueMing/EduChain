<template>
  <main class="login-page">
    <section class="login-canvas">
      <aside class="brand-panel">
        <div class="brand-content">
          <img :src="logoUrl" alt="西南交通大学 EduChain" class="brand-logo" />
          <p class="brand-subtitle">校园学习资料可信交换平台</p>
        </div>

        <img class="brand-watermark" :src="whiteLogoUrl" alt="" aria-hidden="true" />
        <div class="bridge-line" aria-hidden="true"></div>

        <div class="system-status">
          <span class="status-dot dot-ok"></span>
          <span>系统状态：正常</span>
        </div>
      </aside>

      <img class="main-watermark" :src="mainLogoUrl" alt="" aria-hidden="true" />

      <section class="login-card" aria-label="登录系统">
        <h1 class="card-title">登录系统</h1>

        <div v-if="errorMsg" class="error-alert" role="alert">
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <path
              fill="currentColor"
              fill-rule="evenodd"
              d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm1-11a1 1 0 1 0-2 0v4a1 1 0 1 0 2 0V7Zm-1 8a1.15 1.15 0 1 0 0-2.3 1.15 1.15 0 0 0 0 2.3Z"
              clip-rule="evenodd"
            />
          </svg>
          <span>{{ errorMsg }}</span>
        </div>

        <label class="field">
          <span class="field-label">学号</span>
          <span class="input-shell">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <input
              v-model="form.studentId"
              type="text"
              autocomplete="username"
              placeholder="请输入学号"
              @keydown.enter="focusPassword"
            />
          </span>
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <span class="input-shell">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <path d="M7 11V8a5 5 0 0 1 10 0v3" />
            </svg>
            <input
              ref="passwordInput"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="请输入密码"
              @keydown.enter="handleLogin"
            />
            <button
              type="button"
              class="password-toggle"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              @click="showPassword = !showPassword"
            >
              <svg v-if="showPassword" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                <path d="M17.94 17.94A10.8 10.8 0 0 1 12 19C6 19 2 12 2 12a18.2 18.2 0 0 1 4.06-4.94" />
                <path d="M9.9 4.24A9.8 9.8 0 0 1 12 4c6 0 10 8 10 8a17.4 17.4 0 0 1-2.18 3.18" />
                <path d="M14.12 14.12a3 3 0 0 1-4.24-4.24" />
                <path d="M3 3l18 18" />
              </svg>
            </button>
          </span>
        </label>

        <button type="button" class="login-button" :disabled="loading" @click="handleLogin">
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <div class="assist-row">
          <span>测试账号：20240001 / password123（仅供演示使用）</span>
          <button type="button" class="text-button">忘记密码？</button>
        </div>

        <div class="connection-card">
          <div class="connection-item">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v4" />
              <path d="M6.5 7.5 9 10" />
              <path d="m17.5 7.5-2.5 2.5" />
              <path d="M5 17a7 7 0 0 1 14 0" />
              <path d="M8 17h8" />
            </svg>
            <div>
              <span class="connection-label">后端连接</span>
              <span class="connection-value">
                <span class="status-dot dot-ok"></span>
                正常
              </span>
            </div>
          </div>
          <div class="connection-divider"></div>
          <div class="connection-item">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M10 13a5 5 0 0 0 7.54.54l2.2-2.2a5 5 0 0 0-7.08-7.08l-1.26 1.26" />
              <path d="M14 11a5 5 0 0 0-7.54-.54l-2.2 2.2a5 5 0 0 0 7.08 7.08l1.26-1.26" />
            </svg>
            <div>
              <span class="connection-label">链连接</span>
              <span class="connection-value">
                <span class="status-dot dot-ok"></span>
                已连接
              </span>
            </div>
          </div>
        </div>
      </section>

      <section class="intro-panel" aria-label="平台说明">
        <div class="campus-line" aria-hidden="true"></div>

        <div class="intro-copy">
          <h2>欢迎使用 <strong>EduChain</strong></h2>
          <p>校园学习资料可信交换平台</p>
        </div>

        <div class="feature-list">
          <article v-for="item in features" :key="item.title" class="feature-item">
            <span class="feature-icon" v-html="item.icon"></span>
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.text }}</p>
            </div>
          </article>
        </div>

        <div class="auth-note">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <path d="M7 11V8a5 5 0 0 1 10 0v3" />
          </svg>
          <span>请使用西南交通大学统一身份认证账号登录以保障账户安全。</span>
        </div>
      </section>

      <footer class="login-footer">
        <p>© 2024 西南交通大学 · 信息化与网络管理处</p>
        <p>技术支持：EduChain 团队</p>
      </footer>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import logoUrl from '@/assets/images/swjtu-logo-white.png'
import whiteLogoUrl from '@/assets/images/educhain_white_logo.png'
import mainLogoUrl from '@/assets/images/educhain_main_logo_icon.png'

const router = useRouter()

const form = ref({
  studentId: '',
  password: '',
})
const passwordInput = ref(null)
const showPassword = ref(false)
const loading = ref(false)
const errorMsg = ref('')

const features = [
  {
    title: '链上存证',
    text: '基于区块链技术固化资料存证，确保数据真实、不可篡改、全程可追溯。',
    icon: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>',
  },
  {
    title: '资料共享',
    text: '安全高效的资料交换与共享机制，促进知识流通与学术协作。',
    icon: '<svg viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4"/><path d="m15.4 6.5-6.8 4"/></svg>',
  },
  {
    title: '内容验证',
    text: '多维度校验与可信验证机制，保障资料来源可靠、内容可信。',
    icon: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/></svg>',
  },
]

function focusPassword() {
  passwordInput.value?.focus()
}

function handleLogin() {
  const studentId = form.value.studentId.trim()
  const password = form.value.password.trim()

  if (!studentId || !password) {
    errorMsg.value = '学号和密码不能为空'
    return
  }

  loading.value = true
  window.setTimeout(() => {
    loading.value = false
    if (studentId === '20240001' && password === 'password123') {
      errorMsg.value = ''
      router.push('/market')
      return
    }
    errorMsg.value = '学号或密码错误，请重新输入'
  }, 240)
}
</script>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 78% 18%, rgba(0, 121, 186, 0.11), transparent 34%),
    linear-gradient(120deg, #ffffff 0%, #f8fbff 48%, #eef6ff 100%);
}

.login-canvas {
  position: relative;
  width: 100%;
  min-height: 100vh;
  margin: 0;
  display: grid;
  grid-template-columns: 260px 516px 1fr;
  align-items: center;
  column-gap: 58px;
}

.brand-panel {
  position: relative;
  z-index: 5;
  width: 260px;
  height: 100vh;
  min-height: 720px;
  overflow: hidden;
  background: linear-gradient(180deg, #003a70 0%, #002f60 48%, #00284f 100%);
  box-shadow: 8px 0 28px rgba(0, 39, 82, 0.22);
}

.brand-panel::before,
.brand-panel::after {
  position: absolute;
  content: '';
  border: 1px solid rgba(216, 235, 255, 0.24);
  border-radius: 999px;
  pointer-events: none;
}

.brand-panel::before {
  width: 360px;
  height: 136px;
  left: -126px;
  bottom: 170px;
  transform: rotate(-8deg);
}

.brand-panel::after {
  width: 440px;
  height: 180px;
  left: -180px;
  bottom: 118px;
  transform: rotate(-9deg);
}

.brand-content {
  position: relative;
  z-index: 3;
  padding: 78px 24px 0;
}

.brand-logo {
  display: block;
  width: 216px;
  max-height: 78px;
  object-fit: contain;
  object-position: left center;
}

.brand-subtitle {
  margin: 26px 0 0;
  font-size: 16px;
  line-height: 1.6;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.84);
}

.bridge-line {
  display: none;
}

.brand-watermark {
  position: absolute;
  z-index: 1;
  width: 342px;
  height: 342px;
  right: -142px;
  bottom: 160px;
  object-fit: contain;
  opacity: 0.11;
  pointer-events: none;
  transform: rotate(14deg);
  filter: drop-shadow(0 24px 42px rgba(0, 0, 0, 0.2));
}

.system-status {
  position: absolute;
  left: 32px;
  bottom: 54px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
}

.main-watermark {
  position: absolute;
  z-index: 1;
  width: 420px;
  height: 420px;
  top: -86px;
  right: -112px;
  object-fit: contain;
  opacity: 0.08;
  pointer-events: none;
  transform: rotate(-18deg);
  filter: saturate(1.08);
}

.status-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  flex: 0 0 12px;
  border-radius: 50%;
}

.dot-ok {
  background: #16c35b;
  box-shadow: 0 0 0 4px rgba(22, 195, 91, 0.12);
}

.login-card {
  position: relative;
  z-index: 3;
  width: 508px;
  padding: 42px 38px 36px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(177, 191, 209, 0.58);
  border-radius: 8px;
  box-shadow: 0 18px 42px rgba(20, 44, 80, 0.14);
  backdrop-filter: blur(12px);
}

.card-title {
  margin: 0 0 26px;
  color: #10233f;
  font-size: 28px;
  line-height: 1;
  font-weight: 800;
}

.error-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 48px;
  margin-bottom: 22px;
  padding: 0 18px;
  color: #d14343;
  background: #fff5f5;
  border: 1px solid #f0a7a7;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
}

.error-alert svg {
  width: 20px;
  height: 20px;
  flex: 0 0 20px;
}

.field {
  display: block;
  margin-bottom: 22px;
}

.field-label {
  display: block;
  margin-bottom: 10px;
  color: #10233f;
  font-size: 15px;
  font-weight: 700;
}

.input-shell {
  position: relative;
  display: flex;
  align-items: center;
}

.input-shell > svg {
  position: absolute;
  left: 15px;
  width: 20px;
  height: 20px;
  color: #63728a;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  pointer-events: none;
}

.input-shell input {
  width: 100%;
  height: 48px;
  padding: 0 48px;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #cfd9e7;
  border-radius: 6px;
  outline: none;
  font-size: 15px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.input-shell input::placeholder {
  color: #94a1b4;
}

.input-shell input:focus {
  border-color: #0079ba;
  box-shadow: 0 0 0 3px rgba(0, 121, 186, 0.12);
}

.password-toggle {
  position: absolute;
  right: 14px;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  padding: 0;
  color: #63728a;
  background: transparent;
  border: none;
  cursor: pointer;
}

.password-toggle svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.login-button {
  width: 100%;
  height: 52px;
  margin-top: 8px;
  color: #ffffff;
  background: linear-gradient(180deg, #0079ba 0%, #005f92 100%);
  border: none;
  border-radius: 6px;
  box-shadow: 0 10px 18px rgba(0, 121, 186, 0.24);
  cursor: pointer;
  font-size: 17px;
  font-weight: 800;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.login-button:hover:not(:disabled) {
  background: linear-gradient(180deg, #0087cf 0%, #005986 100%);
  box-shadow: 0 12px 22px rgba(0, 121, 186, 0.3);
  transform: translateY(-1px);
}

.login-button:disabled {
  cursor: not-allowed;
  opacity: 0.68;
}

.assist-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 22px;
  color: #728096;
  font-size: 13px;
  line-height: 1.5;
}

.text-button {
  flex: 0 0 auto;
  padding: 0;
  color: #0079ba;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
}

.connection-card {
  display: grid;
  grid-template-columns: 1fr 1px 1fr;
  align-items: center;
  min-height: 74px;
  margin-top: 34px;
  padding: 0 26px;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
}

.connection-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

.connection-item svg {
  width: 32px;
  height: 32px;
  color: #0079ba;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.connection-item div {
  display: grid;
  gap: 5px;
}

.connection-label {
  color: #7a879b;
  font-size: 13px;
  font-weight: 600;
}

.connection-value {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #10233f;
  font-size: 14px;
  font-weight: 800;
}

.connection-value .status-dot {
  width: 10px;
  height: 10px;
  flex-basis: 10px;
}

.connection-divider {
  width: 1px;
  height: 44px;
  background: #dce4ef;
}

.intro-panel {
  position: relative;
  z-index: 2;
  width: 520px;
  min-height: 520px;
  align-self: center;
  padding-top: 88px;
}

.campus-line {
  display: none;
}

.intro-copy {
  margin-bottom: 42px;
}

.intro-copy h2 {
  margin: 0 0 12px;
  color: #10233f;
  font-size: 24px;
  line-height: 1.2;
  font-weight: 500;
}

.intro-copy strong {
  margin-left: 10px;
  color: #0079ba;
  font-size: 32px;
  font-weight: 900;
}

.intro-copy p {
  margin: 0;
  color: #53647c;
  font-size: 18px;
  font-weight: 500;
}

.feature-list {
  display: grid;
  gap: 38px;
}

.feature-item {
  display: grid;
  grid-template-columns: 58px 1fr;
  gap: 22px;
  align-items: start;
}

.feature-icon {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  color: #0079ba;
  background: linear-gradient(135deg, #edf8fe 0%, #dceeff 100%);
  border: 1px solid #d6e8f8;
  border-radius: 8px;
  box-shadow: 0 10px 18px rgba(0, 121, 186, 0.08);
}

.feature-icon :deep(svg) {
  width: 32px;
  height: 32px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.9;
}

.feature-item h3 {
  margin: 2px 0 10px;
  color: #10233f;
  font-size: 17px;
  line-height: 1.2;
  font-weight: 800;
}

.feature-item p {
  margin: 0;
  color: #53647c;
  font-size: 14px;
  line-height: 1.85;
  font-weight: 500;
}

.auth-note {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 410px;
  min-height: 42px;
  margin-top: 48px;
  padding: 0 18px;
  color: #53647c;
  background: linear-gradient(180deg, #edf7ff 0%, #e3f1fc 100%);
  border: 1px solid #c7dff4;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.auth-note svg {
  width: 20px;
  height: 20px;
  color: #53647c;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.login-footer {
  position: absolute;
  left: 260px;
  right: 0;
  bottom: 64px;
  z-index: 2;
  text-align: center;
  color: #728096;
  font-size: 13px;
  line-height: 1.8;
}

.login-footer p {
  margin: 0;
}

@media (max-height: 920px) {
  .login-card {
    transform: scale(0.94);
    transform-origin: center left;
  }

  .intro-panel {
    transform: scale(0.94);
    transform-origin: center left;
  }

  .login-footer {
    bottom: 26px;
  }
}
</style>
