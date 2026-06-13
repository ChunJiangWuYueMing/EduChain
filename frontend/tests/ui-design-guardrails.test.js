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

test('SWJTU visual design assets and page titles remain present', () => {
  for (const page of [login, market, upload, verify, wallet, audit, status]) {
    assert.match(page, /swjtu-logo-white\.png/)
  }
  assert.match(login, /校园学习资料可信交换平台/)
  assert.match(market, /资料市场/)
  assert.match(upload, /上传资料/)
  assert.match(verify, /文件验证/)
  assert.match(wallet, /我的钱包/)
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
  assert.match(status, /\/api\/health/)
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
