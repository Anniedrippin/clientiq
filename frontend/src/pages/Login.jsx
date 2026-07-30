import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { logEvent } from '../api/logger'

export default function Login() {
  const { login } = useAuth()
  const [username, setUsername] = useState('analyst@clientiq.ai')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    logEvent('login_form_submitted', 'info', { username })
    try {
      await login(username, password)
    } catch (err) {
      setError('Invalid username or password.')
      logEvent('login_form_failed', 'warning', { username, error: String(err) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-brand">
        <div className="auth-brand-inner">
          <div className="brand-mark">CIQ</div>
          <h1>ClientIQ</h1>
          <p className="brand-tag">AI Consulting Analytics Copilot</p>
          <div className="ledger-preview">
            <div className="ledger-preview-row">
              <span className="ledger-step">01</span>
              <span>postgres-mcp · get_revenue_by_region</span>
            </div>
            <div className="ledger-preview-row">
              <span className="ledger-step">02</span>
              <span>slack-mcp · search_complaint_messages</span>
            </div>
            <div className="ledger-preview-row">
              <span className="ledger-step">03</span>
              <span>groq_llm · analyze_root_causes</span>
            </div>
            <div className="ledger-preview-row is-muted">
              <span className="ledger-step">04</span>
              <span>generate_executive_summary</span>
            </div>
          </div>
          <p className="brand-foot">Every recommendation, traced back to the data that produced it.</p>
        </div>
      </div>

      <div className="auth-form-panel">
        <form className="auth-form" onSubmit={handleSubmit}>
          <h2>Sign in</h2>
          <p className="auth-sub">Access your engagement workspace.</p>

          <label>Email</label>
          <input
            type="email"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />

          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="Analyst123!"
          />

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>

          <div className="auth-hint">
            <div>Demo credentials:</div>
            <code>analyst@clientiq.ai / Analyst123!</code>
            <code>partner@clientiq.ai / Partner123!</code>
          </div>
        </form>
      </div>
    </div>
  )
}
