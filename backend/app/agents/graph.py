"""LangGraph orchestration for ClientIQ's root-cause analysis pipeline.

Graph shape:

    collect_sales_data -> collect_churn_data -> collect_inventory_data
    -> collect_complaints_data -> collect_logistics_data
    -> collect_forecast_data -> retrieve_historical_context
    -> analyze_root_causes -> generate_recommendations
    -> build_citations -> build_kpi_snapshot -> generate_executive_summary

Each node pulls from exactly one MCP data source (or the vector store /
LLM), and every node's activity is captured in state["trace"] using the
same TraceStep shape — this is what powers the Agent Trace View.
"""

from langgraph.graph import StateGraph, START, END

from app.core.logging_config import get_logger, log_event, Timer
from app.agents.state import AgentState, new_state
from app.agents import nodes

logger = get_logger(__name__)


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("collect_sales_data", nodes.collect_sales_data)
    graph.add_node("collect_churn_data", nodes.collect_churn_data)
    graph.add_node("collect_inventory_data", nodes.collect_inventory_data)
    graph.add_node("collect_complaints_data", nodes.collect_complaints_data)
    graph.add_node("collect_logistics_data", nodes.collect_logistics_data)
    graph.add_node("collect_forecast_data", nodes.collect_forecast_data)
    graph.add_node("retrieve_historical_context", nodes.retrieve_historical_context)
    graph.add_node("analyze_root_causes", nodes.analyze_root_causes)
    graph.add_node("generate_recommendations", nodes.generate_recommendations)
    graph.add_node("build_citations", nodes.build_citations)
    graph.add_node("build_kpi_snapshot", nodes.build_kpi_snapshot)
    graph.add_node("generate_executive_summary", nodes.generate_executive_summary)

    graph.add_edge(START, "collect_sales_data")
    graph.add_edge("collect_sales_data", "collect_churn_data")
    graph.add_edge("collect_churn_data", "collect_inventory_data")
    graph.add_edge("collect_inventory_data", "collect_complaints_data")
    graph.add_edge("collect_complaints_data", "collect_logistics_data")
    graph.add_edge("collect_logistics_data", "collect_forecast_data")
    graph.add_edge("collect_forecast_data", "retrieve_historical_context")
    graph.add_edge("retrieve_historical_context", "analyze_root_causes")
    graph.add_edge("analyze_root_causes", "generate_recommendations")
    graph.add_edge("generate_recommendations", "build_citations")
    graph.add_edge("build_citations", "build_kpi_snapshot")
    graph.add_edge("build_kpi_snapshot", "generate_executive_summary")
    graph.add_edge("generate_executive_summary", END)

    return graph.compile()


_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        timer = Timer()
        _compiled_graph = build_graph()
        log_event(logger, "langgraph_compiled", duration_ms=timer.ms(), node_count=12)
    return _compiled_graph


def run_analysis(question: str, region: str, request_id: str) -> AgentState:
    timer = Timer()
    log_event(logger, "langgraph_run_started", question=question, region=region)

    graph = get_compiled_graph()
    initial_state = new_state(question=question, region=region, request_id=request_id)
    final_state = graph.invoke(initial_state)

    log_event(
        logger,
        "langgraph_run_completed",
        duration_ms=timer.ms(),
        trace_step_count=len(final_state.get("trace", [])),
        status="success",
    )
    return final_state
