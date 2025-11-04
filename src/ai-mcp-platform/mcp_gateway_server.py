# MCP Gateway Server for Chat Copilot AI Platform
# Integrated MCP server exposing platform services for AI tools

import json
import asyncio
import httpx
import os
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP
from mcp.types import TextContent, ImageContent
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
PLATFORM_IP = os.getenv("PLATFORM_IP", "localhost")
CHAT_COPILOT_API_URL = os.getenv("CHAT_COPILOT_API_URL", "http://localhost:11000")

# Service definitions based on Chat Copilot platform
SERVICES = {
    "chat-copilot": {"port": 11000, "path": "/", "description": "Chat Copilot main application"},
    "autogen": {"port": 11001, "path": "/autogen/", "description": "AutoGen multi-agent framework"},
    "webhook": {"port": 11002, "path": "/webhook/", "description": "Webhook management service"},
    "magentic": {"port": 11003, "path": "/magentic/", "description": "Magentic AI orchestration"},
    "grafana": {"port": 11007, "path": "/grafana/", "description": "Grafana monitoring dashboard"},
    "portscanner": {"port": 11010, "path": "/portscanner/", "description": "Network port scanning utility"},
    "perplexica": {"port": 11020, "path": "/perplexica/", "description": "AI-powered search engine"},
    "searxng": {"port": 11021, "path": "/searxng/", "description": "Privacy-focused search engine"},
    "webhook-server": {"port": 11025, "path": "/webhook/", "description": "Advanced webhook server"},
    "openwebui": {"port": 11880, "path": "/", "description": "Open WebUI for LLMs"},
    "vscode": {"port": 57081, "path": "/", "description": "VS Code web interface"},
    "neo4j": {"port": 7474, "path": "/", "description": "Neo4j graph database"},
    "qdrant": {"port": 6333, "path": "/", "description": "Qdrant vector database"},
    "vllm-reasoning": {"port": 8000, "path": "/", "description": "vLLM Reasoning Model Server"},
    "vllm-general": {"port": 8001, "path": "/", "description": "vLLM General Model Server"},
    "vllm-coding": {"port": 8002, "path": "/", "description": "vLLM Coding Model Server"},
    "ai-gateway": {"port": 9000, "path": "/", "description": "AI Gateway Load Balancer"},
    "ollama": {"port": 11434, "path": "/", "description": "Ollama LLM API"},
    "rabbitmq": {"port": 15672, "path": "/", "description": "RabbitMQ message broker"},
    "postgresql": {"port": 5432, "path": "/", "description": "PostgreSQL database"}
}

# Initialize the MCP server
mcp = FastMCP(name="Chat Copilot AI Platform Gateway")

class ServiceClient:
    """HTTP client for interacting with platform services"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_service_url(self, service_name: str) -> Optional[str]:
        """Get the full URL for a service"""
        if service_name not in SERVICES:
            return None

        service = SERVICES[service_name]
        return f"http://{PLATFORM_IP}:{service['port']}{service['path']}"

    async def make_request(self, service_name: str, endpoint: str = "",
                          method: str = "GET", data: Optional[Dict] = None,
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to a service"""
        base_url = await self.get_service_url(service_name)
        if not base_url:
            return {"error": f"Service '{service_name}' not found"}

        url = urljoin(base_url, endpoint)

        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "url": str(response.url),
                "success": response.status_code < 400
            }
        except Exception as e:
            return {"error": str(e), "service": service_name, "url": url, "success": False}

# Initialize service client
service_client = ServiceClient()

# Resources - Expose service discovery and status
@mcp.resource("platform://services")
def list_services() -> Dict[str, Any]:
    """Get list of all available platform services"""
    return {
        "services": {
            name: {
                "description": config["description"],
                "url": f"http://{PLATFORM_IP}:{config['port']}{config['path']}",
                "port": config["port"],
                "path": config["path"]
            }
            for name, config in SERVICES.items()
        },
        "platform_ip": PLATFORM_IP,
        "total_services": len(SERVICES),
        "chat_copilot_url": CHAT_COPILOT_API_URL
    }

