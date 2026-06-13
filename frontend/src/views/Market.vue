<template>
  <main class="market-page">
    <aside class="market-sidebar">
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
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m7 10 5 5 5-5" />
        </svg>
      </div>
    </aside>

    <header class="market-header">
      <h1>资料市场</h1>
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
            登出
          </button>
        </section>
      </div>
    </header>

    <section class="market-content">
      <div class="content-main">
        <section class="hero-card">
          <div>
            <h2>资料市场</h2>
            <p>基于区块链的校园学习资料可信分发平台</p>
          </div>
          <div class="hero-actions">
            <button type="button" class="primary-action" @click="router.push('/upload')">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3v12" />
                <path d="m7 8 5-5 5 5" />
                <path d="M5 15v4h14v-4" />
              </svg>
              上传资料
            </button>
            <button type="button" class="secondary-action" @click="resetFilters">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M21 12a9 9 0 1 1-2.64-6.36" />
                <path d="M21 4v6h-6" />
              </svg>
              刷新
            </button>
          </div>
        </section>

        <section class="filter-card" aria-label="资料筛选">
          <label class="search-field">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input v-model="keyword" type="search" placeholder="搜索资料名或课程" />
          </label>

          <label class="select-field">
            <span>课程筛选</span>
            <select v-model="courseFilter">
              <option value="all">全部课程</option>
              <option value="CS201">CS201</option>
              <option value="CS301">CS301</option>
              <option value="MATH101">MATH101</option>
              <option value="AI202">AI202</option>
            </select>
          </label>

          <label class="select-field">
            <span>访问策略</span>
            <select v-model="policyFilter">
              <option value="all">全部策略</option>
              <option value="same-course">同课程</option>
              <option value="public">公开</option>
            </select>
          </label>

          <button class="refresh-icon" type="button" aria-label="重置筛选" @click="resetFilters">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M21 12a9 9 0 1 1-2.64-6.36" />
              <path d="M21 4v6h-6" />
            </svg>
          </button>
        </section>

        <div class="summary-strip">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 8h.01" />
            <path d="M11 12h1v4h1" />
          </svg>
          当前共 {{ filteredMaterials.length }} 份资料，本周新增 12 份
        </div>

        <section class="table-card">
          <table>
            <colgroup>
              <col class="col-name" />
              <col class="col-course" />
              <col class="col-price" />
              <col class="col-policy" />
              <col class="col-address" />
              <col class="col-version" />
              <col class="col-time" />
              <col class="col-status" />
              <col class="col-actions" />
            </colgroup>
            <thead>
              <tr>
                <th>资料名称</th>
                <th>课程</th>
                <th>价格 EDU</th>
                <th>访问策略</th>
                <th>上传者地址</th>
                <th>版本</th>
                <th>上传时间</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in visibleMaterials"
                :key="item.id"
                :class="{ selected: selectedId === item.id, muted: item.status !== 'normal' }"
                @click="selectedId = item.id"
              >
                <td class="file-name">{{ item.name }}</td>
                <td>{{ item.course }}</td>
                <td>{{ item.price }} EDU</td>
                <td>
                  <span class="policy-tag" :class="item.policy">{{ item.policyText }}</span>
                </td>
                <td class="address-cell">
                  {{ item.uploader }}
                  <button type="button" aria-label="复制上传者地址" @click.stop>
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <rect x="9" y="9" width="11" height="11" rx="2" />
                      <rect x="4" y="4" width="11" height="11" rx="2" />
                    </svg>
                  </button>
                </td>
                <td>{{ item.version }}</td>
                <td>{{ item.uploadedAt }}</td>
                <td>
                  <span class="state" :class="item.status">
                    <span></span>
                    {{ item.statusText }}
                  </span>
                </td>
                <td class="row-actions">
                  <button type="button" @click.stop="selectedId = item.id">详情</button>
                  <button type="button" :disabled="item.status !== 'normal'" @click.stop="verifyMaterial(item)">验证</button>
                  <button type="button" class="download" :disabled="item.status !== 'normal'" @click.stop="downloadMaterial(item)">
                    下载
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-if="filteredMaterials.length === 0" class="empty-state">
            <div class="empty-box">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 7 12 3l8 4-8 4-8-4Z" />
                <path d="M4 7v9l8 5 8-5V7" />
                <path d="M12 11v10" />
              </svg>
            </div>
            <strong>暂无符合条件的资料</strong>
            <button type="button" @click="resetFilters">清除筛选条件</button>
          </div>

          <footer v-else class="table-footer">
            <label>
              每页显示：
              <select v-model.number="pageSize">
                <option :value="4">4</option>
                <option :value="8">8</option>
                <option :value="12">12</option>
              </select>
            </label>
            <div class="pagination">
              <button type="button" :disabled="currentPage === 1" @click="currentPage -= 1">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6" /></svg>
              </button>
              <button
                v-for="page in totalPages"
                :key="page"
                type="button"
                :class="{ active: currentPage === page }"
                @click="currentPage = page"
              >
                {{ page }}
              </button>
              <button type="button" :disabled="currentPage === totalPages" @click="currentPage += 1">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
              </button>
            </div>
            <span>共 {{ totalCount }} 条</span>
          </footer>
        </section>
      </div>

      <aside class="detail-panel" aria-label="资料详情">
        <header>
          <h2>资料详情</h2>
          <button type="button" aria-label="关闭详情">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </header>

        <template v-if="selectedMaterial">
          <section class="detail-title">
            <span class="file-icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
                <path d="M14 2v6h6" />
                <path d="M8 13h8" />
                <path d="M8 17h6" />
              </svg>
            </span>
            <div>
              <strong>{{ selectedMaterial.name }}</strong>
              <span class="state normal"><span></span>正常</span>
            </div>
          </section>

          <dl class="detail-list">
            <div v-for="item in detailRows" :key="item.label">
              <dt>{{ item.label }}</dt>
              <dd>
                {{ item.value }}
                <button v-if="item.copy" type="button" aria-label="复制">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="9" y="9" width="11" height="11" rx="2" />
                    <rect x="4" y="4" width="11" height="11" rx="2" />
                  </svg>
                </button>
              </dd>
            </div>
          </dl>

          <div class="detail-actions">
            <button type="button" class="primary-action" @click="downloadMaterial(selectedMaterial)">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3v12" />
                <path d="m7 10 5 5 5-5" />
                <path d="M5 21h14" />
              </svg>
              下载资料
            </button>
            <button type="button" class="secondary-action" @click="verifyMaterial(selectedMaterial)">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
              验证此资料
            </button>
            <button type="button" class="link-action">查看下载记录</button>
          </div>
        </template>
      </aside>
    </section>

    <div v-if="toast" class="toast" role="status">{{ toast }}</div>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api, { formatTime, policyText, truncate } from '@/utils/api'
