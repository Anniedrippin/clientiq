import React from 'react'

const SOURCE_ICONS = {
  postgres: '⛁',
  csv: '▤',
  slack: '#',
  jira: '◆',
  salesforce: '☁',
  google_sheets: '▦',
  vector_store: '❖',
}

export default function CitationsPanel({ citations }) {
  if (!citations || citations.length === 0) return null

  return (
    <div className="panel citations-panel">
      <div className="panel-header">
        <h3>Sources & Data Lineage</h3>
      </div>
      <ul className="citations-list">
        {citations.map((c, idx) => (
          <li key={idx} className="citation-row">
            <span className="citation-icon">{SOURCE_ICONS[c.source_type] || '•'}</span>
            <div className="citation-body">
              <div className="citation-top">
                <span className="citation-name">{c.source_name}</span>
                <span className="citation-count mono">{c.record_count?.toLocaleString?.() ?? c.record_count}</span>
              </div>
              <div className="citation-ref mono">{c.reference}</div>
              <div className="citation-snippet">{c.snippet}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
