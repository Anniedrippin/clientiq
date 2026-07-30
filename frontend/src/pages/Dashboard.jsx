import React, { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import { logEvent } from '../api/logger'

import KPICard from '../components/KPICard'
import AnomalyAlerts from '../components/AnomalyAlerts'
import ChatPanel from '../components/ChatPanel'
import AgentTraceView from '../components/AgentTraceView'
import CitationsPanel from '../components/CitationsPanel'
import RootCauseViz from '../components/RootCauseViz'
import RecommendationCards from '../components/RecommendationCards'
import ExportButton from '../components/ExportButton'

const REGIONS = ['North', 'South', 'East', 'West']
const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: '◧' },
  { id: 'chat', label: 'Ask AI', icon: '✦' },
  { id: 'trace', label: 'Agent Trace', icon: '≡' },
]

export default function Dashboard() {
  const { user, logout } = useAuth()
  const [region, setRegion] = useState('North')
  const [kpis, setKpis] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [loadingKpis, setLoadingKpis] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [lastAnalysis, setLastAnalysis] = useState(null)

  const loadKpis = useCallback(async (r) => {
    setLoadingKpis(true)
    logEvent('dashboard_kpi_load_started', 'info', { region: r })
    try {
      const data = await api.getKpis(r)
      setKpis(data.kpis || [])
      setAnomalies(data.anomalies || [])
      logEvent('dashboard_kpi_load_completed', 'info', { region: r, kpi_count: data.kpis?.length })
    } catch (err) {
      logEvent('dashboard_kpi_load_failed', 'error', { region: r, error: String(err) })
    } finally {
      setLoadingKpis(false)
    }
  }, [])

  useEffect(() => {
    loadKpis(region)
  }, [region, loadKpis])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark small">CIQ</div>
          <span>ClientIQ</span>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'is-active' : ''}`}
              onClick={() => {
                logEvent('nav_tab_selected', 'info', { tab: item.id })
                setActiveTab(item.id)
              }}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="sidebar-user">
            <div className="avatar">{user?.username?.[0]?.toUpperCase()}</div>
            <div>
              <div className="sidebar-user-name">{user?.username}</div>
              <div className="sidebar-user-role">{user?.role}</div>
            </div>
          </div>
          <button className="btn btn-ghost" onClick={logout}>Sign out</button>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div>
            <h1>Executive Analytics</h1>
            <p className="topbar-sub">Consolidated view across CRM, ERP, support, and inventory systems</p>
          </div>
          <div className="topbar-controls">
            <label className="region-select-label">Region</label>
            <select value={region} onChange={(e) => setRegion(e.target.value)} className="region-select">
              {REGIONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </header>

        <div className="content">
          {activeTab === 'overview' && (
            <OverviewTab
              kpis={kpis}
              anomalies={anomalies}
              loading={loadingKpis}
              lastAnalysis={lastAnalysis}
              onGoToChat={() => setActiveTab('chat')}
              onGoToTrace={() => setActiveTab('trace')}
            />
          )}
          {activeTab === 'chat' && (
            <ChatPanel
              region={region}
              onNewAnalysis={(analysis) => setLastAnalysis(analysis)}
              onViewTrace={() => setActiveTab('trace')}
            />
          )}
          {activeTab === 'trace' && <AgentTraceView analysis={lastAnalysis} />}
        </div>
      </div>
    </div>
  )
}

function OverviewTab({ kpis, anomalies, loading, lastAnalysis, onGoToChat, onGoToTrace }) {
  return (
    <>
      <section className="kpi-grid">
        {loading && <div className="empty-state">Loading KPI snapshot…</div>}
        {!loading && kpis.map((kpi) => <KPICard key={kpi.name} kpi={kpi} />)}
      </section>

      <AnomalyAlerts anomalies={anomalies} onInvestigate={onGoToChat} />

      {lastAnalysis ? (
        <div className="analysis-grid">
          <div className="analysis-main">
            <div className="panel">
              <div className="panel-header">
                <h3>Executive Summary</h3>
                <ExportButton requestId={lastAnalysis.request_id} />
              </div>
              <p className="exec-summary">{lastAnalysis.executive_summary}</p>
            </div>
            <RootCauseViz rootCauses={lastAnalysis.root_causes} />
            <RecommendationCards recommendations={lastAnalysis.recommendations} />
          </div>
          <div className="analysis-side">
            <CitationsPanel citations={lastAnalysis.citations} />
            <button className="btn btn-secondary full-width" onClick={onGoToTrace}>
              View Agent Trace →
            </button>
          </div>
        </div>
      ) : (
        <div className="empty-analysis">
          <p>No analysis yet for this session.</p>
          <button className="btn btn-primary" onClick={onGoToChat}>Ask the AI a question →</button>
        </div>
      )}
    </>
  )
}
