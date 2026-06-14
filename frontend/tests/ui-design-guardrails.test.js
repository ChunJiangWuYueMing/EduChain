const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const frontendRoot = path.join(__dirname, '..')
const read = (...parts) => fs.readFileSync(path.join(frontendRoot, ...parts), 'utf8')

const index = read('index.html')
const router = read('src', 'router', 'index.js')
const api = read('src', 'utils', 'api.js')
const login = read('src', 'views', 'Login.vue')
const market = read('src', 'views', 'Market.vue')
const upload = read('src', 'views', 'Upload.vue')
const verify = read('src', 'views', 'Verify.vue')
const wallet = read('src', 'views', 'Wallet.vue')
const audit = read('src', 'views', 'Audit.vue')
const status = read('src', 'views', 'Status.vue')
const layout = read('src', 'components', 'AppLayout.vue')
const header = read('src', 'components', 'AppHeader.vue')
const sidebar = read('src', 'components', 'AppSidebar.vue')
const navigation = read('src', 'config', 'navigation.js')
const systemStore = read('src', 'stores', 'system.js')

test('Vite entry mounts the Vue application', () => {
  assert.match(index, /id="app"/)
  assert.match(index, /src="\/src\/main\.js"/)
  assert.doesNotMatch(index, /Product dashboard refinement layer/)
})

test('router keeps all seven designed pages and protects business routes', () => {
  for (const route of ['/login', '/market', '/upload', '/verify', '/wallet', '/audit', '/status']) {
    assert.match(router, new RegExp(`path: '${route}'`))
  }
  assert.match(router, /beforeEach/)
  assert.match(router, /requiresAuth/)
})

test('SWJTU visual design and navigation are owned by one persistent app shell', () => {
  assert.match(login, /swjtu-logo-white\.png/)
  assert.match(sidebar, /swjtu-logo-white\.png/)
  assert.match(layout, /<AppSidebar \/>/)
  assert.match(layout, /<AppHeader \/>/)
  assert.match(layout, /<router-view \/>/)
  assert.match(header, /shell-user-card/)
  assert.match(header, /EDU 余额/)
  assert.match(header, /复制钱包地址/)
  for (const page of [market, upload, verify, wallet, audit, status]) {
    assert.doesNotMatch(page, /<aside class="app-sidebar"/)
    assert.doesNotMatch(page, /<header class="app-header"/)
  }
  for (const route of ['/market', '/upload', '/verify', '/wallet', '/audit', '/status']) {
    assert.match(navigation, new RegExp(`path: '${route}'`))
  }
  for (const title of ['资料市场', '上传资料', '文件验证', '我的钱包', '审计追溯', '系统状态']) {
    assert.match(navigation, new RegExp(title))
  }
  assert.match(login, /校园学习资料可信交换平台/)
  assert.match(market, /资料市场/)
  assert.match(upload, /上传资料/)
  assert.match(audit, /审计追溯/)
  assert.match(status, /系统状态/)
})

test('API helper supports sessions, JSON, forms and file downloads', () => {
  assert.match(api, /credentials: 'include'/)
  assert.match(api, /options\.body instanceof FormData/)
  assert.match(api, /Content-Disposition/)
  assert.match(api, /!res\.ok/)
})

test('designed pages are wired to the real backend API', () => {
  assert.match(login, /auth\.login/)
  assert.match(login, /\/api\/health/)
  assert.match(market, /\/api\/material\/list/)
  assert.match(market, /\/download/)
  assert.match(upload, /\/api\/material\/upload/)
  assert.match(verify, /\/api\/material\/verify/)
  assert.match(wallet, /\/api\/token\/balance/)
  assert.match(wallet, /\/api\/token\/history/)
  assert.match(wallet, /\/api\/token\/transfer/)
  assert.match(audit, /\/api\/audit\/downloads/)
  assert.match(audit, /\/api\/audit\/full/)
  assert.match(status, /useSystemStore/)
  assert.match(systemStore, /\/api\/health/)
})

test('formerly static controls now have real handlers and data flow', () => {
  assert.match(market, /copyValue\(item\.uploader/)
  assert.match(market, /viewAudit/)
  assert.match(upload, /policy_value/)
  assert.match(upload, /rulesOpen/)
  assert.match(verify, /loadMaterial/)
  assert.doesNotMatch(verify, /MAT_20260521_001/)
  assert.match(wallet, /paginatedTransactions/)
  assert.match(wallet, /formatTime\(tx\.timestamp\)/)
  assert.match(audit, /\/api\/audit\/downloads\/all/)
  assert.match(status, /copyDiagnostics/)
})

test('old fixed demo identity and fake workflow delays are removed', () => {
  for (const page of [market, upload, verify, wallet, audit, status]) {
    assert.doesNotMatch(page, /学号：20240001/)
    assert.doesNotMatch(page, /0x8f3A\.\.\.91c2/)
  }
  assert.doesNotMatch(login, /studentId === '20240001'/)
  assert.doesNotMatch(upload, /MAT_20260521_008/)
  assert.doesNotMatch(verify, /verdict: 'tampered'/)
})
