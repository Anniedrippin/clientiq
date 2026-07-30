import React from 'react'

function nodeLabel(step) {
  if (step.node === 'mcp_connector') return step.action
  return step.node.replaceAll('_', ' ')
}

export default function AgentTraceView({ analysis }) {
  if (!analysis) {
    return (
      <div className="empty-analysis">
        <p>No agent run to trace yet. Ask a question in the Ask AI tab first.</p>
      </div>
    )
  }

  const trace = analysis.trace || []
  const totalDuration = trace.reduce((sum, s) => sum + (s.duration_ms || 0), 0)

  return (
    <div className="trace-view">
      <div className="trace-header">
        <div>
          <h3>Agent Trace</h3>
          <p className="trace-sub mono">request_id: {analysis.request_id}</p>
        </div>
        <div className="trace-summary-stats">
          <div><span className="mono">{trace.length}</span> steps</div>
          <div><span className="mono">{totalDuration.toFixed(1)}ms</span> total</div>
        </div>
      </div>

      <div className="ledger">
        {trace.map((step, idx) => (
          <div key={idx} className={`ledger-entry status-${step.status}`}>
            <div className="ledger-rail">
              <span className="ledger-number">{String(step.step_id).padStart(2, '0')}</span>
              {idx < trace.length - 1 && <span className="ledger-connector" />}
            </div>
            <div className="ledger-card">
              <div className="ledger-card-top">
                <span className="ledger-node">{nodeLabel(step)}</span>
                {step.tool && <span className="ledger-tool mono">{step.tool}</span>}
                <span className={`ledger-status status-badge-${step.status}`}>{step.status}</span>
                <span className="ledger-duration mono">{step.duration_ms}ms</span>
              </div>
              {step.input && (
                <div className="ledger-io">
                  <span className="io-label">input</span>
                  <code className="mono">{JSON.stringify(step.input)}</code>
                </div>
              )}
              {step.output_summary && (
                <div className="ledger-io">
                  <span className="io-label">output</span>
                  <span>{step.output_summary}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
