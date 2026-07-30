"""Jira MCP connector — operations/logistics ticket board."""

from app.mcp.base import BaseMCPConnector

_DELAY_TICKETS = {
    "north": {"count": 87, "avg_delay_days": 4.6, "prior_avg_delay_days": 2.1},
    "south": {"count": 21, "avg_delay_days": 1.8, "prior_avg_delay_days": 1.6},
    "east": {"count": 14, "avg_delay_days": 1.5, "prior_avg_delay_days": 1.4},
    "west": {"count": 19, "avg_delay_days": 1.9, "prior_avg_delay_days": 1.7},
}


class JiraMCPConnector(BaseMCPConnector):
    server_name = "jira-mcp"

    def _run(self, tool: str, **kwargs) -> dict:
        region = (kwargs.get("region") or "north").lower()

        if tool == "get_logistics_delay_tickets":
            stats = _DELAY_TICKETS.get(region, {"count": 10, "avg_delay_days": 1.5, "prior_avg_delay_days": 1.4})
            change_pct = round(
                (stats["avg_delay_days"] - stats["prior_avg_delay_days"]) / stats["prior_avg_delay_days"] * 100, 1
            )
            return {
                "data": {**stats, "change_pct": change_pct, "project": "OPS-LOGISTICS"},
                "record_count": stats["count"],
                "summary": f"Queried OPS-LOGISTICS board for delivery-delay tickets in {region}, "
                f"found {stats['count']} open/resolved tickets",
            }

        raise ValueError(f"Unknown tool '{tool}' for jira-mcp")


jira_mcp = JiraMCPConnector()
