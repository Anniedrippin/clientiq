import React from 'react'

export default function RootCauseViz({ rootCauses }) {
  if (!rootCauses || rootCauses.length === 0) return null
  const maxChange = Math.max(...rootCauses.map((c) => Math.abs(c.change_pct)), 1)

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Root Cause Analysis</h3>
      </div>
      <div className="root-cause-list">
        {rootCauses.map((cause, idx) => (
          <div key={idx} className="root-cause-row">
            <div className="root-cause-meta">
              <span className={`rank-pill rank-${cause.rank}`}>{cause.rank}</span>
              <span className="root-cause-desc">{cause.description}</span>
            </div>
            <div className="root-cause-bar-track">
              <div
                className="root-cause-bar-fill"
                style={{ width: `${(Math.abs(cause.change_pct) / maxChange) * 100}%` }}
              />
            </div>
            <div className="root-cause-stats">
              <span className="mono">{cause.metric}</span>
              <span className="mono">{cause.change_pct > 0 ? '+' : ''}{cause.change_pct}%</span>
              <span className="mono">{cause.evidence_count.toLocaleString()} evidence pts</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
