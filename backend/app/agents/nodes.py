"""LangGraph node implementations for the ClientIQ analysis graph.

Every node follows the identical pattern:
  1. log_event(..., "<node>_started")
  2. do the work (call an MCP connector and/or the LLM/vector store)
  3. absorb the tool-call trace into state["trace"]
  4. log_event(..., "<node>_completed", duration_ms=...)

This keeps every node individually auditable and gives the Agent Trace
View a uniform structure no matter which node produced a given step.
"""

from app.core.logging_config import get_logger, log_event, Timer
from app.agents.state import AgentState, record_trace_step, absorb_mcp_trace
from app.mcp.registry import MCP_CONNECTORS
from app.services.vector_store import vector_store
from app.services.groq_service import groq_service

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data collection nodes — each hits exactly one MCP connector
# ---------------------------------------------------------------------------

def collect_sales_data(state: AgentState) -> AgentState:
    node = "collect_sales_data"
    timer = Timer()
    log_event(logger, f"{node}_started", region=state.get("region"))
    mcp_trace: list = []
    result = MCP_CONNECTORS["postgres"].call_tool(
        "get_revenue_by_region", trace=mcp_trace, region=state.get("region")
    )
    state["sales_data"] = result["data"]
    absorb_mcp_trace(state, mcp_trace)
    log_event(logger, f"{node}_completed", duration_ms=timer.ms(), rows=len(result["data"]))
    return state


def collect_churn_data(state: AgentState) -> AgentState:
    node = "collect_churn_data"
    timer = Timer()
    log_event(logger, f"{node}_started", region=state.get("region"))
    mcp_trace: list = []
    revenue_result = MCP_CONNECTORS["postgres"].call_tool(
        "get_account_churn", trace=mcp_trace, region=state.get("region")
    )
    reasons_result = MCP_CONNECTORS["salesforce"].call_tool(
        "get_churn_reason_codes", trace=mcp_trace, region=state.get("region")
    )
    state["churn_data"] = {"accounts": revenue_result["data"], "reasons": reasons_result["data"]}
    absorb_mcp_trace(state, mcp_trace)
    log_event(logger, f"{node}_completed", duration_ms=timer.ms())
    return state


def collect_inventory_data(state: AgentState) -> AgentState:
    node = "collect_inventory_data"
    timer = Timer()
    log_event(logger, f"{node}_started", region=state.get("region"))
    mcp_trace: list = []
    result = MCP_CONNECTORS["csv"].call_tool("get_inventory_stockouts", trace=mcp_trace, region=state.get("region"))
    state["inventory_data"] = result
    absorb_mcp_trace(state, mcp_trace)
    log_event(logger, f"{node}_completed", duration_ms=timer.ms(), rows=result.get("record_count"))
    return state


def collect_complaints_data(state: AgentState) -> AgentState:
    node = "collect_complaints_data"
    timer = Timer()
    log_event(logger, f"{node}_started", region=state.get("region"))
    mcp_trace: list = []
    result = MCP_CONNECTORS["slack"].call_tool("search_complaint_messages", trace=mcp_trace, region=state.get("region"))
    state["complaints_data"] = result["data"]
    absorb_mcp_trace(state, mcp_trace)
    log_event(logger, f"{node}_completed", duration_ms=timer.ms(), complaint_count=result["data"]["complaint_count"])
    return state


def collect_logistics_data(state: AgentState) -> AgentState:
    node = "collect_logistics_data"
    timer = Timer()
    log_event(logger, f"{node}_started", region=state.get("region"))
    mcp_trace: list = []
    result = MCP_CONNECTORS["jira"].call_tool("get_logistics_delay_tickets", trace=mcp_trace, region=state.get("region"))
    state["logistics_data"] = result["data"]
    absorb_mcp_trace(state, mcp_trace)
    log_event(logger, f"{node}_completed", duration_ms=timer.ms())
    return state


