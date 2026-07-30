import React from 'react'

export default function RecommendationCards({ recommendations }) {
  if (!recommendations || recommendations.length === 0) return null

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Recommendations</h3>
      </div>
      <div className="rec-grid">
        {recommendations.map((rec, idx) => (
          <div key={idx} className={`rec-card priority-${rec.priority}`}>
            <div className="rec-card-top">
              <span className="rec-priority">{rec.priority} priority</span>
            </div>
            <h4>{rec.title}</h4>
            <p>{rec.detail}</p>
            <div className="rec-impact">{rec.estimated_impact}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
