from fastapi import APIRouter, Depends, Query

from app.core.logging_config import get_logger, log_event, Timer
from app.api.deps import get_current_user
from app.mcp.registry import MCP_CONNECTORS

logger = get_logger(__name__)
router = APIRouter(prefix="/api/kpi", tags=["kpi"])


@router.get("")
async def get_kpis(region: str | None = Query(default=None), user: dict = Depends(get_current_user)):
    """Headline KPI cards + anomaly alerts for the executive dashboard."""
    timer = Timer()
    log_event(logger, "kpi_fetch_started", user=user.get("sub"), region=region)

    revenue_result = MCP_CONNECTORS["postgres"].call_tool("get_revenue_by_region", region=region)
    churn_result = MCP_CONNECTORS["postgres"].call_tool("get_account_churn", region=region)
    inventory_result = MCP_CONNECTORS["csv"].call_tool("get_inventory_stockouts", region=region)

    kpis = []
    for row in revenue_result["data"]:
        kpis.append(
            {
                "name": f"Revenue — {row['region']}",
                "value": row["revenue_usd"],
                "unit": "USD",
                "change_pct": row["change_pct"],
                "trend": "down" if row["change_pct"] < 0 else "up",
                "is_anomaly": abs(row["change_pct"]) >= 10,
            }
        )
    for row in churn_result["data"]:
        kpis.append(
            {
                "name": f"Churn Rate — {row['region']}",
                "value": row["churn_rate_pct"],
                "unit": "%",
                "change_pct": row["churn_rate_pct"],
                "trend": "up",
                "is_anomaly": row["churn_rate_pct"] >= 4,
            }
        )
    for row in inventory_result["data"]:
        kpis.append(
            {
                "name": f"Stockout Rate — {row['region']} ({row['sku_category']})",
                "value": row["stockout_rate_pct"],
                "unit": "%",
                "change_pct": row["change_pct"],
                "trend": "up" if row["change_pct"] > 0 else "down",
                "is_anomaly": row["change_pct"] >= 20,
            }
        )

    anomalies = [k for k in kpis if k["is_anomaly"]]

    log_event(
        logger,
        "kpi_fetch_completed",
        user=user.get("sub"),
        duration_ms=timer.ms(),
        kpi_count=len(kpis),
        anomaly_count=len(anomalies),
    )
    return {"kpis": kpis, "anomalies": anomalies}
