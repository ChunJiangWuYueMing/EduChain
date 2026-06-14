import { spawn } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'


const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const port = 9335
const baseUrl = process.env.EDUCHAIN_UI_URL || 'http://127.0.0.1:5173'
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), 'educhain-ui-audit-'))
const routes = ['/market', '/upload', '/verify', '/wallet', '/audit', '/status']
const viewports = [
  { width: 1500, height: 820 },
  { width: 1366, height: 768 },
]
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
      if (message.error) pending.reject(new Error(message.error.message))
      else pending.resolve(message.result)
    })
  }

  send(method, params = {}) {
    const id = this.nextId++
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject })
      this.socket.send(JSON.stringify({ id, method, params }))
    })
  }

  close() {
    this.socket.close()
  }
}


async function evaluate(cdp, expression) {
  const response = await cdp.send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
  })
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text)
  return response.result.value
}


async function waitFor(cdp, expression, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (await evaluate(cdp, expression)) return
    await sleep(200)
  }
  throw new Error(`Timed out waiting for ${expression}`)
}


async function waitForDebugger() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
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


async function navigate(cdp, route) {
  await cdp.send('Page.navigate', { url: `${baseUrl}${route}` })
  await waitFor(cdp, 'document.readyState === "complete"')
  await waitFor(cdp, 'Boolean(document.querySelector(".shell-header"))')
  await sleep(350)
}


async function collect(cdp, route, viewport) {
  await navigate(cdp, route)
  return evaluate(
    cdp,
    `(() => {
      const roundedRect = (selector) => {
        const element = document.querySelector(selector)
        if (!element) return null
        const rect = element.getBoundingClientRect()
        return Object.fromEntries(
          ['x', 'y', 'width', 'height'].map((key) => [key, Math.round(rect[key])])
        )
      }
      const lineCount = (selector) => {
        const element = document.querySelector(selector)
        if (!element) return null
        const range = document.createRange()
        range.selectNodeContents(element)
        return range.getClientRects().length
      }
      return {
        route: ${JSON.stringify(route)},
        viewport: ${JSON.stringify(viewport)},
        sidebar: roundedRect('.shell-sidebar'),
        header: roundedRect('.shell-header'),
        title: roundedRect('.shell-title'),
        actions: roundedRect('.shell-actions'),
        search: roundedRect('.global-search-trigger'),
        chainStatus: roundedRect('.shell-chain-status'),
        chainLabel: roundedRect('.shell-chain-status > span'),
        chainValue: roundedRect('.shell-chain-status strong'),
        chainLabelLines: lineCount('.shell-chain-status > span'),
        userCard: roundedRect('.shell-user-card'),
        navSignature: Array.from(document.querySelectorAll('.shell-nav-item'))
          .map((item) => item.innerHTML.replace(/\\s+/g, ' ').trim())
          .join('|'),
        activeLinks: document.querySelectorAll('.shell-nav-item.router-link-active').length,
        clientWidth: document.documentElement.clientWidth,
        scrollHeight: document.documentElement.scrollHeight,
        verticallyScrollable: document.documentElement.scrollHeight > window.innerHeight,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
        errors: window.__educhainAuditErrors || [],
      }
    })()`,
  )
}


async function main() {
  const browser = spawn(
    edge,
    [
      '--headless=new',
      '--disable-gpu',
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
    const pageResponse = await fetch(
      `http://127.0.0.1:${port}/json/new?${encodeURIComponent('about:blank')}`,
      { method: 'PUT' },
    )
    const page = await pageResponse.json()
    cdp = new CDP(page.webSocketDebuggerUrl)
    await cdp.connect()
    await cdp.send('Page.enable')
    await cdp.send('Runtime.enable')
    await cdp.send('Page.addScriptToEvaluateOnNewDocument', {
      source: `
        window.__educhainAuditErrors = []
        window.addEventListener('error', (event) => {
          window.__educhainAuditErrors.push(String(event.message || event.error))
        })
        window.addEventListener('unhandledrejection', (event) => {
          window.__educhainAuditErrors.push(String(event.reason))
        })
      `,
    })

    await cdp.send('Page.navigate', { url: `${baseUrl}/login` })
    await waitFor(cdp, 'document.readyState === "complete"')
    const login = await evaluate(
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
        return response.status
      })()`,
    )
    if (login !== 200) throw new Error(`Browser login failed with HTTP ${login}`)

    const results = []
    for (const viewport of viewports) {
      await cdp.send('Emulation.setDeviceMetricsOverride', {
        ...viewport,
        deviceScaleFactor: 1,
        mobile: false,
      })
      for (const route of routes) {
        results.push(await collect(cdp, route, viewport))
      }
    }

    const baselineByViewport = new Map()
    const failures = []
    for (const result of results) {
      const key = `${result.viewport.width}x${result.viewport.height}`
      const baseline = baselineByViewport.get(key)
      if (!baseline) baselineByViewport.set(key, result)
      else {
        for (const field of [
          'sidebar',
          'header',
          'title',
          'actions',
          'search',
          'chainStatus',
          'userCard',
          'navSignature',
        ]) {
          if (JSON.stringify(result[field]) !== JSON.stringify(baseline[field])) {
            failures.push(`${key} ${result.route}: ${field} changed between routes`)
          }
        }
      }
      if (result.activeLinks !== 1) {
        failures.push(`${key} ${result.route}: expected one active navigation item`)
      }
      if (result.horizontalOverflow) {
        failures.push(
          `${key} ${result.route}: horizontal overflow ${result.scrollWidth}px > ${result.innerWidth}px`,
        )
      }
      if ((result.chainLabelLines ?? 0) > 1) {
        failures.push(`${key} ${result.route}: chain status label wraps`)
      }
      if (result.errors.length) {
        failures.push(`${key} ${result.route}: browser errors ${result.errors.join('; ')}`)
      }
    }

    console.log(JSON.stringify({ results, failures }, null, 2))
    if (failures.length) process.exitCode = 1
  } finally {
    cdp?.close()
    browser.kill()
    await Promise.race([
      new Promise((resolve) => browser.once('exit', resolve)),
      sleep(2000),
    ])
    try {
      fs.rmSync(profileDir, { recursive: true, force: true })
    } catch {
      // Edge may release profile files a moment after the process exits.
    }
  }
}


main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
