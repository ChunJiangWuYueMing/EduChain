const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

test('frontend has a restrained product-dashboard refinement layer', () => {
  assert.match(html, /Product dashboard refinement layer/);
  assert.match(html, /\.page-hero h1\s*{[^}]*font-size:\s*28px;/s);
  assert.doesNotMatch(html, /font-size:\s*clamp\(34px,\s*4\.1vw,\s*56px\)/);
});

test('trust workflows use compact dashboard page shells', () => {
  assert.match(html, /class="trust-layout"/);
  assert.match(html, /class="wallet-page-header"/);
  assert.match(html, /class="step-list"/);
});

test('copy is localized for a Chinese campus credit system', () => {
  assert.match(html, /资料广场/);
  assert.match(html, /发布资料/);
  assert.match(html, /真伪校验/);
  assert.match(html, /积分账户/);
  assert.match(html, /EDU 积分/);
  assert.match(html, /文件指纹（SHA-256）/);
  assert.match(html, /内容相似度（SimHash）/);
  assert.doesNotMatch(html, /EduChain Dashboard/);
  assert.doesNotMatch(html, />我的钱包</);
});

test('verification audit wallet and status pages expose practical empty states', () => {
  assert.match(html, /暂无校验结果/);
  assert.match(html, /请输入资料 ID 并上传待校验文件/);
  assert.match(html, /上传资料获得积分/);
  assert.match(html, /下载资料消耗积分/);
  assert.match(html, /同学之间可以转账/);
  assert.match(html, /审计记录/);
  assert.match(html, /服务项/);
  assert.match(html, /当前值/);
  assert.match(html, /状态/);
});

test('market filters are wired once to avoid duplicate refreshes', () => {
  const count = (pattern) => (html.match(new RegExp(pattern, 'g')) || []).length;

  assert.equal(count("searchInput\\.addEventListener\\('input'"), 1);
  assert.equal(count("courseFilter\\.addEventListener\\('change'"), 1);
});

test('wallet layout and copy affordances are usable', () => {
  assert.match(html, /\.wallet-main-grid/);
  assert.match(html, /id="btn-copy-wallet-address"/);
  assert.match(html, /copyText\('wallet-address'/);
  assert.match(html, /copyText\('material-id'/);
  assert.doesNotMatch(html, /alert\(\s*`资料详情/);
});

test('verification keyword chips wrap as complete words', () => {
  assert.match(html, /\.keyword-list/);
  assert.match(html, /\.keyword-chip/);
  assert.match(html, /renderKeywordChips\(v\.common_keywords,\s*'badge-blue'\)/);
  assert.doesNotMatch(html, /common_keywords\|\|\[\]\)\.map\(k => `<span class="badge badge-blue" style="margin:1px;">/);
});

test('mobile navigation is compact instead of a large two-column block', () => {
  assert.match(html, /Mobile compact navigation fix/);
  assert.match(html, /overflow-x:\s*auto;/);
  assert.match(html, /grid-template-columns:\s*none\s*!important;/);
  assert.match(html, /min-height:\s*34px\s*!important;/);
});

test('mobile account actions stay in the top bar with app-scale typography', () => {
  assert.match(html, /Mobile app typography and account bar/);
  assert.match(html, /\.navbar\s*{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s*auto\s*!important;/s);
  assert.match(html, /\.user-area\s*{[^}]*grid-column:\s*2\s*!important;[^}]*grid-row:\s*1\s*!important;/s);
  assert.match(html, /\.nav-links\s*{[^}]*grid-column:\s*1\s*\/\s*-1\s*!important;[^}]*grid-row:\s*2\s*!important;/s);
  assert.match(html, /\.nav-links a,\s*\.nav-links button\s*{[^}]*flex:\s*0\s+0\s+auto\s*!important;[^}]*white-space:\s*nowrap\s*!important;/s);
  assert.match(html, /\.page-hero h1\s*{[^}]*font-size:\s*24px\s*!important;/s);
  assert.match(html, /\.card-header h2,\s*\.section-title\s*{[^}]*font-size:\s*22px\s*!important;/s);
});
