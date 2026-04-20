# Inventory Intelligence Agent
Multi-Agent AI system for manufacturing inventory management
Built for Google Cloud Gen AI Academy APAC Hackathon

## Architecture
```
React Frontend (Cloud Run)
        ↓ HTTPS
FastAPI Backend (Cloud Run)
        ↓ subprocess
MCP Server (port 5000, internal)
        ↓ BigQuery API
Google BigQuery (inventory_db)
```

## Local Development

### 1. Prerequisites
- Python 3.11
- Node.js 18+
- GCP project with BigQuery enabled
- Service account key with BigQuery access

### 2. Setup
```bash
# Clone and enter project
git clone <your-repo>
cd inventory-agent

# Python environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env
cp .env.example .env
# Edit .env — set GOOGLE_APPLICATION_CREDENTIALS and VITE_API_URL
```

### 3. Seed BigQuery (once only)
```bash
python data/seed_bigquery.py --project jyothiapikey1
```

### 4. Run locally (3 terminals)

Terminal 1 — MCP server:
```bash
source .venv/bin/activate
python3.11 -m mcp_server.http_server
```

Terminal 2 — FastAPI backend:
```bash
source .venv/bin/activate
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 3 — React frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Cloud Run Deployment

### Prerequisites
- `gcloud` CLI installed and authenticated
- Project owner or editor role on GCP

### Deploy
```bash
chmod +x deploy.sh
bash deploy.sh
```

The script will:
1. Enable all required GCP APIs
2. Store your service account key in Secret Manager
3. Set IAM permissions
4. Deploy backend to Cloud Run
5. Deploy frontend to Cloud Run with backend URL injected

### Submission URLs
After deploy.sh completes, note:
- **Frontend URL** → submit as your Cloud Run Deployment Link
- **Backend URL/health** → verify agent is running

## Sample Queries
- "Give me an overview of our current inventory status"
- "Which raw materials are below reorder level?"
- "Show me all metals stock"
- "What purchase orders are pending or delayed?"
- "Top 5 most consumed materials this month"
- "Breakdown of stock value by warehouse"

## Tech Stack
- **Agent Framework**: Google ADK (Agent Development Kit)
- **Model**: Gemini 2.0 Flash
- **Database**: Google BigQuery
- **Tools Protocol**: MCP (Model Context Protocol)
- **Backend**: FastAPI + Uvicorn
- **Frontend**: React + Vite
- **Deployment**: Google Cloud Run

## What Was Completed

### Deployment and Cloud Run Fixes
- Backend deployment was stabilized and is running on Cloud Run.
- Frontend Cloud Run build failures were fixed by updating the frontend Docker build command to run Vite directly.
- Frontend runtime API connectivity was fixed by ensuring `VITE_API_URL` fallback points to deployed backend URL.
- Cloud Run environment configuration was updated for Vertex AI mode (`GOOGLE_GENAI_USE_VERTEXAI=true`) to avoid Gemini API-key runtime failures.
- Deployment script was improved to include Vertex AI prerequisites:
  - `aiplatform.googleapis.com` API enablement
  - `roles/aiplatform.user` IAM role binding for runtime service account

### Backend Agent Reliability Fixes
- ADK MCP import compatibility was implemented in `adk_agent/agent.py` to support multiple ADK versions:
  - `McpToolset` and `MCPToolset` class name variants
  - `StdioConnectionParams` and direct `StdioServerParameters` connection variants
- This removed the runtime initialization failure (`McpToolset not found`) seen after deployment.

### Frontend Feature Enhancements
- Voice features were added to chat UI:
  - Voice input (speech-to-text) mic button
  - Voice output (text-to-speech) speaker button per agent message
  - Browser capability fallbacks for unsupported speech APIs
- Chat UX remains the same while adding optional voice controls.

### Security and Operations Notes
- Service account key usage path issue was diagnosed and corrected (path vs JSON content).
- Secret/env type mismatch in Cloud Run configuration was identified with corrective deployment guidance.
- **Important**: service account key was exposed during troubleshooting and should be rotated/revoked in GCP.