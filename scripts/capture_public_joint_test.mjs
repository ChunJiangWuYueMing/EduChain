import { spawn } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { pathToFileURL } from 'node:url'


const root = path.resolve(import.meta.dirname, '..')
const resultDirArg = process.argv[2]
if (!resultDirArg) {
  throw new Error('Usage: node scripts/capture_public_joint_test.mjs <result-dir>')
}
const resultDir = path.resolve(root, resultDirArg)
const resumeEvidence = process.argv.includes('--resume-evidence')
const results = JSON.parse(
  fs.readFileSync(path.join(resultDir, 'joint_test_results.json'), 'utf8'),
)
const screenshotDir = path.join(resultDir, 'screenshots')
fs.mkdirSync(screenshotDir, { recursive: true })

const baseUrl = results.run.base_url
const materialA = results.materials.A.material_id
const testDocs = path.join(root, 'docs', 'test_docs')
const files = {
  A: path.join(testDocs, 'A_区块链技术及应用课程复习资料.pdf'),
  B: path.join(testDocs, 'B_区块链资料完全重复副本.pdf'),
  I: path.join(testDocs, 'I_区块链资料篡改测试版.pdf'),
}
const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const port = 9444
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'educhain-public-test-edge-'))

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))


class CDP {
  constructor(url) {
    this.nextId = 1
    this.pending = new Map()
    this.socket = new WebSocket(url)
  }

  async connect() {
    await new Promise((resolve, reject) => {
      this.socket.addEventListener('open', resolve, { once: true })
      this.socket.addEventListener('error', reject, { once: true })
    })
    this.socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data)
      if (!message.id) return
      const pending = this.pending.get(message.id)
      if (!pending) return
      this.pending.delete(message.id)
      if (message.error) {
        pending.reject(new Error(`${pending.method}: ${message.error.message}`))
      } else {
        pending.resolve(message.result)
      }
    })
  }

  send(method, params = {}) {
    const id = this.nextId++
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, method })
      this.socket.send(JSON.stringify({ id, method, params }))
    })
  }

  close() {
    this.socket.close()
  }
}


async function waitForDebugger() {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/version`)
      if (response.ok) return
    } catch {
      // Edge is still starting.
    }
    await sleep(250)
  }
  throw new Error('Edge remote debugger did not start')
}


async function createPage() {
  const response = await fetch(
    `http://127.0.0.1:${port}/json/new?${encodeURIComponent('about:blank')}`,
    { method: 'PUT' },
  )
  if (!response.ok) throw new Error(`Could not create page: ${response.status}`)
  return response.json()
}


async function evaluate(cdp, expression) {
  const response = await cdp.send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
  })
  if (response.exceptionDetails) {
    throw new Error(
      response.exceptionDetails.exception?.description
      || response.exceptionDetails.text
      || 'Browser evaluation failed',
    )
  }
  return response.result.value
}


async function waitFor(cdp, expression, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (await evaluate(cdp, expression)) return
    await sleep(200)
  }
  throw new Error(`Timed out waiting for: ${expression}`)
}


async function navigate(cdp, url, selector) {
  await cdp.send('Page.navigate', { url })
  await waitFor(cdp, 'document.readyState === "complete"')
  if (selector) {
    await waitFor(cdp, `Boolean(document.querySelector(${JSON.stringify(selector)}))`)
  }
  await sleep(700)
}


async function login(cdp, studentId) {
  const result = await evaluate(
    cdp,
    `(async () => {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          student_id: ${JSON.stringify(studentId)},
          password: '123456'
        })
      })
      return { status: response.status, body: await response.json() }
    })()`,
  )
  if (result.status !== 200) {
    throw new Error(`Login ${studentId} failed: ${JSON.stringify(result.body)}`)
  }
}


async function setFile(cdp, filePath) {
  const documentNode = await cdp.send('DOM.getDocument', { depth: 1 })
  const input = await cdp.send('DOM.querySelector', {
    nodeId: documentNode.root.nodeId,
    selector: 'input[type="file"]',
  })
  if (!input.nodeId) throw new Error('File input not found')
  await cdp.send('DOM.setFileInputFiles', {
    files: [filePath],
    nodeId: input.nodeId,
  })
  await evaluate(
    cdp,
    `(() => {
      const input = document.querySelector('input[type="file"]')
      input.dispatchEvent(new Event('input', { bubbles: true }))
      input.dispatchEvent(new Event('change', { bubbles: true }))
      return true
    })()`,
  )
  await sleep(350)
}


