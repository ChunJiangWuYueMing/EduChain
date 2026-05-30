<template>
  <main class="upload-page">
    <aside class="app-sidebar">
      <div class="sidebar-brand">
        <img :src="logoUrl" alt="西南交通大学 EduChain" />
        <p>校园学习资料可信分发</p>
      </div>

      <nav class="sidebar-nav" aria-label="功能导航">
        <button
          v-for="item in navItems"
          :key="item.label"
          type="button"
          class="nav-item"
          :class="{ active: item.active }"
          :disabled="!item.path"
          @click="item.path && router.push(item.path)"
        >
          <span v-html="item.icon"></span>
          {{ item.label }}
        </button>
      </nav>

      <img class="sidebar-watermark" :src="sidebarArtUrl" alt="" aria-hidden="true" />
      <div class="sidebar-bridge" aria-hidden="true"></div>

      <div class="chain-local">
        <span class="status-dot"></span>
        <span>Ganache Local</span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg>
      </div>
    </aside>

    <header class="app-header">
      <h1>上传资料</h1>
      <div class="header-actions">
        <button class="icon-button" type="button" aria-label="搜索">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
        </button>
        <div class="chain-status">
          <span>链状态</span>
          <span class="status-dot"></span>
          <strong>已连接</strong>
        </div>
        <section class="user-card" aria-label="当前用户">
          <div class="avatar">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="8" r="4" />
              <path d="M4 21a8 8 0 0 1 16 0" />
            </svg>
          </div>
          <div class="user-main">
            <strong>张三</strong>
            <span>学号：20240001</span>
          </div>
          <div class="user-metric">
            <span>EDU 余额</span>
            <strong>120</strong>
          </div>
          <div class="user-address">
            <span>地址</span>
            <strong>0x8f3A...91c2</strong>
            <button type="button" aria-label="复制地址">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <rect x="9" y="9" width="11" height="11" rx="2" />
                <rect x="4" y="4" width="11" height="11" rx="2" />
              </svg>
            </button>
          </div>
          <button class="logout-button" type="button" @click="router.push('/login')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M10 17 15 12l-5-5" />
              <path d="M15 12H3" />
              <path d="M21 19V5a2 2 0 0 0-2-2h-6" />
            </svg>
            登出
          </button>
        </section>
      </div>
    </header>

    <section class="upload-content">
      <div class="upload-main">
        <section class="hero-card">
          <div>
            <h2>上传资料</h2>
            <p>上传文件并完成链上存证</p>
          </div>
        </section>

        <section class="form-card">
          <label
            class="drop-zone"
            :class="{ dragging: isDragging, filled: selectedFile }"
            @dragenter.prevent="isDragging = true"
            @dragover.prevent
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <input ref="fileInput" type="file" :accept="acceptedTypes" hidden @change="handleFileChange" />
            <span class="upload-icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3v12" />
                <path d="m7 8 5-5 5 5" />
                <path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8" />
              </svg>
            </span>
            <strong>{{ selectedFile ? selectedFile.name : '拖拽文件到此处或点击选择文件' }}</strong>
            <p>{{ selectedFile ? formatSize(selectedFile.size) : '支持 pdf、docx、pptx、txt、md，不超过 50MB' }}</p>
            <button type="button" class="select-button" @click.prevent="fileInput?.click()">选择文件</button>
          </label>

          <label class="field">
            <span>课程编号</span>
            <select v-model="form.course">
              <option value="">选择课程或输入课程编号</option>
              <option value="CS201">CS201 计算机网络</option>
              <option value="CS301">CS301 数据结构</option>
              <option value="MATH101">MATH101 高等数学</option>
              <option value="AI202">AI202 人工智能导论</option>
            </select>
          </label>

          <label class="field">
            <span>下载价格（EDU）</span>
            <div class="number-shell">
              <input v-model.number="form.price" type="number" min="0" max="999" />
              <span>EDU</span>
            </div>
          </label>

          <fieldset class="policy-group">
            <legend>访问策略</legend>
            <label>
              <input v-model="form.policy" type="radio" value="public" />
              <span>公开</span>
              <em>任何人可见并下载</em>
            </label>
            <label>
              <input v-model="form.policy" type="radio" value="same-course" />
              <span>同课程</span>
              <em>仅本课程学生可见</em>
            </label>
            <label class="disabled">
              <input type="radio" disabled />
              <span>白名单（预留）</span>
              <em>暂不可用</em>
            </label>
          </fieldset>

          <button type="button" class="submit-button" :disabled="!canSubmit || loading" @click="handleUpload">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v12" />
              <path d="m7 8 5-5 5 5" />
              <path d="M5 15v4h14v-4" />
            </svg>
            {{ loading ? '上传并存证中...' : '上传并存证' }}
          </button>
        </section>

        <section class="progress-card">
          <h2>上传进度</h2>
          <div class="steps">
            <div v-for="step in steps" :key="step.title" class="step" :class="{ active: step.index === currentStep, done: step.index < currentStep }">
              <span>{{ step.index }}</span>
              <strong>{{ step.title }}</strong>
              <p>{{ step.desc }}</p>
            </div>
          </div>
        </section>
      </div>

      <aside class="result-panel">
        <section class="result-card">
          <h2>上传结果</h2>

          <div v-if="result" class="success-banner">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m8 12 3 3 5-6" />
              <circle cx="12" cy="12" r="9" />
            </svg>
            <div>
              <strong>上传成功，已完成链上存证</strong>
              <p>文件已安全存证至区块链</p>
            </div>
          </div>

          <div v-else class="pending-banner">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v12" />
              <path d="m7 8 5-5 5 5" />
              <path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8" />
            </svg>
            <div>
              <strong>等待上传</strong>
              <p>选择文件并提交后，将展示链上存证结果</p>
            </div>
          </div>

          <dl class="result-list">
            <div v-for="row in resultRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd>
                {{ row.value }}
                <button v-if="row.copy" type="button" aria-label="复制">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="9" y="9" width="11" height="11" rx="2" />
                    <rect x="4" y="4" width="11" height="11" rx="2" />
                  </svg>
                </button>
              </dd>
            </div>
          </dl>
        </section>

        <section class="similar-card">
          <h2>相似资料 <span>（基于 SimHash）</span></h2>
          <table v-if="result">
            <thead>
              <tr>
                <th>资料 ID</th>
                <th>资料名称</th>
                <th>课程</th>
                <th>相似度 / 汉明距离</th>
                <th>分类</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in similarMaterials" :key="item.id">
                <td>{{ item.id }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.course }}</td>
                <td>{{ item.score }} / {{ item.distance }}</td>
                <td><span class="similar-tag" :class="item.type">{{ item.label }}</span></td>
              </tr>
            </tbody>
          </table>
          <div v-else class="similar-empty">上传完成后会自动比对相似资料。</div>
        </section>

        <section class="notice-card">
          <div>
            <strong>上传须知</strong>
            <p>请确保您拥有资料的合法版权或授权，上传的资料需遵守学校相关规定与法律法规。</p>
          </div>
          <button type="button">查看上传规则</button>
        </section>

        <div class="panel-actions">
          <button type="button" class="secondary-action" @click="router.push('/market')">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>
            返回市场
          </button>
          <button type="button" class="primary-action" :disabled="!result" @click="resetForm">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12" /><path d="m7 8 5-5 5 5" /><path d="M5 15v4h14v-4" /></svg>
            {{ result ? '继续上传' : '等待上传' }}
          </button>
        </div>
      </aside>
    </section>

    <div v-if="toast" class="toast" role="status">{{ toast }}</div>
  </main>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import logoUrl from '@/assets/images/swjtu-logo-white.png'
