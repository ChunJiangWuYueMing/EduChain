<template>
  <main class="audit-page">
    <aside class="app-sidebar">
      <div class="sidebar-brand">
        <img :src="logoUrl" alt="西南交通大学 EduChain" />
        <p>校园学习资料可信分发</p>
      </div>
      <nav class="sidebar-nav" aria-label="功能导航">
        <button v-for="item in navItems" :key="item.label" type="button" class="nav-item" :class="{ active: item.active }" :disabled="!item.path" @click="item.path && router.push(item.path)">
          <span v-html="item.icon"></span>{{ item.label }}
        </button>
      </nav>
      <img class="sidebar-watermark" :src="sidebarArtUrl" alt="" aria-hidden="true" />
      <div class="sidebar-bridge" aria-hidden="true"></div>
      <div class="chain-local"><span class="status-dot"></span><span>Ganache Local</span><svg viewBox="0 0 24 24"><path d="m7 10 5 5 5-5" /></svg></div>
    </aside>

    <header class="app-header">
      <h1>审计追溯</h1>
      <div class="header-actions">
        <button class="icon-button" type="button" aria-label="搜索"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg></button>
        <div class="chain-status"><span>链状态</span><span class="status-dot"></span><strong>已连接</strong></div>
        <section class="user-card" aria-label="当前用户">
          <div class="avatar"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg></div>
          <div class="user-main"><strong>张三</strong><span>学号：20240001</span></div>
          <div class="user-metric"><span>EDU 余额</span><strong>120</strong></div>
          <div class="user-address"><span>地址</span><strong>0x8f3A...91c2</strong><button type="button" aria-label="复制地址"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></div>
          <button class="logout-button" type="button" @click="router.push('/login')"><svg viewBox="0 0 24 24"><path d="M10 17 15 12l-5-5" /><path d="M15 12H3" /><path d="M21 19V5a2 2 0 0 0-2-2h-6" /></svg>退出</button>
        </section>
      </div>
    </header>

    <section class="audit-content">
      <section class="hero-card">
        <div>
          <h2>审计追溯</h2>
          <p>查询下载记录、我的下载与我的上传</p>
        </div>
        <div class="campus-line" aria-hidden="true"></div>
      </section>

      <section class="records-card">
        <div class="tabs" role="tablist" aria-label="审计记录类型">
          <button v-for="tab in tabs" :key="tab.key" type="button" class="tab" :class="{ active: activeTab === tab.key }" :disabled="tab.disabled" @click="selectTab(tab.key)">
            {{ tab.label }}
            <span v-if="tab.disabled" class="lock"><svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>{{ tab.note }}</span>
          </button>
        </div>

        <form class="search-row" @submit.prevent="applySearch">
          <label for="material-id">资料 ID</label>
          <input id="material-id" v-model.trim="draftKeyword" type="text" placeholder="请输入完整资料 ID" />
          <button class="primary-button" type="submit"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>查询</button>
          <button class="ghost-button" type="button" @click="resetSearch"><svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-2.64-6.36" /><path d="M21 4v6h-6" /></svg>重置</button>
        </form>

        <div class="table-wrap">
          <table>
            <colgroup>
              <col class="col-id" />
              <col class="col-name" />
              <col class="col-person" />
              <col class="col-person" />
              <col class="col-price" />
              <col class="col-hash" />
              <col class="col-time" />
              <col class="col-action" />
            </colgroup>
            <thead>
              <tr>
                <th>资料 ID</th>
                <th>资料名称</th>
                <th>{{ activeTab === 'uploads' ? '上传者' : '下载者' }}</th>
                <th>{{ activeTab === 'uploads' ? '最近下载者' : '上传者' }}</th>
                <th>价格 EDU</th>
                <th>文件哈希 (SHA-256)</th>
                <th>时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in pagedRecords" :key="record.id" :class="{ selected: selectedRecord?.id === record.id }">
                <td><button class="link-cell" type="button" @click="selectedRecord = record">{{ record.materialId }}</button><button class="copy-button" type="button" aria-label="复制资料 ID"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td>
                <td>{{ record.name }}</td>
                <td><strong>{{ record.downloader }}</strong><span>{{ record.downloaderId }}</span></td>
                <td><strong>{{ record.uploader }}</strong><span>{{ record.uploaderId }}</span></td>
                <td>{{ record.price }}</td>
                <td>{{ record.hash }}<button class="copy-button" type="button" aria-label="复制哈希"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td>
                <td>{{ record.time }}</td>
                <td><button class="detail-button" type="button" @click="selectedRecord = record">详情</button></td>
              </tr>
              <tr v-if="pagedRecords.length === 0">
                <td class="empty" colspan="8">暂无符合条件的审计记录</td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="pager">
          <label>每页显示：<select v-model.number="pageSize"><option :value="10">10</option><option :value="20">20</option></select></label>
          <div>
            <button type="button" :disabled="page === 1" @click="page -= 1">‹</button>
            <button v-for="item in pageButtons" :key="item" type="button" :class="{ active: page === item }" @click="page = item">{{ item }}</button>
            <span>...</span>
            <button type="button" @click="page = totalPages">{{ totalPages }}</button>
            <button type="button" :disabled="page === totalPages" @click="page += 1">›</button>
          </div>
          <span>共 {{ totalCount }} 条</span>
        </footer>
      </section>

      <div class="bottom-tip">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01" /><path d="M11 12h1v4h1" /></svg>
        当前仅展示与当前账号相关的审计记录；全局审计需管理员权限。
        <strong v-if="selectedRecord">已选中：{{ selectedRecord.materialId }} · {{ selectedRecord.hash }}</strong>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import logoUrl from '@/assets/images/swjtu-logo-white.png'
