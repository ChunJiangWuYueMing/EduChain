<template>
  <main class="wallet-page">
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
      <h1>我的钱包</h1>
      <div class="header-actions">
        <button class="icon-button" type="button" aria-label="搜索"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg></button>
        <div class="chain-status"><span>链状态</span><span class="status-dot"></span><strong>已连接</strong></div>
        <section class="user-card" aria-label="当前用户">
          <div class="avatar"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg></div>
          <div class="user-main"><strong>{{ auth.user?.name || '--' }}</strong><span>学号：{{ auth.user?.student_id || '--' }}</span></div>
          <div class="user-metric"><span>EDU 余额</span><strong>{{ balance }}</strong></div>
          <div class="user-address"><span>地址</span><strong>{{ truncate(auth.user?.eth_address) }}</strong><button type="button" aria-label="复制地址"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></div>
          <button class="logout-button" type="button" @click="handleLogout"><svg viewBox="0 0 24 24"><path d="M10 17 15 12l-5-5" /><path d="M15 12H3" /><path d="M21 19V5a2 2 0 0 0-2-2H6" /></svg>退出</button>
        </section>
      </div>
    </header>

    <section class="wallet-content">
      <p class="subtitle">查看 EDU 余额与链上通证交易历史</p>
      <section class="summary-grid">
        <article class="balance-card">
          <div><span>当前 EDU 余额</span><strong>{{ balance }} <em>EDU</em></strong><p><i></i> 链上实时余额</p></div>
          <svg viewBox="0 0 24 24"><path d="M4 7h15a2 2 0 0 1 2 2v10H4a2 2 0 0 1-2-2V5a2 2 0 0 0 2 2Z" /><path d="M16 13h4" /></svg>
        </article>
        <article class="info-card"><span class="round user"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg></span><p>用户名</p><strong>{{ auth.user?.name || '--' }}</strong><small>学号：{{ auth.user?.student_id || '--' }}</small></article>
        <article class="info-card"><span class="round link"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l2.2-2.2a5 5 0 0 0-7.08-7.08l-1.26 1.26" /><path d="M14 11a5 5 0 0 0-7.54-.54l-2.2 2.2a5 5 0 0 0 7.08 7.08l1.26-1.26" /></svg></span><p>钱包地址</p><strong>{{ truncate(auth.user?.eth_address) }}</strong><small>以太坊兼容网络</small></article>
        <article class="info-card"><span class="round gift"><svg viewBox="0 0 24 24"><path d="M20 12v10H4V12" /><path d="M2 7h20v5H2z" /><path d="M12 22V7" /><path d="M12 7H7.5a2.5 2.5 0 1 1 0-5C11 2 12 7 12 7Z" /><path d="M12 7h4.5a2.5 2.5 0 1 0 0-5C13 2 12 7 12 7Z" /></svg></span><p>账户权益</p><strong>注册奖励已领取</strong><small class="green">+100 EDU</small></article>
      </section>

      <section class="wallet-grid">
        <article class="table-card">
          <div class="table-toolbar">
            <label>交易类型<select v-model="typeFilter"><option value="all">全部类型</option><option value="in">收入</option><option value="out">支出</option><option value="mint">铸造</option><option value="burn">销毁</option></select></label>
            <button type="button" @click="loadWallet"><svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-2.64-6.36" /><path d="M21 4v6h-6" /></svg>刷新</button>
          </div>
          <table>
            <colgroup>
              <col class="col-type" />
              <col class="col-amount" />
              <col class="col-address" />
              <col class="col-address" />
              <col class="col-block" />
              <col class="col-hash" />
              <col class="col-time" />
            </colgroup>
            <thead><tr><th>类型</th><th>数量 EDU</th><th>From 地址</th><th>To 地址</th><th>区块号</th><th>交易哈希</th><th>时间</th></tr></thead>
            <tbody>
              <tr v-for="tx in filteredTransactions" :key="tx.hash">
                <td><span class="tx-type" :class="tx.kind"><i>{{ tx.arrow }}</i>{{ tx.label }}</span></td>
                <td :class="tx.amount > 0 ? 'amount-in' : 'amount-out'">{{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}</td>
                <td>{{ tx.from }} <button type="button" aria-label="复制"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td>
                <td>{{ tx.to }} <button type="button" aria-label="复制"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td>
                <td>{{ tx.block }}</td><td>{{ tx.hash }} <button type="button" aria-label="复制"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2" /><rect x="4" y="4" width="11" height="11" rx="2" /></svg></button></td><td>{{ tx.time }}</td>
              </tr>
              <tr v-if="filteredTransactions.length === 0"><td colspan="7">暂无链上交易记录</td></tr>
            </tbody>
          </table>
          <footer><label>每页显示：<select><option>50</option></select></label><div><button class="active">1</button></div><span>共 {{ filteredTransactions.length }} 条</span></footer>
        </article>
        <aside class="stats-card">
          <h2>近期统计</h2><p class="month">链上实时数据</p>
          <div class="stat-item income"><i>↓</i><span>累计收入</span><strong>+{{ incomeTotal }} <em>EDU</em></strong><small>{{ incomeCount }} 笔交易</small></div>
          <div class="stat-item expense"><i>↑</i><span>累计支出</span><strong>-{{ expenseTotal }} <em>EDU</em></strong><small>{{ expenseCount }} 笔交易</small></div>
          <div class="stat-item count"><i>▤</i><span>最近交易数</span><strong>{{ transactions.length }}</strong><small>最多展示 50 笔</small></div>
          <form class="transfer-form" @submit.prevent="handleTransfer">
            <h3>EDU 转账</h3>
            <input v-model.trim="transfer.to" placeholder="接收方 0x 地址" required />
            <input v-model.number="transfer.amount" type="number" min="1" step="1" placeholder="数量" required />
            <button type="submit" :disabled="transferring">{{ transferring ? '转账中...' : '确认转账' }}</button>
            <p>{{ transferMessage }}</p>
          </form>
        </aside>
      </section>
      <div class="bottom-tip"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01" /><path d="M11 12h1v4h1" /></svg>提示：EDU 用于购买资料、支付服务费用及参与平台激励，所有交易记录均上链可追溯。</div>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { truncate } from '@/utils/api'
import { useAuthStore } from '@/stores/auth'
import logoUrl from '@/assets/images/swjtu-logo-white.png'
import sidebarArtUrl from '@/assets/images/educhain_white_logo.png'

const router = useRouter()
const auth = useAuthStore()
const typeFilter = ref('all')
const balance = ref(0)
const transactions = ref([])
const transferring = ref(false)
const transferMessage = ref('')
const transfer = reactive({ to: '', amount: 1 })
const navItems = [
  { label: '资料市场', active: false, path: '/market', icon: '<svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h5"/><path d="M10 13h6"/><path d="M10 17h6"/></svg>' },
  { label: '上传资料', active: false, path: '/upload', icon: '<svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/><path d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 0-8"/></svg>' },
  { label: '文件验证', active: false, path: '/verify', icon: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>' },
  { label: '我的钱包', active: true, path: '/wallet', icon: '<svg viewBox="0 0 24 24"><path d="M4 7h15a2 2 0 0 1 2 2v10H4a2 2 0 0 1-2-2V5a2 2 0 0 0 2 2Z"/><path d="M16 13h4"/></svg>' },
  { label: '审计追溯', active: false, path: '/audit', icon: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><circle cx="11" cy="15" r="2"/><path d="m13 17 3 3"/></svg>' },
  { label: '系统状态', active: false, path: '/status', icon: '<svg viewBox="0 0 24 24"><path d="M3 4h18v14H3z"/><path d="M8 22h8"/><path d="M12 18v4"/><path d="m7 13 3-3 2 2 4-5"/></svg>' },
]
const filteredTransactions = computed(() => typeFilter.value === 'all' ? transactions.value : transactions.value.filter((tx) => tx.group === typeFilter.value || tx.kind === typeFilter.value))
const incomeTotal = computed(() => transactions.value.filter((tx) => tx.amount > 0).reduce((sum, tx) => sum + tx.amount, 0))
const expenseTotal = computed(() => Math.abs(transactions.value.filter((tx) => tx.amount < 0).reduce((sum, tx) => sum + tx.amount, 0)))
const incomeCount = computed(() => transactions.value.filter((tx) => tx.amount > 0).length)
const expenseCount = computed(() => transactions.value.filter((tx) => tx.amount < 0).length)

async function loadWallet() {
  transferMessage.value = ''
  try {
    const [balanceRes, historyRes] = await Promise.all([
      api.get('/api/token/balance'),
      api.get('/api/token/history'),
    ])
    balance.value = balanceRes.data.balance
    auth.user.edu_balance = balance.value
    transactions.value = (historyRes.data.transactions || []).map((tx) => {
      const outgoing = tx.type === 'send' || tx.type === 'burn'
      return {
        kind: tx.type,
        label: { mint: '铸造 (Mint)', receive: '接收 (Receive)', send: '发送 (Send)', burn: '销毁 (Burn)' }[tx.type] || tx.type,
        arrow: outgoing ? '↑' : '↓',
        amount: outgoing ? -Number(tx.amount) : Number(tx.amount),
        from: truncate(tx.from),
        to: truncate(tx.to),
        block: tx.block,
        hash: truncate(tx.tx_hash),
        time: '--',
        group: outgoing ? 'out' : 'in',
      }
    })
  } catch (error) {
    transferMessage.value = error.message || '钱包数据加载失败'
  }
}

async function handleTransfer() {
  transferring.value = true
  transferMessage.value = ''
  try {
    const res = await api.post('/api/token/transfer', {
      to_address: transfer.to,
      amount: Number(transfer.amount),
    })
    await loadWallet()
    transferMessage.value = `转账成功：${truncate(res.data.tx_hash)}`
  } catch (error) {
    transferMessage.value = error.message || '转账失败'
  } finally {
    transferring.value = false
  }
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

onMounted(loadWallet)
</script>

<style scoped>
.wallet-page{min-width:1200px;min-height:100vh;overflow-x:hidden;color:var(--text-primary);background:#f4f7fa}svg{fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}button,select{font:inherit}button{cursor:pointer}.app-sidebar{position:fixed;inset:0 auto 0 0;z-index:20;width:248px;overflow:hidden;background:linear-gradient(180deg,#003a70 0%,#002f60 48%,#00284f 100%);box-shadow:8px 0 28px rgba(0,39,82,.2)}.sidebar-brand{padding:34px 20px 26px}.sidebar-brand img{width:210px;height:78px;object-fit:contain;object-position:left center}.sidebar-brand p{margin:14px 0 0;color:rgba(255,255,255,.86);font-size:16px;font-weight:600}.sidebar-nav{position:relative;z-index:2;display:grid;gap:10px;padding:0 8px}.nav-item{display:flex;align-items:center;gap:15px;height:60px;padding:0 22px;color:rgba(255,255,255,.88);background:transparent;border:1px solid transparent;border-radius:6px;font-size:16px;font-weight:700;text-align:left}.nav-item:disabled{cursor:default}.nav-item.active{color:#fff;background:linear-gradient(135deg,#0079ba 0%,#005f92 100%);border-color:rgba(255,255,255,.08);box-shadow:0 12px 24px rgba(0,36,90,.22)}.nav-item span,.nav-item :deep(svg){width:24px;height:24px;flex:0 0 24px}.nav-item :deep(svg){fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}.sidebar-watermark{position:absolute;z-index:1;width:340px;height:340px;right:-118px;bottom:148px;object-fit:contain;opacity:.1;pointer-events:none;transform:rotate(-10deg);filter:drop-shadow(0 22px 42px rgba(0,0,0,.16))}.sidebar-bridge{position:absolute;left:-52px;right:0;bottom:96px;height:210px;opacity:.2;border-top:1px solid rgba(209,232,255,.35);border-bottom:1px solid rgba(209,232,255,.25);border-radius:50%;transform:rotate(-8deg)}.sidebar-bridge:before,.sidebar-bridge:after{position:absolute;left:-80px;width:380px;height:120px;content:'';border-top:1px solid rgba(209,232,255,.28);border-radius:50%}.sidebar-bridge:before{top:40px}.sidebar-bridge:after{top:84px}.chain-local{position:absolute;left:30px;right:26px;bottom:30px;display:flex;align-items:center;gap:12px;color:#fff;font-size:16px}.chain-local svg{width:18px;height:18px;margin-left:auto}.status-dot{display:inline-block;width:12px;height:12px;border-radius:50%;background:#16a34a;box-shadow:0 0 0 4px rgba(22,163,74,.12)}.app-header{position:fixed;top:0;left:248px;right:0;z-index:15;display:flex;align-items:center;justify-content:space-between;height:72px;padding:0 14px 0 30px;background:rgba(255,255,255,.94);border-bottom:1px solid #dce4ef;backdrop-filter:blur(14px)}.app-header h1{margin:0;color:#10233f;font-size:30px;font-weight:800}.header-actions{display:flex;align-items:center;gap:16px}.icon-button{width:44px;height:44px;display:grid;place-items:center;color:#10233f;background:#fff;border:1px solid #dce4ef;border-radius:8px}.icon-button svg{width:22px;height:22px}.chain-status{display:flex;align-items:center;gap:10px;padding-left:16px;border-left:1px solid #dce4ef;color:#53647c;font-size:14px}.chain-status strong{color:#10233f}.user-card{display:grid;grid-template-columns:48px 126px 100px 170px 82px;align-items:center;min-height:58px;overflow:hidden;background:#fff;border:1px solid #dce4ef;border-radius:8px;box-shadow:0 10px 26px rgba(15,23,42,.06)}.avatar{width:38px;height:38px;display:grid;place-items:center;margin-left:12px;color:#2f6fbc;background:#e8f2ff;border-radius:50%}.avatar svg{width:25px;height:25px;fill:currentColor;stroke:none}.user-main,.user-metric,.user-address{display:grid;gap:4px;height:58px;align-content:center;padding:0 14px;border-left:1px solid #e5e7eb}.user-main{border-left:none}.user-main strong,.user-address strong{color:#10233f;font-size:15px}.user-main span,.user-metric span,.user-address span{color:#53647c;font-size:12px}.user-metric strong{color:#0079ba;font-size:17px}.user-address{grid-template-columns:1fr auto}.user-address span,.user-address strong{grid-column:1}.user-address button{grid-column:2;grid-row:1/span 2;color:#53647c;background:transparent;border:none}.user-address svg{width:18px;height:18px}.logout-button{height:58px;display:flex;align-items:center;justify-content:center;gap:7px;color:#10233f;background:#fff;border:none;border-left:1px solid #e5e7eb;font-size:14px}.logout-button svg{width:18px;height:18px}
.wallet-content{min-height:100vh;padding:96px 22px 18px 270px}.subtitle{margin:0 0 24px;color:#53647c;font-size:16px}.summary-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:14px;margin-bottom:22px}.balance-card,.info-card,.table-card,.stats-card,.bottom-tip{background:#fff;border:1px solid #e5e7eb;border-radius:8px;box-shadow:0 10px 30px rgba(15,23,42,.06)}.balance-card{position:relative;min-height:190px;display:flex;align-items:center;padding:0 26px;overflow:hidden}.balance-card strong{display:block;margin:18px 0;color:#005bd1;font-size:64px;line-height:1;font-weight:900}.balance-card em{color:#53647c;font-size:24px;font-style:normal;font-weight:500}.balance-card span{font-weight:800}.balance-card p{margin:0;color:#53647c}.balance-card i{display:inline-block;width:12px;height:12px;margin-right:10px;background:#16a34a;border-radius:50%}.balance-card svg{position:absolute;right:55px;width:120px;height:120px;color:#dbeafe;opacity:.7}.info-card{min-height:190px;padding:30px 26px}.round{width:58px;height:58px;display:grid;place-items:center;border-radius:50%;margin-bottom:24px}.round svg{width:30px;height:30px}.round.user,.round.link{color:#1d66d2;background:#e8f2ff}.round.gift{color:#16a34a;background:#dcfce7}.info-card p{margin:0 0 12px;color:#53647c}.info-card strong{display:block;margin-bottom:12px;font-size:18px}.info-card small{color:#53647c;font-size:14px}.info-card small.green{color:#16a34a;font-size:16px;font-weight:800}.wallet-grid{display:grid;grid-template-columns:minmax(760px,1fr) 220px;gap:14px}.table-card{overflow:hidden}.table-toolbar{height:76px;display:flex;align-items:center;gap:18px;padding:0 20px;border-bottom:1px solid #e5e7eb}.table-toolbar label{display:flex;align-items:center;gap:12px;color:#53647c}.table-toolbar select{width:190px;height:42px;padding:0 14px;border:1px solid #dce4ef;border-radius:7px;background:#fff;color:#10233f}.table-toolbar button{height:42px;display:flex;align-items:center;gap:8px;padding:0 18px;color:#0079ba;background:#fff;border:1px solid #dce4ef;border-radius:7px;font-weight:800}.table-toolbar svg{width:18px;height:18px}table{width:100%;border-collapse:collapse;table-layout:fixed}.col-type{width:190px}.col-amount{width:90px}.col-address{width:130px}.col-block{width:95px}.col-hash{width:135px}.col-time{width:145px}th,td{height:62px;padding:0 14px;border-bottom:1px solid #e5e7eb;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:14px}th{height:52px;background:#f9fafb;color:#10233f;font-weight:800}.tx-type{display:inline-flex;align-items:center;gap:8px;padding:5px 9px;border-radius:999px;font-weight:800}.tx-type i{width:28px;height:28px;display:grid;place-items:center;border-radius:50%;font-style:normal;font-size:16px}.mint,.receive{color:#16a34a;background:#dcfce7}.mint i,.receive i{background:#dcfce7}.send{color:#dc2626;background:#fee2e2}.send i{background:#fee2e2}.burn{color:#f97316;background:#ffedd5}.burn i{background:#ffedd5}.amount-in{color:#16a34a;font-weight:900}.amount-out{color:#dc2626;font-weight:900}td button{width:22px;height:22px;margin-left:4px;color:#53647c;background:transparent;border:none;vertical-align:middle}td button svg{width:16px;height:16px}.table-card footer{height:72px;display:flex;align-items:center;gap:24px;padding:0 18px;color:#53647c}.table-card footer label{margin-right:auto}.table-card footer select{height:34px;border:1px solid #dce4ef;border-radius:6px;background:#fff}.table-card footer div{display:flex;align-items:center;gap:8px}.table-card footer button{width:34px;height:34px;border:1px solid #dce4ef;border-radius:6px;background:#fff;color:#10233f;font-weight:800}.table-card footer button.active{color:#fff;background:#0079ba;border-color:#0079ba}.stats-card{padding:26px 14px}.stats-card h2{margin:0 0 18px;font-size:18px}.month{margin:0 0 24px;color:#53647c}.stat-item{min-height:116px;padding:20px 14px;margin-bottom:14px;border:1px solid #e5e7eb;border-radius:8px}.stat-item i{float:left;width:34px;height:34px;display:grid;place-items:center;margin-right:14px;border-radius:50%;font-style:normal;font-size:22px}.stat-item span{display:block;color:#53647c}.stat-item strong{display:block;margin:8px 0;font-size:24px}.stat-item em{font-size:14px;font-style:normal}.stat-item small{color:#53647c}.income{color:#16a34a}.income i{background:#dcfce7}.expense{color:#dc2626}.expense i{background:#fee2e2}.count{color:#005bd1}.count i{background:#dbeafe}.updated{margin:20px 0 0;color:#8a97aa;font-size:13px}.bottom-tip{min-height:44px;display:flex;align-items:center;gap:10px;margin-top:16px;padding:0 18px;color:#53647c;background:#edf7ff;border-color:#c7dff4;font-size:13px}.bottom-tip svg{width:18px;height:18px;color:#0079ba;fill:#0079ba}
.transfer-form{display:grid;gap:9px;margin-top:12px;padding-top:16px;border-top:1px solid #e5e7eb}.transfer-form h3{margin:0 0 4px;color:#10233f;font-size:15px}.transfer-form input{height:38px;padding:0 10px;border:1px solid #dce4ef;border-radius:6px}.transfer-form button{height:40px;color:#fff;background:#005bd1;border:0;border-radius:6px;font-weight:800}.transfer-form button:disabled{opacity:.65}.transfer-form p{min-height:18px;margin:0;color:#53647c;font-size:12px}
</style>
