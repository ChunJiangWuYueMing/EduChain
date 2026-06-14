<template>
  <main class="status-page">
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
          <div><h3>后端状态</h3><strong :class="{ failed: !backendRunning }"><i></i> {{ backendRunning ? '运行中' : '不可用' }}</strong><p>{{ backendRunning ? '健康检查响应正常' : system.error || '等待健康检查' }}</p></div>
        </article>
        <article class="status-card ganache">
          <span class="round"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2" /><circle cx="5" cy="19" r="2" /><circle cx="19" cy="19" r="2" /><path d="m11 7-5 10" /><path d="m13 7 5 10" /><path d="M7 19h10" /></svg></span>
          <div><h3>Ganache 连接状态</h3><strong :class="{ failed: !system.health.ganacheConnected }"><i></i> {{ system.health.ganacheConnected ? '已连接' : '未连接' }}</strong><p>{{ system.health.ganacheConnected ? '区块链节点连接正常' : '请检查节点与合约配置' }}</p></div>
        </article>
        <article class="status-card block">
          <span class="round"><svg viewBox="0 0 24 24"><path d="m12 2 8 4.5v9L12 20l-8-4.5v-9Z" /><path d="M12 11 4 6.5" /><path d="m12 11 8-4.5" /><path d="M12 11v9" /></svg></span>
          <div><h3>当前区块号</h3><b>{{ system.health.blockNumber ?? '--' }}</b><p>状态更新时间：{{ lastCheckedTime }}</p></div>
        </article>
        <article class="status-card stats">
          <span class="round"><svg viewBox="0 0 24 24"><path d="M5 20V11" /><path d="M12 20V5" /><path d="M19 20v-8" /><path d="M3 20h18" /></svg></span>
          <div><h3>数据统计</h3><p>资料总数 <b>{{ system.health.materialCount }}</b></p><p>下载记录总数 <b>{{ system.health.downloadCount }}</b></p></div>
        </article>
      </section>

      <section class="main-grid">
        <article class="detail-card">
          <h2>系统详情</h2>
          <table>
            <thead><tr><th>项目</th><th>详情</th></tr></thead>
            <tbody>
              <tr><td>后端服务</td><td><span class="ok-dot" :class="{ failed: !backendRunning }"></span>{{ backendRunning ? '运行中' : '不可用' }}</td></tr>
              <tr><td>Ganache URL</td><td><code>{{ system.health.ganacheUrl || '--' }}</code><button type="button" aria-label="复制 Ganache URL" @click="copyValue(system.health.ganacheUrl, 'Ganache URL')"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td></tr>
              <tr v-for="item in contractRows" :key="item.label"><td>{{ item.label }}</td><td><code>{{ item.value }}</code><button type="button" :aria-label="`复制${item.label}`" @click="copyValue(item.value, item.label)"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td></tr>
              <tr><td>网络</td><td>{{ networkName }}</td></tr>
              <tr><td>链 ID</td><td>{{ system.health.chainId ?? '--' }}</td></tr>
            </tbody>
          </table>

          <div class="health-strip">
            <div><span class="circle success" :class="{ failed: !contractsReady }"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /><path d="m9 12 2 2 4-4" /></svg></span><p>合约部署状态</p><strong :class="{ failed: !contractsReady }">{{ contractsReady ? '合约地址完整' : '合约配置不完整' }}</strong></div>
            <div><span class="circle link" :class="{ failed: !system.connected }"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l2.2-2.2a5 5 0 0 0-7.08-7.08l-1.26 1.26" /><path d="M14 11a5 5 0 0 0-7.54-.54l-2.2 2.2a5 5 0 0 0 7.08 7.08l1.26-1.26" /></svg></span><p>链连接状态</p><strong :class="{ failed: !system.connected }">{{ system.connected ? '节点连接正常' : '节点连接异常' }}</strong></div>
          </div>
        </article>

        <aside class="check-card">
          <h2>最近检查结果</h2>
          <div v-for="record in checkRecords" :key="record.title" class="check-item" :class="{ failed: !record.passed }">
            <span><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path :d="record.passed ? 'm8 12 3 3 5-6' : 'M9 9l6 6m0-6-6 6'" /></svg></span>
            <div><strong>{{ record.title }}</strong><p>{{ record.desc }}</p></div>
            <time>{{ record.time }}</time>
            <b>{{ record.passed ? '通过' : '失败' }}</b>
          </div>
          <button class="all-checks" type="button" @click="copyDiagnostics">复制诊断摘要 <svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button>
        </aside>
      </section>
    </section>
    <div v-if="toast" class="status-toast" role="status">{{ toast }}</div>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useSystemStore } from '@/stores/system'
