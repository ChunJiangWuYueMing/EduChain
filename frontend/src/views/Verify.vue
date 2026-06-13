<template>
  <main class="verify-page">
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
      <h1>文件验证</h1>
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
            <strong>{{ auth.user?.name || '--' }}</strong>
            <span>学号：{{ auth.user?.student_id || '--' }}</span>
          </div>
          <div class="user-metric">
            <span>EDU 余额</span>
            <strong>{{ auth.user?.edu_balance ?? '--' }}</strong>
          </div>
          <div class="user-address">
            <span>地址</span>
            <strong>{{ truncate(auth.user?.eth_address) }}</strong>
            <button type="button" aria-label="复制地址">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <rect x="9" y="9" width="11" height="11" rx="2" />
                <rect x="4" y="4" width="11" height="11" rx="2" />
              </svg>
            </button>
          </div>
          <button class="logout-button" type="button" @click="handleLogout">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M10 17 15 12l-5-5" />
              <path d="M15 12H3" />
              <path d="M21 19V5a2 2 0 0 0-2-2h-6" />
            </svg>
            退出
          </button>
        </section>
      </div>
    </header>

    <section class="verify-content">
      <section class="material-bar">
        <label>
          <span>资料 ID</span>
          <input v-model.trim="materialId" type="text" placeholder="请输入链上资料 ID" />
          <button type="button" aria-label="复制资料 ID">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="9" y="9" width="11" height="11" rx="2" />
              <rect x="4" y="4" width="11" height="11" rx="2" />
            </svg>
          </button>
        </label>
        <button type="button" class="load-button" @click="materialId = 'MAT_20260521_001'">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M21 12a9 9 0 1 1-2.64-6.36" />
            <path d="M21 4v6h-6" />
          </svg>
          从资料详情带入
        </button>
      </section>

      <div class="verify-grid">
        <section class="file-card">
          <h2>选择待验证文件</h2>

          <label
            class="drop-zone"
            :class="{ dragging: isDragging, filled: selectedFile }"
            @dragenter.prevent="isDragging = true"
            @dragover.prevent
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <input ref="fileInput" type="file" :accept="acceptedTypes" hidden @change="handleFileChange" />
            <span class="shield-art">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
                <path d="m8.5 12 2.2 2.2 4.8-5" />
              </svg>
            </span>
            <strong>{{ selectedFile ? selectedFile.name : '点击或拖拽文件到此处上传' }}</strong>
            <p>{{ selectedFile ? formatSize(selectedFile.size) : '支持 PDF、DOCX、PPTX、TXT 等常见格式，单文件 ≤ 100MB' }}</p>
          </label>

          <div v-if="selectedFile" class="file-chip">
            <span class="file-icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
                <path d="M14 2v6h6" />
                <path d="M8 13h8" />
                <path d="M8 17h6" />
              </svg>
            </span>
            <div>
              <strong>{{ selectedFile.name }}</strong>
              <span>{{ fileExt }} · {{ formatSize(selectedFile.size) }}</span>
            </div>
            <button type="button" aria-label="移除文件" @click="clearFile">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          </div>

          <button type="button" class="verify-button" :disabled="!canVerify || loading" @click="handleVerify">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m8 5 11 7-11 7V5Z" />
            </svg>
            {{ loading ? '验证中...' : '开始验证' }}
          </button>

          <div class="hint-box">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8h.01" />
              <path d="M11 12h1v4h1" />
            </svg>
            验证将对文件进行哈希与相似度比对，确保与链上记录一致。
          </div>
        </section>

        <section class="report-card">
          <h2>验证报告</h2>

          <div v-if="report" class="danger-banner">
            <span>
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
                <path d="M12 8v5" />
                <path d="M12 17h.01" />
              </svg>
            </span>
            <div>
              <strong>{{ report.is_tampered ? '检测到文件差异' : '文件完整可信' }}</strong>
              <p>{{ report.is_tampered ? '该文件与链上记录存在差异，建议人工复核。' : 'SHA-256 与链上记录一致。' }}</p>
            </div>
            <time>验证时间：2026-05-21 14:32:18</time>
          </div>

          <div v-else class="waiting-banner">
            <span>
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
                <path d="m8.5 12 2.2 2.2 4.8-5" />
              </svg>
            </span>
            <div>
              <strong>等待验证</strong>
              <p>选择本地文件并开始验证后，将生成链上比对报告。</p>
            </div>
          </div>

          <dl class="report-list">
            <div v-for="row in reportRows" :key="row.label">
              <dt>{{ row.label }}</dt>
              <dd>
                <template v-if="row.kind === 'match'">
                  <span class="fail-dot">×</span>
                  否
                </template>
                <template v-else-if="row.kind === 'similarity'">
                  <span class="similarity-bar"><i :style="{ width: row.value }"></i></span>
                  {{ row.value }}
                </template>
                <template v-else-if="row.kind === 'tag'">
                  <span class="risk-tag">{{ row.value }}</span>
                </template>
                <template v-else-if="row.kind === 'tampered'">
                  <span class="tampered">是</span>
                  <span class="fail-dot">!</span>
                </template>
                <template v-else>
                  {{ row.value }}
                  <button v-if="row.copy" type="button" aria-label="复制">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <rect x="9" y="9" width="11" height="11" rx="2" />
                      <rect x="4" y="4" width="11" height="11" rx="2" />
                    </svg>
                  </button>
                </template>
              </dd>
            </div>
          </dl>

          <section v-if="report" class="keyword-card">
            <h3>差异关键词 <span>（基于文本对比）</span></h3>
            <div class="keyword-grid">
              <div class="keyword-box added">
                <header>
                  <strong>新增关键词（本地独有）</strong>
                  <span>{{ report.added_keywords?.length || 0 }} 个</span>
                </header>
                <p>
                  <span v-for="keyword in report.added_keywords || []" :key="keyword">{{ keyword }}</span>
                  <span v-if="!report.added_keywords?.length">无</span>
                </p>
              </div>
              <div class="keyword-box missing">
                <header>
                  <strong>缺失关键词（链上存在）</strong>
                  <span>{{ report.removed_keywords?.length || 0 }} 个</span>
                </header>
                <p>
                  <span v-for="keyword in report.removed_keywords || []" :key="keyword">{{ keyword }}</span>
                  <span v-if="!report.removed_keywords?.length">无</span>
                </p>
              </div>
            </div>
          </section>
        </section>
      </div>

      <div class="bottom-tip">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8h.01" />
          <path d="M11 12h1v4h1" />
        </svg>
        提示：相似度 ≥ 95% 且 SHA-256 不匹配时，判定为疑似篡改，建议人工检验文件差异后再确认结果。
      </div>
    </section>

    <div v-if="toast" class="toast" role="status">{{ toast }}</div>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { truncate } from '@/utils/api'
