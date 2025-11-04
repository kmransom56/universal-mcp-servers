# MCP Gateway Server for AI Application Services
# This server exposes your microservices as MCP tools for integration with AI tools

import json
import asyncio
import httpx
import os
import sys
import logging
import yaml
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from urllib.parse import urljoin

from fastmcp import FastMCP
from fastmcp.types import Image, TextContent

# --- Environment and Service Definitions ---

PLATFORM_IP = os.getenv("PLATFORM_IP", "localhost")

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

# --- Enhanced MCP Server Class ---

class EnhancedMCPServer(FastMCP):
    """Enhanced MCP Server with additional enterprise features"""
    
    def __init__(self, name: str, config_file: Optional[str] = None):
        super().__init__(name)
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.service_registry = {}
        self.metrics = {"requests": 0, "errors": 0, "start_time": datetime.now()}
        
    def load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from YAML file"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def setup_logging(self):
        """Setup structured logging"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mcp_server.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

# --- Service Client ---

class ServiceClient:
    """HTTP client for interacting with platform services"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_service_url(self, service_name: str) -> Optional[str]:
        """Get the full URL for a service"""
        if service_name not in SERVICES:
            return None
        
        service = SERVICES[service_name]
        return f"http://{PLATFORM_IP}:{service['port']}"
    
    async def make_request(self, service_name: str, endpoint: str = "", 
                          method: str = "GET", data: Optional[Dict] = None,
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to a service"""
        base_url = await self.get_service_url(service_name)
        if not base_url:
            mcp_enhanced.metrics["errors"] += 1
            return {"error": f"Service '{service_name}' not found"}
        
        url = urljoin(base_url, SERVICES[service_name].get('path', '/') + endpoint)
        mcp_enhanced.metrics["requests"] += 1
        
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
                mcp_enhanced.metrics["errors"] += 1
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "url": str(response.url)
            }
        except httpx.HTTPStatusError as e:
            mcp_enhanced.metrics["errors"] += 1
            return {"error": str(e), "service": service_name, "url": url, "status_code": e.response.status_code, "response": e.response.text}
        except Exception as e:
            mcp_enhanced.metrics["errors"] += 1
            return {"error": str(e), "service": service_name, "url": url}

# --- Server and Client Initialization ---

mcp_enhanced = EnhancedMCPServer("AI Platform Gateway Enhanced", "config.yaml")
service_client = ServiceClient()

# --- Basic Resources and Tools ---

@mcp_enhanced.resource("platform://services")
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

@mcp_enhanced.resource("platform://services/{service_name}")
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

@mcp_enhanced.tool()
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

# --- Service-Specific Tools ---

@mcp_enhanced.tool()
async def ollama_chat(prompt: str, model: str = "llama2") -> Dict[str, Any]:
    """Chat with Ollama models"""
    data = {"model": model, "prompt": prompt, "stream": False}
    return await service_client.make_request("ollama", "api/generate", "POST", data)

@mcp_enhanced.tool()
async def n8n_execute_workflow(workflow_id: str, data: Optional[str] = None) -> Dict[str, Any]:
    """Execute n8n workflow"""
    parsed_data = json.loads(data) if data else {}
    return await service_client.make_request("n8n", f"webhook/{workflow_id}", "POST", parsed_data)

@mcp_enhanced.tool()
async def search_perplexica(query: str) -> Dict[str, Any]:
    """Search using Perplexica AI search engine"""
    return await service_client.make_request("perplexica", "api/search", "POST", {"query": query})

@mcp_enhanced.tool()
async def neo4j_query(cypher: str) -> Dict[str, Any]:
    """Execute Cypher query on Neo4j"""
    data = {"statements": [{"statement": cypher}]}
    headers = {"Content-Type": "application/json"}
    return await service_client.make_request("neo4j", "db/data/transaction/commit", "POST", data, headers)

@mcp_enhanced.tool()
async def qdrant_search(collection: str, query_vector: str, limit: int = 10) -> Dict[str, Any]:
    """Search vectors in Qdrant"""
    try:
        vector = json.loads(query_vector)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in query_vector"}
    data = {"vector": vector, "limit": limit, "with_payload": True}
    return await service_client.make_request("qdrant", f"collections/{collection}/points/search", "POST", data)

@mcp_enhanced.tool()
async def scan_port(target: str, port: int) -> Dict[str, Any]:
    """Scan a specific port using the port scanner service"""
    return await service_client.make_request("portscanner", "scan", "POST", {"target": target, "port": port})

# --- Network Observability Tools ---

@mcp_enhanced.tool()
async def meraki_get_organization_networks(org_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves the list of networks for a Cisco Meraki organization.
    
    Args:
        org_id: The Meraki organization ID. If not provided, uses the one from .env.
    """
    api_key = os.getenv("MERAKI_API_KEY")
    organization_id = org_id or os.getenv("MERAKI_ORG_ID")
    if not api_key or not organization_id:
        return {"error": "Meraki API key or Organization ID not configured in .env"}

    url = f"https://api.meraki.com/api/v1/organizations/{organization_id}/networks"
    headers = {"X-Cisco-Meraki-API-Key": api_key}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

@mcp_enhanced.tool()
async def fortinet_get_system_status() -> Dict[str, Any]:
    """
    Retrieves the system status and performance metrics from a FortiGate device.
    """
    token = os.getenv("FORTINET_API_TOKEN")
    host = os.getenv("FORTINET_HOST")
    if not token or not host:
        return {"error": "Fortinet host or API token not configured in .env"}

    # Note: FortiGate APIs often use self-signed certs, hence verify=False.
    # In a production environment, you should handle certificates properly.
    url = f"https://{host}/api/v2/monitor/system/status"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

# --- Advanced Tools ---

@mcp_enhanced.tool()
async def get_service_metrics() -> Dict[str, Any]:
    """Get server performance metrics and service health"""
    uptime = datetime.now() - mcp_enhanced.metrics["start_time"]
    health_checks = {}
    for service_name in SERVICES.keys():
        try:
            # Using a simple GET request to the service root as a health check
            result = await service_client.make_request(service_name, "", "GET")
            health_checks[service_name] = {
                "status": "healthy" if result.get("status_code", 500) < 400 else "unhealthy",
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            health_checks[service_name] = {"status": "error", "error": str(e), "last_check": datetime.now().isoformat()}
    
    return {
        "server_metrics": {
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": mcp_enhanced.metrics["requests"],
            "total_errors": mcp_enhanced.metrics["errors"],
        },
        "service_health": health_checks
    }

@mcp_enhanced.tool()
async def batch_service_calls(requests: str) -> List[Dict[str, Any]]:
    """Execute multiple service calls in parallel"""
    try:
        request_list = json.loads(requests)
    except json.JSONDecodeError:
        return [{"error": "Invalid JSON format for requests"}]
    
    tasks = [call_service(**req) for req in request_list]
    results = await asyncio.gather(*tasks)
    return [{"request": req, "response": res} for req, res in zip(request_list, results)]

@mcp_enhanced.resource("platform://config")
def get_platform_config() -> Dict[str, Any]:
    """Get current platform configuration"""
    return {
        "platform_ip": PLATFORM_IP,
        "services": SERVICES,
        "server_config": mcp_enhanced.config,
        "environment": {"python_version": sys.version, "platform": sys.platform}
    }

@mcp_enhanced.tool()
async def discover_services(category: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
    """Discover and filter available services"""
    categories = {
        "ai": ["ollama", "openwebui", "autogen", "magentic", "copilot"],
        "data": ["neo4j", "qdrant", "postgresql"],
        "workflow": ["n8n", "windmill", "webhook"],
        "monitoring": ["grafana", "portscanner"],
        "search": ["perplexica", "searxng"],
        "development": ["vscode"],
        "infrastructure": ["rabbitmq"]
    }
    
    health_metrics = await get_service_metrics()
    health_status = {name: info['status'] for name, info in health_metrics.get('service_health', {}).items()}

    filtered_services = {}
    for service_name, config in SERVICES.items():
        if category and category not in [c for c, s in categories.items() if service_name in s]:
            continue
        if status and health_status.get(service_name) != status:
            continue
        
        filtered_services[service_name] = {
            **config,
            "health_status": health_status.get(service_name, "unknown"),
            "categories": [c for c, s in categories.items() if service_name in s]
        }
    
    return {"services": filtered_services, "total_found": len(filtered_services)}

@mcp_enhanced.tool()
async def create_ai_pipeline(pipeline_config: str) -> Dict[str, Any]:
    """Create an AI processing pipeline using multiple services"""
    try:
        config = json.loads(pipeline_config)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON configuration"}
    
    results = []
    for step in config.get("steps", []):
        try:
            result = await call_service(**step)
            step_result = {"step": step, "status": "completed", "result": result}
        except Exception as e:
            step_result = {"step": step, "status": "failed", "error": str(e)}
            if not config.get("continue_on_error", False):
                results.append(step_result)
                break
        results.append(step_result)
    
    return {"pipeline_status": "completed", "steps": results}

# --- Prompts ---

@mcp_enhanced.prompt()
def service_health_check(services: str = "all") -> str:
    """Generate health check commands for platform services"""
    service_list = list(SERVICES.keys()) if services.lower() == "all" else [s.strip() for s in services.split(",")]
    commands = "\n".join([f"call_service('{s}', 'health', 'GET')" for s in service_list if s in SERVICES])
    return f"Please check the health of these services:\n{commands}\nAnalyze the responses and summarize."

@mcp_enhanced.prompt()
def ai_workflow_setup(task_description: str) -> str:
    """Generate workflow setup for AI tasks"""
    return f"""
Based on your task: "{task_description}", here is a suggested workflow using the platform services.
1.  **Data Sources**: Use neo4j, qdrant, or postgresql.
2.  **AI Processing**: Use ollama, openwebui, or autogen.
3.  **Automation**: Use n8n or windmill to orchestrate.
Please specify which services you'd like to use.
"""

# --- Main Execution ---

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp_enhanced.run(transport="stdio")
    else:
        print(f"Starting MCP Gateway Server on http://localhost:8000")
        print(f"Platform IP: {PLATFORM_IP}")
        print(f"Available services: {len(SERVICES)}")
        mcp_enhanced.run(transport="sse", port=8000)
