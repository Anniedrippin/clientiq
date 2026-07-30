"""Renders a stored analysis into an executive-ready PDF (reportlab)."""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from app.core.logging_config import get_logger, log_event, Timer

logger = get_logger(__name__)

INK = colors.HexColor("#0F1B2D")
COBALT = colors.HexColor("#2D4FFF")
SLATE = colors.HexColor("#55606E")

_EXPORT_DIR = "/tmp/clientiq_exports"
os.makedirs(_EXPORT_DIR, exist_ok=True)


def render_analysis_pdf(analysis: dict, request_id: str) -> str:
    timer = Timer()
    log_event(logger, "pdf_export_started", request_id=request_id)

    out_path = os.path.join(_EXPORT_DIR, f"clientiq_report_{request_id}.pdf")
    doc = SimpleDocTemplate(out_path, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CIQTitle", parent=styles["Title"], textColor=INK, fontSize=20, spaceAfter=6)
    h2 = ParagraphStyle("CIQH2", parent=styles["Heading2"], textColor=INK, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("CIQBody", parent=styles["Normal"], textColor=SLATE, fontSize=10, leading=14)
    meta = ParagraphStyle("CIQMeta", parent=styles["Normal"], textColor=SLATE, fontSize=8)

    story = []
    story.append(Paragraph("ClientIQ — Executive Analysis Report", title_style))
    story.append(Paragraph(f"Question: {analysis.get('question', '')}", body))
    story.append(Paragraph(f"Report ID: {request_id}", meta))
    story.append(HRFlowable(width="100%", color=COBALT, thickness=1.2, spaceAfter=10))

    story.append(Paragraph("Executive Summary", h2))
    story.append(Paragraph(analysis.get("executive_summary", ""), body))

    story.append(Paragraph("Root Causes", h2))
    rc_rows = [["Rank", "Description", "Metric", "Change %", "Evidence"]]
    for c in analysis.get("root_causes", []):
        rc_rows.append([
            c.get("rank", ""), c.get("description", ""), c.get("metric", ""),
            f"{c.get('change_pct', 0)}%", str(c.get("evidence_count", "")),
        ])
    rc_table = Table(rc_rows, colWidths=[0.7 * inch, 2.6 * inch, 1.1 * inch, 0.8 * inch, 0.9 * inch])
    rc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DADDE2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F5F1")]),
    ]))
    story.append(rc_table)

    story.append(Paragraph("Recommendations", h2))
    for r in analysis.get("recommendations", []):
        story.append(Paragraph(f"<b>{r.get('title')}</b> ({r.get('priority', '').upper()})", body))
        story.append(Paragraph(r.get("detail", ""), body))
        story.append(Paragraph(f"<i>Estimated impact: {r.get('estimated_impact', '')}</i>", body))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Citations & Data Lineage", h2))
    cit_rows = [["Source", "Reference", "Records"]]
    for c in analysis.get("citations", []):
        cit_rows.append([c.get("source_name", ""), c.get("reference", ""), str(c.get("record_count", ""))])
    cit_table = Table(cit_rows, colWidths=[2.0 * inch, 2.8 * inch, 1.3 * inch])
    cit_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COBALT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DADDE2")),
    ]))
    story.append(cit_table)

    doc.build(story)

    log_event(logger, "pdf_export_completed", request_id=request_id, duration_ms=timer.ms(), path=out_path)
    return out_path
