"""CSV MCP connector — analyst-uploaded spreadsheets (e.g. inventory logs).

Represents the "CSV upload" data source in the brief. Reads whatever is in
app/data/*.csv today; a real deployment would point this at an MCP
filesystem/CSV server rooted at the client's shared drive.
"""

import csv
import os
from app.mcp.base import BaseMCPConnector

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mock_inventory.csv")


class CSVMCPConnector(BaseMCPConnector):
    server_name = "csv-mcp"

    def _load(self):
        with open(_DATA_PATH, newline="") as f:
            return list(csv.DictReader(f))

    def _run(self, tool: str, **kwargs) -> dict:
        rows = self._load()
        region = kwargs.get("region")

        if tool == "get_inventory_stockouts":
            if region:
                rows = [r for r in rows if r["region"].lower() == region.lower()]
            data = []
            total_events = 0
            for r in rows:
                rate = float(r["stockout_rate_pct"])
                prior = float(r["prior_quarter_rate_pct"])
                change_pct = round((rate - prior) / prior * 100, 2)
                total_events += int(r["stockout_events"])
                data.append(
                    {
                        "region": r["region"],
                        "sku_category": r["sku_category"],
                        "stockout_events": int(r["stockout_events"]),
                        "stockout_rate_pct": rate,
                        "change_pct": change_pct,
                    }
                )
            avg_change = round(sum(d["change_pct"] for d in data) / len(data), 1) if data else 0
            return {
                "data": data,
                "record_count": len(data),
                "total_stockout_events": total_events,
                "avg_stockout_rate_change_pct": avg_change,
                "summary": f"Parsed inventory_shortages_q2_2026.csv, {len(data)} SKU-category rows"
                + (f" for region '{region}'" if region else ""),
            }

        raise ValueError(f"Unknown tool '{tool}' for csv-mcp")


csv_mcp = CSVMCPConnector()
