import os
from importlib import import_module
from dotenv import load_dotenv

# Load .env
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)

from google.adk.agents import Agent
from mcp import StdioServerParameters

from adk_agent.sub_agents.report_agent import make_report_agent

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AGENT_NAME = "inventory_intelligence_agent"

AGENT_INSTRUCTION = """
You are an expert Manufacturing Inventory Intelligence Assistant.
Always use tools to fetch real data. Never hallucinate.
"""


def _resolve_mcp_classes():
    """
    Resolve ADK MCP symbols across multiple google-adk versions.
    """
    toolset_module_candidates = [
        "google.adk.tools.mcp_tool.mcp_toolset",
        "google.adk.tools",
    ]
    toolset_class_names = ["McpToolset", "MCPToolset"]

    mcp_toolset_cls = None
    for module_name in toolset_module_candidates:
        try:
            module = import_module(module_name)
        except ImportError:
            continue

        for class_name in toolset_class_names:
            if hasattr(module, class_name):
                mcp_toolset_cls = getattr(module, class_name)
                break
        if mcp_toolset_cls:
            break

    if not mcp_toolset_cls:
        raise ImportError("MCP Toolset class not found in google-adk.")

    stdio_connection_params_cls = None
    try:
        session_module = import_module("google.adk.tools.mcp_tool.mcp_session_manager")
        stdio_connection_params_cls = getattr(session_module, "StdioConnectionParams", None)
    except ImportError:
        stdio_connection_params_cls = None

    return mcp_toolset_cls, stdio_connection_params_cls


def create_agent() -> Agent:
    """
    Create ADK agent with MCP toolset
    """

    mcp_toolset_cls, stdio_connection_params_cls = _resolve_mcp_classes()

    stdio_server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.stdio_server"],
        env={
            **os.environ,
            "PYTHONPATH": PROJECT_ROOT,
        },
    )

    if stdio_connection_params_cls:
        connection_params = stdio_connection_params_cls(
            server_params=stdio_server_params,
            timeout=20.0,
        )
    else:
        # Some ADK versions accept StdioServerParameters directly.
        connection_params = stdio_server_params

    mcp_toolset = mcp_toolset_cls(connection_params=connection_params)

    return Agent(
        name=AGENT_NAME,
        model="gemini-2.5-flash",
        description="Inventory Intelligence Agent",
        instruction=AGENT_INSTRUCTION,
        tools=[mcp_toolset],
        sub_agents=[make_report_agent()],
    )