import sidebarArtUrl from '@/assets/images/educhain_white_logo.png'

const router = useRouter()
const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const loading = ref(false)
const result = ref(null)
const toast = ref('')
const acceptedTypes = '.pdf,.docx,.pptx,.txt,.md'

const form = reactive({
  course: '',
  price: 12,
  policy: 'public',
})

const navItems = [
  { label: '资料市场', active: false, path: '/market', icon: '<svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h5"/><path d="M10 13h6"/><path d="M10 17h6"/></svg>' },
  { label: '上传资料', active: true, path: '/upload', icon: '<svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/><path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8"/></svg>' },
  { label: '文件验证', active: false, path: '/verify', icon: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>' },
  { label: '我的钱包', active: false, path: '/wallet', icon: '<svg viewBox="0 0 24 24"><path d="M4 7h15a2 2 0 0 1 2 2v10H4a2 2 0 0 1-2-2V5a2 2 0 0 0 2 2Z"/><path d="M16 13h4"/></svg>' },
  { label: '审计追溯', active: false, path: '/audit', icon: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><circle cx="11" cy="15" r="2"/><path d="m13 17 3 3"/></svg>' },
  { label: '系统状态', active: false, path: '/status', icon: '<svg viewBox="0 0 24 24"><path d="M3 4h18v14H3z"/><path d="M8 22h8"/><path d="M12 18v4"/><path d="m7 13 3-3 2 2 4-5"/></svg>' },
]

const steps = [
  { index: 1, title: '文件指纹计算中', desc: '计算文件哈希与指纹' },
  { index: 2, title: '链上登记中', desc: '将元数据写入区块链' },
  { index: 3, title: '上传奖励确认中', desc: '确认并发放上传奖励' },
]

const similarMaterials = [
  { id: 'MAT_20260521_003', name: '机器学习实验指导书_v1.pdf', course: 'CS201', score: '0.00', distance: '0', type: 'same', label: '完全相同' },
  { id: 'MAT_20260418_011', name: '机器学习实验指导书_旧版.pdf', course: 'CS201', score: '0.93', distance: '6', type: 'high', label: '高度相似' },
  { id: 'MAT_20260402_006', name: '机器学习实验报告示例.pdf', course: 'CS201', score: '0.78', distance: '14', type: 'derived', label: '衍生资料' },
  { id: 'MAT_20260330_002', name: '深度学习实验指导书.pdf', course: 'CS302', score: '0.42', distance: '25', type: 'low', label: '差异较大' },
]

const canSubmit = computed(() => selectedFile.value && form.course && form.price >= 0)
const currentStep = computed(() => {
  if (result.value) return 4
  if (loading.value) return 2
  if (selectedFile.value) return 1
  return 0
})
const resultRows = computed(() => {
  const data = result.value
  return [
    { label: '资料 ID', value: data?.id || '--', copy: !!data },
    { label: '资料名称', value: data?.name || '--', copy: !!data },
    { label: 'SHA-256', value: data?.sha || '--', copy: !!data },
    { label: 'SimHash', value: data?.simhash || '--', copy: !!data },
    { label: '文本长度', value: data?.length || '--', copy: !!data },
    { label: '价格', value: `${form.price || 0} EDU` },
    { label: '上传奖励', value: data ? '+20 EDU' : '--' },
    { label: '交易哈希', value: data?.tx || '--', copy: !!data },
    { label: '上传时间', value: data?.time || '--', copy: !!data },
    { label: '状态', value: data ? '已存证' : '未上传' },
  ]
})

function validateFile(file) {
  if (!file) return false
  const ext = `.${file.name.split('.').pop()?.toLowerCase()}`
  if (!acceptedTypes.split(',').includes(ext)) {
    showToast('仅支持 pdf、docx、pptx、txt、md 文件')
    return false
  }
  if (file.size > 50 * 1024 * 1024) {
    showToast('文件大小不能超过 50MB')
    return false
  }
  return true
}

function setFile(file) {
  if (!validateFile(file)) return
  selectedFile.value = file
  result.value = null
}

function handleFileChange(event) {
  setFile(event.target.files?.[0])
}

function handleDrop(event) {
  isDragging.value = false
  setFile(event.dataTransfer.files?.[0])
}

function handleUpload() {
  if (!canSubmit.value) {
    showToast('请先选择文件并填写课程编号')
    return
  }

  loading.value = true
  window.setTimeout(() => {
    loading.value = false
    result.value = {
      id: 'MAT_20260521_008',
      name: selectedFile.value.name,
      sha: 'a1d9...f220',
      simhash: '0x73bd...1a09',
      length: '18640',
      tx: '0x73bc...0a91',
      time: '2026-05-21 15:08:42',
    }
    showToast('上传成功，资料已完成链上存证')
  }, 680)
}

function resetForm() {
  selectedFile.value = null
  result.value = null
  form.course = ''
  form.price = 12
  form.policy = 'public'
  if (fileInput.value) fileInput.value.value = ''
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function showToast(message) {
  toast.value = message
  window.clearTimeout(showToast.timer)
  showToast.timer = window.setTimeout(() => {
    toast.value = ''
  }, 1800)
}
</script>

<style scoped>
.upload-page {
  min-width: 1200px;
  min-height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  color: var(--text-primary);
  background: #f4f7fa;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

button,
input,
select {
  font: inherit;
}

button {
  cursor: pointer;
}

.app-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  width: 248px;
  overflow: hidden;
  background: linear-gradient(180deg, #003a70 0%, #002f60 48%, #00284f 100%);
  box-shadow: 8px 0 28px rgba(0, 39, 82, 0.2);
}

.sidebar-brand {
  padding: 34px 20px 26px;
}

.sidebar-brand img {
  width: 210px;
  height: 78px;
  object-fit: contain;
  object-position: left center;
}

.sidebar-brand p {
  margin: 14px 0 0;
  color: rgba(255, 255, 255, 0.86);
  font-size: 16px;
  font-weight: 600;
}

.sidebar-nav {
  position: relative;
  z-index: 2;
  display: grid;
  gap: 10px;
  padding: 0 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 15px;
  height: 60px;
  padding: 0 22px;
  color: rgba(255, 255, 255, 0.88);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 700;
  text-align: left;
}

.nav-item:disabled {
  cursor: default;
}

.nav-item.active {
  color: #ffffff;
  background: linear-gradient(135deg, #0079ba 0%, #005f92 100%);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 24px rgba(0, 36, 90, 0.22);
}

.nav-item span,
.nav-item :deep(svg) {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
}

.nav-item :deep(svg) {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.sidebar-bridge {
  position: absolute;
  left: -52px;
  right: 0;
  bottom: 96px;
  height: 210px;
  opacity: 0.2;
  border-top: 1px solid rgba(209, 232, 255, 0.35);
  border-bottom: 1px solid rgba(209, 232, 255, 0.25);
  border-radius: 50%;
  transform: rotate(-8deg);
}

.sidebar-watermark {
  position: absolute;
  z-index: 1;
  width: 340px;
  height: 340px;
  right: -118px;
  bottom: 148px;
  object-fit: contain;
  opacity: 0.1;
  pointer-events: none;
  transform: rotate(-10deg);
  filter: drop-shadow(0 22px 42px rgba(0, 0, 0, 0.16));
}

.sidebar-bridge::before,
.sidebar-bridge::after {
  position: absolute;
  left: -80px;
  width: 380px;
  height: 120px;
  content: '';
  border-top: 1px solid rgba(209, 232, 255, 0.28);
  border-radius: 50%;
}

.sidebar-bridge::before { top: 40px; }
.sidebar-bridge::after { top: 84px; }

.chain-local {
  position: absolute;
  left: 30px;
  right: 26px;
  bottom: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #ffffff;
  font-size: 16px;
}

.chain-local svg {
  width: 18px;
  height: 18px;
  margin-left: auto;
}

.status-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #16a34a;
  box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.12);
}

.app-header {
  position: fixed;
  top: 0;
  left: 248px;
  right: 0;
  z-index: 15;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72px;
  padding: 0 14px 0 30px;
  background: rgba(255, 255, 255, 0.94);
  border-bottom: 1px solid #dce4ef;
  backdrop-filter: blur(14px);
}

.app-header h1 {
  margin: 0;
  color: #10233f;
  font-size: 30px;
  font-weight: 800;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-button {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
}

.icon-button svg {
  width: 22px;
  height: 22px;
}

.chain-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-left: 16px;
  border-left: 1px solid #dce4ef;
  color: #53647c;
  font-size: 14px;
}

.chain-status strong {
  color: #10233f;
}

.user-card {
  display: grid;
  grid-template-columns: 48px 126px 100px 170px 82px;
  align-items: center;
  min-height: 58px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
}

.avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  margin-left: 12px;
  color: #2f6fbc;
  background: #e8f2ff;
  border-radius: 50%;
}

.avatar svg {
  width: 25px;
  height: 25px;
  fill: currentColor;
  stroke: none;
}

.user-main,
.user-metric,
.user-address {
  display: grid;
  gap: 4px;
  height: 58px;
  align-content: center;
  padding: 0 14px;
  border-left: 1px solid #e5e7eb;
}

.user-main {
  border-left: none;
}

.user-main strong,
.user-address strong {
  color: #10233f;
  font-size: 15px;
}

.user-main span,
.user-metric span,
.user-address span {
  color: #53647c;
  font-size: 12px;
}

.user-metric strong {
  color: #0079ba;
  font-size: 17px;
}

.user-address {
  grid-template-columns: 1fr auto;
}

.user-address span,
.user-address strong {
  grid-column: 1;
}

.user-address button {
  grid-column: 2;
  grid-row: 1 / span 2;
  color: #53647c;
  background: transparent;
  border: none;
}

.user-address svg {
  width: 18px;
  height: 18px;
}

.logout-button {
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #10233f;
  background: #ffffff;
  border: none;
  border-left: 1px solid #e5e7eb;
  font-size: 14px;
}

.logout-button svg {
  width: 18px;
  height: 18px;
}

.upload-content {
  min-height: 100vh;
  padding: 88px 16px 28px 264px;
  display: grid;
  grid-template-columns: minmax(590px, 1fr) 520px;
  gap: 16px;
  align-items: start;
}

.upload-main {
  min-width: 0;
  display: grid;
  grid-template-rows: auto auto auto;
  align-content: start;
  gap: 12px;
}

.hero-card,
.form-card,
.progress-card,
.result-card,
.similar-card,
.notice-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.hero-card {
  min-height: 122px;
  display: flex;
  align-items: center;
  padding: 0 28px;
  position: relative;
  overflow: hidden;
}

.hero-card::before {
  position: absolute;
  inset: 20px 20px auto auto;
  width: 340px;
  height: 86px;
  content: '';
  border-top: 1px solid rgba(0, 121, 186, 0.13);
  border-bottom: 1px solid rgba(0, 121, 186, 0.08);
  border-radius: 50%;
  transform: rotate(-8deg);
}

.hero-card h2 {
  margin: 0 0 12px;
  color: #10233f;
  font-size: 28px;
  font-weight: 800;
}

.hero-card p {
  margin: 0;
  color: #53647c;
  font-size: 15px;
}

.form-card {
  padding: 20px;
}

.drop-zone {
  min-height: 224px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 12px;
  color: #10233f;
  background: #f7fbff;
  border: 2px dashed #9fc7f1;
  border-radius: 8px;
  text-align: center;
  transition: 0.2s;
}

.drop-zone.dragging,
.drop-zone:hover {
  border-color: #0079ba;
  box-shadow: 0 0 0 4px rgba(0, 121, 186, 0.1);
}

.drop-zone.filled {
  background: #eef8ff;
}

.upload-icon {
  width: 70px;
  height: 70px;
  display: grid;
  place-items: center;
  color: #0079ba;
  background: #ffffff;
  border-radius: 50%;
  box-shadow: 0 14px 34px rgba(0, 121, 186, 0.14);
}

.upload-icon svg {
  width: 42px;
  height: 42px;
}

.drop-zone strong {
  color: #003a70;
  font-size: 18px;
}

.drop-zone p {
  margin: 0;
  color: #53647c;
  font-size: 14px;
}

.select-button {
  height: 40px;
  padding: 0 28px;
  color: #0079ba;
  background: #ffffff;
  border: 1px solid #0079ba;
  border-radius: 6px;
  font-weight: 700;
}

.field {
  display: grid;
  gap: 9px;
  margin-top: 18px;
}

.field span,
.policy-group legend {
  color: #10233f;
  font-size: 14px;
  font-weight: 800;
}

.field select,
.number-shell {
  width: 100%;
  height: 42px;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 7px;
  outline: none;
}

.field select {
  padding: 0 14px;
}

.number-shell {
  display: grid;
  grid-template-columns: 1fr 70px;
  align-items: center;
}

.number-shell input {
  min-width: 0;
  height: 40px;
  padding: 0 12px;
  color: #10233f;
  border: none;
  outline: none;
}

.number-shell span {
  display: grid;
  place-items: center;
  height: 40px;
  color: #53647c;
  border-left: 1px solid #dce4ef;
}

.policy-group {
  display: grid;
  gap: 12px;
  margin: 18px 0 0;
  padding: 0;
  border: none;
}

.policy-group label {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 28px;
}

.policy-group input {
  width: 18px;
  height: 18px;
  accent-color: #0079ba;
}

.policy-group span {
  min-width: 66px;
  color: #10233f;
  font-weight: 700;
}

.policy-group em {
  padding: 3px 10px;
  color: #15803d;
  background: #dcfce7;
  border-radius: 999px;
  font-size: 12px;
  font-style: normal;
}

.policy-group label:nth-of-type(2) em {
  color: #b45309;
  background: #fef3c7;
}

.policy-group .disabled {
  color: #9ca3af;
}

.policy-group .disabled span {
  color: #9ca3af;
}

.policy-group .disabled em {
  color: #6b7280;
  background: #e5e7eb;
}

.submit-button {
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  margin-top: 20px;
  color: #ffffff;
  background: linear-gradient(180deg, #0079ba 0%, #005f92 100%);
  border: 1px solid #00649a;
  border-radius: 6px;
  box-shadow: 0 8px 18px rgba(0, 121, 186, 0.22);
  font-size: 16px;
  font-weight: 800;
}

.submit-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.submit-button svg {
  width: 20px;
  height: 20px;
}

.progress-card {
  padding: 18px 26px 22px;
}

.progress-card h2,
.result-card h2,
.similar-card h2 {
  margin: 0 0 18px;
  color: #10233f;
  font-size: 18px;
  font-weight: 800;
}

.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  text-align: center;
}

.step {
  position: relative;
  display: grid;
  gap: 8px;
  color: #8a97aa;
}

.step:not(:last-child)::after {
  position: absolute;
  left: calc(50% + 28px);
  top: 16px;
  width: calc(100% - 56px);
  height: 1px;
  content: '';
  background: #dce4ef;
}

.step span {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  justify-self: center;
  color: #53647c;
  background: #e5e7eb;
  border-radius: 50%;
  font-weight: 800;
}

.step.active span,
.step.done span {
  color: #ffffff;
  background: #0079ba;
  box-shadow: 0 8px 18px rgba(0, 121, 186, 0.18);
}

.step strong {
  color: #53647c;
  font-size: 14px;
}

.step.active strong,
.step.done strong {
  color: #0079ba;
}

.step p {
  margin: 0;
  font-size: 12px;
}

.result-panel {
  min-width: 0;
  position: sticky;
  top: 88px;
  height: calc(100vh - 104px);
  overflow: auto;
  display: grid;
  align-content: start;
  gap: 12px;
}

.result-card,
.similar-card {
  padding: 18px;
}

.success-banner,
.pending-banner {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 12px;
  align-items: center;
  min-height: 74px;
  padding: 0 16px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.success-banner {
  color: #15803d;
  background: #ecfdf5;
  border: 1px solid #bbf7d0;
}

.pending-banner {
  color: #0079ba;
  background: #e6f4fa;
  border: 1px solid #bfdbfe;
}

.success-banner svg,
.pending-banner svg {
  width: 32px;
  height: 32px;
}

.success-banner p,
.pending-banner p {
  margin: 6px 0 0;
  color: #53647c;
  font-size: 13px;
}

.result-list {
  margin: 0;
}

.result-list div {
  display: grid;
  grid-template-columns: 120px 1fr;
  align-items: center;
  min-height: 36px;
  border-bottom: 1px solid #e5e7eb;
}

.result-list dt {
  color: #53647c;
  font-size: 14px;
}

.result-list dd {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  color: #10233f;
  font-size: 14px;
  text-align: right;
}

.result-list button {
  width: 24px;
  height: 24px;
  color: #53647c;
  background: transparent;
  border: none;
}

.result-list svg {
  width: 17px;
  height: 17px;
}

.similar-card h2 span {
  color: #53647c;
  font-weight: 500;
}

.similar-card table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.similar-card th,
.similar-card td {
  height: 34px;
  padding: 0 9px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.similar-card th {
  color: #53647c;
  background: #f9fafb;
  font-weight: 800;
}

.similar-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 999px;
  font-weight: 800;
}

.similar-tag.same {
  color: #15803d;
  background: #dcfce7;
}

.similar-tag.high {
  color: #b45309;
  background: #fef3c7;
}

.similar-tag.derived {
  color: #0079ba;
  background: #e6f4fa;
}

.similar-tag.low {
  color: #6b7280;
  background: #e5e7eb;
}

.similar-empty {
  display: grid;
  place-items: center;
  min-height: 96px;
  color: #53647c;
  background: #f9fafb;
  border-radius: 8px;
}

.notice-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 54px;
  padding: 0 14px;
  color: #9a5c00;
  background: #fff7ed;
  border-color: #fdba74;
}

.notice-card strong {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
}

.notice-card p {
  margin: 0;
  color: #53647c;
  font-size: 12px;
}

.notice-card button {
  flex: 0 0 auto;
  color: #0079ba;
  background: transparent;
  border: none;
  font-weight: 800;
}

.panel-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.primary-action,
.secondary-action {
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 800;
}

.primary-action {
  color: #ffffff;
  background: linear-gradient(180deg, #0079ba 0%, #005f92 100%);
  border: 1px solid #00649a;
}

.primary-action:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.secondary-action {
  color: #0079ba;
  background: #ffffff;
  border: 1px solid #0079ba;
}

.primary-action svg,
.secondary-action svg {
  width: 19px;
  height: 19px;
}

.toast {
  position: fixed;
  left: 50%;
  bottom: 28px;
  z-index: 50;
  transform: translateX(-50%);
  padding: 10px 18px;
  color: #ffffff;
  background: rgba(16, 35, 63, 0.92);
  border-radius: 999px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
  font-size: 14px;
}
</style>
