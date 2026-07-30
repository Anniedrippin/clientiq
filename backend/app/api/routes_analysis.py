from fastapi import APIRouter, Depends

from app.core.logging_config import get_logger, log_event, Timer, get_request_id
from app.api.deps import get_current_user
from app.models.schemas import AskRequest, AnalysisResponse
from app.agents.graph import run_analysis
from app.services.trace_service import store_analysis, get_analysis, list_recent

logger = get_logger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/ask", response_model=AnalysisResponse)
async def ask(payload: AskRequest, user: dict = Depends(get_current_user)):
    """Powers the 'Ask the AI' chat panel: runs the full LangGraph pipeline
    (MCP data collection -> root-cause analysis -> recommendations ->
    executive summary) and returns a fully-cited AnalysisResponse."""
    timer = Timer()
    request_id = get_request_id()
    log_event(
        logger,
        "analysis_request_started",
        user=user.get("sub"),
        question=payload.question,
        region=payload.region,
    )

    final_state = run_analysis(question=payload.question, region=payload.region, request_id=request_id)

    response = AnalysisResponse(
        request_id=request_id,
        question=payload.question,
        executive_summary=final_state.get("executive_summary", ""),
        root_causes=final_state.get("root_causes", []),
        recommendations=final_state.get("recommendations", []),
        citations=final_state.get("citations", []),
        trace=final_state.get("trace", []),
        kpi_snapshot=final_state.get("kpi_snapshot", {}),
    )
    store_analysis(request_id, response.model_dump())

    log_event(
        logger,
        "analysis_request_completed",
        user=user.get("sub"),
        request_id=request_id,
        duration_ms=timer.ms(),
        status="success",
        trace_steps=len(response.trace),
    )
    return response


@router.get("/history")
async def history(user: dict = Depends(get_current_user)):
    log_event(logger, "analysis_history_requested", user=user.get("sub"))
    return {"items": list_recent(limit=10)}


@router.get("/{request_id}")
async def get_by_id(request_id: str, user: dict = Depends(get_current_user)):
    log_event(logger, "analysis_lookup_requested", user=user.get("sub"), request_id=request_id)
    result = get_analysis(request_id)
    return result or {"error": "not_found"}
