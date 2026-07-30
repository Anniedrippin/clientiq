import React, { useState } from 'react'
import { api } from '../api/client'
import { logEvent } from '../api/logger'

export default function ExportButton({ requestId }) {
  const [exporting, setExporting] = useState(false)

  async function handleExport() {
    setExporting(true)
    logEvent('pdf_export_clicked', 'info', { request_id: requestId })
    try {
      const blob = await api.exportPdf(requestId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `clientiq_report_${requestId}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      logEvent('pdf_export_downloaded', 'info', { request_id: requestId })
    } catch (err) {
      logEvent('pdf_export_ui_failed', 'error', { request_id: requestId, error: String(err) })
    } finally {
      setExporting(false)
    }
  }

  return (
    <button className="btn btn-secondary btn-small" onClick={handleExport} disabled={exporting}>
      {exporting ? 'Exporting…' : 'Export PDF'}
    </button>
  )
}