import sidebarArtUrl from '@/assets/images/educhain_white_logo.png'

const router = useRouter()
const activeTab = ref('downloads')
const draftKeyword = ref('')
const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const selectedRecord = ref(null)

const navItems = [
  { label: '资料市场', active: false, path: '/market', icon: '<svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h5"/><path d="M10 13h6"/><path d="M10 17h6"/></svg>' },
  { label: '上传资料', active: false, path: '/upload', icon: '<svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/><path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8"/></svg>' },
  { label: '文件验证', active: false, path: '/verify', icon: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>' },
  { label: '我的钱包', active: false, path: '/wallet', icon: '<svg viewBox="0 0 24 24"><path d="M4 7h15a2 2 0 0 1 2 2v10H4a2 2 0 0 1-2-2V5a2 2 0 0 0 2 2Z"/><path d="M16 13h4"/></svg>' },
  { label: '审计追溯', active: true, path: '/audit', icon: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><circle cx="11" cy="15" r="2"/><path d="m13 17 3 3"/></svg>' },
  { label: '系统状态', active: false, path: '/status', icon: '<svg viewBox="0 0 24 24"><path d="M3 4h18v14H3z"/><path d="M8 22h8"/><path d="M12 18v4"/><path d="m7 13 3-3 2 2 4-5"/></svg>' },
]

const tabs = [
  { key: 'mine', label: '我的下载' },
  { key: 'uploads', label: '我的上传' },
  { key: 'downloads', label: '资料下载记录' },
  { key: 'global', label: '全局审计', disabled: true, note: '管理员可见' },
]

const downloadRecords = [
  { id: 1, materialId: 'MAT_20260521_001', name: '计算机网络期末复习提纲.pdf', downloader: '张三', downloaderId: '2024001', uploader: '李四', uploaderId: '2023008', price: 10, hash: '0x21B4...9A01', time: '2026-05-21 14:30:15' },
  { id: 2, materialId: 'CS301_20260520_002', name: '数据结构习题整理.docx', downloader: '王五', downloaderId: '2023106', uploader: '李四', uploaderId: '2023008', price: 8, hash: '0x77Aa...13F0', time: '2026-05-20 09:18:42' },
  { id: 3, materialId: 'MATH101_20260519_003', name: '高等数学知识点汇总.pdf', downloader: '赵六', downloaderId: '2023109', uploader: '孙七', uploaderId: '2022102', price: 0, hash: '0x3B1C...7D22', time: '2026-05-19 20:10:03' },
  { id: 4, materialId: 'AI202_20260518_004', name: '人工智能导论实验报告模板.docx', downloader: '周周', downloaderId: '2024115', uploader: '吴九', uploaderId: '2022106', price: 5, hash: '0x90CD...1AF8', time: '2026-05-18 17:42:31' },
  { id: 5, materialId: 'CS201_20260518_005', name: '操作系统期末复习要点.pdf', downloader: '钱十', downloaderId: '2024007', uploader: '陈晨', uploaderId: '2022013', price: 10, hash: '0xA1F9...C3D4', time: '2026-05-18 13:05:11' },
  { id: 6, materialId: 'EE301_20260517_006', name: '数字信号处理课件汇总.pdf', downloader: '吴桐', downloaderId: '2023112', uploader: '郑一', uploaderId: '2022004', price: 12, hash: '0x6E12...8F90', time: '2026-05-17 19:26:48' },
  { id: 7, materialId: 'PHY201_20260516_007', name: '大学物理期末复习笔记.pdf', downloader: '冯二', downloaderId: '2023103', uploader: '朱三', uploaderId: '2022007', price: 8, hash: '0xD5A3...2B11', time: '2026-05-16 16:54:12' },
  { id: 8, materialId: 'CS401_20260515_008', name: '计算机组成原理总结.pdf', downloader: '何四', downloaderId: '2022116', uploader: '张三', uploaderId: '2024001', price: 15, hash: '0x4C81...F2E7', time: '2026-05-15 22:31:27' },
]

const myDownloads = downloadRecords.filter((item) => item.downloader === '张三')
const myUploads = downloadRecords.filter((item) => item.uploader === '张三')

const recordsByTab = computed(() => {
  if (activeTab.value === 'mine') return myDownloads
  if (activeTab.value === 'uploads') return myUploads
  return downloadRecords
})
const filteredRecords = computed(() => {
  const value = keyword.value.toLowerCase()
  if (!value) return recordsByTab.value
  return recordsByTab.value.filter((item) => item.materialId.toLowerCase().includes(value))
})
const totalCount = computed(() => activeTab.value === 'downloads' && !keyword.value ? 128 : filteredRecords.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))
const pageButtons = computed(() => Array.from({ length: Math.min(3, totalPages.value) }, (_, index) => index + 1))
const pagedRecords = computed(() => filteredRecords.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))