@mcp.resource("platform://services/{service_name}")
def get_service_info(service_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific service"""
    if service_name not in SERVICES:
        return {"error": f"Service '{service_name}' not found"}

    config = SERVICES[service_name]
    return {
        "name": service_name,
        "description": config["description"],
        "url": f"http://{PLATFORM_IP}:{config['port']}{config['path']}",
        "port": config["port"],
        "path": config["path"],
        "platform_ip": PLATFORM_IP
    }

# Tools - Service interaction capabilities
@mcp.tool()
async def call_service(service_name: str, endpoint: str = "",
                      method: str = "GET", data: Optional[str] = None,
                      headers: Optional[str] = None) -> Dict[str, Any]:
    """
    Make HTTP requests to Chat Copilot platform services

    Args:
        service_name: Name of the service (e.g., 'chat-copilot', 'openwebui', 'vllm-reasoning')
        endpoint: API endpoint path (optional, e.g., 'healthz', 'api/v1/models')
        method: HTTP method (GET, POST, PUT, DELETE)
        data: JSON data for POST/PUT requests (as string)
        headers: Additional headers (as JSON string)
    """

    # Parse optional JSON strings
    parsed_data = None
    if data:
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in data parameter", "success": False}

    parsed_headers = None
    if headers:
        try:
            parsed_headers = json.loads(headers)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in headers parameter", "success": False}

    return await service_client.make_request(
        service_name=service_name,
        endpoint=endpoint,
        method=method,
        data=parsed_data,
        headers=parsed_headers
    )

@mcp.tool()
async def check_platform_health() -> Dict[str, Any]:
    """
    Check health status of all Chat Copilot platform services
    """
    health_results = {}

    for service_name in SERVICES.keys():
        try:
            result = await service_client.make_request(service_name, "healthz", "GET")
            health_results[service_name] = {
                "status": "healthy" if result.get("success", False) else "unhealthy",
                "status_code": result.get("status_code", "unknown"),
                "url": result.get("url", "unknown"),
                "response_available": "body" in result
            }
        except Exception as e:
            health_results[service_name] = {
                "status": "error",
                "error": str(e)
            }

    healthy_count = sum(1 for h in health_results.values() if h.get("status") == "healthy")

    return {
        "platform_status": "healthy" if healthy_count > len(SERVICES) // 2 else "degraded",
        "healthy_services": healthy_count,
        "total_services": len(SERVICES),
        "services": health_results
    }

@mcp.tool()
async def chat_with_vllm(prompt: str, model_type: str = "general", max_tokens: int = 1000) -> Dict[str, Any]:
    """
    Chat with vLLM models running on the platform

    Args:
        prompt: The prompt to send to the model
        model_type: Type of model - 'reasoning', 'general', or 'coding'
        max_tokens: Maximum tokens to generate
    """
    service_map = {
        "reasoning": "vllm-reasoning",
        "general": "vllm-general",
        "coding": "vllm-coding"
    }

    service_name = service_map.get(model_type, "vllm-general")

    data = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False
    }

    return await service_client.make_request(
        service_name=service_name,
        endpoint="v1/completions",
        method="POST",
        data=data,
        headers={"Content-Type": "application/json"}
    )

@mcp.tool()
async def search_with_perplexica(query: str) -> Dict[str, Any]:
    """
    Search using Perplexica AI search engine

    Args:
        query: Search query
    """
    data = {"query": query, "mode": "web"}

    return await service_client.make_request(
        service_name="perplexica",
        endpoint="api/search",
        method="POST",
        data=data
    )

@mcp.tool()
async def query_neo4j_graph(cypher: str) -> Dict[str, Any]:
    """
    Execute Cypher query on Neo4j graph database

    Args:
        cypher: Cypher query to execute
    """
    data = {"statements": [{"statement": cypher}]}

    return await service_client.make_request(
        service_name="neo4j",
        endpoint="db/data/transaction/commit",
        method="POST",
        data=data,
        headers={"Content-Type": "application/json"}
    )

@mcp.tool()
async def scan_network_port(target: str, port: int) -> Dict[str, Any]:
    """
    Scan a specific port using the port scanner service

    Args:
        target: Target IP or hostname
        port: Port number to scan
    """
    data = {"target": target, "port": port}

    return await service_client.make_request(
        service_name="portscanner",
        endpoint="scan",
        method="POST",
        data=data
    )

@mcp.tool()
async def get_deepmcp_integration_status() -> Dict[str, Any]:
    """
    Check status of DeepMCP integration hub
    """
    deepmcp_path = os.getenv("DEEPMCP_INTEGRATION_PATH", "/home/keith/deepmcp-integration")
    deepmcp_url = os.getenv("DEEPMCP_HUB_URL", "http://localhost:8000")

    try:
        # Try to connect to DeepMCP hub
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{deepmcp_url}/health")
            return {
                "status": "connected",
                "deepmcp_url": deepmcp_url,
                "deepmcp_path": deepmcp_path,
                "response": response.text,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "deepmcp_url": deepmcp_url,
            "deepmcp_path": deepmcp_path,
            "error": str(e)
        }

# Prompts - Pre-configured interaction templates
@mcp.prompt()
def platform_overview() -> str:
    """
    Generate overview of the Chat Copilot AI Platform
    """
    return f"""
# Chat Copilot AI Platform Overview

## Available Services
The platform consists of {len(SERVICES)} integrated services:

### Core AI Services
- **Chat Copilot**: Main application interface (port 11000)
- **vLLM Models**: Reasoning (8000), General (8001), Coding (8002)
- **OpenWebUI**: User-friendly LLM interface (port 11880)
- **AI Gateway**: Load balancer for AI services (port 9000)

### Automation & Orchestration
- **AutoGen**: Multi-agent framework (port 11001)
- **Magentic**: AI orchestration (port 11003)
- **Webhook Server**: Event-driven automation (port 11002)

### Data & Search
- **Neo4j**: Graph database for knowledge (port 7474)
- **Qdrant**: Vector database for embeddings (port 6333)
- **Perplexica**: AI-powered search (port 11020)
- **SearXNG**: Privacy-focused web search (port 11021)

### Development & Monitoring
- **VS Code Web**: Development environment (port 57081)
- **Grafana**: Monitoring dashboards (port 11007)
- **Port Scanner**: Network security tools (port 11010)

## Platform Integration
- **DeepMCP Hub**: Integrated MCP server management
- **Syncthing**: Real-time file synchronization
- **Docker**: Containerized service deployment

Use the available tools to interact with any of these services programmatically.
"""

@mcp.prompt()
def ai_workflow_recommendations(task_description: str) -> str:
    """
    Generate AI workflow recommendations based on task description

    Args:
        task_description: Description of the AI task to accomplish
    """
    return f"""
# AI Workflow Recommendations

**Task**: {task_description}

## Recommended Service Flow

### 1. Input Processing
- **Chat Copilot**: For interactive user interface
- **Perplexica**: For research and information gathering
- **SearXNG**: For web search when needed

### 2. AI Processing
Choose based on task type:
- **vLLM Reasoning**: For complex reasoning tasks
- **vLLM General**: For general-purpose language tasks
- **vLLM Coding**: For code generation and analysis
- **AutoGen**: For multi-agent collaboration

### 3. Data Management
- **Neo4j**: For knowledge graph operations
- **Qdrant**: For vector similarity search
- **PostgreSQL**: For structured data storage

### 4. Automation
- **Webhook Server**: For event-driven workflows
- **Magentic**: For AI orchestration
- **N8N**: For workflow automation

### 5. Monitoring
- **Grafana**: For performance monitoring
- **Health checks**: Use platform health tools

## Next Steps
1. Check platform health: `check_platform_health()`
2. Test service connectivity: `call_service("service-name", "healthz")`
3. Execute your workflow using the recommended services
"""

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        # Run with stdio transport for integration with MCP clients
        print("Starting Chat Copilot MCP Gateway with stdio transport...", file=sys.stderr)
        mcp.run(transport="stdio")
    else:
        # Run with SSE transport for HTTP access
        print(f"Starting Chat Copilot MCP Gateway Server on http://localhost:8000")
        print(f"Platform IP: {PLATFORM_IP}")
        print(f"Chat Copilot URL: {CHAT_COPILOT_API_URL}")
        print(f"Available services: {len(SERVICES)}")
        mcp.run(transport="sse", port=8000)