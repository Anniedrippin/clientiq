"""Shared state schema for the ClientIQ LangGraph analysis graph, plus the
trace-recording helper used by every node so the Agent Trace View always
receives entries in one consistent shape."""

from typing import TypedDict, Any, Optional
from datetime import datetime, timezone


class AgentState(TypedDict, total=False):
    question: str
    region: Optional[str]
    request_id: str

    sales_data: dict
    churn_data: dict
    inventory_data: dict
    complaints_data: dict
    logistics_data: dict
    forecast_data: dict
    historical_context: list

    root_causes: list
    recommendations: list
    executive_summary: str
    citations: list
    kpi_snapshot: dict

    trace: list  # append-only list of trace step dicts


def new_state(question: str, region: Optional[str], request_id: str) -> AgentState:
    return AgentState(question=question, region=region, request_id=request_id, trace=[])


def record_trace_step(state: AgentState, node: str, action: str, status: str,
                       duration_ms: float, tool: Optional[str] = None,
                       input_payload: Any = None, output_summary: Optional[str] = None) -> None:
    """Every LangGraph node calls this exactly the same way so the trace
    the frontend renders is uniform regardless of which node produced it."""
    step = {
        "step_id": len(state["trace"]) + 1,
        "node": node,
        "action": action,
        "tool": tool,
        "input": input_payload,
        "output_summary": output_summary,
        "status": status,
        "duration_ms": duration_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    state["trace"].append(step)


def absorb_mcp_trace(state: AgentState, mcp_trace: list) -> None:
    """MCP connectors append raw call records into a plain list (see
    mcp/base.py); this promotes each into a proper numbered TraceStep."""
    for raw in mcp_trace:
        step = {
            "step_id": len(state["trace"]) + 1,
            "node": raw.get("node", "mcp_connector"),
            "action": raw.get("action"),
            "tool": raw.get("tool"),
            "input": raw.get("input"),
            "output_summary": raw.get("output_summary"),
            "status": raw.get("status"),
            "duration_ms": raw.get("duration_ms"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["trace"].append(step)
