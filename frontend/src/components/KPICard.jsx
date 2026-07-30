import React from 'react'

function formatValue(kpi) {
  if (kpi.unit === 'USD') {
    return `$${(kpi.value / 1_000_000).toFixed(2)}M`
  }
  return `${kpi.value}${kpi.unit}`
}

export default function KPICard({ kpi }) {
  const trendClass = kpi.trend === 'up' ? 'trend-up' : kpi.trend === 'down' ? 'trend-down' : 'trend-flat'
  const isNegativeGood = kpi.name.startsWith('Revenue')
  const changeIsBad = isNegativeGood ? kpi.change_pct < 0 : kpi.change_pct > 0

  return (
    <div className={`kpi-card ${kpi.is_anomaly ? 'is-anomaly' : ''}`}>
      {kpi.is_anomaly && <span className="kpi-flag">Anomaly</span>}
      <div className="kpi-name">{kpi.name}</div>
      <div className="kpi-value">{formatValue(kpi)}</div>
      <div className={`kpi-change ${changeIsBad ? 'is-bad' : 'is-good'} ${trendClass}`}>
        {kpi.change_pct > 0 ? '▲' : kpi.change_pct < 0 ? '▼' : '—'} {Math.abs(kpi.change_pct)}%
      </div>
    </div>
  )
}
