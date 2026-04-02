"""
FastAPI API Layer for Inventory Intelligence Agent
Cloud Run compatible — spawns MCP server as background process
"""
import os
import sys
import uuid
import subprocess
import time
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adk_agent.agent import root_agent

APP_NAME = "inventory-intelligence-agent"
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

mcp_process = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_process

    # Start MCP server as background subprocess on port 5000
    mcp_process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.http_server"],
        env={**os.environ},
    )
    time.sleep(2)  # Give MCP server time to start
    print("🔧 MCP server started (pid:", mcp_process.pid, ")")
    print("🚀 Inventory Intelligence Agent API started")

    yield

    # Shutdown MCP server
    if mcp_process:
        mcp_process.send_signal(signal.SIGTERM)
        mcp_process.wait()
    print("🛑 Shutting down")


app = FastAPI(
    title="Inventory Intelligence Agent",
    version="1.0.0",
    lifespan=lifespan,
)

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
        {"label": "📦 Inventory Overview",   "query": "Give me an overview of our current inventory status"},
        {"label": "⚠️ Low Stock Alert",      "query": "Which raw materials are below reorder level?"},
        {"label": "🔩 Metals Stock",         "query": "Show me the stock status for all metal materials"},
        {"label": "🚚 Pending Orders",       "query": "What purchase orders are pending or delayed?"},
        {"label": "🔥 Fast-Moving Stock",    "query": "What are our top 5 most consumed materials this month?"},
        {"label": "🏭 Warehouse Breakdown",  "query": "Give me a breakdown of stock value by warehouse"},
    ]


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name=APP_NAME,
        user_id="user",
        session_id=session_id,
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

    return AskResponse(
        answer=answer,
        session_id=session_id,
        question=req.question,
    )