def collect_forecast_data(state: AgentState) -> AgentState:
    node = "collect_forecast_data"
    timer = Timer()
    log_event(logger, f"{node}_started", region=state.get("region"))
    mcp_trace: list = []
    result = MCP_CONNECTORS["google_sheets"].call_tool("get_recovery_forecast", trace=mcp_trace, region=state.get("region"))
    state["forecast_data"] = result["data"]
    absorb_mcp_trace(state, mcp_trace)
    log_event(logger, f"{node}_completed", duration_ms=timer.ms())
    return state


def retrieve_historical_context(state: AgentState) -> AgentState:
    node = "retrieve_historical_context"
    timer = Timer()
    log_event(logger, f"{node}_started", question=state["question"])
    docs = vector_store.query(state["question"], n_results=3, region=state.get("region"))
    state["historical_context"] = docs
    record_trace_step(
        state,
        node="retrieve_historical_context",
        action="Queried ChromaDB vector store for prior quarterly reports",
        tool="chromadb.query",
        input_payload={"query": state["question"], "n_results": 3},
        output_summary=f"Retrieved {len(docs)} historical report(s)",
        status="success",
        duration_ms=timer.ms(),
    )
    log_event(logger, f"{node}_completed", duration_ms=timer.ms(), doc_count=len(docs))
    return state


# ---------------------------------------------------------------------------
# Reasoning nodes
# ---------------------------------------------------------------------------

def analyze_root_causes(state: AgentState) -> AgentState:
    node = "analyze_root_causes"
    timer = Timer()
    log_event(logger, f"{node}_started")

    inventory = state.get("inventory_data", {})
    logistics = state.get("logistics_data", {})
    complaints = state.get("complaints_data", {})

    fallback_causes = []
    if inventory.get("avg_stockout_rate_change_pct", 0) > 0:
        fallback_causes.append(
            {
                "rank": "primary",
                "description": "Inventory stockouts increased across core SKU categories, "
                "driving backorders and lost sales.",
                "metric": "stockout_rate_pct",
                "change_pct": inventory.get("avg_stockout_rate_change_pct", 0),
                "evidence_count": inventory.get("total_stockout_events", 0),
            }
        )
    if logistics.get("change_pct", 0) > 0:
        fallback_causes.append(
            {
                "rank": "secondary",
                "description": "Delivery delays increased, correlating with a rise in customer "
                "churn and complaint volume.",
                "metric": "avg_delay_days",
                "change_pct": logistics.get("change_pct", 0),
                "evidence_count": logistics.get("count", 0),
            }
        )
    if not fallback_causes:
        fallback_causes.append(
            {
                "rank": "primary",
                "description": "No single dominant driver identified; performance change is "
                "broadly distributed across regions/categories.",
                "metric": "revenue_usd",
                "change_pct": 0,
                "evidence_count": complaints.get("complaint_count", 0),
            }
        )

    llm_result = groq_service.generate_json(
        system_prompt=(
            "You are a senior management consultant. Given structured evidence about revenue, "
            "inventory stockouts, delivery delays, and customer complaints, identify the primary "
            "and secondary root causes of the business performance change. Return strict JSON: "
            '{"root_causes": [{"rank": "primary"|"secondary", "description": str, "metric": str, '
            '"change_pct": number, "evidence_count": int}]}'
        ),
        user_prompt=(
            f"Question: {state['question']}\n"
            f"Inventory data: {inventory}\n"
            f"Logistics data: {logistics}\n"
            f"Complaints data: {complaints}\n"
        ),
        fallback={"root_causes": fallback_causes},
    )
    state["root_causes"] = llm_result.get("root_causes", fallback_causes)

    record_trace_step(
        state,
        node="analyze_root_causes",
        action="Compared inventory, logistics, and complaint patterns to identify root causes",
        tool="groq_llm.reasoning" if groq_service.enabled else "local_fallback_reasoning",
        input_payload={"signals": ["inventory", "logistics", "complaints"]},
        output_summary=f"Identified {len(state['root_causes'])} root cause(s)",
        status="success",
        duration_ms=timer.ms(),
    )
    log_event(logger, f"{node}_completed", duration_ms=timer.ms(), cause_count=len(state["root_causes"]))
    return state


