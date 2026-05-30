<template>
  <main class="status-page">
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
      <h1>系统状态</h1>
      <div class="header-actions">
        <button class="icon-button" type="button" aria-label="搜索"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg></button>
        <div class="chain-status"><span>链状态:</span><span class="status-dot"></span><strong>已连接</strong></div>
        <section class="user-card" aria-label="当前用户">
          <div class="avatar"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg></div>
          <div class="user-main"><strong>张三</strong><span>学号：20240001</span></div>
          <div class="user-metric"><span>EDU 余额</span><strong>120</strong></div>
          <div class="user-address"><span>地址</span><strong>0x8f3A...91c2</strong><button type="button" aria-label="复制地址"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></div>
          <button class="logout-button" type="button" @click="router.push('/login')"><svg viewBox="0 0 24 24"><path d="M10 17 15 12l-5-5" /><path d="M15 12H3" /><path d="M21 19V5a2 2 0 0 0-2-2h-6" /></svg>退出</button>
        </section>
      </div>
    </header>

    <section class="status-content">
      <section class="hero-card">
        <div>
          <h2>系统状态</h2>
          <p>查看后端、区块链与合约运行状态</p>
        </div>
        <div class="campus-line" aria-hidden="true"></div>
        <button class="refresh-button" type="button" :disabled="refreshing" @click="refreshStatus">
          <svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-2.64-6.36" /><path d="M21 4v6h-6" /></svg>
          {{ refreshing ? '刷新中' : '刷新' }}
        </button>
      </section>

      <section class="summary-grid">
        <article class="status-card backend">
          <span class="round"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="5" rx="1" /><rect x="4" y="10" width="16" height="5" rx="1" /><rect x="4" y="16" width="16" height="5" rx="1" /></svg></span>
          <div><h3>后端状态</h3><strong><i></i> 运行中</strong><p>服务正常</p></div>
        </article>
        <article class="status-card ganache">
          <span class="round"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2" /><circle cx="5" cy="19" r="2" /><circle cx="19" cy="19" r="2" /><path d="m11 7-5 10" /><path d="m13 7 5 10" /><path d="M7 19h10" /></svg></span>
          <div><h3>Ganache 连接状态</h3><strong><i></i> 已连接</strong><p>本地节点连接正常</p></div>
        </article>
        <article class="status-card block">
          <span class="round"><svg viewBox="0 0 24 24"><path d="m12 2 8 4.5v9L12 20l-8-4.5v-9Z" /><path d="M12 11 4 6.5" /><path d="m12 11 8-4.5" /><path d="M12 11v9" /></svg></span>
          <div><h3>当前区块号</h3><b>{{ status.blockNumber }}</b><p>最后区块时间：{{ status.lastBlockTime }}</p></div>
        </article>
        <article class="status-card stats">
          <span class="round"><svg viewBox="0 0 24 24"><path d="M5 20V11" /><path d="M12 20V5" /><path d="M19 20v-8" /><path d="M3 20h18" /></svg></span>
          <div><h3>数据统计</h3><p>资料总数 <b>{{ status.materialCount }}</b></p><p>下载记录总数 <b>{{ status.downloadCount }}</b></p></div>
        </article>
      </section>

      <section class="main-grid">
        <article class="detail-card">
          <h2>系统详情</h2>
          <table>
            <thead><tr><th>项目</th><th>详情</th></tr></thead>
            <tbody>
              <tr><td>后端服务</td><td><span class="ok-dot"></span>运行中 <em>(v1.0.0)</em></td></tr>
              <tr><td>Ganache URL</td><td><code>http://127.0.0.1:8545</code><button type="button" aria-label="复制 Ganache URL"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td></tr>
              <tr v-for="item in contractRows" :key="item.label"><td>{{ item.label }}</td><td><code>{{ item.value }}</code><button type="button" :aria-label="`复制${item.label}`"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td></tr>
              <tr><td>网络</td><td>Ganache（Local）</td></tr>
              <tr><td>链 ID</td><td>1337</td></tr>
            </tbody>
          </table>

          <div class="health-strip">
            <div><span class="circle success"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /><path d="m9 12 2 2 4-4" /></svg></span><p>合约部署状态</p><strong>合约部署正常</strong></div>
            <div><span class="circle link"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l2.2-2.2a5 5 0 0 0-7.08-7.08l-1.26 1.26" /><path d="M14 11a5 5 0 0 0-7.54-.54l-2.2 2.2a5 5 0 0 0 7.08 7.08l1.26-1.26" /></svg></span><p>链同步状态</p><strong>链同步正常</strong></div>
          </div>
        </article>

        <aside class="check-card">
          <h2>最近检查结果</h2>
          <div v-for="record in checkRecords" :key="record.title" class="check-item">
            <span><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="m8 12 3 3 5-6" /></svg></span>
            <div><strong>{{ record.title }}</strong><p>{{ record.desc }}</p></div>
            <time>{{ record.time }}</time>
            <b>通过</b>
          </div>
          <button class="all-checks" type="button">查看全部检查记录 <svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6" /></svg></button>
        </aside>
      </section>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import logoUrl from '@/assets/images/swjtu-logo-white.png'
