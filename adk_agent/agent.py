import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from adk_agent.sub_agents.report_agent import report_agent

MCP_PARAMS = StdioServerParameters(
    command="python3",
    args=["-m", "mcp_server.http_server"],
    env={
        "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
        "GOOGLE_CLOUD_PROJECT": os.environ.get("GOOGLE_CLOUD_PROJECT", "jyothiapikey1"),
        "PATH": os.environ.get("PATH", ""),
    },
)

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
2. For broad questions call get_inventory_

cat > api/main.py << 'EOF'
import os
import sys
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adk_agent.agent import root_agent, _mcp_params

APP_NAME = "inventory-intelligence-agent"
session_service = InMemorySessionService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Inventory Intelligence Agent API started")
    yield
    print("🛑 Shutting down")

app = FastAPI(title="Inventory Intelligence Agent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str
    session_id: str | None = None

class AskResponse(BaseModel):
    answer: str
    session_id: str
    question: str

@app.get("/health")
def health():
    return {"status": "ok", "agent": root_agent.name}

@app.get("/samples")
def sample_queries():
    return [
        {"label": "📦 Inventory Overview",  "query": "Give me an overview of our current inventory status"},
        {"label": "⚠️ Low Stock Alert",     "query": "Which raw materials are below reorder level?"},
        {"label": "🔩 Metals Stock",        "query": "Show me the stock status for all metal materials"},
        {"label": "🚚 Pending Orders",      "query": "What purchase orders are pending or delayed?"},
        {"label": "🔥 Fast-Moving Stock",   "query": "What are our top 5 most consumed materials this month?"},
        {"label": "🏭 Warehouse Breakdown", "query": "Give me a breakdown of stock value by warehouse"},
    ]

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async with MCPToolset(connection_params=_mcp_params) as toolset:
        tools, _ = await toolset.get_tools_async()
        root_agent.tools = tools

        session_id = str(uuid.uuid4())
        await session_service.create_session(
            app_name=APP_NAME,
            user_id="user",
            session_id=session_id,
        )

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        message = types.Content(
            role="user",
            parts=[types.Part(text=req.question)]
        )

        answer_parts = []
        async for event in runner.run_async(
            user_id="user",
            session_id=session_id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        answer_parts.append(part.text)

    answer = "\n".join(answer_parts).strip() or "No response generated."
    return AskResponse(answer=answer, session_id=session_id, question=req.question)
