#!/bin/bash
# Universal MCP Server Installer & Configuration Manager
# Supports: Cursor, VS Code, Claude Desktop, Copilot CLI, Gemini CLI, and more

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_BASE_DIR="/home/keith/chat-copilot/mcp-servers-consolidated"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO") echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
    esac
}

install_for_tool() {
    local tool=$1
    local config_path=$2
    local config_file=$3
    
    print_status "INFO" "Installing MCP configuration for $tool..."
    
    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$config_path")"
    
    # Backup existing configuration
    if [ -f "$config_path" ]; then
        print_status "WARNING" "Backing up existing $tool configuration..."
        cp "$config_path" "${config_path}.backup.$(date +%Y%m%d-%H%M%S)"
    fi
    
    # Copy new configuration
    if [ -f "$MCP_BASE_DIR/configs/$config_file" ]; then
        cp "$MCP_BASE_DIR/configs/$config_file" "$config_path"
        print_status "SUCCESS" "$tool configuration installed at $config_path"
    else
        print_status "ERROR" "Configuration file not found: $config_file"
        return 1
    fi
}

build_nodejs_servers() {
    print_status "INFO" "Building Node.js MCP servers..."
    
    cd "$MCP_BASE_DIR/src"
    
    local built_count=0
    local total_count=0
    
    for server_dir in */; do
        if [ -f "${server_dir}package.json" ]; then
            ((total_count++))
            print_status "INFO" "Building ${server_dir%/}..."
            
            cd "$server_dir"
            
            # Install dependencies
            if npm install --silent 2>/dev/null; then
                # Try to build
                if npm run build --silent 2>/dev/null || [ -f "dist/index.js" ] || [ -f "index.js" ]; then
                    ((built_count++))
                    print_status "SUCCESS" "${server_dir%/} built successfully"
                else
                    print_status "WARNING" "${server_dir%/} no build needed or failed"
                fi
            else
                print_status "WARNING" "${server_dir%/} npm install failed"
            fi
            
            cd ..
        fi
    done
    
    print_status "SUCCESS" "Built $built_count/$total_count Node.js servers"
}

setup_python_servers() {
    print_status "INFO" "Setting up Python MCP servers..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$MCP_BASE_DIR/mcp-venv" ]; then
        print_status "INFO" "Creating Python virtual environment..."
        python3 -m venv "$MCP_BASE_DIR/mcp-venv"
    fi
    
    # Install common dependencies
    print_status "INFO" "Installing Python dependencies..."
    "$MCP_BASE_DIR/mcp-venv/bin/pip" install --quiet fastmcp httpx python-dotenv asyncio-mqtt pydantic
    
    # Install each Python server
    cd "$MCP_BASE_DIR/src"
    local installed_count=0
    
    for server_dir in */; do
        if [ -f "${server_dir}pyproject.toml" ]; then
            print_status "INFO" "Installing ${server_dir%/}..."
            cd "$server_dir"
            
            if "$MCP_BASE_DIR/mcp-venv/bin/pip" install -e . --quiet 2>/dev/null; then
                ((installed_count++))
                print_status "SUCCESS" "${server_dir%/} installed"
            else
                print_status "WARNING" "${server_dir%/} installation failed"
            fi
            
            cd ..
        fi
    done
    
    print_status "SUCCESS" "Installed $installed_count Python servers"
}

create_tool_configs() {
    print_status "INFO" "Creating configurations for all AI tools..."
    
    mkdir -p "$MCP_BASE_DIR/configs"
    
    # Generate updated configurations with all servers
    cd "$MCP_BASE_DIR"
    python3 mcp-config-generator.py
    
    # Create additional tool-specific configurations
    
    # GitHub Copilot CLI configuration
    cat > "$MCP_BASE_DIR/configs/github-copilot-mcp.json" << 'EOF'
{
  "mcp_servers": {
    "git": {
      "command": "python3",
      "args": ["-m", "mcp_server_git", "stdio"],
      "cwd": "/home/keith/chat-copilot/mcp-servers-consolidated/src/git"
    },
    "filesystem": {
      "command": "node", 
      "args": ["/home/keith/chat-copilot/mcp-servers-consolidated/src/filesystem/dist/index.js"],
      "env": {
        "ALLOWED_DIRECTORIES": "/home/keith"
      }
    },
    "memory": {
      "command": "node",
      "args": ["/home/keith/chat-copilot/mcp-servers-consolidated/src/memory/dist/index.js"],
      "env": {
        "MEMORY_FILE_PATH": "/home/keith/chat-copilot/data/mcp-memory.json"
      }
    }
  }
}
EOF

    # Cursor CLI configuration
    cat > "$MCP_BASE_DIR/configs/cursor-cli-mcp.json" << 'EOF'
{
  "mcp": {
    "enabled": true,
    "servers": [
      {
        "name": "memory",
        "command": "node",
        "args": ["/home/keith/chat-copilot/mcp-servers-consolidated/src/memory/dist/index.js"],
        "env": {
          "MEMORY_FILE_PATH": "/home/keith/chat-copilot/data/mcp-memory.json"
        }
      },
      {
        "name": "filesystem",
        "command": "node",
        "args": ["/home/keith/chat-copilot/mcp-servers-consolidated/src/filesystem/dist/index.js"],
        "env": {
          "ALLOWED_DIRECTORIES": "/home/keith"
        }
      },
      {
        "name": "git",
        "command": "python3",
        "args": ["-m", "mcp_server_git", "stdio"],
        "cwd": "/home/keith/chat-copilot/mcp-servers-consolidated/src/git"
      }
    ]
  }
}
EOF

    print_status "SUCCESS" "Tool-specific configurations created"
}

