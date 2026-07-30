"""Slack MCP connector — reads customer-facing support/complaint channels.

Mocked with deterministic, region-seeded volumes so a demo run is
reproducible. Swap `_run` for real calls against an MCP Slack server
(`conversations.history` / `search.messages`) to go live.
"""

import hashlib
from app.mcp.base import BaseMCPConnector

_REGION_COMPLAINT_BASE = {
    "north": 1243,
    "south": 312,
    "east": 198,
    "west": 227,
}

_TOP_THEMES_BY_REGION = {
    "north": [
        {"theme": "product unavailable / backorder", "share_pct": 46},
        {"theme": "late delivery", "share_pct": 33},
        {"theme": "billing question", "share_pct": 12},
        {"theme": "other", "share_pct": 9},
    ],
    "default": [
        {"theme": "late delivery", "share_pct": 30},
        {"theme": "product unavailable / backorder", "share_pct": 20},
        {"theme": "billing question", "share_pct": 25},
        {"theme": "other", "share_pct": 25},
    ],
}


def _seeded_count(region: str) -> int:
    key = region.lower()
    if key in _REGION_COMPLAINT_BASE:
        return _REGION_COMPLAINT_BASE[key]
    # deterministic fallback for unlisted regions
    h = int(hashlib.sha1(key.encode()).hexdigest(), 16)
    return 150 + (h % 250)


class SlackMCPConnector(BaseMCPConnector):
    server_name = "slack-mcp"

    def _run(self, tool: str, **kwargs) -> dict:
        region = (kwargs.get("region") or "all-regions")

        if tool == "search_complaint_messages":
            count = _seeded_count(region)
            themes = _TOP_THEMES_BY_REGION.get(region.lower(), _TOP_THEMES_BY_REGION["default"])
            return {
                "data": {"complaint_count": count, "top_themes": themes, "channel": "#customer-support"},
                "record_count": count,
                "summary": f"Searched #customer-support for '{region}' complaints last quarter, found {count} messages",
            }

        raise ValueError(f"Unknown tool '{tool}' for slack-mcp")


slack_mcp = SlackMCPConnector()
