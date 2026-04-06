FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY adk_agent/ ./adk_agent/
COPY api/ ./api/
COPY mcp_server/ ./mcp_server/

# Add __init__.py files so Python treats these as packages
RUN touch adk_agent/__init__.py
RUN touch adk_agent/sub_agents/__init__.py
RUN touch mcp_server/__init__.py

ENV PORT=8080
ENV PYTHONPATH=/app

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT"]