import { copyText } from '@/utils/clipboard'
import { formatTime } from '@/utils/api'

const system = useSystemStore()
const toast = ref('')
const refreshing = computed(() => system.loading)
const backendRunning = computed(() => system.health.status === 'running')
const contractsReady = computed(() => ['edu_token', 'material_registry', 'download_log']
  .every((key) => Boolean(system.health.contracts?.[key])))
const lastCheckedTime = computed(() => formatTime(system.lastCheckedAt))
const networkName = computed(() => system.health.ganacheUrl?.includes('127.0.0.1') || system.health.ganacheUrl?.includes('localhost')
  ? 'Ganache（Local）'
  : 'EVM 兼容网络')
const contractRows = computed(() => [
  { label: 'Deployer 地址', value: system.health.deployer || '--' },
  { label: 'EduToken 合约地址', value: system.health.contracts?.edu_token || '--' },
  { label: 'MaterialRegistry 合约地址', value: system.health.contracts?.material_registry || '--' },
  { label: 'DownloadLog 合约地址', value: system.health.contracts?.download_log || '--' },
])
const checkRecords = computed(() => [
  { title: '后端健康检查', desc: backendRunning.value ? '健康检查接口响应正常' : system.error || '接口未响应', time: lastCheckedTime.value, passed: backendRunning.value },
  { title: '区块链连接检查', desc: system.health.ganacheConnected ? `区块高度 ${system.health.blockNumber ?? '--'}` : '节点未连接', time: lastCheckedTime.value, passed: system.health.ganacheConnected },
  { title: '合约配置检查', desc: contractsReady.value ? '三个核心合约地址均已配置' : '存在缺失的合约地址', time: lastCheckedTime.value, passed: contractsReady.value },
])

async function refreshStatus() {
  await system.refresh()
}

async function copyValue(value, label) {
  const copied = value && value !== '--' && await copyText(String(value))
  showToast(copied ? `${label}已复制` : '当前没有可复制的数据')
}

async function copyDiagnostics() {
  const summary = [
    `检查时间：${lastCheckedTime.value}`,
    `后端状态：${backendRunning.value ? '运行中' : '不可用'}`,
    `区块链连接：${system.health.ganacheConnected ? '已连接' : '未连接'}`,
    `链 ID：${system.health.chainId ?? '--'}`,
    `当前区块：${system.health.blockNumber ?? '--'}`,
    `合约配置：${contractsReady.value ? '完整' : '不完整'}`,
    `资料数：${system.health.materialCount}`,
    `下载记录数：${system.health.downloadCount}`,
  ].join('\n')
  const copied = await copyText(summary)
  showToast(copied ? '诊断摘要已复制' : '诊断摘要复制失败')
}

function showToast(message) {
  toast.value = message
  window.clearTimeout(showToast.timer)
  showToast.timer = window.setTimeout(() => {
    toast.value = ''
  }, 1800)
}

onMounted(refreshStatus)
</script>

