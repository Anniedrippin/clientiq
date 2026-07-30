"""Salesforce-like CRM MCP connector — churn reason codes & account health."""

from app.mcp.base import BaseMCPConnector

_CHURN_REASONS = {
    "north": [
        {"reason": "Repeated stockouts", "share_pct": 41},
        {"reason": "Late delivery", "share_pct": 29},
        {"reason": "Price", "share_pct": 18},
        {"reason": "Switched vendor", "share_pct": 12},
    ],
    "default": [
        {"reason": "Price", "share_pct": 34},
        {"reason": "Switched vendor", "share_pct": 26},
        {"reason": "Support quality", "share_pct": 22},
        {"reason": "Other", "share_pct": 18},
    ],
}


class SalesforceMCPConnector(BaseMCPConnector):
    server_name = "salesforce-mcp"

    def _run(self, tool: str, **kwargs) -> dict:
        region = (kwargs.get("region") or "").lower()

        if tool == "get_churn_reason_codes":
            reasons = _CHURN_REASONS.get(region, _CHURN_REASONS["default"])
            return {
                "data": reasons,
                "record_count": len(reasons),
                "summary": f"Queried CRM closed-lost opportunities for region '{region or 'all'}'",
            }

        raise ValueError(f"Unknown tool '{tool}' for salesforce-mcp")


salesforce_mcp = SalesforceMCPConnector()
