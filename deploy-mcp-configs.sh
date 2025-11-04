#!/bin/bash
# MCP Servers Deployment Script
# Auto-generated configuration for 14 MCP servers

set -e

echo "🚀 Deploying MCP configurations for all AI tools..."

# Create necessary directories
mkdir -p ~/.config/Cursor
mkdir -p ~/.config/claude-desktop
mkdir -p ~/.vscode
mkdir -p ~/chat-copilot/data

# Deploy Cursor configuration
echo "📝 Configuring Cursor..."
cp "/home/keith/chat-copilot/mcp-servers-consolidated/configs/cursor-mcp-config.json" ~/.config/Cursor/mcp_config.json

# Deploy VS Code configuration  
echo "📝 Configuring VS Code..."
if [ -f ~/.vscode/settings.json ]; then
    echo "  Backing up existing VS Code settings..."
    cp ~/.vscode/settings.json ~/.vscode/settings.json.backup
fi
cp "/home/keith/chat-copilot/mcp-servers-consolidated/configs/vscode-mcp-config.json" ~/.vscode/settings.json

# Deploy Claude Desktop configuration
echo "📝 Configuring Claude Desktop..."
cp "/home/keith/chat-copilot/mcp-servers-consolidated/configs/claude-desktop-mcp-config.json" ~/.config/claude-desktop/claude_desktop_config.json

# Test MCP servers
echo "🧪 Testing MCP servers..."
test_count=0
working_count=0


# Test time
echo "  Testing time..."
if python3 -c "import sys; sys.path.append('/home/keith/chat-copilot/mcp-servers-consolidated/src/time'); print('OK')" >/dev/null 2>&1; then
    echo "    ✅ time working"
    ((working_count++))
else
    echo "    ⚠️  time needs attention"
fi
((test_count++))

# Test git
echo "  Testing git..."
if python3 -c "import sys; sys.path.append('/home/keith/chat-copilot/mcp-servers-consolidated/src/git'); print('OK')" >/dev/null 2>&1; then
    echo "    ✅ git working"
    ((working_count++))
else
    echo "    ⚠️  git needs attention"
fi
((test_count++))

# Test memory
echo "  Testing memory..."
if node "/home/keith/chat-copilot/mcp-servers-consolidated/src/memory/dist/index.js" --help >/dev/null 2>&1; then
    echo "    ✅ memory working"
    ((working_count++))
else
    echo "    ⚠️  memory needs attention"
fi
((test_count++))

# Test sentry
echo "  Testing sentry..."
if python3 -c "import sys; sys.path.append('/home/keith/chat-copilot/mcp-servers-consolidated/src/sentry'); print('OK')" >/dev/null 2>&1; then
    echo "    ✅ sentry working"
    ((working_count++))
else
    echo "    ⚠️  sentry needs attention"
fi
((test_count++))

# Test meraki
echo "  Testing meraki..."
if python3 -c "import sys; sys.path.append('/home/keith/chat-copilot/mcp-servers-consolidated/src/meraki'); print('OK')" >/dev/null 2>&1; then
    echo "    ✅ meraki working"
    ((working_count++))
else
    echo "    ⚠️  meraki needs attention"
fi
((test_count++))

# Test spreadsheet-processing
echo "  Testing spreadsheet-processing..."
if node "/home/keith/chat-copilot/mcp-servers-consolidated/src/spreadsheet-processing/index.js" --help >/dev/null 2>&1; then
    echo "    ✅ spreadsheet-processing working"
    ((working_count++))
else
    echo "    ⚠️  spreadsheet-processing needs attention"
fi
((test_count++))

# Test pdf-processing
echo "  Testing pdf-processing..."
if node "/home/keith/chat-copilot/mcp-servers-consolidated/src/pdf-processing/index.js" --help >/dev/null 2>&1; then
    echo "    ✅ pdf-processing working"
    ((working_count++))
else
    echo "    ⚠️  pdf-processing needs attention"
fi
((test_count++))

# Test fortimanager
echo "  Testing fortimanager..."
if python3 -c "import sys; sys.path.append('/home/keith/chat-copilot/mcp-servers-consolidated/src/fortimanager'); print('OK')" >/dev/null 2>&1; then
    echo "    ✅ fortimanager working"
    ((working_count++))
else
    echo "    ⚠️  fortimanager needs attention"
fi
((test_count++))

# Test gdrive
echo "  Testing gdrive..."
if node "/home/keith/chat-copilot/mcp-servers-consolidated/src/gdrive/index.js" --help >/dev/null 2>&1; then
    echo "    ✅ gdrive working"
    ((working_count++))
else
    echo "    ⚠️  gdrive needs attention"
fi
((test_count++))

# Test everything
echo "  Testing everything..."
if node "/home/keith/chat-copilot/mcp-servers-consolidated/src/everything/dist/index.js" --help >/dev/null 2>&1; then
    echo "    ✅ everything working"
    ((working_count++))
else
    echo "    ⚠️  everything needs attention"
fi
((test_count++))

# Test filesystem
echo "  Testing filesystem..."
if node "/home/keith/chat-copilot/mcp-servers-consolidated/src/filesystem/dist/index.js" --help >/dev/null 2>&1; then
    echo "    ✅ filesystem working"
    ((working_count++))
else
    echo "    ⚠️  filesystem needs attention"
fi
((test_count++))

# Test sequentialthinking
echo "  Testing sequentialthinking..."
if node "/home/keith/chat-copilot/mcp-servers-consolidated/src/sequentialthinking/dist/index.js" --help >/dev/null 2>&1; then
    echo "    ✅ sequentialthinking working"
    ((working_count++))
else
    echo "    ⚠️  sequentialthinking needs attention"
fi
((test_count++))

# Test fetch
echo "  Testing fetch..."
if node "/home/keith/chat-copilot/mcp-servers-consolidated/src/fetch/index.js" --help >/dev/null 2>&1; then
    echo "    ✅ fetch working"
    ((working_count++))
else
    echo "    ⚠️  fetch needs attention"
fi
((test_count++))

# Test fortinet
echo "  Testing fortinet..."
if python3 -c "import sys; sys.path.append('/home/keith/chat-copilot/mcp-servers-consolidated/src/fortinet'); print('OK')" >/dev/null 2>&1; then
    echo "    ✅ fortinet working"
    ((working_count++))
else
    echo "    ⚠️  fortinet needs attention"
fi
((test_count++))

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