def generate_recommendations(state: AgentState) -> AgentState:
    node = "generate_recommendations"
    timer = Timer()
    log_event(logger, f"{node}_started")

    forecast = state.get("forecast_data", {})
    uplift = forecast.get("safety_stock_uplift_pct", 15)
    recovery = forecast.get("estimated_annual_recovery_usd", 0)

    fallback_recs = [
        {
            "title": f"Increase safety stock by {uplift}%",
            "detail": "Raise buffer inventory for the SKU categories showing the sharpest "
            "stockout-rate increase to reduce backorders.",
            "estimated_impact": f"Recover ~${recovery:,.0f} annual revenue" if recovery else "Reduces backorder rate",
            "priority": "high",
        },
        {
            "title": "Reroute logistics for high-delay lanes",
            "detail": "Shift fulfillment for the affected region to a secondary carrier/warehouse "
            "to cut average delivery delay back toward baseline.",
            "estimated_impact": "Reduces churn linked to late-delivery complaints",
            "priority": "high",
        },
        {
            "title": "Proactive outreach to at-risk accounts",
            "detail": "Use CRM churn-reason data to contact accounts citing stockouts/delays "
            "before contract renewal.",
            "estimated_impact": "Improves retention of accounts already flagged as at-risk",
            "priority": "medium",
        },
    ]

    llm_result = groq_service.generate_json(
        system_prompt=(
            "You are a senior management consultant. Given root causes and a recovery forecast, "
            "produce 2-4 concrete, prioritized recommendations. Return strict JSON: "
            '{"recommendations": [{"title": str, "detail": str, "estimated_impact": str, '
            '"priority": "high"|"medium"|"low"}]}'
        ),
        user_prompt=f"Root causes: {state.get('root_causes')}\nForecast: {forecast}",
        fallback={"recommendations": fallback_recs},
    )
    state["recommendations"] = llm_result.get("recommendations", fallback_recs)

    record_trace_step(
        state,
        node="generate_recommendations",
        action="Formed prioritized action plan from root causes + recovery forecast",
        tool="groq_llm.reasoning" if groq_service.enabled else "local_fallback_reasoning",
        output_summary=f"Generated {len(state['recommendations'])} recommendation(s)",
        status="success",
        duration_ms=timer.ms(),
    )
    log_event(logger, f"{node}_completed", duration_ms=timer.ms(), rec_count=len(state["recommendations"]))
    return state


def build_citations(state: AgentState) -> AgentState:
    node = "build_citations"
    timer = Timer()
    log_event(logger, f"{node}_started")

    citations = []
    complaints = state.get("complaints_data", {})
    inventory = state.get("inventory_data", {})
    logistics = state.get("logistics_data", {})
    sales = state.get("sales_data", [])

    if sales:
        citations.append(
            {
                "source_type": "postgres",
                "source_name": "Sales Data Warehouse",
                "reference": "fact_sales (Q2-2026)",
                "snippet": f"{len(sales)} region revenue record(s) retrieved via SQL query",
                "record_count": len(sales),
            }
        )
    if complaints:
        citations.append(
            {
                "source_type": "slack",
                "source_name": "#customer-support",
                "reference": "customer complaint search",
                "snippet": f"{complaints.get('complaint_count', 0)} complaint messages analyzed for recurring themes",
                "record_count": complaints.get("complaint_count", 0),
            }
        )
    if inventory:
        citations.append(
            {
                "source_type": "csv",
                "source_name": "inventory_shortages_q2_2026.csv",
                "reference": "analyst-uploaded inventory log",
                "snippet": f"{inventory.get('record_count', 0)} SKU-category rows, "
                f"{inventory.get('total_stockout_events', 0)} stockout events",
                "record_count": inventory.get("record_count", 0),
            }
        )
    if logistics:
        citations.append(
            {
                "source_type": "jira",
                "source_name": "OPS-LOGISTICS board",
                "reference": "delivery delay tickets",
                "snippet": f"{logistics.get('count', 0)} tickets, avg delay {logistics.get('avg_delay_days')} days",
                "record_count": logistics.get("count", 0),
            }
        )
    for doc in state.get("historical_context", []):
        citations.append(
            {
                "source_type": "vector_store",
                "source_name": "ChromaDB historical reports",
                "reference": doc.get("id", "unknown"),
                "snippet": doc.get("text", "")[:180],
                "record_count": 1,
            }
        )

    state["citations"] = citations
    record_trace_step(
        state,
        node="build_citations",
        action="Assembled data lineage for every source used in the analysis",
        output_summary=f"{len(citations)} citation(s) with full data lineage",
        status="success",
        duration_ms=timer.ms(),
    )
    log_event(logger, f"{node}_completed", duration_ms=timer.ms(), citation_count=len(citations))
    return state


