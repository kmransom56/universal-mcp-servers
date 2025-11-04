---
title: "README"
date: "2025-10-24"
tags: [chat-copilot, auto-tagged]
source: auto-import
status: imported
---

# AIAutoDash MCP Server

MCP server that exposes AIAutoDash agents as tools for AI assistants.

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Usage

```bash
python mcp_server.py
```

## Tools

- `list_agents` - List all agents with status
- `execute_agent` - Execute a specific agent
- `get_agent_details` - Get detailed agent information
- `get_stats` - Get overall statistics
- `health_check` - Check service health

## Configuration

Set `AIAUTODASH_BASE_URL` environment variable to change the AIAutoDash endpoint (default: http://localhost:5902)