import { useAuthStore } from '@/stores/auth'
import logoUrl from '@/assets/images/swjtu-logo-white.png'
import sidebarArtUrl from '@/assets/images/educhain_white_logo.png'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const loading = ref(false)
const materialId = ref(String(route.query.materialId || ''))
const report = ref(null)
const toast = ref('')
const acceptedTypes = '.pdf,.docx,.pptx,.txt,.md'

const navItems = [
  { label: '资料市场', active: false, path: '/market', icon: '<svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h5"/><path d="M10 13h6"/><path d="M10 17h6"/></svg>' },
  { label: '上传资料', active: false, path: '/upload', icon: '<svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/><path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8"/></svg>' },
  { label: '文件验证', active: true, path: '/verify', icon: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>' },
  { label: '我的钱包', active: false, path: '/wallet', icon: '<svg viewBox="0 0 24 24"><path d="M4 7h15a2 2 0 0 1 2 2v10H4a2 2 0 0 1 2 2Z"/><path d="M16 13h4"/></svg>' },
  { label: '审计追溯', active: false, path: '/audit', icon: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><circle cx="11" cy="15" r="2"/><path d="m13 17 3 3"/></svg>' },
  { label: '系统状态', active: false, path: '/status', icon: '<svg viewBox="0 0 24 24"><path d="M3 4h18v14H3z"/><path d="M8 22h8"/><path d="M12 18v4"/><path d="m7 13 3-3 2 2 4-5"/></svg>' },
]

const canVerify = computed(() => selectedFile.value && materialId.value)
const fileExt = computed(() => selectedFile.value?.name.split('.').pop()?.toUpperCase() || 'FILE')
const reportRows = computed(() => {
  if (!report.value) {
    return [
      { label: 'SHA-256 是否匹配', value: '--' },
      { label: '本地 SHA-256', value: '--' },
      { label: '链上 SHA-256', value: '--' },
      { label: '本地 SimHash', value: '--' },
      { label: '链上 SimHash', value: '--' },
      { label: '汉明距离', value: '--' },
      { label: '相似度', value: '--' },
      { label: '分类', value: '--' },
      { label: '是否被篡改', value: '--' },
    ]
  }

  const data = report.value
  return [
    { label: 'SHA-256 是否匹配', value: data.sha256_match ? '是' : '否' },
    { label: '本地 SHA-256', value: data.sha256_local, copy: true },
    { label: '链上 SHA-256', value: data.sha256_chain, copy: true },
    { label: '本地 SimHash', value: data.sim_hash_local, copy: true },
    { label: '链上 SimHash', value: data.sim_hash_chain, copy: true },
    { label: '汉明距离', value: data.hamming_dist },
    { label: '相似度', value: `${data.similarity_pct}%`, kind: 'similarity' },
    { label: '分类', value: data.classification, kind: 'tag' },
    { label: '是否被篡改', value: data.is_tampered ? '是' : '否' },
  ]
})

function validateFile(file) {
  if (!file) return false
  const ext = `.${file.name.split('.').pop()?.toLowerCase()}`
  if (!acceptedTypes.split(',').includes(ext)) {
    showToast('仅支持 pdf、docx、pptx、txt、md 文件')
    return false
  }
  if (file.size > 100 * 1024 * 1024) {
    showToast('文件大小不能超过 100MB')
    return false
  }
  return true
}

function setFile(file) {
  if (!validateFile(file)) return
  selectedFile.value = file
  report.value = null
}

function handleFileChange(event) {
  setFile(event.target.files?.[0])
}

function handleDrop(event) {
  isDragging.value = false
  setFile(event.dataTransfer.files?.[0])
}

function clearFile() {
  selectedFile.value = null
  report.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function handleVerify() {
  if (!canVerify.value) {
    showToast('请填写资料 ID 并选择待验证文件')
    return
  }
  loading.value = true
  try {
    const data = new FormData()
    data.append('file', selectedFile.value)
    data.append('material_id', materialId.value)
    const res = await api.postForm('/api/material/verify', data)
    report.value = res.data
    showToast(res.data.is_tampered ? '验证完成：检测到文件差异' : '验证完成：文件与链上记录一致')
  } catch (error) {
    showToast(error.message || '验证失败')
  } finally {
    loading.value = false
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function showToast(message) {
  toast.value = message
  window.clearTimeout(showToast.timer)
  showToast.timer = window.setTimeout(() => {
    toast.value = ''
  }, 1800)
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.verify-page {
  min-width: 1200px;
  min-height: 100vh;
  overflow-x: hidden;
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
input {
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

.verify-content {
  min-height: 100vh;
  padding: 96px 16px 18px 264px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 16px;
}

.material-bar,
.file-card,
.report-card,
.bottom-tip {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.material-bar {
  min-height: 76px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 22px;
}

.material-bar label {
  display: grid;
  grid-template-columns: 70px 320px 36px;
  align-items: center;
  gap: 12px;
}

.material-bar label span {
  color: #10233f;
  font-weight: 800;
}

.material-bar input {
  height: 42px;
  padding: 0 14px;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 7px;
  outline: none;
}

.material-bar label button,
.load-button {
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #0079ba;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 7px;
  font-weight: 800;
}

.material-bar label button {
  width: 36px;
}

.material-bar svg {
  width: 18px;
  height: 18px;
}

.load-button {
  padding: 0 18px;
}

.verify-grid {
  display: grid;
  grid-template-columns: 420px minmax(620px, 1fr);
  gap: 16px;
  min-height: 0;
}

.file-card,
.report-card {
  padding: 18px;
}

.file-card h2,
.report-card h2 {
  margin: 0 0 18px;
  color: #10233f;
  font-size: 20px;
  font-weight: 800;
}

.drop-zone {
  min-height: 276px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 12px;
  color: #10233f;
  background: #ffffff;
  border: 2px dashed #c4d4e8;
  border-radius: 8px;
  text-align: center;
  transition: 0.2s;
}

.drop-zone.dragging,
.drop-zone:hover {
  border-color: #0079ba;
  box-shadow: 0 0 0 4px rgba(0, 121, 186, 0.08);
}

.shield-art {
  width: 118px;
  height: 118px;
  display: grid;
  place-items: center;
  color: #6fa8ff;
  background: radial-gradient(circle, #eaf4ff 0%, #f7fbff 60%, transparent 62%);
}

.shield-art svg {
  width: 92px;
  height: 92px;
  fill: rgba(111, 168, 255, 0.26);
  stroke-width: 1.5;
}

.drop-zone strong {
  font-size: 16px;
}

.drop-zone p {
  margin: 0;
  color: #53647c;
  font-size: 13px;
}

.file-chip {
  min-height: 66px;
  display: grid;
  grid-template-columns: 44px 1fr 30px;
  align-items: center;
  gap: 14px;
  margin-top: 28px;
  padding: 0 14px;
  background: #f9fafb;
  border: 1px solid #dce4ef;
  border-radius: 8px;
}

.file-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  color: #ffffff;
  background: #0079ba;
  border-radius: 6px;
}

.file-icon svg {
  width: 24px;
  height: 24px;
}

.file-chip strong {
  display: block;
  color: #10233f;
  font-size: 14px;
}

.file-chip span {
  color: #53647c;
  font-size: 13px;
}

.file-chip button {
  color: #10233f;
  background: transparent;
  border: none;
}

.file-chip button svg {
  width: 18px;
  height: 18px;
}

.verify-button {
  width: 100%;
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  margin-top: 28px;
  color: #ffffff;
  background: linear-gradient(180deg, #0079ba 0%, #005f92 100%);
  border: 1px solid #00649a;
  border-radius: 6px;
  box-shadow: 0 8px 18px rgba(0, 121, 186, 0.22);
  font-size: 16px;
  font-weight: 800;
}

.verify-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.verify-button svg {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.hint-box {
  min-height: 50px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 32px;
  padding: 0 14px;
  color: #53647c;
  background: #edf7ff;
  border: 1px solid #c7dff4;
  border-radius: 8px;
  font-size: 13px;
}

.hint-box svg {
  width: 18px;
  height: 18px;
  color: #0079ba;
  fill: #0079ba;
}

.danger-banner,
.waiting-banner {
  display: grid;
  grid-template-columns: 92px 1fr auto;
  gap: 16px;
  align-items: center;
  min-height: 108px;
  margin-bottom: 12px;
  padding: 0 24px;
  border-radius: 8px;
}

.danger-banner {
  color: #dc2626;
  background: #fff7f7;
  border: 1px solid #f3b7b7;
}

.waiting-banner {
  grid-template-columns: 70px 1fr;
  color: #0079ba;
  background: #e6f4fa;
  border: 1px solid #bfdbfe;
}

.danger-banner > span,
.waiting-banner > span {
  width: 72px;
  height: 72px;
  display: grid;
  place-items: center;
  border-radius: 16px;
}

.danger-banner > span {
  color: #ffffff;
  background: #ef4444;
  box-shadow: 0 12px 26px rgba(220, 38, 38, 0.22);
}

.waiting-banner > span {
  color: #0079ba;
  background: #ffffff;
}

.danger-banner svg,
.waiting-banner svg {
  width: 48px;
  height: 48px;
}

.danger-banner strong {
  display: block;
  color: #dc2626;
  font-size: 26px;
  font-weight: 900;
}

.waiting-banner strong {
  display: block;
  color: #0079ba;
  font-size: 20px;
  font-weight: 900;
}

.danger-banner p,
.waiting-banner p {
  margin: 8px 0 0;
  color: #53647c;
}

.danger-banner time {
  color: #53647c;
  font-size: 13px;
}

.report-list {
  margin: 0;
}

.report-list div {
  display: grid;
  grid-template-columns: 210px 1fr;
  align-items: center;
  min-height: 46px;
  border-bottom: 1px solid #e5e7eb;
}

.report-list dt {
  color: #10233f;
  font-size: 14px;
  font-weight: 800;
}

.report-list dd {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #53647c;
  font-size: 14px;
  min-width: 0;
}

.report-list dd button {
  margin-left: auto;
  color: #53647c;
  background: transparent;
  border: none;
}

.report-list dd svg {
  width: 17px;
  height: 17px;
}

.fail-dot {
  width: 18px;
  height: 18px;
  display: inline-grid;
  place-items: center;
  color: #ffffff;
  background: #ef4444;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 900;
}

.similarity-bar {
  width: min(58%, 460px);
  height: 7px;
  overflow: hidden;
  background: #dce4ef;
  border-radius: 999px;
}

.similarity-bar i {
  display: block;
  height: 100%;
  background: #ef4444;
  border-radius: inherit;
}

.risk-tag {
  padding: 4px 12px;
  color: #dc2626;
  background: #fee2e2;
  border-radius: 6px;
  font-weight: 800;
}

.tampered {
  color: #dc2626;
  font-weight: 900;
}

.keyword-card {
  margin-top: 18px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.keyword-card h3 {
  margin: 0 0 14px;
  font-size: 17px;
}

.keyword-card h3 span {
  color: #53647c;
  font-weight: 500;
}

.keyword-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.keyword-box {
  min-height: 124px;
  padding: 14px;
  border-radius: 8px;
}

.keyword-box.added {
  color: #15803d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.keyword-box.missing {
  color: #dc2626;
  background: #fff7f7;
  border: 1px solid #fecaca;
}

.keyword-box header {
  display: flex;
  justify-content: space-between;
  font-weight: 900;
}

.keyword-box p {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin: 14px 0 0;
}

.keyword-box p span {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.62);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
}

.bottom-tip {
  min-height: 44px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px;
  color: #53647c;
  background: #edf7ff;
  border-color: #c7dff4;
  font-size: 13px;
}

.bottom-tip svg {
  width: 18px;
  height: 18px;
  color: #0079ba;
  fill: #0079ba;
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
