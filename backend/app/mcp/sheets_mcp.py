"""Google Sheets MCP connector — finance team's rolling forecast workbook."""

from app.mcp.base import BaseMCPConnector


class GoogleSheetsMCPConnector(BaseMCPConnector):
    server_name = "google-sheets-mcp"

    def _run(self, tool: str, **kwargs) -> dict:
        region = (kwargs.get("region") or "north").lower()

        if tool == "get_recovery_forecast":
            # Modest, defensible planning assumption used across regions.
            safety_stock_uplift_pct = 15
            data = {
                "region": region,
                "safety_stock_uplift_pct": safety_stock_uplift_pct,
                "estimated_annual_recovery_usd": 2100000 if region == "north" else 850000,
            }
            return {
                "data": data,
                "record_count": 1,
                "summary": "Read 'FY26 Recovery Scenarios' tab, row for safety-stock uplift scenario",
            }

        raise ValueError(f"Unknown tool '{tool}' for google-sheets-mcp")


sheets_mcp = GoogleSheetsMCPConnector()
