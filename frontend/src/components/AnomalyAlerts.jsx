import React from 'react'

export default function AnomalyAlerts({ anomalies, onInvestigate }) {
  if (!anomalies || anomalies.length === 0) return null

  return (
    <section className="anomaly-banner">
      <div className="anomaly-banner-header">
        <span className="anomaly-dot" />
        <strong>{anomalies.length} anomaly signal{anomalies.length > 1 ? 's' : ''} detected</strong>
        <button className="btn btn-primary btn-small" onClick={onInvestigate}>Investigate with AI →</button>
      </div>
      <ul className="anomaly-list">
        {anomalies.map((a) => (
          <li key={a.name}>
            <span className="anomaly-name">{a.name}</span>
            <span className="anomaly-change">
              {a.change_pct > 0 ? '+' : ''}
              {a.change_pct}% change
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
