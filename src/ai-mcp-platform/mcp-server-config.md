---
title: "mcp server config"
date: "2025-09-20"
tags: [chat-copilot, auto-tagged]
source: auto-import
status: imported
---

# MCP Server Configuration Files

## requirements.txt
```txt
fastmcp>=0.2.0
httpx>=0.25.0
asyncio-mqtt>=0.11.0
python-dotenv>=1.0.0
```

## pyproject.toml
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-platform-mcp-server"
version = "0.1.0"
description = "MCP Server for AI Platform Services Integration"
authors = [{name = "AI Platform Team"}]
dependencies = [
    "fastmcp>=0.2.0",
    "httpx>=0.25.0",
    "python-dotenv>=1.0.0",
]
requires-python = ">=3.8"

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "black", "ruff"]

[project.scripts]
ai-mcp-server = "mcp_server_gateway:main"
```

## .env.example
```env
# Platform configuration
PLATFORM_IP=localhost
MCP_SERVER_NAME="AI Platform Gateway"
MCP_SERVER_VERSION="0.1.0"

# Authentication (optional)
MCP_API_KEY=""
MCP_SECRET_KEY=""

# Service-specific configurations
OLLAMA_MODEL_DEFAULT="llama2"
NEO4J_USER="neo4j"
NEO4J_PASSWORD=""
QDRANT_API_KEY=""

# Server configuration
MCP_PORT=8000
MCP_HOST="0.0.0.0"
MCP_DEBUG=false
```

## docker-compose.yml
```yaml
version: '3.8'
services:
  mcp-gateway:
    build: .
    environment:
      - PLATFORM_IP=${PLATFORM_IP:-localhost}
      - MCP_PORT=${MCP_PORT:-8000}
      - MCP_DEBUG=${MCP_DEBUG:-false}
    ports:
      - "${MCP_PORT:-8000}:8000"
    networks:
      - ai-platform
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

networks:
  ai-platform:
    external: true
```

## Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Run the MCP server
CMD ["python", "mcp_server_gateway.py", "stdio"]
```

## config.json (MCP Client Configuration)
```json
{
  "mcpServers": {
    "ai-platform-gateway": {
      "command": "python",
      "args": ["mcp_server_gateway.py", "stdio"],
      "env": {
        "PLATFORM_IP": "localhost"
      },
      "cwd": "/path/to/your/mcp/server"
    }
  }
}
```

## VSCode Integration (settings.json)
```json
{
  "mcp.servers": [
    {
      "id": "ai-platform-gateway",
      "name": "AI Platform Gateway",
      "command": "python",
      "args": ["mcp_server_gateway.py", "stdio"],
      "cwd": "${workspaceFolder}/mcp-server",
      "env": {
        "PLATFORM_IP": "localhost"
      }
    }
  ]
}
```

## Claude Desktop Configuration (claude_desktop_config.json)
```json
{
  "globalShortcut": "CommandOrControl+;",
  "mcpServers": {
    "ai-platform-gateway": {
      "command": "python",
      "args": ["/path/to/mcp_server_gateway.py", "stdio"],
      "env": {
        "PLATFORM_IP": "localhost"
      }
    }
  }
}
```

## Setup Instructions

### 1. Install Dependencies
```bash
# Using pip
pip install -r requirements.txt

# Using uv (recommended)
uv init ai-mcp-server
cd ai-mcp-server  
uv add "fastmcp>=0.2.0" "httpx>=0.25.0" "python-dotenv>=1.0.0"
```

### 2. Environment Setup
```bash
# Copy environment file
cp .env.example .env

# Edit with your platform configuration
nano .env
```

### 3. Test the Server
```bash
# Test with MCP Inspector
npx @modelcontextprotocol/inspector python mcp_server_gateway.py stdio

# Or run directly
python mcp_server_gateway.py
```

### 4. Integration Examples

#### Cursor IDE
1. Install the MCP extension
2. Add server configuration to settings.json
3. Restart Cursor
4. Access via Command Palette: "MCP: Connect to Server"

#### VS Code
1. Install MCP extension
2. Configure in settings.json
3. Use Command Palette: "MCP: List Tools"

#### CLI Usage
```bash
# Using MCP CLI tools
mcp connect ai-platform-gateway
mcp call call_service --service_name=vllm --endpoint=api/tags
mcp call search_perplexica --query="network automation"
```

### 5. Docker Deployment
```bash
# Build image
docker build -t ai-mcp-server .

# Run with docker-compose
docker-compose up -d

# Or run directly
docker run -d \
  --name ai-mcp-server \
  -p 8000:8000 \
  -e PLATFORM_IP=your-platform-ip \
  ai-mcp-server
```
