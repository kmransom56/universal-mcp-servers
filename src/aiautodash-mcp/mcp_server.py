#!/usr/bin/env python3
"""
AIAutoDash MCP Server
Exposes AIAutoDash agents as MCP tools for AI assistants
"""

import asyncio
import httpx
from typing import Any
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Initialize MCP server
server = Server("aiautodash-agents")

AIAUTODASH_BASE_URL = "http://localhost:5902"

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available AIAutoDash tools
    """
    return [
        types.Tool(
            name="list_agents",
            description="List all AIAutoDash agents with their current status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
        ),
        types.Tool(
            name="execute_agent",
            description="Execute a specific AIAutoDash agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "The agent ID (e.g., 'agent-001', 'agent-002')",
                    }
                },
                "required": ["agent_id"],
            },
        ),
        types.Tool(
            name="get_agent_details",
            description="Get detailed information about a specific agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "The agent ID to query",
                    }
                },
                "required": ["agent_id"],
            },
        ),
        types.Tool(
            name="get_stats",
            description="Get overall AIAutoDash statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
        ),
        types.Tool(
            name="health_check",
            description="Check AIAutoDash service health",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
        ),
        types.Tool(
            name="recommend_agent",
            description="Get AI-powered agent recommendation for a specific task type (Phase 3)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_type": {
                        "type": "string",
                        "description": "Task type: analysis, reporting, automation, support, or development",
                        "enum": ["analysis", "reporting", "automation", "support", "development"]
                    }
                },
                "required": []
            },
        ),
        types.Tool(
            name="ai_analyze_agent",
            description="AI-powered analysis of agent performance and recommendations (Phase 3)",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "The agent ID to analyze (e.g., 'agent-001')",
                    },
                    "custom_prompt": {
                        "type": "string",
                        "description": "Optional custom analysis prompt",
                    }
                },
                "required": ["agent_id"]
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests
    """
    if arguments is None:
        arguments = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if name == "list_agents":
                response = await client.get(f"{AIAUTODASH_BASE_URL}/registry")
                data = response.json()
                return [types.TextContent(
                    type="text",
                    text=f"AIAutoDash Agents:\n\n{format_agents(data.get('agents', []))}"
                )]

            elif name == "execute_agent":
                agent_id = arguments.get("agent_id")
                response = await client.post(f"{AIAUTODASH_BASE_URL}/registry/{agent_id}/execute")
                data = response.json()
                return [types.TextContent(
                    type="text",
                    text=f"Agent Execution Result:\n{format_dict(data)}"
                )]

            elif name == "get_agent_details":
                agent_id = arguments.get("agent_id")
                response = await client.get(f"{AIAUTODASH_BASE_URL}/registry/{agent_id}")
                data = response.json()
                return [types.TextContent(
                    type="text",
                    text=f"Agent Details:\n{format_dict(data)}"
                )]

            elif name == "get_stats":
                response = await client.get(f"{AIAUTODASH_BASE_URL}/api/stats")
                data = response.json()
                return [types.TextContent(
                    type="text",
                    text=f"AIAutoDash Statistics:\n{format_dict(data)}"
                )]

            elif name == "health_check":
                response = await client.get(f"{AIAUTODASH_BASE_URL}/health")
                data = response.json()
                return [types.TextContent(
                    type="text",
                    text=f"AIAutoDash Health:\n{format_dict(data)}"
                )]

            elif name == "recommend_agent":
                task_type = arguments.get("task_type", "")
                url = f"{AIAUTODASH_BASE_URL}/api/agents/recommend"
                params = {"task_type": task_type} if task_type else {}
                response = await client.get(url, params=params)
                data = response.json()

                if data.get("status") == "success":
                    agent = data.get("recommended_agent", {})
                    result = f"Recommended Agent for {data.get('task_type', 'general')} tasks:\n\n"
                    result += f"• {agent.get('name')} ({agent.get('id')})\n"
                    result += f"  Status: {agent.get('status')}\n"
                    result += f"  Type: {agent.get('type')}\n"
                    result += f"  Tasks Completed: {agent.get('tasks_completed')}\n"
                    result += f"  Confidence: {data.get('confidence', 0.0):.2%}\n"
                    result += f"  Reasoning: {data.get('reasoning')}\n"
                    return [types.TextContent(type="text", text=result)]
                else:
                    return [types.TextContent(type="text", text=f"Error: {data.get('message', 'Unknown error')}")]

            elif name == "ai_analyze_agent":
                agent_id = arguments.get("agent_id")
                custom_prompt = arguments.get("custom_prompt")

                url = f"{AIAUTODASH_BASE_URL}/api/agents/{agent_id}/ai-analyze"
                params = {"prompt": custom_prompt} if custom_prompt else {}
                response = await client.post(url, params=params)
                data = response.json()

                if data.get("status") == "success":
                    result = f"AI Analysis for {data.get('agent_name')}:\n\n"
                    result += f"Model: {data.get('ai_model')}\n"
                    result += f"Timestamp: {data.get('timestamp')}\n\n"
                    result += f"Analysis:\n{data.get('analysis')}\n"
                    return [types.TextContent(type="text", text=result)]
                else:
                    return [types.TextContent(type="text", text=f"Error: {data.get('message', 'Unknown error')}")]

            else:
                return [types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]

        except httpx.RequestError as e:
            return [types.TextContent(
                type="text",
                text=f"Error connecting to AIAutoDash: {str(e)}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error executing tool: {str(e)}"
            )]

def format_agents(agents: list) -> str:
    """Format agent list for display"""
    if not agents:
        return "No agents found"

    result = []
    for agent in agents:
        result.append(f"• {agent['name']} ({agent['id']})")
        result.append(f"  Status: {agent['status']}")
        result.append(f"  Type: {agent['type']}")
        result.append(f"  Tasks Completed: {agent['tasks_completed']}")
        result.append(f"  Description: {agent['description']}")
        result.append("")

    return "\n".join(result)

def format_dict(data: dict) -> str:
    """Format dictionary for display"""
    result = []
    for key, value in data.items():
        if isinstance(value, dict):
            result.append(f"{key}:")
            for k, v in value.items():
                result.append(f"  {k}: {v}")
        else:
            result.append(f"{key}: {value}")
    return "\n".join(result)

async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="aiautodash-agents",
                server_version="1.0.0-phase3",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
