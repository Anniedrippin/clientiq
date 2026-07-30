"""
Postgres MCP connector — sales & revenue warehouse.

In production this issues real SQL through an MCP Postgres server
(e.g. `mcp-server-postgres`) over the given POSTGRES_DSN. For this
build it reads a seeded CSV so the demo is fully reproducible without
external infra, but the tool surface (`get_revenue_by_region`,
`get_account_churn`) is exactly what the real connector would expose.
"""

import csv
import os
from app.core.config import settings
from app.mcp.base import BaseMCPConnector

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mock_sales.csv")


class PostgresMCPConnector(BaseMCPConnector):
    server_name = "postgres-mcp"

    def _load(self):
        with open(_DATA_PATH, newline="") as f:
            return list(csv.DictReader(f))

    def _run(self, tool: str, **kwargs) -> dict:
        rows = self._load()
        region = kwargs.get("region")

        if tool == "get_revenue_by_region":
            if region:
                rows = [r for r in rows if r["region"].lower() == region.lower()]
            data = []
            for r in rows:
                revenue = float(r["revenue_usd"])
                prior = float(r["prior_quarter_revenue_usd"])
                change_pct = round((revenue - prior) / prior * 100, 2)
                data.append(
                    {
                        "region": r["region"],
                        "quarter": r["quarter"],
                        "revenue_usd": revenue,
                        "prior_quarter_revenue_usd": prior,
                        "change_pct": change_pct,
                        "units_sold": int(r["units_sold"]),
                    }
                )
            return {
                "data": data,
                "record_count": len(data),
                "summary": f"Queried revenue for {len(data)} region(s) via SQL: "
                f"SELECT region, revenue_usd FROM fact_sales WHERE quarter='Q2-2026'"
                + (f" AND region='{region}'" if region else ""),
            }

        if tool == "get_account_churn":
            if region:
                rows = [r for r in rows if r["region"].lower() == region.lower()]
            data = [
                {
                    "region": r["region"],
                    "churned_accounts": int(r["churned_accounts"]),
                    "active_accounts": int(r["active_accounts"]),
                    "churn_rate_pct": round(int(r["churned_accounts"]) / int(r["active_accounts"]) * 100, 2),
                }
                for r in rows
            ]
            return {
                "data": data,
                "record_count": len(data),
                "summary": "Queried churn via SQL: SELECT region, churned_accounts, active_accounts FROM dim_accounts",
            }

        raise ValueError(f"Unknown tool '{tool}' for postgres-mcp")


postgres_mcp = PostgresMCPConnector()
