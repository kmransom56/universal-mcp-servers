# Advanced MCP Server Features

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Union
import yaml
from datetime import datetime

# Enhanced MCP server with additional features
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

# Configuration-driven service registration
mcp_enhanced = EnhancedMCPServer("AI Platform Gateway Enhanced", "config.yaml")

# Health monitoring tools
@mcp_enhanced.tool()
async def get_service_metrics() -> Dict[str, Any]:
    """Get server performance metrics and service health"""
    uptime = datetime.now() - mcp_enhanced.metrics["start_time"]
    
    health_checks = {}
    for service_name in SERVICES.keys():
        try:
            result = await service_client.make_request(service_name, "health", "GET")
            health_checks[service_name] = {
                "status": "healthy" if result.get("status_code", 500) < 400 else "unhealthy",
                "response_time": result.get("response_time", "unknown"),
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            health_checks[service_name] = {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    return {
        "server_metrics": {
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": mcp_enhanced.metrics["requests"],
            "total_errors": mcp_enhanced.metrics["errors"],
            "start_time": mcp_enhanced.metrics["start_time"].isoformat()
        },
        "service_health": health_checks,
        "platform_ip": PLATFORM_IP
    }

# Batch operations
@mcp_enhanced.tool()
async def batch_service_calls(requests: str) -> List[Dict[str, Any]]:
    """
    Execute multiple service calls in parallel
    
    Args:
        requests: JSON array of request objects with service_name, endpoint, method, data
    """
    try:
        request_list = json.loads(requests)
    except json.JSONDecodeError:
        return [{"error": "Invalid JSON format for requests"}]
    
    results = []
    for req in request_list:
        try:
            result = await service_client.make_request(
                service_name=req.get("service_name", ""),
                endpoint=req.get("endpoint", ""),
                method=req.get("method", "GET"),
                data=req.get("data")
            )
            results.append({
                "request": req,
                "response": result,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "request": req,
                "error": str(e),
                "status": "error"
            })
    
    return results

# Configuration management
@mcp_enhanced.resource("platform://config")
def get_platform_config() -> Dict[str, Any]:
    """Get current platform configuration"""
    return {
        "platform_ip": PLATFORM_IP,
        "services": SERVICES,
        "server_config": mcp_enhanced.config,
        "environment": {
            "python_version": sys.version,
            "mcp_version": "1.0.0",
            "platform": sys.platform
        }
    }

# Service discovery with filtering
@mcp_enhanced.tool()
async def discover_services(category: Optional[str] = None, 
                           status: Optional[str] = None) -> Dict[str, Any]:
    """
    Discover and filter available services
    
    Args:
        category: Filter by service category (ai, data, workflow, monitoring)
        status: Filter by health status (healthy, unhealthy, error)
    """
    
    # Service categorization
    categories = {
        "ai": ["ollama", "openwebui", "autogen", "magentic", "copilot"],
        "data": ["neo4j", "qdrant", "postgresql"],
        "workflow": ["n8n", "windmill", "webhook"],
        "monitoring": ["grafana", "portscanner"],
        "search": ["perplexica", "searxng"],
        "development": ["vscode"],
        "infrastructure": ["rabbitmq"]
    }
    
    # Get service health status
    health_status = {}
    for service_name in SERVICES.keys():
        try:
            result = await service_client.make_request(service_name, "health", "GET")
            health_status[service_name] = "healthy" if result.get("status_code", 500) < 400 else "unhealthy"
        except:
            health_status[service_name] = "error"
    
    # Apply filters
    filtered_services = {}
    for service_name, config in SERVICES.items():
        # Category filter
        if category:
            service_categories = [cat for cat, services in categories.items() if service_name in services]
            if category not in service_categories:
                continue
        
        # Status filter
        if status and health_status.get(service_name) != status:
            continue
        
        filtered_services[service_name] = {
            **config,
            "health_status": health_status.get(service_name, "unknown"),
            "categories": [cat for cat, services in categories.items() if service_name in services]
        }
    
    return {
        "services": filtered_services,
        "total_found": len(filtered_services),
        "filters_applied": {"category": category, "status": status}
    }

# Advanced workflow automation
@mcp_enhanced.tool()
async def create_ai_pipeline(pipeline_config: str) -> Dict[str, Any]:
    """
    Create an AI processing pipeline using multiple services
    
    Args:
        pipeline_config: JSON configuration for the pipeline steps
    """
    try:
        config = json.loads(pipeline_config)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON configuration"}
    
    pipeline_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    results = []
    
    for step_idx, step in enumerate(config.get("steps", [])):
        step_result = {
            "step": step_idx + 1,
            "name": step.get("name", f"Step {step_idx + 1}"),
            "service": step.get("service"),
            "status": "pending"
        }
        
        try:
            # Execute the step
            result = await service_client.make_request(
                service_name=step["service"],
                endpoint=step.get("endpoint", ""),
                method=step.get("method", "POST"),
                data=step.get("data", {})
            )
            
            step_result.update({
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            step_result.update({
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            # Stop pipeline on error if not configured to continue
            if not config.get("continue_on_error", False):
                break
        
        results.append(step_result)
    
    return {
        "pipeline_id": pipeline_id,
        "status": "completed" if all(r["status"] == "completed" for r in results) else "failed",
        "steps": results,
        "total_steps": len(results),
        "execution_time": datetime.now().isoformat()
    }

# Advanced prompt for complex workflows
@mcp_enhanced.prompt()
def ai_automation_wizard(task_type: str, requirements: str) -> str:
    """
    AI Automation Wizard - Generate complete automation workflows
    
    Args:
        task_type: Type of automation (data_processing, content_generation, monitoring)
        requirements: Detailed requirements for the automation
    """
    
    service_recommendations = {
        "data_processing": {
            "primary": ["neo4j", "qdrant", "postgresql"],
            "secondary": ["n8n", "windmill"],
            "ai": ["ollama", "autogen"]
        },
        "content_generation": {
            "primary": ["ollama", "openwebui"],
            "secondary": ["perplexica", "searxng"],
            "storage": ["neo4j", "qdrant"]
        },
        "monitoring": {
            "primary": ["grafana", "portscanner"],
            "secondary": ["webhook", "rabbitmq"],
            "data": ["postgresql", "neo4j"]
        }
    }
    
    recommended = service_recommendations.get(task_type, {})
    
    return f"""
# AI Automation Workflow Generator

## Task: {task_type.title().replace('_', ' ')}
## Requirements: {requirements}

## Recommended Service Stack:

### Primary Services:
{chr(10).join(f"- **{service}**: {SERVICES.get(service, {}).get('description', 'Service description')}" for service in recommended.get('primary', []))}

### Supporting Services:
{chr(10).join(f"- **{service}**: {SERVICES.get(service, {}).get('description', 'Service description')}" for service in recommended.get('secondary', []))}

## Suggested Workflow Steps:

1. **Data Ingestion & Preparation**
   - Use `call_service()` to prepare data sources
   - Validate data quality and format

2. **Processing Pipeline**
   - Execute core processing using primary services
   - Implement error handling and retry logic

3. **AI Enhancement**
   - Apply AI models for analysis/generation
   - Use batch processing for large datasets

4. **Results & Monitoring**
   - Store results in appropriate databases
   - Set up monitoring and alerts

## Example Pipeline Configuration:
```json
{
  "steps": [
    {"service": "data_source", "endpoint": "prepare", "method": "POST"},
    {"service": "ai_processor", "endpoint": "analyze", "method": "POST"},
    {"service": "storage", "endpoint": "save", "method": "PUT"}
  ],
  "continue_on_error": false
}
```

Use `create_ai_pipeline()` to execute this workflow.
"""

if __name__ == "__main__":
    mcp_enhanced.run(transport="stdio" if len(sys.argv) > 1 and sys.argv[1] == "stdio" else "sse")