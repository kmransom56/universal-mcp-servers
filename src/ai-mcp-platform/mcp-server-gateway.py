# MCP Gateway Server for AI Application Services
# This server exposes your microservices as MCP tools for integration with AI tools

import json
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP
from fastmcp.types import Image, TextContent
import os
from urllib.parse import urljoin

# Environment variables
PLATFORM_IP = os.getenv("PLATFORM_IP", "localhost")

# Service definitions based on your port mapping
SERVICES = {
    "copilot": {"port": 11000, "path": "/copilot/", "description": "GitHub Copilot service"},
    "autogen": {"port": 11001, "path": "/autogen/", "description": "AutoGen multi-agent framework"},
    "magentic": {"port": 11003, "path": "/magentic/", "description": "Magentic AI orchestration"},
    "webhook": {"port": 11025, "path": "/webhook/", "description": "Webhook management service"},
    "grafana": {"port": 11007, "path": "/grafana/", "description": "Grafana monitoring dashboard"},
    "promptforge": {"port": 11500, "path": "/promptforge/", "description": "Prompt engineering and management"},
    "n8n": {"port": 11510, "path": "/n8n/", "description": "Workflow automation platform"},
    "portscanner": {"port": 11010, "path": "/portscanner/", "description": "Network port scanning utility"},
    "openwebui": {"port": 11880, "path": "/openwebui/", "description": "Open WebUI for LLMs"},
    "vscode": {"port": 57081, "path": "/vscode/", "description": "VS Code web interface"},
    "perplexica": {"port": 11020, "path": "/perplexica/", "description": "AI-powered search engine"},
    "searxng": {"port": 11021, "path": "/searxng/", "description": "Privacy-focused search engine"},
    "neo4j": {"port": 7474, "path": "/neo4j/", "description": "Neo4j graph database"},
    "qdrant": {"port": 6333, "path": "/qdrant/", "description": "Qdrant vector database"},
    "genai_stack": {"port": 8505, "path": "/genai-stack/", "description": "GenAI Stack main interface"},
    "genai_loader": {"port": 8502, "path": "/genai-stack/loader/", "description": "GenAI Stack data loader"},
    "genai_import": {"port": 8081, "path": "/genai-stack/import/", "description": "GenAI Stack import service"},
    "genai_bot": {"port": 8501, "path": "/genai-stack/bot/", "description": "GenAI Stack bot interface"},
    "genai_pdf": {"port": 8503, "path": "/genai-stack/pdf/", "description": "GenAI Stack PDF processing"},
    "genai_api": {"port": 8504, "path": "/genai-stack/api/", "description": "GenAI Stack API"},
    "ollama": {"port": 11434, "path": "/ollama-api/", "description": "Ollama LLM API"},
    "windmill": {"port": 11006, "path": "/windmill/", "description": "Windmill workflow engine"},
    "rabbitmq": {"port": 15672, "path": "/rabbitmq/", "description": "RabbitMQ message broker"},
    "postgresql": {"port": 5432, "path": "/postgresql/", "description": "PostgreSQL database"}
}

# Initialize the MCP server
mcp = FastMCP(name="AI Platform Gateway")

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
                "url": str(response.url)
            }
        except Exception as e:
            return {"error": str(e), "service": service_name, "url": url}

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
        "total_services": len(SERVICES)
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
    Make HTTP requests to platform services
    
    Args:
        service_name: Name of the service to call (e.g., 'ollama', 'grafana', 'n8n')
        endpoint: API endpoint path (optional, e.g., 'api/tags', 'health')
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
            return {"error": "Invalid JSON in data parameter"}
    
    parsed_headers = None
    if headers:
        try:
            parsed_headers = json.loads(headers)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in headers parameter"}
    
    return await service_client.make_request(
        service_name=service_name,
        endpoint=endpoint,
        method=method,
        data=parsed_data,
        headers=parsed_headers
    )

