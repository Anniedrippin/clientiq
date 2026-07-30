"""
Base class for MCP (Model Context Protocol) data-source connectors.

Each connector below models what a real MCP client call looks like
(`server`, `tool`, structured `input`/`output`) so swapping the mock
`_run()` implementation for a real `mcp` python-sdk `ClientSession.call_tool()`
against a live Postgres/Slack/Jira/Salesforce MCP server is a drop-in change —
nothing above this layer (agents, API routes) needs to change.

Every connector call is logged with the exact same template via
`log_event`, and every call also appends a TraceStep-shaped record to
the current AgentTrace (see agents/state.py) so the frontend's Agent
Trace View can show precisely which MCP tools were invoked, with what
query, and what came back.
"""

import abc
from typing import Any, Optional

from app.core.logging_config import get_logger, log_event, Timer

logger = get_logger(__name__)


class MCPToolError(Exception):
    pass


class BaseMCPConnector(abc.ABC):
    server_name: str = "unknown-mcp-server"

    @abc.abstractmethod
    def _run(self, tool: str, **kwargs) -> dict:
        """Executes the tool call against the (mock) data source and
        returns a dict with at minimum: {"data": ..., "record_count": int}"""
        raise NotImplementedError

    def call_tool(self, tool: str, trace: Optional[list] = None, **kwargs) -> dict:
        timer = Timer()
        log_event(
            logger,
            "mcp_tool_call_started",
            server=self.server_name,
            tool=tool,
            input=kwargs,
        )
        try:
            result = self._run(tool, **kwargs)
            duration = timer.ms()
            log_event(
                logger,
                "mcp_tool_call_completed",
                server=self.server_name,
                tool=tool,
                status="success",
                duration_ms=duration,
                record_count=result.get("record_count"),
            )
            if trace is not None:
                trace.append(
                    {
                        "node": "mcp_connector",
                        "action": f"Called {self.server_name}",
                        "tool": tool,
                        "input": kwargs,
                        "output_summary": result.get("summary", f"{result.get('record_count', 0)} records returned"),
                        "status": "success",
                        "duration_ms": duration,
                    }
                )
            return result
        except Exception as exc:  # noqa: BLE001
            duration = timer.ms()
            log_event(
                logger,
                "mcp_tool_call_failed",
                level="error",
                server=self.server_name,
                tool=tool,
                status="error",
                error=str(exc),
                duration_ms=duration,
            )
            if trace is not None:
                trace.append(
                    {
                        "node": "mcp_connector",
                        "action": f"Called {self.server_name}",
                        "tool": tool,
                        "input": kwargs,
                        "output_summary": f"error: {exc}",
                        "status": "error",
                        "duration_ms": duration,
                    }
                )
            raise MCPToolError(str(exc)) from exc