async function capture(cdp, fileName, delay = 250) {
  await evaluate(cdp, 'window.scrollTo(0, 0); true')
  await sleep(delay)
  const screenshot = await cdp.send('Page.captureScreenshot', {
    format: 'png',
    fromSurface: true,
    captureBeyondViewport: false,
  })
  fs.writeFileSync(
    path.join(screenshotDir, fileName),
    Buffer.from(screenshot.data, 'base64'),
  )
  console.log(`Captured ${fileName}`)
}

async function showApiEvidence(cdp, title, result) {
  await evaluate(
    cdp,
    `(() => {
      document.querySelector('.automation-evidence')?.remove()
      const panel = document.createElement('section')
      panel.className = 'automation-evidence'
      panel.innerHTML = [
        '<strong>${String(title).replaceAll("'", "\\'")}</strong>',
        '<span>HTTP ${result.status}</span>',
        '<p>${String(result.message).replaceAll("'", "\\'").replaceAll('\n', ' ')}</p>'
      ].join('')
      Object.assign(panel.style, {
        position: 'fixed',
        left: '280px',
        right: '28px',
        bottom: '24px',
        zIndex: '99999',
        display: 'grid',
        gridTemplateColumns: '220px 100px 1fr',
        gap: '14px',
        alignItems: 'center',
        padding: '16px 20px',
        color: ${result.status >= 400 ? "'#991b1b'" : "'#166534'"},
        background: ${result.status >= 400 ? "'#fff1f2'" : "'#f0fdf4'"},
        border: '2px solid ${result.status >= 400 ? '#f87171' : '#4ade80'}',
        borderRadius: '10px',
        boxShadow: '0 18px 40px rgba(15,23,42,.22)',
        fontFamily: '"Microsoft YaHei", sans-serif'
      })
      panel.querySelector('strong').style.fontSize = '18px'
      panel.querySelector('span').style.fontWeight = '900'
      panel.querySelector('p').style.margin = '0'
      document.body.appendChild(panel)
      return true
    })()`,
  )
}


function buildSummaryHtml() {
  const balances = results.balances.final_recovered || results.balances.final || {}
  const accountRows = Object.entries(results.accounts)
    .map(([studentId, account]) => `
      <tr>
        <td>${studentId}</td>
        <td>${account.name}</td>
        <td>${account.role}</td>
        <td>${account.eth_address}</td>
        <td>${balances[studentId] ?? '--'} EDU</td>
      </tr>
    `)
    .join('')
  const hasIssues = results.issues.length > 0
  const issues = hasIssues
    ? results.issues
      .map((issue) => `<li><b>${issue.severity.toUpperCase()}</b> ${issue.title}</li>`)
      .join('')
    : '<li>未发现阻断测试的问题，全部用例通过。</li>'
  const html = `<!doctype html>
  <html lang="zh-CN">
  <meta charset="utf-8">
  <title>EduChain 公网联动测试证据摘要</title>
  <style>
    body{margin:0;padding:34px;background:#f4f7fa;color:#10233f;font-family:"Microsoft YaHei",Arial,sans-serif}
    h1{margin:0 0 8px;color:#005f92}p{margin:5px 0;color:#53647c}
    .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}
    .card{padding:18px;background:#fff;border:1px solid #dce4ef;border-radius:10px}
    .card strong{display:block;margin-top:8px;color:#0079ba;font-size:28px}
    table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dce4ef}
    th,td{padding:10px 12px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:13px}
    th{background:#edf7ff}.issues{padding:18px 28px;background:#fff7f7;border:1px solid #f3b7b7;border-radius:10px}
    .issues.ok{color:#166534;background:#f0fdf4;border-color:#86efac}
    li{margin:8px 0}b{color:#b42318}
  </style>
  <body>
    <h1>EduChain 公网九账号联动测试</h1>
    <p>服务器：${results.run.base_url}</p>
    <p>测试时间：${results.run.started_at} 至 ${results.run.finished_at}</p>
    <div class="cards">
      <div class="card">通过<strong>${results.summary.passed}</strong></div>
      <div class="card">未通过<strong>${results.summary.failed}</strong></div>
      <div class="card">区块高度<strong>${results.health_after.block_number}</strong></div>
      <div class="card">审计记录<strong>${results.health_after.download_count}</strong></div>
    </div>
    <h2>九账号、钱包与最终余额</h2>
    <table>
      <thead><tr><th>账号</th><th>姓名</th><th>角色</th><th>钱包地址</th><th>余额</th></tr></thead>
      <tbody>${accountRows}</tbody>
    </table>
    <h2>本轮发现的问题</h2>
    <ul class="issues${hasIssues ? '' : ' ok'}">${issues}</ul>
  </body></html>`
  const target = path.join(resultDir, 'evidence_summary.html')
  fs.writeFileSync(target, html, 'utf8')
  return target
}


