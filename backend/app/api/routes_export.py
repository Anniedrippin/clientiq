from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.core.logging_config import get_logger, log_event
from app.api.deps import get_current_user
from app.services.trace_service import get_analysis
from app.services.pdf_export import render_analysis_pdf

logger = get_logger(__name__)
router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{request_id}/pdf")
async def export_pdf(request_id: str, user: dict = Depends(get_current_user)):
    log_event(logger, "pdf_export_requested", user=user.get("sub"), request_id=request_id)
    analysis = get_analysis(request_id)
    if not analysis:
        log_event(logger, "pdf_export_not_found", level="warning", request_id=request_id)
        raise HTTPException(status_code=404, detail="No analysis found for this request_id")

    path = render_analysis_pdf(analysis, request_id)
    return FileResponse(path, media_type="application/pdf", filename=f"clientiq_report_{request_id}.pdf")
