// Mirrors the backend's JSON logging template (see app/core/logging_config.py)
// so the whole application — frontend and backend — logs major functionality
// in exactly the same shape. Every entry point (API calls, auth, chat, trace,
// export) calls logEvent() the same way.

const SERVICE_NAME = 'clientiq-frontend'

export function logEvent(event, level = 'info', fields = {}) {
  const record = {
    timestamp: new Date().toISOString(),
    level: level.toUpperCase(),
    service: SERVICE_NAME,
    event,
    ...fields,
  }
  const fn = level === 'error' ? console.error : level === 'warning' ? console.warn : console.log
  fn(JSON.stringify(record))
}

export class FrontendTimer {
  constructor() {
    this.start = performance.now()
  }
  ms() {
    return Math.round((performance.now() - this.start) * 100) / 100
  }
}