def generate_executive_summary(state: AgentState) -> AgentState:
    node = "generate_executive_summary"
    timer = Timer()
    log_event(logger, f"{node}_started")

    causes = state.get("root_causes", [])
    recs = state.get("recommendations", [])
    primary = next((c for c in causes if c.get("rank") == "primary"), causes[0] if causes else None)
    secondary = next((c for c in causes if c.get("rank") == "secondary"), None)

    fallback_summary = (
        f"Analysis of {state['question']!r} found "
        + (f"a primary cause: {primary['description']} " if primary else "")
        + (f"A secondary cause: {secondary['description']} " if secondary else "")
        + f"Evidence spans {len(state.get('citations', []))} data sources across CRM, ERP, support, and inventory systems. "
        + (f"Top recommendation: {recs[0]['title']}. {recs[0]['estimated_impact']}." if recs else "")
    )

    llm_result = groq_service.generate_json(
        system_prompt=(
            "You are a senior partner at a top-tier consulting firm writing a crisp, "
            "executive-ready summary (3-5 sentences, no fluff, quantified where possible). "
            'Return strict JSON: {"executive_summary": str}'
        ),
        user_prompt=f"Question: {state['question']}\nRoot causes: {causes}\nRecommendations: {recs}",
        fallback={"executive_summary": fallback_summary},
    )
    state["executive_summary"] = llm_result.get("executive_summary", fallback_summary)

    record_trace_step(
        state,
        node="generate_executive_summary",
        action="Synthesized root causes + recommendations into an executive summary",
        tool="groq_llm.generation" if groq_service.enabled else "local_fallback_reasoning",
        output_summary="Executive summary generated",
        status="success",
        duration_ms=timer.ms(),
    )
    log_event(logger, f"{node}_completed", duration_ms=timer.ms(), summary_chars=len(state["executive_summary"]))
    return state


def build_kpi_snapshot(state: AgentState) -> AgentState:
    node = "build_kpi_snapshot"
    timer = Timer()
    log_event(logger, f"{node}_started")

    sales = state.get("sales_data", [])
    churn = state.get("churn_data", {})
    inventory = state.get("inventory_data", {})

    revenue_row = sales[0] if sales else {}
    churn_rows = churn.get("accounts", [])
    churn_row = churn_rows[0] if churn_rows else {}

    snapshot = {
        "revenue_usd": revenue_row.get("revenue_usd"),
        "revenue_change_pct": revenue_row.get("change_pct"),
        "churn_rate_pct": churn_row.get("churn_rate_pct"),
        "stockout_rate_change_pct": inventory.get("avg_stockout_rate_change_pct"),
    }
    state["kpi_snapshot"] = snapshot
    record_trace_step(
        state,
        node="build_kpi_snapshot",
        action="Computed headline KPI snapshot for dashboard cards",
        output_summary="KPI snapshot ready",
        status="success",
        duration_ms=timer.ms(),
    )
    log_event(logger, f"{node}_completed", duration_ms=timer.ms())
    return state
