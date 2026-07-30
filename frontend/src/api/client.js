import { logEvent, FrontendTimer } from './logger'

const BASE_URL = ''  // same-origin via Vite proxy in dev, same-origin in prod build

let authToken = null

export function setAuthToken(token) {
  authToken = token
}

async function request(method, path, { body, event } = {}) {
  const timer = new FrontendTimer()
  const eventName = event || `${method.toLowerCase()}_${path.replace(/\W+/g, '_')}`
  logEvent(`${eventName}_started`, 'info', { method, path })

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    })

    if (!res.ok) {
      const text = await res.text()
      logEvent(`${eventName}_failed`, 'error', {
        method,
        path,
        status: res.status,
        duration_ms: timer.ms(),
        error: text,
      })
      const err = new Error(text || `Request failed with status ${res.status}`)
      err.status = res.status
      throw err
    }

    const contentType = res.headers.get('content-type') || ''
    const data = contentType.includes('application/json') ? await res.json() : await res.blob()

    logEvent(`${eventName}_completed`, 'info', {
      method,
      path,
      status_code: res.status,
      duration_ms: timer.ms(),
    })
    return data
  } catch (err) {
    if (!err.status) {
      logEvent(`${eventName}_failed`, 'error', { method, path, error: String(err), duration_ms: timer.ms() })
    }
    throw err
  }
}

export const api = {
  login: (username, password) =>
    request('POST', '/api/auth/login', { body: { username, password }, event: 'login_attempt' }),

  getKpis: (region) =>
    request('GET', `/api/kpi${region ? `?region=${encodeURIComponent(region)}` : ''}`, { event: 'kpi_fetch' }),

  ask: (question, region) =>
    request('POST', '/api/analysis/ask', { body: { question, region }, event: 'analysis_request' }),

  getTrace: (requestId) =>
    request('GET', `/api/trace/${requestId}`, { event: 'trace_view_fetch' }),

  history: () => request('GET', '/api/analysis/history', { event: 'analysis_history_fetch' }),

  exportPdf: (requestId) => request('GET', `/api/export/${requestId}/pdf`, { event: 'pdf_export' }),
}
