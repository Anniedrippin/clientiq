import React, { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'
import { logEvent } from '../api/logger'
import RootCauseViz from './RootCauseViz'
import RecommendationCards from './RecommendationCards'
import CitationsPanel from './CitationsPanel'
import ExportButton from './ExportButton'

const SUGGESTIONS = [
  'Why did revenue drop by 12% in the North region last quarter?',
  'What is driving customer churn this quarter?',
  'Why have delivery delays increased?',
]

export default function ChatPanel({ region, onNewAnalysis, onViewTrace }) {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  async function submitQuestion(q) {
    const text = (q ?? question).trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', text }])
    setQuestion('')
    setLoading(true)
    logEvent('chat_question_submitted', 'info', { question: text, region })

    try {
      const analysis = await api.ask(text, region)
      setMessages((prev) => [...prev, { role: 'assistant', analysis }])
      onNewAnalysis(analysis)
      logEvent('chat_answer_rendered', 'info', { request_id: analysis.request_id })
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', error: true, text: 'Something went wrong running the analysis.' }])
      logEvent('chat_answer_failed', 'error', { question: text, error: String(err) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <h3>Ask ClientIQ anything about this engagement</h3>
            <p>It will query your connected data sources, compare patterns, and produce a cited root-cause analysis.</p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="suggestion-chip" onClick={() => submitQuestion(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, idx) => (
          <div key={idx} className={`chat-message ${m.role}`}>
            {m.role === 'user' ? (
              <div className="chat-bubble user-bubble">{m.text}</div>
            ) : m.error ? (
              <div className="chat-bubble error-bubble">{m.text}</div>
            ) : (
              <div className="chat-answer">
                <div className="panel">
                  <div className="panel-header">
                    <h3>Executive Summary</h3>
                    <ExportButton requestId={m.analysis.request_id} />
                  </div>
                  <p className="exec-summary">{m.analysis.executive_summary}</p>
                </div>
                <RootCauseViz rootCauses={m.analysis.root_causes} />
                <RecommendationCards recommendations={m.analysis.recommendations} />
                <CitationsPanel citations={m.analysis.citations} />
                <button className="btn btn-secondary" onClick={onViewTrace}>
                  View Agent Trace ({m.analysis.trace.length} steps) →
                </button>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-message assistant">
            <div className="chat-bubble thinking-bubble">
              <span className="dot" /><span className="dot" /><span className="dot" />
              Running LangGraph analysis across connected data sources…
            </div>
          </div>
        )}
      </div>

      <form
        className="chat-input-row"
        onSubmit={(e) => {
          e.preventDefault()
          submitQuestion()
        }}
      >
        <input
          type="text"
          placeholder={`Ask about ${region} performance…`}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" className="btn btn-primary" disabled={loading}>Ask</button>
      </form>
    </div>
  )
}
