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