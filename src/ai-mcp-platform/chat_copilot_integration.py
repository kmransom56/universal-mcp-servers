#!/usr/bin/env python3
"""
Chat Copilot MCP Integration Bridge
Connects the Chat Copilot backend with MCP servers via HTTP API calls
"""

import asyncio
import json
import httpx
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Chat Copilot MCP Bridge", version="1.0.0")

# Enable CORS for Chat Copilot frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CHAT_COPILOT_URL = os.getenv("CHAT_COPILOT_API_URL", "http://localhost:11000")
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8000")
DEEPMCP_HUB_URL = os.getenv("DEEPMCP_HUB_URL", "http://localhost:8001")

class MCPRequest(BaseModel):
    server_name: str
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ChatCopilotMessage(BaseModel):
    message: str
    use_mcp: bool = True
    mcp_tools: Optional[list] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "chat_copilot": CHAT_COPILOT_URL,
            "mcp_gateway": MCP_GATEWAY_URL,
            "deepmcp_hub": DEEPMCP_HUB_URL
        }
    }

@app.get("/mcp/services")
async def get_mcp_services():
    """Get available MCP services from the gateway"""
    try:
        async with httpx.AsyncClient() as client:
            # Try to get services from MCP gateway
            try:
                response = await client.get(f"{MCP_GATEWAY_URL}/resources/platform://services")
                gateway_services = response.json() if response.status_code == 200 else {}
            except:
                gateway_services = {}

            # Try to get services from DeepMCP hub
            try:
                response = await client.get(f"{DEEPMCP_HUB_URL}/servers")
                deepmcp_services = response.json() if response.status_code == 200 else {}
            except:
                deepmcp_services = {}

            return {
                "gateway_services": gateway_services,
                "deepmcp_services": deepmcp_services,
                "integration_status": "active"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get MCP services: {str(e)}")

@app.post("/mcp/call")
async def call_mcp_tool(request: MCPToolCall):
    """Call an MCP tool through the gateway"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First try the MCP gateway
            try:
                response = await client.post(
                    f"{MCP_GATEWAY_URL}/tools/{request.tool_name}",
                    json=request.arguments
                )
                if response.status_code == 200:
                    return {
                        "success": True,
                        "result": response.json(),
                        "source": "mcp_gateway"
                    }
            except Exception as gateway_error:
                # Fall back to DeepMCP hub
                try:
                    response = await client.post(
                        f"{DEEPMCP_HUB_URL}/call_tool",
                        json={
                            "tool_name": request.tool_name,
                            "arguments": request.arguments
                        }
                    )
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "result": response.json(),
                            "source": "deepmcp_hub"
                        }
                except Exception as hub_error:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Both MCP services failed. Gateway: {gateway_error}, Hub: {hub_error}"
                    )

            raise HTTPException(status_code=500, detail="All MCP services are unavailable")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP call failed: {str(e)}")

@app.post("/mcp/platform/health")
async def check_platform_health():
    """Check health of all platform services via MCP"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MCP_GATEWAY_URL}/tools/check_platform_health",
                json={}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Platform health check failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Platform health check error: {str(e)}")

@app.post("/mcp/chat/enhance")
async def enhance_chat_with_mcp(request: ChatCopilotMessage):
    """Enhance Chat Copilot messages with MCP tool capabilities"""
    try:
        enhanced_response = {
            "original_message": request.message,
            "mcp_enhanced": request.use_mcp,
            "available_tools": [],
            "suggested_actions": []
        }

        if request.use_mcp:
            # Get available MCP tools
            services = await get_mcp_services()

            # Analyze message for potential MCP tool usage
            message_lower = request.message.lower()

            suggested_actions = []

            if any(word in message_lower for word in ["health", "status", "check"]):
                suggested_actions.append({
                    "tool": "check_platform_health",
                    "description": "Check the health of all platform services",
                    "arguments": {}
                })

            if any(word in message_lower for word in ["search", "find", "look"]):
                suggested_actions.append({
                    "tool": "search_with_perplexica",
                    "description": "Search using AI-powered Perplexica",
                    "arguments": {"query": request.message}
                })

            if any(word in message_lower for word in ["code", "program", "function"]):
                suggested_actions.append({
                    "tool": "chat_with_vllm",
                    "description": "Get coding assistance from vLLM",
                    "arguments": {"prompt": request.message, "model_type": "coding"}
                })

            if any(word in message_lower for word in ["graph", "database", "query"]):
                suggested_actions.append({
                    "tool": "query_neo4j_graph",
                    "description": "Query the Neo4j knowledge graph",
                    "arguments": {"cypher": f"// Generated from: {request.message}"}
                })

            enhanced_response["suggested_actions"] = suggested_actions
            enhanced_response["available_tools"] = list(services.get("gateway_services", {}).get("services", {}).keys())

        return enhanced_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Message enhancement failed: {str(e)}")

@app.get("/mcp/integration/status")
async def get_integration_status():
    """Get status of all MCP integrations"""
    status = {
        "timestamp": "2025-09-20T04:48:00Z",
        "services": {},
        "overall_status": "unknown"
    }

    # Check each service
    services_to_check = [
        ("chat_copilot", CHAT_COPILOT_URL),
        ("mcp_gateway", MCP_GATEWAY_URL),
        ("deepmcp_hub", DEEPMCP_HUB_URL)
    ]

    healthy_count = 0

    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, url in services_to_check:
            try:
                if service_name == "chat_copilot":
                    response = await client.get(f"{url}/healthz")
                else:
                    response = await client.get(f"{url}/health")

                status["services"][service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": url,
                    "status_code": response.status_code,
                    "response_time": "< 10s"
                }

                if response.status_code == 200:
                    healthy_count += 1

            except Exception as e:
                status["services"][service_name] = {
                    "status": "error",
                    "url": url,
                    "error": str(e),
                    "response_time": "timeout"
                }

    if healthy_count == len(services_to_check):
        status["overall_status"] = "healthy"
    elif healthy_count > 0:
        status["overall_status"] = "degraded"
    else:
        status["overall_status"] = "unhealthy"

    return status

if __name__ == "__main__":
    print("🚀 Starting Chat Copilot MCP Integration Bridge...")
    print(f"🔗 Chat Copilot: {CHAT_COPILOT_URL}")
    print(f"🛠️  MCP Gateway: {MCP_GATEWAY_URL}")
    print(f"🔥 DeepMCP Hub: {DEEPMCP_HUB_URL}")
    print(f"📡 Integration Bridge: http://localhost:8002")

    uvicorn.run(app, host="0.0.0.0", port=8002)