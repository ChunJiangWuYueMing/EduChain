/* ============================================================
   EduChain — API 请求封装
   ============================================================ */

const BASE = '' // Vite proxy handles /api

async function request(url, options = {}) {
  const defaults = {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  }
  if (options.body instanceof FormData) {
    delete defaults.headers['Content-Type']
  }
  const headers = {
    ...defaults.headers,
    ...(options.headers || {}),
  }
  const res = await fetch(BASE + url, { ...defaults, ...options, headers })

  // 文件下载（非 JSON）
  const ct = res.headers.get('Content-Type') || ''
  if (ct.includes('octet-stream') || res.headers.get('Content-Disposition')) {
    if (!res.ok) throw new Error('下载失败')
    return res
  }

  let json
  try {
    json = await res.json()
  } catch {
    throw new Error(`请求失败（HTTP ${res.status}）`)
  }
  if (!res.ok || json.code >= 400) {
    const error = new Error(json.msg || '请求失败')
    error.status = res.status
    error.data = json.data
    throw error
  }
  return json
}

export default {
  get: (url) => request(url),
  post: (url, body) => request(url, { method: 'POST', body: JSON.stringify(body) }),
  postForm: (url, formData) => request(url, { method: 'POST', body: formData }),
  del: (url) => request(url, { method: 'DELETE' }),
}

/**
 * 前端 SHA-256（Web Crypto API）
 */
export async function sha256File(file) {
  const buffer = await file.arrayBuffer()
  const hash = await crypto.subtle.digest('SHA-256', buffer)
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

/**
 * 截断哈希/地址
 */
export function truncate(str, head = 8, tail = 6) {
  if (!str || str.length <= head + tail + 3) return str || ''
  return str.slice(0, head) + '...' + str.slice(-tail)
}

/**
 * 格式化时间戳
 */
export function formatTime(ts) {
  if (!ts) return '--'
  const d = new Date(typeof ts === 'number' && ts < 1e12 ? ts * 1000 : ts)
  return d.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

/**
 * 策略类型文字
 */
export function policyText(type) {
  return { 0: '公开', 1: '同课程', 2: '白名单' }[type] ?? '未知'
}
