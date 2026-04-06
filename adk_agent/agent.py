import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from adk_agent.sub_agents.report_agent import report_agent

root_agent = Agent(
    name="inventory_intelligence_agent",
    model="gemini-2.0-flash",
    description="Manufacturing Inventory Intelligence Agent powered by BigQuery and MCP",
    instruction="""
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
1. Always call the most relevant tool first - do not guess from memory.
2. For broad questions call get_inventory_summary THEN get_low_stock_materials.
3. For category questions call get_materials_by_category with the category name.
4. Always mention INR (Rs.) for cost/value figures.
5. If no data matches, say so clearly - never fabricate inventory numbers.
""",
    sub_agents=[report_agent],
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="python3",
                args=["-m", "mcp_server.http_server"],
                env={
                    "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
                    "GOOGLE_CLOUD_PROJECT": os.environ.get("GOOGLE_CLOUD_PROJECT", "jyothiapikey1"),
                },
            )
        )
    ],
)