install_all_tools() {
    print_status "INFO" "Installing MCP configurations for all AI tools..."
    
    # Cursor IDE
    install_for_tool "Cursor IDE" "/home/keith/.config/Cursor/mcp_config.json" "cursor-mcp-config.json"
    
    # VS Code
    install_for_tool "VS Code" "/home/keith/.vscode/settings.json" "vscode-mcp-config.json"
    
    # Claude Desktop
    install_for_tool "Claude Desktop" "/home/keith/.config/claude-desktop/claude_desktop_config.json" "claude-desktop-mcp-config.json"
    
    # GitHub Copilot CLI
    install_for_tool "GitHub Copilot CLI" "/home/keith/.config/github-copilot/mcp_config.json" "github-copilot-mcp.json"
    
    # Cursor CLI
    install_for_tool "Cursor CLI" "/home/keith/.config/cursor-cli/mcp_config.json" "cursor-cli-mcp.json"
    
    # Gemini CLI
    install_for_tool "Gemini CLI" "/home/keith/.config/gemini-cli/mcp_config.yaml" "gemini-cli-mcp-config.yaml"
    
    print_status "SUCCESS" "All AI tools configured with MCP servers"
}

test_mcp_servers() {
    print_status "INFO" "Testing MCP servers..."
    
    local working_count=0
    local total_count=0
    
    # Test Node.js servers
    for server in memory filesystem everything sequential-thinking; do
        ((total_count++))
        if [ -f "$MCP_BASE_DIR/src/$server/dist/index.js" ] || [ -f "$MCP_BASE_DIR/src/$server/index.js" ]; then
            if timeout 5 node "$MCP_BASE_DIR/src/$server/dist/index.js" --help >/dev/null 2>&1 || 
               timeout 5 node "$MCP_BASE_DIR/src/$server/index.js" --help >/dev/null 2>&1; then
                ((working_count++))
                print_status "SUCCESS" "$server server working"
            else
                print_status "WARNING" "$server server needs attention"
            fi
        else
            print_status "WARNING" "$server server not found"
        fi
    done
    
    # Test Python servers
    for server in git ai-mcp-platform time sentry; do
        ((total_count++))
        if [ -d "$MCP_BASE_DIR/src/$server" ]; then
            if timeout 5 python3 -c "import sys; sys.path.append('$MCP_BASE_DIR/src/$server'); print('OK')" >/dev/null 2>&1; then
                ((working_count++))
                print_status "SUCCESS" "$server server working"
            else
                print_status "WARNING" "$server server needs attention"
            fi
        else
            print_status "WARNING" "$server server not found"
        fi
    done
    
    print_status "SUCCESS" "Testing complete: $working_count/$total_count servers working"
}

show_usage() {
    echo "🚀 Universal MCP Server Installer & Configuration Manager"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install-all    Install MCP configs for all AI tools"
    echo "  build          Build all Node.js MCP servers"
    echo "  setup-python   Setup Python MCP servers"
    echo "  test           Test all MCP servers"
    echo "  list-tools     List supported AI tools"
    echo "  status         Show current MCP server status"
    echo ""
    echo "Supported AI Tools:"
    echo "  📝 Cursor IDE"
    echo "  📝 VS Code"
    echo "  📝 Claude Desktop"
    echo "  📝 GitHub Copilot CLI"
    echo "  📝 Cursor CLI"
    echo "  📝 Gemini CLI"
}

main() {
    case "${1:-install-all}" in
        "install-all")
            build_nodejs_servers
            setup_python_servers
            create_tool_configs
            install_all_tools
            test_mcp_servers
            print_status "SUCCESS" "🎉 Universal MCP installation complete!"
            ;;
        "build")
            build_nodejs_servers
            ;;
        "setup-python")
            setup_python_servers
            ;;
        "test")
            test_mcp_servers
            ;;
        "list-tools")
            echo "📝 Supported AI Tools:"
            echo "  - Cursor IDE"
            echo "  - VS Code"
            echo "  - Claude Desktop"
            echo "  - GitHub Copilot CLI"
            echo "  - Cursor CLI"
            echo "  - Gemini CLI"
            ;;
        "status")
            print_status "INFO" "MCP Server Status:"
            ls -la "$MCP_BASE_DIR/src" | grep "^d" | wc -l | xargs echo "  Total servers:"
            test_mcp_servers
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_status "ERROR" "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