async function main() {
  const summaryPath = buildSummaryHtml()
  const browser = spawn(
    edge,
    [
      '--headless=new',
      '--disable-gpu',
      '--hide-scrollbars',
      '--no-first-run',
      '--no-default-browser-check',
      '--remote-allow-origins=*',
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${profileDir}`,
      '--window-size=1600,900',
      '--force-device-scale-factor=1',
      'about:blank',
    ],
    { detached: false, stdio: 'ignore', windowsHide: true },
  )

  let cdp
  try {
    await waitForDebugger()
    const page = await createPage()
    cdp = new CDP(page.webSocketDebuggerUrl)
    await cdp.connect()
    await cdp.send('Page.enable')
    await cdp.send('Runtime.enable')
    await cdp.send('DOM.enable')
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: 1600,
      height: 900,
      deviceScaleFactor: 1,
      mobile: false,
    })
    await cdp.send('Page.setDownloadBehavior', {
      behavior: 'deny',
    })

    if (!resumeEvidence) {
      await navigate(cdp, pathToFileURL(summaryPath).href, 'table')
      await capture(cdp, '00-test-summary.png')

      await navigate(cdp, `${baseUrl}/login`, '.login-page')
      await waitFor(cdp, 'document.body.innerText.includes("系统状态：正常")')
      await capture(cdp, '01-public-login.png')

      await login(cdp, 'admin_2023112379')
      await navigate(cdp, `${baseUrl}/status`, '.status-page')
      await waitFor(
        cdp,
        'document.querySelector(".status-card.block b")?.textContent.trim() !== "--"',
      )
      await capture(cdp, '02-admin-system-status.png')

      await navigate(cdp, `${baseUrl}/market`, '.market-page')
      await waitFor(cdp, 'document.querySelectorAll("tbody tr").length >= 4')
      await evaluate(
        cdp,
        `(() => {
          const select = [...document.querySelectorAll('select')]
            .find((item) => [...item.options].some((option) => option.value === '12'))
          if (select) {
            select.value = '12'
            select.dispatchEvent(new Event('change', { bubbles: true }))
          }
          return true
        })()`,
      )
      await sleep(400)
      await capture(cdp, '03-admin-material-market.png')

      await navigate(cdp, `${baseUrl}/wallet`, '.wallet-page')
      await waitFor(cdp, 'Boolean(document.querySelector(".admin-form"))')
      await capture(cdp, '04-admin-wallet-controls.png')

      await navigate(cdp, `${baseUrl}/audit`, '.audit-page')
      await evaluate(
        cdp,
        `(() => {
          const tab = [...document.querySelectorAll('.tab')]
            .find((button) => button.textContent.includes('全局审计'))
          tab?.click()
          return Boolean(tab)
        })()`,
      )
      await waitFor(cdp, 'document.querySelectorAll("tbody tr").length >= 4')
      await capture(cdp, '05-admin-global-audit.png')

      await login(cdp, '2023112317')
      await navigate(cdp, `${baseUrl}/wallet`, '.wallet-page')
      await waitFor(cdp, 'document.querySelector(".balance-card strong")?.textContent.includes("82")')
      await waitFor(cdp, 'document.body.innerText.includes("共 5 条")')
      await capture(cdp, '06-fang-wallet-history.png')
    } else {
      await navigate(cdp, `${baseUrl}/login`, '.login-page')
    }

    await login(cdp, '2023112385')
    await navigate(cdp, `${baseUrl}/upload`, '.upload-page')
    await setFile(cdp, files.B)
    const duplicateResult = await evaluate(
      cdp,
      `(async () => {
        const file = document.querySelector('input[type="file"]').files[0]
        const data = new FormData()
        data.append('file', file)
        data.append('name', file.name)
        data.append('course', 'BC401')
        data.append('price', '5')
        data.append('policy_type', '0')
        data.append('policy_value', '')
        const response = await fetch('/api/material/upload', {
          method: 'POST',
          body: data,
          credentials: 'include'
        })
        const body = await response.json()
        return { status: response.status, message: body.msg || JSON.stringify(body) }
      })()`,
    )
    await showApiEvidence(cdp, '完全重复上传测试', duplicateResult)
    await capture(cdp, '07-duplicate-upload-rejected.png')

    await login(cdp, '2023112379')
    await navigate(cdp, `${baseUrl}/market`, '.market-page')
    await waitFor(cdp, 'document.querySelectorAll("tbody tr").length >= 4')
    await evaluate(
      cdp,
      `(() => {
        const select = [...document.querySelectorAll('select')]
          .find((item) => [...item.options].some((option) => option.value === '12'))
        if (select) {
          select.value = '12'
          select.dispatchEvent(new Event('change', { bubbles: true }))
        }
        return true
      })()`,
    )
    await sleep(350)
    const courseDenied = await evaluate(
      cdp,
      `(async () => {
        const response = await fetch(
          '/api/material/${results.materials.F.material_id}/download',
          { credentials: 'include' }
        )
        const body = await response.json()
        return { status: response.status, message: body.msg || JSON.stringify(body) }
      })()`,
    )
    await showApiEvidence(cdp, '课程权限拒绝测试', courseDenied)
    await capture(cdp, '08-course-permission-rejected.png')

    await login(cdp, '2023112392')
    await navigate(cdp, `${baseUrl}/market`, '.market-page')
    await waitFor(cdp, 'document.querySelectorAll("tbody tr").length >= 4')
    await evaluate(
      cdp,
      `(() => {
        const select = [...document.querySelectorAll('select')]
          .find((item) => [...item.options].some((option) => option.value === '12'))
        if (select) {
          select.value = '12'
          select.dispatchEvent(new Event('change', { bubbles: true }))
        }
        return true
      })()`,
    )
    await sleep(350)
    const whitelistDenied = await evaluate(
      cdp,
      `(async () => {
        const response = await fetch(
          '/api/material/${results.materials.G.material_id}/download',
          { credentials: 'include' }
        )
        const body = await response.json()
        return { status: response.status, message: body.msg || JSON.stringify(body) }
      })()`,
    )
    await showApiEvidence(cdp, '白名单权限拒绝测试', whitelistDenied)
    await capture(cdp, '09-whitelist-permission-rejected.png')

    await navigate(
      cdp,
      `${baseUrl}/verify?materialId=${encodeURIComponent(materialA)}`,
      '.verify-page',
    )
    await setFile(cdp, files.A)
    await evaluate(cdp, 'document.querySelector(".verify-button").click(); true')
    await waitFor(
      cdp,
      'document.querySelector(".danger-banner.trusted")?.textContent.includes("文件完整可信")',
      60000,
    )
    await capture(cdp, '10-original-file-verified.png')

    await navigate(
      cdp,
      `${baseUrl}/verify?materialId=${encodeURIComponent(materialA)}`,
      '.verify-page',
    )
    await setFile(cdp, files.I)
    await evaluate(cdp, 'document.querySelector(".verify-button").click(); true')
    await waitFor(
      cdp,
      'document.querySelector(".danger-banner:not(.trusted)")?.textContent.includes("检测到文件差异")',
      60000,
    )
    await capture(cdp, '11-tampered-file-detected.png')
  } finally {
    cdp?.close()
    browser.kill()
    await sleep(800)
    fs.rmSync(profileDir, { recursive: true, force: true })
  }
}


main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