import sidebarArtUrl from '@/assets/images/educhain_white_logo.png'

const router = useRouter()
const refreshing = ref(false)
const status = reactive({
  blockNumber: 128,
  materialCount: 128,
  downloadCount: 256,
  lastBlockTime: '2026-05-21 14:30:18',
})
const checkRecords = ref([
  { title: '系统健康检查', desc: '后端、Ganache 与合约状态检查', time: '2026-05-21 14:30:18' },
  { title: '链同步检查', desc: '当前区块高度与节点同步检查', time: '2026-05-21 14:20:18' },
  { title: '合约完整性检查', desc: '合约代码与部署地址校验', time: '2026-05-21 14:10:18' },
])

const navItems = [
  { label: '资料市场', active: false, path: '/market', icon: '<svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h5"/><path d="M10 13h6"/><path d="M10 17h6"/></svg>' },
  { label: '上传资料', active: false, path: '/upload', icon: '<svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/><path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8"/></svg>' },
  { label: '文件验证', active: false, path: '/verify', icon: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>' },
  { label: '我的钱包', active: false, path: '/wallet', icon: '<svg viewBox="0 0 24 24"><path d="M4 7h15a2 2 0 0 1 2 2v10H4a2 2 0 0 1-2-2V5a2 2 0 0 0 2 2Z"/><path d="M16 13h4"/></svg>' },
  { label: '审计追溯', active: false, path: '/audit', icon: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><circle cx="11" cy="15" r="2"/><path d="m13 17 3 3"/></svg>' },
  { label: '系统状态', active: true, path: '/status', icon: '<svg viewBox="0 0 24 24"><path d="M3 4h18v14H3z"/><path d="M8 22h8"/><path d="M12 18v4"/><path d="m7 13 3-3 2 2 4-5"/></svg>' },
]

const contractRows = [
  { label: 'Deployer 地址', value: '0x12ab...89ef' },
  { label: 'EduToken 合约地址', value: '0x3b1C7a2d8E6b4d1F2c9A7eF6dB3eC4Fa1B2d3E4F' },
  { label: 'MaterialRegistry 合约地址', value: '0x7FAaC9b8E1d4f2A3c6D5e7F90123456789AbCdEf' },
  { label: 'DownloadLog 合约地址', value: '0x9C0D1e2F3aB4c5D6e7F809abcdef1234567890AB' },
]

function refreshStatus() {
  refreshing.value = true
  window.setTimeout(() => {
    status.blockNumber += 1
    status.lastBlockTime = '2026-05-21 14:30:48'
    checkRecords.value = [
      { title: '系统健康检查', desc: '后端、Ganache 与合约状态检查', time: status.lastBlockTime },
      ...checkRecords.value.slice(0, 2),
    ]
    refreshing.value = false
  }, 500)
}
</script>

<style scoped>
.status-page{min-width:1200px;min-height:100vh;overflow-x:hidden;color:var(--text-primary);background:#f4f7fa}svg{fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}button{font:inherit;cursor:pointer}.app-sidebar{position:fixed;inset:0 auto 0 0;z-index:20;width:248px;overflow:hidden;background:linear-gradient(180deg,#003a70 0%,#002f60 48%,#00284f 100%);box-shadow:8px 0 28px rgba(0,39,82,.2)}.sidebar-brand{padding:34px 20px 26px}.sidebar-brand img{width:210px;height:78px;object-fit:contain;object-position:left center}.sidebar-brand p{margin:14px 0 0;color:rgba(255,255,255,.86);font-size:16px;font-weight:600}.sidebar-nav{position:relative;z-index:2;display:grid;gap:10px;padding:0 8px}.nav-item{display:flex;align-items:center;gap:15px;height:60px;padding:0 22px;color:rgba(255,255,255,.88);background:transparent;border:1px solid transparent;border-radius:6px;font-size:16px;font-weight:700;text-align:left}.nav-item.active{color:#fff;background:linear-gradient(135deg,#0079ba 0%,#005f92 100%);border-color:rgba(255,255,255,.08);box-shadow:0 12px 24px rgba(0,36,90,.22)}.nav-item span,.nav-item :deep(svg){width:24px;height:24px;flex:0 0 24px}.nav-item :deep(svg){fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}.sidebar-watermark{position:absolute;z-index:1;width:340px;height:340px;right:-118px;bottom:148px;object-fit:contain;opacity:.1;pointer-events:none;transform:rotate(-10deg);filter:drop-shadow(0 22px 42px rgba(0,0,0,.16))}.sidebar-bridge{position:absolute;left:-52px;right:0;bottom:96px;height:210px;opacity:.2;border-top:1px solid rgba(209,232,255,.35);border-bottom:1px solid rgba(209,232,255,.25);border-radius:50%;transform:rotate(-8deg)}.sidebar-bridge:before,.sidebar-bridge:after{position:absolute;left:-80px;width:380px;height:120px;content:'';border-top:1px solid rgba(209,232,255,.28);border-radius:50%}.sidebar-bridge:before{top:40px}.sidebar-bridge:after{top:84px}.chain-local{position:absolute;left:30px;right:26px;bottom:30px;display:flex;align-items:center;gap:12px;color:#fff;font-size:16px}.chain-local svg{width:18px;height:18px;margin-left:auto}.status-dot{display:inline-block;width:12px;height:12px;border-radius:50%;background:#16a34a;box-shadow:0 0 0 4px rgba(22,163,74,.12)}.app-header{position:fixed;top:0;left:248px;right:0;z-index:15;display:flex;align-items:center;justify-content:space-between;height:72px;padding:0 14px 0 30px;background:rgba(255,255,255,.94);border-bottom:1px solid #dce4ef;backdrop-filter:blur(14px)}.app-header h1{margin:0;color:#10233f;font-size:30px;font-weight:800}.header-actions{display:flex;align-items:center;gap:16px}.icon-button{width:44px;height:44px;display:grid;place-items:center;color:#10233f;background:#fff;border:1px solid #dce4ef;border-radius:8px}.icon-button svg{width:22px;height:22px}.chain-status{display:flex;align-items:center;gap:10px;padding-left:16px;border-left:1px solid #dce4ef;color:#53647c;font-size:14px}.chain-status strong{color:#10233f}.user-card{display:grid;grid-template-columns:48px 126px 100px 170px 82px;align-items:center;min-height:58px;overflow:hidden;background:#fff;border:1px solid #dce4ef;border-radius:8px;box-shadow:0 10px 26px rgba(15,23,42,.06)}.avatar{width:38px;height:38px;display:grid;place-items:center;margin-left:12px;color:#2f6fbc;background:#e8f2ff;border-radius:50%}.avatar svg{width:25px;height:25px;fill:currentColor;stroke:none}.user-main,.user-metric,.user-address{display:grid;gap:4px;height:58px;align-content:center;padding:0 14px;border-left:1px solid #e5e7eb}.user-main{border-left:none}.user-main strong,.user-address strong{color:#10233f;font-size:15px}.user-main span,.user-metric span,.user-address span{color:#53647c;font-size:12px}.user-metric strong{color:#0079ba;font-size:17px}.user-address{grid-template-columns:1fr auto}.user-address span,.user-address strong{grid-column:1}.user-address button{grid-column:2;grid-row:1/span 2;color:#53647c;background:transparent;border:none}.user-address svg{width:18px;height:18px}.logout-button{height:58px;display:flex;align-items:center;justify-content:center;gap:7px;color:#10233f;background:#fff;border:none;border-left:1px solid #e5e7eb;font-size:14px}.logout-button svg{width:18px;height:18px}.status-content{min-height:100vh;padding:90px 12px 20px 260px}.hero-card,.status-card,.detail-card,.check-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;box-shadow:0 10px 30px rgba(15,23,42,.06)}.hero-card{position:relative;height:132px;display:flex;align-items:center;margin-bottom:18px;padding:0 28px;overflow:hidden}.hero-card h2{margin:0 0 12px;color:#10233f;font-size:30px;font-weight:900}.hero-card p{margin:0;color:#53647c}.campus-line{position:absolute;left:340px;right:280px;bottom:-18px;height:116px;opacity:.3;border-top:1px solid #b9d8f0;border-radius:50%}.campus-line:before,.campus-line:after{position:absolute;content:'';border-top:1px solid #c7dff4;border-radius:50%}.campus-line:before{inset:28px -70px auto 60px;height:80px}.campus-line:after{inset:56px -100px auto 110px;height:90px}.refresh-button{position:absolute;right:34px;top:50%;height:42px;display:flex;align-items:center;gap:8px;padding:0 22px;color:#005bd1;background:#fff;border:1px solid #005bd1;border-radius:6px;font-weight:800;transform:translateY(-50%)}.refresh-button:disabled{opacity:.7}.refresh-button svg{width:18px;height:18px}.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:18px}.status-card{min-height:150px;display:flex;align-items:center;gap:24px;padding:0 24px}.round{width:72px;height:72px;display:grid;place-items:center;flex:0 0 72px;border-radius:50%}.round svg{width:40px;height:40px}.backend .round,.block .round{color:#005bd1;background:#e8f2ff}.ganache .round{color:#16a34a;background:#dcfce7}.stats .round{color:#6d28d9;background:#ede9fe}.status-card h3{margin:0 0 14px;color:#10233f;font-size:18px}.status-card strong{display:flex;align-items:center;gap:10px;margin-bottom:16px;color:#16a34a;font-size:17px}.status-card strong i,.ok-dot{width:12px;height:12px;display:inline-block;background:#16a34a;border-radius:50%}.status-card b{display:block;margin-bottom:16px;color:#005bd1;font-size:28px}.status-card p{margin:9px 0;color:#53647c}.stats p{display:flex;justify-content:space-between;gap:26px}.stats b{display:inline;margin:0;font-size:22px}.main-grid{display:grid;grid-template-columns:minmax(680px,1fr) 520px;gap:18px}.detail-card,.check-card{padding:20px 18px}.detail-card h2,.check-card h2{margin:0 0 16px;color:#10233f;font-size:18px}.detail-card table{width:100%;border-collapse:collapse;table-layout:fixed;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}.detail-card th,.detail-card td{height:42px;padding:0 14px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px}.detail-card th{background:#f9fafb;color:#53647c}.detail-card th:first-child,.detail-card td:first-child{width:190px}.detail-card td{color:#10233f}.detail-card em{color:#53647c;font-style:normal}.detail-card code{display:inline-block;max-width:520px;padding:4px 6px;color:#10233f;background:#fbfdff;border:1px solid #dce4ef;border-radius:4px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}.detail-card td button{width:22px;height:22px;margin-left:8px;color:#53647c;background:transparent;border:none;vertical-align:middle}.detail-card td button svg{width:16px;height:16px}.health-strip{display:grid;grid-template-columns:1fr 1fr;margin-top:18px;border:1px solid #e5e7eb;border-radius:8px}.health-strip div{display:grid;grid-template-columns:58px 1fr;column-gap:16px;align-items:center;padding:18px 26px}.health-strip div+div{border-left:1px solid #e5e7eb}.circle{grid-row:1/3;width:54px;height:54px;display:grid;place-items:center;border-radius:50%}.circle svg{width:30px;height:30px}.circle.success{color:#16a34a;background:#dcfce7}.circle.link{color:#005bd1;background:#dbeafe}.health-strip p{margin:0 0 6px;color:#53647c}.health-strip strong{color:#16a34a;font-size:17px}.check-card{min-height:524px}.check-item{display:grid;grid-template-columns:56px 1fr 150px 40px;align-items:center;min-height:94px;margin-bottom:12px;padding:0 14px;border:1px solid #e5e7eb;border-radius:8px}.check-item>span{width:46px;height:46px;display:grid;place-items:center;color:#16a34a;background:#dcfce7;border-radius:50%}.check-item svg{width:30px;height:30px}.check-item strong{display:block;margin-bottom:8px;color:#10233f}.check-item p{margin:0;color:#53647c}.check-item time{color:#53647c;text-align:right}.check-item b{color:#16a34a;text-align:right}.all-checks{width:100%;height:48px;display:flex;align-items:center;justify-content:center;gap:10px;color:#005bd1;background:#fff;border:1px solid #e5e7eb;border-radius:8px;font-weight:800}.all-checks svg{width:18px;height:18px}
.summary-grid .status-card{gap:18px;padding:0 20px}.summary-grid .round{width:66px;height:66px;flex-basis:66px}.summary-grid .round svg{width:36px;height:36px}.summary-grid h3{font-size:17px;white-space:nowrap}.status-card.block p{font-size:13px}
</style>
