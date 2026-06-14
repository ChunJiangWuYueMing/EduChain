import { spawn } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'


const root = path.resolve(import.meta.dirname, '..')
const assetDir = path.join(root, 'docs', 'report_assets')
const resultPath = path.join(assetDir, 'report_e2e_results.json')
const results = JSON.parse(fs.readFileSync(resultPath, 'utf8'))
const materialId = results.material.material_id
const originalFile = fs.readdirSync(path.join(root, 'demo'))
  .map((name) => path.join(root, 'demo', name))
  .find((file) => path.basename(file).startsWith('original_'))
const tamperedFile = fs.readdirSync(path.join(root, 'demo'))
  .map((name) => path.join(root, 'demo', name))
  .find((file) => path.basename(file).startsWith('tampered_'))

const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const port = 9333
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'educhain-report-edge-'))

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
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/version`)
      if (response.ok) return
    } catch {
      // Browser is still starting.
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
    throw new Error(response.exceptionDetails.text || 'Browser evaluation failed')
  }
  return response.result.value
}


async function waitFor(cdp, expression, timeoutMs = 15000) {
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
  await sleep(500)
}


async function capture(cdp, fileName) {
  await evaluate(cdp, 'window.scrollTo(0, 0); true')
  await sleep(250)
  const screenshot = await cdp.send('Page.captureScreenshot', {
    format: 'png',
    fromSurface: true,
    captureBeyondViewport: false,
  })
  fs.writeFileSync(path.join(assetDir, fileName), Buffer.from(screenshot.data, 'base64'))
  console.log(`Captured ${fileName}`)
}


async function main() {
  fs.mkdirSync(assetDir, { recursive: true })
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
      '--window-size=1500,820',
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
      width: 1500,
      height: 820,
      deviceScaleFactor: 1,
      mobile: false,
    })

    await navigate(cdp, 'http://localhost:8080/login', '.login-page')
    await capture(cdp, 'image10-login.png')

    const loginResult = await evaluate(
      cdp,
      `(async () => {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            student_id: '2023116101',
            password: '2023116101'
          })
        })
        return { status: response.status, body: await response.json() }
      })()`,
    )
    if (loginResult.status !== 200) {
      throw new Error(`Browser login failed: ${JSON.stringify(loginResult.body)}`)
    }

    await navigate(cdp, 'http://localhost:8080/upload', '.upload-page')
    await setFile(cdp, originalFile)
    await evaluate(
      cdp,
      `(() => {
        const input = document.querySelector('input[type="file"]')
        input.dispatchEvent(new Event('input', { bubbles: true }))
        input.dispatchEvent(new Event('change', { bubbles: true }))
        return true
      })()`,
    )
    await waitFor(cdp, 'Boolean(document.querySelector(".drop-zone.filled"))')
    await evaluate(
      cdp,
      `(() => {
        const select = document.querySelector('.field select')
        select.value = 'CS201'
        select.dispatchEvent(new Event('input', { bubbles: true }))
        select.dispatchEvent(new Event('change', { bubbles: true }))
        const price = document.querySelector('input[type="number"]')
        price.value = '5'
        price.dispatchEvent(new Event('input', { bubbles: true }))
        price.dispatchEvent(new Event('change', { bubbles: true }))

        window.__reportNativeFetch = window.fetch.bind(window)
        const replay = ${JSON.stringify({
          code: 200,
          data: results.material,
          msg: '上传成功',
        })}
        window.fetch = async (input, init) => {
          const url = typeof input === 'string' ? input : input.url
          if (url.includes('/api/material/upload')) {
            return new Response(JSON.stringify(replay), {
              status: 200,
              headers: { 'Content-Type': 'application/json' }
            })
          }
          return window.__reportNativeFetch(input, init)
        }
        return true
      })()`,
    )
    await waitFor(cdp, '!document.querySelector(".submit-button").disabled')
    await evaluate(cdp, 'document.querySelector(".submit-button").click(); true')
    await waitFor(cdp, 'Boolean(document.querySelector(".success-banner"))', 30000)
    await capture(cdp, 'image11-upload-result.png')

    await navigate(cdp, 'http://localhost:8080/market', '.market-page')
    await waitFor(cdp, 'document.querySelectorAll("tbody tr").length > 0')
    await capture(cdp, 'image13-market.png')

    await navigate(cdp, 'http://localhost:8080/wallet', '.wallet-page')
    await capture(cdp, 'image14-wallet.png')

    await navigate(
      cdp,
      `http://localhost:8080/verify?materialId=${encodeURIComponent(materialId)}`,
      '.verify-page',
    )
    await setFile(cdp, tamperedFile)
    await evaluate(cdp, 'document.querySelector(".verify-button").click(); true')
    await waitFor(cdp, 'Boolean(document.querySelector(".danger-banner"))', 30000)
    await capture(cdp, 'image15-verify-tampered.png')

    await navigate(cdp, 'http://localhost:8080/audit', '.audit-page')
    await evaluate(
      cdp,
      `(() => {
        const tab = [...document.querySelectorAll('.tab')]
          .find((button) => button.textContent.includes('资料下载记录'))
        tab.click()
        const input = document.querySelector('#material-id')
        input.value = ${JSON.stringify(materialId)}
        input.dispatchEvent(new Event('input', { bubbles: true }))
        document.querySelector('.search-row').dispatchEvent(
          new Event('submit', { bubbles: true, cancelable: true })
        )
        return true
      })()`,
    )
    await waitFor(cdp, 'document.querySelectorAll("tbody tr").length > 0')
    await sleep(700)
    await evaluate(
      cdp,
      'document.querySelector(".detail-button")?.click(); true',
    )
    await sleep(700)
    await capture(cdp, 'image16-audit.png')

    await navigate(cdp, 'http://localhost:8080/status', '.status-page')
    await waitFor(cdp, 'document.querySelector(".status-card.block b")?.textContent.trim() !== "--"')
    await capture(cdp, 'image17-status.png')
  } finally {
    cdp?.close()
    browser.kill()
    await sleep(500)
    fs.rmSync(profileDir, { recursive: true, force: true })
  }
}


main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
