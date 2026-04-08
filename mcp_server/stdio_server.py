#!/usr/bin/env python3
"""
MCP Stdio Server for inventory tools — compatible with google-adk MCPToolset
Communicates over stdin/stdout using JSON-RPC 2.0 (MCP protocol)
"""
import json
import sys
import os
from pathlib import Path

import yaml
from google.cloud import bigquery

# ── Load tools.yaml ──────────────────────────────────────────────────────────
TOOLS_FILE = Path(__file__).parent / "tools.yaml"
with open(TOOLS_FILE) as f:
    config = yaml.safe_load(f)

project_id = config["sources"]["inventory_bq"]["project"]
bq_client = None


def get_bq_client():
    global bq_client
    if bq_client is None:
        bq_client = bigquery.Client(project=project_id)
    return bq_client


# ── Tool helpers ──────────────────────────────────────────────────────────────
def build_tools_list():
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
    return tools


def call_tool(tool_name: str, arguments: dict):
    if tool_name not in config["tools"]:
        return {"error": f"Tool '{tool_name}' not found"}

    tool_config = config["tools"][tool_name]
    sql = tool_config["statement"]

    # Safely substitute parameters
    for param_name, param_value in arguments.items():
        sql = sql.replace(f"@{param_name}", f"'{param_value}'")

    try:
        results = get_bq_client().query(sql).result()
        rows = [dict(row) for row in results]
        return {"result": rows}
    except Exception as e:
        return {"error": str(e)}


# ── JSON-RPC transport ────────────────────────────────────────────────────────
def send(obj: dict):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method", "")
        req_id = req.get("id")

        # ── MCP handshake ─────────────────────────────────────────────────────
        if method == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "inventory-mcp-server", "version": "1.0.0"},
                    "capabilities": {"tools": {}},
                },
            })

        elif method == "notifications/initialized":
            pass  # notification — no response required

        # ── Tool discovery ────────────────────────────────────────────────────
        elif method == "tools/list":
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": build_tools_list()},
            })

        # ── Tool execution ────────────────────────────────────────────────────
        elif method == "tools/call":
            params = req.get("params", {})
            result = call_tool(
                tool_name=params.get("name", ""),
                arguments=params.get("arguments", {}),
            )
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}]
                },
            })

        # ── Unknown method ────────────────────────────────────────────────────
        else:
            if req_id is not None:
                send({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                })


if __name__ == "__main__":
    main()