<style scoped>
.status-page{min-width:1200px;min-height:100vh;overflow-x:hidden;color:var(--text-primary);background:#f4f7fa}svg{fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}button{font:inherit;cursor:pointer}.app-sidebar{position:fixed;inset:0 auto 0 0;z-index:20;width:248px;overflow:hidden;background:linear-gradient(180deg,#003a70 0%,#002f60 48%,#00284f 100%);box-shadow:8px 0 28px rgba(0,39,82,.2)}.sidebar-brand{padding:34px 20px 26px}.sidebar-brand img{width:210px;height:78px;object-fit:contain;object-position:left center}.sidebar-brand p{margin:14px 0 0;color:rgba(255,255,255,.86);font-size:16px;font-weight:600}.sidebar-nav{position:relative;z-index:2;display:grid;gap:10px;padding:0 8px}.nav-item{display:flex;align-items:center;gap:15px;height:60px;padding:0 22px;color:rgba(255,255,255,.88);background:transparent;border:1px solid transparent;border-radius:6px;font-size:16px;font-weight:700;text-align:left}.nav-item.active{color:#fff;background:linear-gradient(135deg,#0079ba 0%,#005f92 100%);border-color:rgba(255,255,255,.08);box-shadow:0 12px 24px rgba(0,36,90,.22)}.nav-item span,.nav-item :deep(svg){width:24px;height:24px;flex:0 0 24px}.nav-item :deep(svg){fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}.sidebar-watermark{position:absolute;z-index:1;width:340px;height:340px;right:-118px;bottom:148px;object-fit:contain;opacity:.1;pointer-events:none;transform:rotate(-10deg);filter:drop-shadow(0 22px 42px rgba(0,0,0,.16))}.sidebar-bridge{position:absolute;left:-52px;right:0;bottom:96px;height:210px;opacity:.2;border-top:1px solid rgba(209,232,255,.35);border-bottom:1px solid rgba(209,232,255,.25);border-radius:50%;transform:rotate(-8deg)}.sidebar-bridge:before,.sidebar-bridge:after{position:absolute;left:-80px;width:380px;height:120px;content:'';border-top:1px solid rgba(209,232,255,.28);border-radius:50%}.sidebar-bridge:before{top:40px}.sidebar-bridge:after{top:84px}.chain-local{position:absolute;left:30px;right:26px;bottom:30px;display:flex;align-items:center;gap:12px;color:#fff;font-size:16px}.chain-local svg{width:18px;height:18px;margin-left:auto}.status-dot{display:inline-block;width:12px;height:12px;border-radius:50%;background:#16a34a;box-shadow:0 0 0 4px rgba(22,163,74,.12)}.app-header{position:fixed;top:0;left:248px;right:0;z-index:15;display:flex;align-items:center;justify-content:space-between;height:72px;padding:0 14px 0 30px;background:rgba(255,255,255,.94);border-bottom:1px solid #dce4ef;backdrop-filter:blur(14px)}.app-header h1{margin:0;color:#10233f;font-size:30px;font-weight:800}.header-actions{display:flex;align-items:center;gap:16px}.icon-button{width:44px;height:44px;display:grid;place-items:center;color:#10233f;background:#fff;border:1px solid #dce4ef;border-radius:8px}.icon-button svg{width:22px;height:22px}.chain-status{display:flex;align-items:center;gap:10px;padding-left:16px;border-left:1px solid #dce4ef;color:#53647c;font-size:14px}.chain-status strong{color:#10233f}.user-card{display:grid;grid-template-columns:48px 126px 100px 170px 82px;align-items:center;min-height:58px;overflow:hidden;background:#fff;border:1px solid #dce4ef;border-radius:8px;box-shadow:0 10px 26px rgba(15,23,42,.06)}.avatar{width:38px;height:38px;display:grid;place-items:center;margin-left:12px;color:#2f6fbc;background:#e8f2ff;border-radius:50%}.avatar svg{width:25px;height:25px;fill:currentColor;stroke:none}.user-main,.user-metric,.user-address{display:grid;gap:4px;height:58px;align-content:center;padding:0 14px;border-left:1px solid #e5e7eb}.user-main{border-left:none}.user-main strong,.user-address strong{color:#10233f;font-size:15px}.user-main span,.user-metric span,.user-address span{color:#53647c;font-size:12px}.user-metric strong{color:#0079ba;font-size:17px}.user-address{grid-template-columns:1fr auto}.user-address span,.user-address strong{grid-column:1}.user-address button{grid-column:2;grid-row:1/span 2;color:#53647c;background:transparent;border:none}.user-address svg{width:18px;height:18px}.logout-button{height:58px;display:flex;align-items:center;justify-content:center;gap:7px;color:#10233f;background:#fff;border:none;border-left:1px solid #e5e7eb;font-size:14px}.logout-button svg{width:18px;height:18px}.status-content{min-height:100vh;padding:90px 12px 20px 260px}.hero-card,.status-card,.detail-card,.check-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;box-shadow:0 10px 30px rgba(15,23,42,.06)}.hero-card{position:relative;height:132px;display:flex;align-items:center;margin-bottom:18px;padding:0 28px;overflow:hidden}.hero-card h2{margin:0 0 12px;color:#10233f;font-size:30px;font-weight:900}.hero-card p{margin:0;color:#53647c}.campus-line{position:absolute;left:340px;right:280px;bottom:-18px;height:116px;opacity:.3;border-top:1px solid #b9d8f0;border-radius:50%}.campus-line:before,.campus-line:after{position:absolute;content:'';border-top:1px solid #c7dff4;border-radius:50%}.campus-line:before{inset:28px -70px auto 60px;height:80px}.campus-line:after{inset:56px -100px auto 110px;height:90px}.refresh-button{position:absolute;right:34px;top:50%;height:42px;display:flex;align-items:center;gap:8px;padding:0 22px;color:#005bd1;background:#fff;border:1px solid #005bd1;border-radius:6px;font-weight:800;transform:translateY(-50%)}.refresh-button:disabled{opacity:.7}.refresh-button svg{width:18px;height:18px}.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:18px}.status-card{min-height:150px;display:flex;align-items:center;gap:24px;padding:0 24px}.round{width:72px;height:72px;display:grid;place-items:center;flex:0 0 72px;border-radius:50%}.round svg{width:40px;height:40px}.backend .round,.block .round{color:#005bd1;background:#e8f2ff}.ganache .round{color:#16a34a;background:#dcfce7}.stats .round{color:#6d28d9;background:#ede9fe}.status-card h3{margin:0 0 14px;color:#10233f;font-size:18px}.status-card strong{display:flex;align-items:center;gap:10px;margin-bottom:16px;color:#16a34a;font-size:17px}.status-card strong i,.ok-dot{width:12px;height:12px;display:inline-block;background:#16a34a;border-radius:50%}.status-card b{display:block;margin-bottom:16px;color:#005bd1;font-size:28px}.status-card p{margin:9px 0;color:#53647c}.stats p{display:flex;justify-content:space-between;gap:26px}.stats b{display:inline;margin:0;font-size:22px}.main-grid{display:grid;grid-template-columns:minmax(680px,1fr) 520px;gap:18px}.detail-card,.check-card{padding:20px 18px}.detail-card h2,.check-card h2{margin:0 0 16px;color:#10233f;font-size:18px}.detail-card table{width:100%;border-collapse:collapse;table-layout:fixed;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}.detail-card th,.detail-card td{height:42px;padding:0 14px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px}.detail-card th{background:#f9fafb;color:#53647c}.detail-card th:first-child,.detail-card td:first-child{width:190px}.detail-card td{color:#10233f}.detail-card em{color:#53647c;font-style:normal}.detail-card code{display:inline-block;max-width:520px;padding:4px 6px;color:#10233f;background:#fbfdff;border:1px solid #dce4ef;border-radius:4px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}.detail-card td button{width:22px;height:22px;margin-left:8px;color:#53647c;background:transparent;border:none;vertical-align:middle}.detail-card td button svg{width:16px;height:16px}.health-strip{display:grid;grid-template-columns:1fr 1fr;margin-top:18px;border:1px solid #e5e7eb;border-radius:8px}.health-strip div{display:grid;grid-template-columns:58px 1fr;column-gap:16px;align-items:center;padding:18px 26px}.health-strip div+div{border-left:1px solid #e5e7eb}.circle{grid-row:1/3;width:54px;height:54px;display:grid;place-items:center;border-radius:50%}.circle svg{width:30px;height:30px}.circle.success{color:#16a34a;background:#dcfce7}.circle.link{color:#005bd1;background:#dbeafe}.health-strip p{margin:0 0 6px;color:#53647c}.health-strip strong{color:#16a34a;font-size:17px}.check-card{min-height:524px}.check-item{display:grid;grid-template-columns:56px 1fr 150px 40px;align-items:center;min-height:94px;margin-bottom:12px;padding:0 14px;border:1px solid #e5e7eb;border-radius:8px}.check-item>span{width:46px;height:46px;display:grid;place-items:center;color:#16a34a;background:#dcfce7;border-radius:50%}.check-item svg{width:30px;height:30px}.check-item strong{display:block;margin-bottom:8px;color:#10233f}.check-item p{margin:0;color:#53647c}.check-item time{color:#53647c;text-align:right}.check-item b{color:#16a34a;text-align:right}.all-checks{width:100%;height:48px;display:flex;align-items:center;justify-content:center;gap:10px;color:#005bd1;background:#fff;border:1px solid #e5e7eb;border-radius:8px;font-weight:800}.all-checks svg{width:18px;height:18px}
.summary-grid .status-card{gap:18px;padding:0 20px}.summary-grid .round{width:66px;height:66px;flex-basis:66px}.summary-grid .round svg{width:36px;height:36px}.summary-grid h3{font-size:17px;white-space:nowrap}.status-card.block p{font-size:13px}
.status-page{min-width:0;min-height:calc(100vh - var(--header-height));overflow:visible}.status-content{min-height:calc(100vh - var(--header-height));padding:16px}.status-card strong.failed,.health-strip strong.failed,.check-item.failed b{color:#dc2626}.status-card strong.failed i,.ok-dot.failed{background:#dc2626}.circle.failed,.check-item.failed>span{color:#dc2626;background:#fee2e2}.status-toast{position:fixed;left:50%;bottom:28px;z-index:50;transform:translateX(-50%);padding:10px 18px;color:#fff;background:rgba(16,35,63,.92);border-radius:999px;box-shadow:0 10px 30px rgba(15,23,42,.18);font-size:14px}
@media (max-width:1450px){.main-grid{grid-template-columns:1fr}.check-card{min-height:0}.detail-card code{max-width:calc(100vw - 560px)}}
</style>