@mcp.tool()
async def ollama_chat(prompt: str, model: str = "llama2") -> Dict[str, Any]:
    """
    Chat with Ollama models
    
    Args:
        prompt: The prompt to send to the model
        model: Model name (default: llama2)
    """
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    return await service_client.make_request(
        service_name="ollama",
        endpoint="api/generate",
        method="POST",
        data=data
    )

@mcp.tool()
async def n8n_execute_workflow(workflow_id: str, data: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute n8n workflow
    
    Args:
        workflow_id: ID of the workflow to execute
        data: Input data for the workflow (as JSON string)
    """
    parsed_data = {}
    if data:
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in data parameter"}
    
    return await service_client.make_request(
        service_name="n8n",
        endpoint=f"webhook/{workflow_id}",
        method="POST",
        data=parsed_data
    )

@mcp.tool()
async def search_perplexica(query: str) -> Dict[str, Any]:
    """
    Search using Perplexica AI search engine
    
    Args:
        query: Search query
    """
    data = {"query": query}
    
    return await service_client.make_request(
        service_name="perplexica",
        endpoint="api/search",
        method="POST",
        data=data
    )

@mcp.tool()
async def neo4j_query(cypher: str) -> Dict[str, Any]:
    """
    Execute Cypher query on Neo4j
    
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
async def qdrant_search(collection: str, query_vector: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search vectors in Qdrant
    
    Args:
        collection: Collection name
        query_vector: Query vector (as JSON array string)
        limit: Number of results to return
    """
    try:
        vector = json.loads(query_vector)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in query_vector parameter"}
    
    data = {
        "vector": vector,
        "limit": limit,
        "with_payload": True
    }
    
    return await service_client.make_request(
        service_name="qdrant",
        endpoint=f"collections/{collection}/points/search",
        method="POST",
        data=data
    )

@mcp.tool()
async def scan_port(target: str, port: int) -> Dict[str, Any]:
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

# Prompts - Pre-configured interaction templates
@mcp.prompt()
def service_health_check(services: str = "all") -> str:
    """
    Generate health check commands for platform services
    
    Args:
        services: Comma-separated list of services to check, or 'all'
    """
    if services.lower() == "all":
        service_list = list(SERVICES.keys())
    else:
        service_list = [s.strip() for s in services.split(",")]
    
    commands = []
    for service in service_list:
        if service in SERVICES:
            commands.append(f"call_service('{service}', 'health', 'GET')")
    
    return f"""
Please check the health status of the following services:

{chr(10).join(f"- {service}: {SERVICES.get(service, {}).get('description', 'Unknown service')}" for service in service_list)}

Use these commands:
{chr(10).join(commands)}

Analyze the responses and provide a summary of service availability.
"""

@mcp.prompt()
def ai_workflow_setup(task_description: str) -> str:
    """
    Generate workflow setup for AI tasks
    
    Args:
        task_description: Description of the AI task to accomplish
    """
    return f"""
Based on the task: "{task_description}"

I'll help you set up a workflow using the available AI platform services:

1. **Data Sources & Knowledge**:
   - Neo4j: For graph-based knowledge retrieval
   - Qdrant: For vector similarity search
   - PostgreSQL: For structured data queries

2. **AI Processing**:
   - Ollama: For local LLM inference
   - OpenWebUI: For interactive AI interfaces
   - AutoGen: For multi-agent conversations
   - Magentic: For AI orchestration

3. **Workflow Automation**:
   - N8N: For building automated workflows
   - Windmill: For workflow execution
   - Webhooks: For service integration

4. **Search & Discovery**:
   - Perplexica: For AI-powered search
   - SearXNG: For privacy-focused web search

Please specify which services you'd like to use and I'll help configure the workflow.
"""

if __name__ == "__main__":
    # Run the server
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        # Run with stdio transport for integration with MCP clients
        mcp.run(transport="stdio")
    else:
        # Run with SSE transport for HTTP access
        print(f"Starting MCP Gateway Server on http://localhost:8000")
        print(f"Platform IP: {PLATFORM_IP}")
        print(f"Available services: {len(SERVICES)}")
        mcp.run(transport="sse", port=8000)