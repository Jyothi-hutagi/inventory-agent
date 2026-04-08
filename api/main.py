"""
FastAPI API Layer for Inventory Intelligence Agent
"""
import os
import sys
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "inventory-intelligence-agent"
AGENT_NAME = "inventory_intelligence_agent"

_runner = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _runner

    try:
        logger.info("Importing ADK dependencies...")
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from adk_agent.agent import create_agent

        logger.info("Creating agent...")
        agent = create_agent()

        logger.info("Creating session service...")
        session_service = InMemorySessionService()

        logger.info("Creating runner...")
        _runner = Runner(
            agent=agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        # Store session_service on runner for use in ask()
        _runner._session_service_ref = session_service

        logger.info("🚀 Inventory Intelligence Agent API started")

    except Exception as e:
        logger.exception(f"❌ Failed to start agent: {e}")
        raise

    yield
    logger.info("🛑 Shutting down")


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
    return {"status": "ok", "agent": AGENT_NAME}


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
    from google.genai import types

    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if _runner is None:
        raise HTTPException(status_code=503, detail="Agent not ready yet")

    session_service = _runner._session_service_ref
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name=APP_NAME,
        user_id="user",
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=req.question)],
    )

    answer_parts = []
    async for event in _runner.run_async(
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))