import { useAuthStore } from '@/stores/auth'
import logoUrl from '@/assets/images/swjtu-logo-white.png'
import sidebarArtUrl from '@/assets/images/educhain_white_logo.png'

const router = useRouter()
const auth = useAuthStore()

const navItems = [
  { label: '资料市场', active: true, path: '/market', icon: '<svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h5"/><path d="M10 13h6"/><path d="M10 17h6"/></svg>' },
  { label: '上传资料', active: false, path: '/upload', icon: '<svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/><path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8"/></svg>' },
  { label: '文件验证', active: false, path: '/verify', icon: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>' },
  { label: '我的钱包', active: false, path: '/wallet', icon: '<svg viewBox="0 0 24 24"><path d="M4 7h15a2 2 0 0 1 2 2v10H4a2 2 0 0 1-2-2V5a2 2 0 0 0 2 2Z"/><path d="M16 13h4"/></svg>' },
  { label: '审计追溯', active: false, path: '/audit', icon: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><circle cx="11" cy="15" r="2"/><path d="m13 17 3 3"/></svg>' },
  { label: '系统状态', active: false, path: '/status', icon: '<svg viewBox="0 0 24 24"><path d="M3 4h18v14H3z"/><path d="M8 22h8"/><path d="M12 18v4"/><path d="m7 13 3-3 2 2 4-5"/></svg>' },
]

const materials = ref([])
const loading = ref(false)

const keyword = ref('')
const courseFilter = ref('all')
const policyFilter = ref('all')
const currentPage = ref(1)
const pageSize = ref(4)
const selectedId = ref('')
const toast = ref('')

const filteredMaterials = computed(() => {
  const normalized = keyword.value.trim().toLowerCase()
  return materials.value.filter((item) => {
    const matchesKeyword = !normalized || item.name.toLowerCase().includes(normalized) || item.course.toLowerCase().includes(normalized)
    const matchesCourse = courseFilter.value === 'all' || item.course === courseFilter.value
    const matchesPolicy = policyFilter.value === 'all' || item.policy === policyFilter.value
    return matchesKeyword && matchesCourse && matchesPolicy
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredMaterials.value.length / pageSize.value)))
const visibleMaterials = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredMaterials.value.slice(start, start + pageSize.value)
})
const totalCount = computed(() => filteredMaterials.value.length)
const selectedMaterial = computed(() => filteredMaterials.value.find((item) => item.id === selectedId.value) || filteredMaterials.value[0] || null)
const detailRows = computed(() => {
  if (!selectedMaterial.value) return []
  const item = selectedMaterial.value
  return [
    { label: '资料 ID', value: item.id, copy: true },
    { label: '资料名称', value: item.name },
    { label: '课程', value: item.course },
    { label: '上传者地址', value: item.uploader, copy: true },
    { label: 'SHA-256', value: item.sha, copy: true },
    { label: 'SimHash', value: item.simhash, copy: true },
    { label: '文本长度', value: item.length },
    { label: '价格', value: `${item.price} EDU` },
    { label: '版本', value: item.version },
    { label: '访问策略', value: item.policyText },
    { label: '链上时间', value: item.uploadedAt },
  ]
})

watch([keyword, courseFilter, policyFilter, pageSize], () => {
  currentPage.value = 1
})

watch(filteredMaterials, (items) => {
  if (!items.some((item) => item.id === selectedId.value)) {
    selectedId.value = items[0]?.id || ''
  }
})

function resetFilters() {
  keyword.value = ''
  courseFilter.value = 'all'
  policyFilter.value = 'all'
}

function showToast(message) {
  toast.value = message
  window.clearTimeout(showToast.timer)
  showToast.timer = window.setTimeout(() => {
    toast.value = ''
  }, 1800)
}

function verifyMaterial(item) {
  router.push({ path: '/verify', query: { materialId: item.id } })
}

async function downloadMaterial(item) {
  if (!item) return
  try {
    const response = await api.get(`/api/material/${encodeURIComponent(item.id)}/download`)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = item.name
    link.click()
    URL.revokeObjectURL(url)
    await auth.refreshBalance()
    showToast(`${item.name} 下载成功`)
  } catch (error) {
    showToast(error.message || '下载失败')
  }
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

function mapMaterial(item) {
  return {
    id: item.id,
    name: item.name,
    course: item.course,
    price: item.price,
    policy: item.policy_type === 0 ? 'public' : item.policy_type === 1 ? 'same-course' : 'whitelist',
    policyText: policyText(item.policy_type),
    uploader: item.uploader,
    version: `v${item.version}`,
    uploadedAt: formatTime(item.timestamp),
    status: item.deleted ? 'removed' : 'normal',
    statusText: item.deleted ? '已删除' : '正常',
    sha: item.sha256_hash,
    simhash: typeof item.sim_hash === 'number' ? `0x${item.sim_hash.toString(16)}` : item.sim_hash,
    length: item.text_length,
  }
}

async function loadMaterials() {
  loading.value = true
  try {
    const res = await api.get('/api/material/list?page=1&page_size=100')
    materials.value = (res.data?.items || []).map(mapMaterial)
    selectedId.value = materials.value[0]?.id || ''
  } catch (error) {
    showToast(error.message || '资料加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadMaterials)
</script>

<style scoped>
.market-page {
  min-width: 1200px;
  height: 100vh;
  overflow: hidden;
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
select,
input {
  font: inherit;
}

button {
  cursor: pointer;
}

.market-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: 248px;
  background: linear-gradient(180deg, #003a70 0%, #002f60 48%, #00284f 100%);
  box-shadow: 8px 0 28px rgba(0, 39, 82, 0.2);
  overflow: hidden;
  z-index: 20;
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
  content: '';
  width: 380px;
  height: 120px;
  left: -80px;
  border-top: 1px solid rgba(209, 232, 255, 0.28);
  border-radius: 50%;
}

.sidebar-bridge::before {
  top: 40px;
}

.sidebar-bridge::after {
  top: 84px;
}

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

.market-header {
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

.market-header h1 {
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

.icon-button,
.refresh-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
}

.icon-button svg,
.refresh-icon svg {
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
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
  overflow: hidden;
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

.market-content {
  height: 100vh;
  padding: 88px 16px 16px 264px;
  display: grid;
  grid-template-columns: minmax(760px, 1fr) 340px;
  gap: 16px;
}

.content-main {
  min-width: 0;
  overflow: hidden;
  display: grid;
  grid-template-rows: auto auto auto auto;
  align-content: start;
  gap: 12px;
}

.hero-card,
.filter-card,
.table-card,
.detail-panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.hero-card {
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  overflow: hidden;
  position: relative;
}

.hero-card::after {
  position: absolute;
  content: '';
  inset: 22px 210px auto auto;
  width: 420px;
  height: 95px;
  border-top: 1px solid rgba(0, 121, 186, 0.13);
  border-bottom: 1px solid rgba(0, 121, 186, 0.08);
  border-radius: 50%;
  transform: rotate(-8deg);
}

.hero-card::before {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 8px;
  content: '';
  background: linear-gradient(90deg, #0079ba 0%, #005f92 45%, rgba(0, 121, 186, 0.12) 100%);
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

.hero-actions,
.detail-actions {
  display: flex;
  gap: 14px;
}

.primary-action,
.secondary-action {
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 0 20px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 700;
}

.primary-action {
  color: #ffffff;
  background: linear-gradient(180deg, #0079ba 0%, #005f92 100%);
  border: 1px solid #00649a;
  box-shadow: 0 8px 18px rgba(0, 121, 186, 0.22);
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

.filter-card {
  min-height: 86px;
  display: grid;
  grid-template-columns: minmax(230px, 1fr) 190px 190px 44px;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
}

.search-field,
.select-field {
  display: grid;
  gap: 8px;
}

.search-field {
  position: relative;
}

.search-field svg {
  position: absolute;
  left: 14px;
  bottom: 12px;
  width: 20px;
  height: 20px;
  color: #53647c;
}

.search-field input,
.select-field select {
  width: 100%;
  height: 42px;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 7px;
  outline: none;
}

.search-field input {
  padding: 0 14px 0 42px;
}

.select-field span {
  color: #53647c;
  font-size: 13px;
}

.select-field select {
  padding: 0 14px;
}

.summary-strip {
  min-height: 44px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  color: #005f92;
  background: #e6f4fa;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
}

.summary-strip svg {
  width: 19px;
  height: 19px;
  fill: #005f92;
  stroke: #005f92;
}

.table-card {
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.col-name { width: 23%; }
.col-course { width: 7%; }
.col-price { width: 9%; }
.col-policy { width: 9%; }
.col-address { width: 11%; }
.col-version { width: 6%; }
.col-time { width: 12%; }
.col-status { width: 6%; }
.col-actions { width: 17%; }

th,
td {
  height: 58px;
  padding: 0 9px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  color: #10233f;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

th {
  height: 48px;
  color: #10233f;
  background: #f9fafb;
  font-size: 13px;
  font-weight: 800;
}

tbody tr {
  transition: background 0.18s ease;
}

tbody tr:hover,
tbody tr.selected {
  background: #f1f8fd;
}

tbody tr.muted {
  color: #9ca3af;
}

tbody tr.muted td {
  color: #9ca3af;
}

.file-name {
  font-weight: 700;
}

.policy-tag {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
}

.policy-tag.public {
  color: #15803d;
  background: #dcfce7;
}

.policy-tag.same-course {
  color: #b45309;
  background: #fef3c7;
}

.address-cell {
  color: #53647c;
}

.address-cell button,
dd button {
  width: 24px;
  height: 24px;
  margin-left: 5px;
  vertical-align: middle;
  color: #53647c;
  background: transparent;
  border: none;
}

.address-cell svg,
dd svg {
  width: 17px;
  height: 17px;
}

.state {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-weight: 700;
}

.state span {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #9ca3af;
}

.state.normal span {
  background: #16a34a;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

.row-actions button {
  height: 30px;
  min-width: 34px;
  padding: 0 5px;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 5px;
  font-size: 12px;
}

.row-actions .download {
  min-width: 40px;
  color: #ffffff;
  background: #0079ba;
  border-color: #0079ba;
}

.row-actions button:disabled {
  color: #9ca3af;
  background: #eef0f3;
  border-color: #dce4ef;
  cursor: not-allowed;
}

.empty-state {
  flex: 1;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 14px;
  min-height: 250px;
  color: #53647c;
}

.empty-box {
  width: 86px;
  height: 74px;
  display: grid;
  place-items: center;
  color: #8bbce3;
  background: #e6f4fa;
  border-radius: 50%;
}

.empty-box svg {
  width: 54px;
  height: 54px;
}

.empty-state strong {
  color: #10233f;
}

.empty-state button {
  height: 34px;
  padding: 0 16px;
  color: #0079ba;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 6px;
  font-weight: 700;
}

.table-footer {
  min-height: 58px;
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 18px;
  color: #53647c;
  font-size: 14px;
}

.table-footer label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: auto;
}

.table-footer select {
  height: 34px;
  padding: 0 12px;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 6px;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination button {
  width: 34px;
  height: 34px;
  color: #10233f;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 6px;
  font-weight: 700;
}

.pagination button.active {
  color: #ffffff;
  background: #0079ba;
  border-color: #0079ba;
}

.pagination button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.pagination svg {
  width: 18px;
  height: 18px;
}

.detail-panel {
  min-width: 0;
  height: calc(100vh - 104px);
  overflow: auto;
}

.detail-panel > header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  border-bottom: 1px solid #e5e7eb;
}

.detail-panel h2 {
  margin: 0;
  font-size: 18px;
}

.detail-panel header button {
  color: #10233f;
  background: transparent;
  border: none;
}

.detail-panel header svg {
  width: 22px;
  height: 22px;
}

.detail-title {
  display: grid;
  grid-template-columns: 52px 1fr;
  gap: 16px;
  align-items: center;
  padding: 22px;
  border-bottom: 1px solid #e5e7eb;
}

.file-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  color: #ffffff;
  background: #0079ba;
  border-radius: 8px;
  box-shadow: 0 10px 20px rgba(0, 121, 186, 0.16);
}

.file-icon svg {
  width: 30px;
  height: 30px;
}

.detail-title strong {
  display: block;
  margin-bottom: 8px;
  color: #10233f;
  font-size: 16px;
}

.detail-list {
  margin: 0;
}

.detail-list div {
  display: grid;
  grid-template-columns: 120px 1fr;
  align-items: center;
  min-height: 52px;
  padding: 0 22px;
  border-bottom: 1px solid #e5e7eb;
}

.detail-list dt {
  color: #53647c;
  font-size: 14px;
}

.detail-list dd {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  color: #10233f;
  font-size: 14px;
  text-align: right;
}

.detail-actions {
  flex-direction: column;
  padding: 18px 22px 26px;
}

.detail-actions .primary-action,
.detail-actions .secondary-action {
  width: 100%;
  height: 44px;
}

.link-action {
  height: 36px;
  color: #0079ba;
  background: transparent;
  border: none;
  font-weight: 700;
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
