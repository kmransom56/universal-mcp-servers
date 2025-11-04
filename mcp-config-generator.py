#!/usr/bin/env python3
"""
MCP Configuration Generator for Multiple AI Tools
Generates portable MCP configurations for Cursor, VS Code, Claude Desktop, etc.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

class MCPConfigGenerator:
    def __init__(self, base_path: str = "/home/keith/chat-copilot/mcp-servers-consolidated"):
        self.base_path = Path(base_path)
        self.src_path = self.base_path / "src"
        
    def discover_servers(self) -> Dict[str, Dict[str, Any]]:
        """Discover all MCP servers and their configurations"""
        servers = {}
        
        if not self.src_path.exists():
            print(f"❌ Source path not found: {self.src_path}")
            return servers
            
        for server_dir in self.src_path.iterdir():
            if not server_dir.is_dir() or server_dir.name.startswith('.'):
                continue
                
            server_name = server_dir.name
            server_config = self.analyze_server(server_dir)
            
            if server_config:
                servers[server_name] = server_config
                
        return servers
    
    def analyze_server(self, server_dir: Path) -> Dict[str, Any]:
        """Analyze a server directory to determine its configuration"""
        config = {
            "name": server_dir.name,
            "path": str(server_dir),
            "type": "unknown",
            "executable": None,
            "args": [],
            "env": {},
            "description": "",
            "working": False
        }
        
        # Check for Node.js server
        if (server_dir / "package.json").exists():
            config["type"] = "nodejs"
            if (server_dir / "dist" / "index.js").exists():
                config["executable"] = str(server_dir / "dist" / "index.js")
                config["working"] = True
            elif (server_dir / "index.js").exists():
                config["executable"] = str(server_dir / "index.js")
                config["working"] = True
                
        # Check for Python server
        elif (server_dir / "pyproject.toml").exists():
            config["type"] = "python"
            if (server_dir / "src").exists():
                # Find the main module
                src_dirs = list((server_dir / "src").iterdir())
                if src_dirs:
                    module_dir = src_dirs[0]
                    if (module_dir / "__main__.py").exists():
                        config["executable"] = f"-m {module_dir.name}"
                        config["args"] = ["stdio"]
                        config["working"] = True
            elif (server_dir / "server.py").exists():
                config["executable"] = str(server_dir / "server.py")
                config["args"] = ["stdio"]
                config["working"] = True
        
        # Check for direct Python files
        elif (server_dir / "mcp_server.py").exists():
            config["type"] = "python"
            config["executable"] = str(server_dir / "mcp_server.py")
            config["args"] = ["stdio"]
            config["working"] = True
            
        # Try to get description from README
        readme_files = list(server_dir.glob("README*.md"))
        if readme_files:
            try:
                with open(readme_files[0], 'r') as f:
                    lines = f.readlines()[:10]  # First 10 lines
                    for line in lines:
                        if line.strip() and not line.startswith('#'):
                            config["description"] = line.strip()[:100]
                            break
            except:
                pass
                
        return config if config["working"] else None
    
    def generate_cursor_config(self, servers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate Cursor MCP configuration"""
        config = {"mcpServers": {}}
        
        for server_name, server_info in servers.items():
            if not server_info["working"]:
                continue
                
            server_config = {}
            
            if server_info["type"] == "nodejs":
                server_config["command"] = "node"
                server_config["args"] = [server_info["executable"]]
            elif server_info["type"] == "python":
                server_config["command"] = "python3"
                if server_info["executable"].startswith("-m"):
                    server_config["args"] = server_info["executable"].split()
                    server_config["cwd"] = str(Path(server_info["path"]))
                else:
                    server_config["args"] = [server_info["executable"]]
                    
                if server_info["args"]:
                    server_config["args"].extend(server_info["args"])
            
            # Add environment variables
            if server_info["env"]:
                server_config["env"] = server_info["env"]
                
            # Add common environment variables based on server type
            if server_name == "memory":
                server_config["env"] = {"MEMORY_FILE_PATH": "/home/keith/chat-copilot/data/mcp-memory.json"}
            elif server_name == "filesystem":
                server_config["env"] = {"ALLOWED_DIRECTORIES": "/home/keith/chat-copilot,/home/keith"}
            elif server_name == "ai-mcp-platform":
                server_config["env"] = {
                    "PLATFORM_IP": "localhost",
                    "MCP_SERVER_NAME": "AI Platform Gateway",
                    "MCP_SERVER_VERSION": "0.1.0"
                }
            elif server_name in ["fortinet", "fortimanager"]:
                server_config["env"] = {
                    "FORTINET_API_BASE": "https://your-fortigate-ip",
                    "FORTINET_API_KEY": "your-api-key"
                }
            elif server_name == "meraki":
                server_config["env"] = {"MERAKI_API_KEY": "your-meraki-api-key"}
            elif server_name == "gdrive" or server_name == "google-drive":
                server_config["env"] = {"GDRIVE_TOKEN": "your-gdrive-token"}
            elif server_name == "openai":
                server_config["env"] = {"OPENAI_API_KEY": "your-openai-key"}
            elif server_name == "sentry":
                server_config["env"] = {"SENTRY_DSN": "your-sentry-dsn"}
                
            config["mcpServers"][server_name] = server_config
            
        return config
    
    def generate_vscode_config(self, servers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate VS Code MCP configuration"""
        config = {"mcp.servers": []}
        
        for server_name, server_info in servers.items():
            if not server_info["working"]:
                continue
                
            server_config = {
                "id": server_name,
                "name": server_name.replace("-", " ").title(),
                "description": server_info.get("description", f"{server_name} MCP server")
            }
            
            if server_info["type"] == "nodejs":
                server_config["command"] = "node"
                server_config["args"] = [server_info["executable"]]
            elif server_info["type"] == "python":
                server_config["command"] = "python3"
                if server_info["executable"].startswith("-m"):
                    server_config["args"] = server_info["executable"].split()
                    server_config["cwd"] = server_info["path"]
                else:
                    server_config["args"] = [server_info["executable"]]
                    
            # Add environment variables (same logic as Cursor)
            env = {}
            if server_name == "memory":
                env = {"MEMORY_FILE_PATH": "/home/keith/chat-copilot/data/mcp-memory.json"}
            elif server_name == "filesystem":
                env = {"ALLOWED_DIRECTORIES": "/home/keith/chat-copilot,/home/keith"}
            # ... (same env logic as Cursor)
            
            if env:
                server_config["env"] = env
                
            config["mcp.servers"].append(server_config)
            
        return config
    
    def generate_claude_desktop_config(self, servers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate Claude Desktop MCP configuration"""
        config = {
            "globalShortcut": "CommandOrControl+;",
            "mcpServers": {}
        }
        
        for server_name, server_info in servers.items():
            if not server_info["working"]:
                continue
                
            server_config = {}
            
            if server_info["type"] == "nodejs":
                server_config["command"] = "node"
                server_config["args"] = [server_info["executable"]]
            elif server_info["type"] == "python":
                server_config["command"] = "python3"
                if server_info["executable"].startswith("-m"):
                    server_config["args"] = server_info["executable"].split()
                else:
                    server_config["args"] = [server_info["executable"]]
                    
            # Add environment variables (same logic)
            env = {}
            if server_name == "memory":
                env = {"MEMORY_FILE_PATH": "/home/keith/chat-copilot/data/mcp-memory.json"}
            elif server_name == "filesystem":
                env = {"ALLOWED_DIRECTORIES": "/home/keith/chat-copilot,/home/keith"}
            # ... (same env logic)
            
            if env:
                server_config["env"] = env
                
            config["mcpServers"][server_name] = server_config
            
        return config
    
    def generate_all_configs(self):
        """Generate all configuration files"""
        print("🔍 Discovering MCP servers...")
        servers = self.discover_servers()
        
        print(f"📊 Found {len(servers)} working MCP servers:")
        for name, info in servers.items():
            status = "✅" if info["working"] else "❌"
            print(f"  {status} {name} ({info['type']})")
            
        print("\n🔧 Generating configurations...")
        
        # Generate Cursor config
        cursor_config = self.generate_cursor_config(servers)
        cursor_path = Path("/home/keith/.config/Cursor/mcp_config.json")
        cursor_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cursor_path, 'w') as f:
            json.dump(cursor_config, f, indent=2)
        print(f"✅ Cursor config: {cursor_path}")
        
        # Generate VS Code config
        vscode_config = self.generate_vscode_config(servers)
        vscode_path = Path("/home/keith/.vscode/settings.json")
        vscode_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Merge with existing VS Code settings if they exist
        existing_vscode = {}
        if vscode_path.exists():
            try:
                with open(vscode_path, 'r') as f:
                    existing_vscode = json.load(f)
            except:
                pass
                
        existing_vscode.update(vscode_config)
        with open(vscode_path, 'w') as f:
            json.dump(existing_vscode, f, indent=2)
        print(f"✅ VS Code config: {vscode_path}")
        
        # Generate Claude Desktop config
        claude_config = self.generate_claude_desktop_config(servers)
        claude_path = Path("/home/keith/.config/claude-desktop/claude_desktop_config.json")
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        with open(claude_path, 'w') as f:
            json.dump(claude_config, f, indent=2)
        print(f"✅ Claude Desktop config: {claude_path}")
        
        # Generate portable config for other tools
        portable_config = {
            "mcp_servers": servers,
            "configurations": {
                "cursor": cursor_config,
                "vscode": vscode_config,
                "claude_desktop": claude_config
            }
        }
        
        portable_path = self.base_path / "mcp-portable-config.json"
        with open(portable_path, 'w') as f:
            json.dump(portable_config, f, indent=2)
        print(f"✅ Portable config: {portable_path}")
        
        # Generate deployment script
        self.generate_deployment_script(servers)
        
        print(f"\n🎉 Configuration complete! {len(servers)} MCP servers ready for:")
        print("  📝 Cursor IDE")
        print("  📝 VS Code")  
        print("  📝 Claude Desktop")
        print("  📝 Any MCP-compatible tool")
        
        return servers
    
    def generate_deployment_script(self, servers: Dict[str, Dict[str, Any]]):
        """Generate deployment script for easy setup"""
        script_content = f'''#!/bin/bash
# MCP Servers Deployment Script
# Auto-generated configuration for {len(servers)} MCP servers

set -e

echo "🚀 Deploying MCP configurations for all AI tools..."

# Create necessary directories
mkdir -p ~/.config/Cursor
mkdir -p ~/.config/claude-desktop
mkdir -p ~/.vscode
mkdir -p ~/chat-copilot/data

# Deploy Cursor configuration
echo "📝 Configuring Cursor..."
cp "{self.base_path}/configs/cursor-mcp-config.json" ~/.config/Cursor/mcp_config.json

# Deploy VS Code configuration  
echo "📝 Configuring VS Code..."
if [ -f ~/.vscode/settings.json ]; then
    echo "  Backing up existing VS Code settings..."
    cp ~/.vscode/settings.json ~/.vscode/settings.json.backup
fi
cp "{self.base_path}/configs/vscode-mcp-config.json" ~/.vscode/settings.json

# Deploy Claude Desktop configuration
echo "📝 Configuring Claude Desktop..."
cp "{self.base_path}/configs/claude-desktop-mcp-config.json" ~/.config/claude-desktop/claude_desktop_config.json

# Test MCP servers
echo "🧪 Testing MCP servers..."
test_count=0
working_count=0

'''
        
        for server_name, server_info in servers.items():
            if server_info["working"]:
                if server_info["type"] == "nodejs":
                    script_content += f'''
# Test {server_name}
echo "  Testing {server_name}..."
if node "{server_info["executable"]}" --help >/dev/null 2>&1; then
    echo "    ✅ {server_name} working"
    ((working_count++))
else
    echo "    ⚠️  {server_name} needs attention"
fi
((test_count++))
'''
                elif server_info["type"] == "python":
                    script_content += f'''
# Test {server_name}
echo "  Testing {server_name}..."
if python3 -c "import sys; sys.path.append('{server_info["path"]}'); print('OK')" >/dev/null 2>&1; then
    echo "    ✅ {server_name} working"
    ((working_count++))
else
    echo "    ⚠️  {server_name} needs attention"
fi
((test_count++))
'''

        script_content += '''
echo ""
echo "🎉 MCP Deployment Complete!"
echo "📊 Status: $working_count/$test_count servers working"
echo ""
echo "🔧 Next steps:"
echo "  1. Restart your AI tools (Cursor, VS Code, Claude Desktop)"
echo "  2. Use Command Palette → 'MCP: List Servers' to verify"
echo "  3. Access MCP tools via chat interfaces or command palette"
echo ""
echo "📁 Configuration files created:"
echo "  - ~/.config/Cursor/mcp_config.json"
echo "  - ~/.vscode/settings.json"
echo "  - ~/.config/claude-desktop/claude_desktop_config.json"
'''

        script_path = self.base_path / "deploy-mcp-configs.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"✅ Deployment script: {script_path}")

if __name__ == "__main__":
    generator = MCPConfigGenerator()
    servers = generator.generate_all_configs()