function selectTab(key) {
  activeTab.value = key
  selectedRecord.value = null
}
function applySearch() {
  keyword.value = draftKeyword.value
  page.value = 1
}
function resetSearch() {
  draftKeyword.value = ''
  keyword.value = ''
  page.value = 1
  selectedRecord.value = null
}
watch([activeTab, pageSize], () => { page.value = 1 })
</script>

<style scoped>
.audit-page{min-width:1200px;min-height:100vh;overflow-x:hidden;color:var(--text-primary);background:#f4f7fa}svg{fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}button,input,select{font:inherit}button{cursor:pointer}.app-sidebar{position:fixed;inset:0 auto 0 0;z-index:20;width:248px;overflow:hidden;background:linear-gradient(180deg,#003a70 0%,#002f60 48%,#00284f 100%);box-shadow:8px 0 28px rgba(0,39,82,.2)}.sidebar-brand{padding:34px 20px 26px}.sidebar-brand img{width:210px;height:78px;object-fit:contain;object-position:left center}.sidebar-brand p{margin:14px 0 0;color:rgba(255,255,255,.86);font-size:16px;font-weight:600}.sidebar-nav{position:relative;z-index:2;display:grid;gap:10px;padding:0 8px}.nav-item{display:flex;align-items:center;gap:15px;height:60px;padding:0 22px;color:rgba(255,255,255,.88);background:transparent;border:1px solid transparent;border-radius:6px;font-size:16px;font-weight:700;text-align:left}.nav-item:disabled{cursor:default}.nav-item.active{color:#fff;background:linear-gradient(135deg,#0079ba 0%,#005f92 100%);border-color:rgba(255,255,255,.08);box-shadow:0 12px 24px rgba(0,36,90,.22)}.nav-item span,.nav-item :deep(svg){width:24px;height:24px;flex:0 0 24px}.nav-item :deep(svg){fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}.sidebar-watermark{position:absolute;z-index:1;width:340px;height:340px;right:-118px;bottom:148px;object-fit:contain;opacity:.1;pointer-events:none;transform:rotate(-10deg);filter:drop-shadow(0 22px 42px rgba(0,0,0,.16))}.sidebar-bridge{position:absolute;left:-52px;right:0;bottom:96px;height:210px;opacity:.2;border-top:1px solid rgba(209,232,255,.35);border-bottom:1px solid rgba(209,232,255,.25);border-radius:50%;transform:rotate(-8deg)}.sidebar-bridge:before,.sidebar-bridge:after{position:absolute;left:-80px;width:380px;height:120px;content:'';border-top:1px solid rgba(209,232,255,.28);border-radius:50%}.sidebar-bridge:before{top:40px}.sidebar-bridge:after{top:84px}.chain-local{position:absolute;left:30px;right:26px;bottom:30px;display:flex;align-items:center;gap:12px;color:#fff;font-size:16px}.chain-local svg{width:18px;height:18px;margin-left:auto}.status-dot{display:inline-block;width:12px;height:12px;border-radius:50%;background:#16a34a;box-shadow:0 0 0 4px rgba(22,163,74,.12)}.app-header{position:fixed;top:0;left:248px;right:0;z-index:15;display:flex;align-items:center;justify-content:space-between;height:72px;padding:0 14px 0 30px;background:rgba(255,255,255,.94);border-bottom:1px solid #dce4ef;backdrop-filter:blur(14px)}.app-header h1{margin:0;color:#10233f;font-size:30px;font-weight:800}.header-actions{display:flex;align-items:center;gap:16px}.icon-button{width:44px;height:44px;display:grid;place-items:center;color:#10233f;background:#fff;border:1px solid #dce4ef;border-radius:8px}.icon-button svg{width:22px;height:22px}.chain-status{display:flex;align-items:center;gap:10px;padding-left:16px;border-left:1px solid #dce4ef;color:#53647c;font-size:14px}.chain-status strong{color:#10233f}.user-card{display:grid;grid-template-columns:48px 126px 100px 170px 82px;align-items:center;min-height:58px;overflow:hidden;background:#fff;border:1px solid #dce4ef;border-radius:8px;box-shadow:0 10px 26px rgba(15,23,42,.06)}.avatar{width:38px;height:38px;display:grid;place-items:center;margin-left:12px;color:#2f6fbc;background:#e8f2ff;border-radius:50%}.avatar svg{width:25px;height:25px;fill:currentColor;stroke:none}.user-main,.user-metric,.user-address{display:grid;gap:4px;height:58px;align-content:center;padding:0 14px;border-left:1px solid #e5e7eb}.user-main{border-left:none}.user-main strong,.user-address strong{color:#10233f;font-size:15px}.user-main span,.user-metric span,.user-address span{color:#53647c;font-size:12px}.user-metric strong{color:#0079ba;font-size:17px}.user-address{grid-template-columns:1fr auto}.user-address span,.user-address strong{grid-column:1}.user-address button{grid-column:2;grid-row:1/span 2;color:#53647c;background:transparent;border:none}.user-address svg{width:18px;height:18px}.logout-button{height:58px;display:flex;align-items:center;justify-content:center;gap:7px;color:#10233f;background:#fff;border:none;border-left:1px solid #e5e7eb;font-size:14px}.logout-button svg{width:18px;height:18px}.audit-content{min-height:100vh;padding:90px 12px 12px 260px}.hero-card,.records-card,.bottom-tip{background:#fff;border:1px solid #e5e7eb;border-radius:8px;box-shadow:0 10px 30px rgba(15,23,42,.06)}.hero-card{position:relative;height:116px;display:flex;align-items:center;margin-bottom:16px;padding:0 28px;overflow:hidden}.hero-card h2{margin:0 0 10px;color:#10233f;font-size:28px;font-weight:900}.hero-card p{margin:0;color:#53647c}.campus-line{position:absolute;right:170px;bottom:-14px;width:520px;height:110px;opacity:.32;border-top:1px solid #b9d8f0;border-radius:50%;transform:rotate(2deg)}.campus-line:before,.campus-line:after{position:absolute;content:'';border-top:1px solid #c7dff4;border-radius:50%}.campus-line:before{inset:28px -70px auto 60px;height:80px}.campus-line:after{inset:54px -100px auto 120px;height:90px}.records-card{overflow:hidden}.tabs{height:68px;display:flex;align-items:end;gap:34px;padding:0 24px;border-bottom:1px solid #e5e7eb}.tab{position:relative;height:50px;display:flex;align-items:center;gap:8px;padding:0 0 16px;color:#10233f;background:transparent;border:none;border-bottom:3px solid transparent;font-weight:800}.tab.active{color:#005bd1;border-bottom-color:#005bd1}.tab:disabled{color:#8a97aa;cursor:not-allowed}.lock{display:inline-flex;align-items:center;gap:7px;font-size:13px;font-weight:600;color:#8a97aa}.lock svg{width:16px;height:16px}.search-row{height:78px;display:flex;align-items:center;gap:14px;padding:0 24px}.search-row label{color:#53647c;font-weight:700}.search-row input{width:240px;height:40px;padding:0 14px;border:1px solid #dce4ef;border-radius:6px;color:#10233f}.primary-button,.ghost-button{height:40px;display:flex;align-items:center;justify-content:center;gap:8px;border-radius:6px;font-weight:800}.primary-button{padding:0 18px;color:#fff;background:#005bd1;border:1px solid #005bd1}.ghost-button{margin-left:auto;padding:0 18px;color:#10233f;background:#fff;border:1px solid #dce4ef}.primary-button svg,.ghost-button svg{width:18px;height:18px}.table-wrap{padding:0 16px 0}.table-wrap table{width:100%;border-collapse:collapse;table-layout:fixed;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}.col-id{width:210px}.col-name{width:240px}.col-person{width:108px}.col-price{width:95px}.col-hash{width:185px}.col-time{width:130px}.col-action{width:90px}th,td{height:66px;padding:0 16px;border-bottom:1px solid #e5e7eb;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:14px}th{height:52px;background:#f9fafb;color:#10233f;font-weight:800}tbody tr:hover,tbody tr.selected{background:#f8fbff}td span{display:block;margin-top:4px;color:#53647c;font-size:13px}.link-cell{max-width:160px;padding:0;color:#005bd1;background:transparent;border:none;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}.copy-button{width:22px;height:22px;margin-left:6px;color:#53647c;background:transparent;border:none;vertical-align:middle}.copy-button svg{width:16px;height:16px}.detail-button{height:32px;padding:0 16px;color:#005bd1;background:#fff;border:1px solid #dce4ef;border-radius:6px;font-weight:800}.empty{height:180px;color:#8a97aa;text-align:center}.pager{height:74px;display:flex;align-items:center;gap:24px;padding:0 24px;color:#53647c}.pager label{margin-right:auto}.pager select{height:34px;border:1px solid #dce4ef;border-radius:6px;background:#fff}.pager div{display:flex;align-items:center;gap:8px}.pager button{width:34px;height:34px;color:#10233f;background:#fff;border:1px solid #dce4ef;border-radius:6px;font-weight:800}.pager button.active{color:#fff;background:#005bd1;border-color:#005bd1}.pager button:disabled{opacity:.45;cursor:not-allowed}.bottom-tip{min-height:42px;display:flex;align-items:center;gap:10px;margin-top:12px;padding:0 18px;color:#53647c;background:#edf7ff;border-color:#c7dff4;font-size:13px}.bottom-tip svg{width:18px;height:18px;color:#005bd1;fill:#005bd1}.bottom-tip strong{margin-left:auto;color:#10233f;font-size:13px}
.table-wrap .col-id{width:220px}.table-wrap .col-name{width:215px}.table-wrap .col-price{width:105px}.table-wrap .col-hash{width:175px}.table-wrap .col-time{width:145px}.table-wrap .col-action{width:92px}.table-wrap td:nth-child(7){white-space:normal;line-height:1.45}.table-wrap td:last-child{overflow:visible;text-overflow:clip}.table-wrap .link-cell{max-width:170px}.table-wrap .detail-button{padding:0 14px}
</style>
