FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY adk_agent/ ./adk_agent/
COPY api/ ./api/
COPY mcp_server/ ./mcp_server/

# Cloud Run uses PORT env variable
ENV PORT=8080

# Start the FastAPI server
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT"]