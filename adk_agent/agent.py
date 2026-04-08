import os
from dotenv import load_dotenv

# Load .env from project root
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)

from mcp import StdioServerParameters
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from adk_agent.sub_agents.report_agent import make_report_agent

# Project root — ensures `python3 -m mcp_server.stdio_server` resolves correctly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AGENT_NAME = "inventory_intelligence_agent"

AGENT_INSTRUCTION = """
You are an expert Manufacturing Inventory Intelligence Assistant.
You help factory managers, purchase officers, and operations teams make
fast, data-driven decisions about raw material inventory.

You have access to live BigQuery data via MCP tools:
- get_low_stock_materials       -> materials at or below reorder level
- get_inventory_summary         -> high-level overview of entire inventory
- get_materials_by_category     -> filter by category (Metals, Polymers, etc.)
- get_pending_purchase_orders   -> open/delayed purchase orders
- get_top_consumed_materials    -> fastest moving materials (last 30 days)
- get_warehouse_stock_breakdown -> stock value per warehouse

BEHAVIOR RULES:
1. Always call the most relevant tool first — do not guess from memory.
2. For broad questions call get_inventory_summary first.
3. For category questions call get_materials_by_category.
4. For purchase order issues call get_pending_purchase_orders.
5. When you have raw data, delegate formatting to the report_agent.
6. Always cite exact numbers (stock levels, values in ₹, lead times).
7. Never invent data — only use what the tools return.
"""


def create_agent() -> Agent:
    """
    Creates the root agent with McpToolset wired in.
    In ADK 1.28.1+, McpToolset is a BaseToolset passed directly in tools=[].
    The framework calls get_tools() automatically at runtime — no async setup needed.
    """
    mcp_toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python3",
                args=["-m", "mcp_server.stdio_server"],
                env={
                    **os.environ,
                    "PYTHONPATH": PROJECT_ROOT,
                },
            ),
            timeout=10.0,
        ),
    )

    return Agent(
        name=AGENT_NAME,
        model="gemini-2.5-flash",
        description="Manufacturing Inventory Intelligence Agent powered by BigQuery and MCP",
        instruction=AGENT_INSTRUCTION,
        tools=[mcp_toolset],
        sub_agents=[make_report_agent()],
    )