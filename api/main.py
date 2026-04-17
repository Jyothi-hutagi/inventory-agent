"""
FastAPI API Layer for Inventory Intelligence Agent (Cloud Run Ready)
"""

import os
import sys
import uuid
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.adk
print("ADK VERSION:", google.adk.__version__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "inventory-intelligence-agent"
AGENT_NAME = "inventory_intelligence_agent"

# 🔥 Lazy-loaded runner (IMPORTANT for Cloud Run)
_runner = None


def get_runner():
    """
    Lazy initialization of ADK Runner.
    Prevents Cloud Run startup timeout.
    """
    global _runner

    if _runner is None:
        logger.info("⚡ Initializing agent (lazy load)...")

        try:
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from adk_agent.agent import create_agent

            agent = create_agent()
            session_service = InMemorySessionService()

            _runner = Runner(
                agent=agent,
                app_name=APP_NAME,
                session_service=session_service,
            )

            _runner._session_service_ref = session_service

            logger.info("✅ Agent initialized successfully")

        except Exception as e:
            logger.exception("❌ Failed to initialize agent")
            raise RuntimeError(f"Agent initialization failed: {str(e)}")

    return _runner


# 🚀 FastAPI app (NO lifespan → faster startup)
app = FastAPI(
    title="Inventory Intelligence Agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────
# Request / Response Models
# ─────────────────────────────

class AskRequest(BaseModel):
    question: str
    session_id: str | None = None


class AskResponse(BaseModel):
    answer: str
    session_id: str
    question: str


# ─────────────────────────────
# Health Check
# ─────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}


# ─────────────────────────────
# Sample Queries
# ─────────────────────────────

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


# ─────────────────────────────
# Main API
# ─────────────────────────────

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    from google.genai import types

    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        runner = get_runner()
        session_service = runner._session_service_ref

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

    except Exception as e:
        logger.exception("❌ Error processing request")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────
# Local Run (for testing)
# ─────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting server on port {port}")

    uvicorn.run(app, host="0.0.0.0", port=port)