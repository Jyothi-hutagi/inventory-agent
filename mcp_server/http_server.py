#!/usr/bin/env python3.11
"""
MCP HTTP/SSE Server for inventory tools
"""
import json
import os
import asyncio
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from google.cloud import bigquery

app = FastAPI()

# Load tools.yaml
TOOLS_FILE = Path(__file__).parent / "tools.yaml"
with open(TOOLS_FILE) as f:
    config = yaml.safe_load(f)

project_id = config["sources"]["inventory_bq"]["project"]
bq_client = bigquery.Client(project=project_id)

@app.get("/mcp")
async def list_tools():
    """List available tools."""
    tools = []
    for tool_name, tool_config in config["tools"].items():
        tool = {
            "name": tool_name,
            "description": tool_config.get("description", ""),
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
        
        if "parameters" in tool_config:
            for param in tool_config["parameters"]:
                tool["inputSchema"]["properties"][param["name"]] = {
                    "type": param.get("type", "string"),
                    "description": param.get("description", ""),
                }
                tool["inputSchema"]["required"].append(param["name"])
        
        tools.append(tool)
    
    return {"tools": tools}

@app.post("/mcp/call")
async def call_tool(request: dict[str, Any]):
    """Execute a tool."""
    tool_name = request.get("name")
    arguments = request.get("arguments", {})
    
    if tool_name not in config["tools"]:
        return {"error": f"Tool {tool_name} not found"}
    
    tool_config = config["tools"][tool_name]
    sql = tool_config["statement"]
    
    # Replace parameters in SQL
    for param_name, param_value in arguments.items():
        sql = sql.replace(f"@{param_name}", f"'{param_value}'")
    
    try:
        query_job = bq_client.query(sql)
        results = query_job.result()
        
        rows = [dict(row) for row in results]
        return {"result": rows}
    except Exception as e:
        return {"error": str(e)}

@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for MCP client (fallback)."""
    async def event_generator():
        yield f"data: {json.dumps({'jsonrpc': '2.0', 'method': 'initialize'})}\n\n"
        import asyncio
        try:
            while True:
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
