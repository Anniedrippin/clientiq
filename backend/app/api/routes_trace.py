from fastapi import APIRouter, Depends, HTTPException

from app.core.logging_config import get_logger, log_event
from app.api.deps import get_current_user
from app.services.trace_service import get_analysis

logger = get_logger(__name__)
router = APIRouter(prefix="/api/trace", tags=["trace"])


@router.get("/{request_id}")
async def get_trace(request_id: str, user: dict = Depends(get_current_user)):
    """Returns the raw LangGraph + MCP trace for the Agent Trace View:
    which tools were called, what queries ran, what came back, and how
    long each step took."""
    log_event(logger, "trace_view_requested", user=user.get("sub"), request_id=request_id)
    analysis = get_analysis(request_id)
    if not analysis:
        log_event(logger, "trace_view_not_found", level="warning", request_id=request_id)
        raise HTTPException(status_code=404, detail="No trace found for this request_id")
    return {"request_id": request_id, "trace": analysis.get("trace", [])}
