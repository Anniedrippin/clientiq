"""Central registry of all MCP connectors ClientIQ is wired up to.

The agent graph pulls connectors from here rather than importing each
module directly, so adding a new enterprise data source is one line.
"""

from app.core.logging_config import get_logger, log_event
from app.mcp.postgres_mcp import postgres_mcp
from app.mcp.csv_mcp import csv_mcp
from app.mcp.slack_mcp import slack_mcp
from app.mcp.jira_mcp import jira_mcp
from app.mcp.salesforce_mcp import salesforce_mcp
from app.mcp.sheets_mcp import sheets_mcp

logger = get_logger(__name__)

MCP_CONNECTORS = {
    "postgres": postgres_mcp,
    "csv": csv_mcp,
    "slack": slack_mcp,
    "jira": jira_mcp,
    "salesforce": salesforce_mcp,
    "google_sheets": sheets_mcp,
}

log_event(
    logger,
    "mcp_registry_initialized",
    connectors=list(MCP_CONNECTORS.keys()),
)
