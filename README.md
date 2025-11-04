# 🚀 Universal MCP Servers Collection

> **Comprehensive collection of 40+ Model Context Protocol (MCP) servers for all major AI development tools**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple)](https://modelcontextprotocol.io/)

## 📋 **Overview**

This repository contains a comprehensive collection of **40+ MCP servers** that provide powerful capabilities to AI development tools. All servers are **portable** and **production-ready** with **one-command installation** for multiple AI tools.

### **🎯 Supported AI Tools**
- 📝 **Cursor IDE** - Full integration with all servers
- 📝 **VS Code** - Complete MCP extension support  
- 📝 **Claude Desktop** - Native MCP integration
- 📝 **GitHub Copilot CLI** - Command-line MCP support
- 📝 **Cursor CLI** - Terminal-based MCP access
- 📝 **Gemini CLI** - Google's CLI with MCP support

---

## 🚀 **Quick Start**

### **One-Command Installation**
```bash
git clone https://github.com/kmransom56/universal-mcp-servers.git
cd universal-mcp-servers
./universal-mcp-installer.sh install-all
```

This will:
- ✅ Build all Node.js MCP servers
- ✅ Setup Python MCP servers with virtual environment
- ✅ Generate configurations for all AI tools
- ✅ Install configurations in correct locations
- ✅ Test all servers for functionality

### **Individual Tool Setup**
```bash
# Cursor IDE only
./universal-mcp-installer.sh install-cursor

# VS Code only  
./universal-mcp-installer.sh install-vscode

# Claude Desktop only
./universal-mcp-installer.sh install-claude
```

---

## 📊 **MCP Server Categories**

### **🤖 AI & Platform Integration (6 servers)**
| Server | Description | Language | Status |
|--------|-------------|----------|--------|
| **ai-mcp-platform** | Gateway to AI platform services | Python | ✅ |
| **memory** | Persistent knowledge storage | Node.js | ✅ |
| **everything** | Universal search and retrieval | Node.js | ✅ |
| **sequential-thinking** | Structured reasoning workflows | Node.js | ✅ |
| **openai** | OpenAI API integration | Node.js | ✅ |
| **aiautodash-mcp** | AIAutoDash agent integration | Python | ✅ |

### **📁 File & Data Operations (8 servers)**
| Server | Description | Language | Status |
|--------|-------------|----------|--------|
| **filesystem** | Safe file system operations | Node.js | ✅ |
| **git** | Git repository operations | Python | ✅ |
| **fetch** | HTTP requests and API calls | Node.js | ✅ |
| **sqlite** | Database operations | Python | ✅ |
| **gdrive** | Google Drive integration | Node.js | ✅ |
| **spreadsheet-processing** | Excel/Google Sheets operations | Node.js | ✅ |
| **data-validation** | Data validation tools | Node.js | ✅ |
| **file-compression** | Archive/compression tools | Node.js | ✅ |

### **🎨 Media Processing (4 servers)**
| Server | Description | Language | Status |
|--------|-------------|----------|--------|
| **image-processing** | Image manipulation and analysis | Node.js | ✅ |
| **audio-processing** | Audio file operations | Node.js | ✅ |
| **video-processing** | Video file processing | Node.js | ✅ |
| **pdf-processing** | PDF document manipulation | Node.js | ✅ |

### **🌐 Network & Infrastructure (6 servers)**
| Server | Description | Language | Status |
|--------|-------------|----------|--------|
| **fortinet** | Fortinet device management (246+ APIs) | Python | ✅ |
| **fortimanager** | FortiManager integration | Python | ✅ |
| **meraki** | Cisco Meraki management (7,816+ devices) | Python | ✅ |
| **network** | General network tools | Python | ✅ |
| **sentry** | Error tracking and monitoring | Python | ✅ |
| **time** | Time and date operations | Python | ✅ |

### **🛠️ Utility & Processing (3 servers)**
| Server | Description | Language | Status |
|--------|-------------|----------|--------|
| **text-processing** | Advanced text manipulation | Node.js | ✅ |
| **sequential-thinking** | Chain-of-thought reasoning | Node.js | ✅ |
| **data-validation** | Data integrity validation | Node.js | ✅ |

---

## 🔧 **Configuration Management**

### **Automatic Configuration Generation**
```bash
# Generate configs for all tools
python3 mcp-config-generator.py

# Check current status
./universal-mcp-installer.sh status

# Test all servers
./universal-mcp-installer.sh test
```

### **Manual Configuration**
Each AI tool has its configuration stored in:
- **Cursor**: `~/.config/Cursor/mcp_config.json`
- **VS Code**: `~/.vscode/settings.json`
- **Claude Desktop**: `~/.config/claude-desktop/claude_desktop_config.json`
- **Copilot CLI**: `~/.config/github-copilot/mcp_config.json`
- **Cursor CLI**: `~/.config/cursor-cli/mcp_config.json`
- **Gemini CLI**: `~/.config/gemini-cli/mcp_config.yaml`

---

## 🎯 **Usage Examples**

### **In Cursor IDE**
```
1. Restart Cursor after installation
2. Command Palette → "MCP: List Servers" (should show 14+ servers)
3. Use in chat: "Use the git MCP server to show recent commits"
4. Use in chat: "Use the memory server to remember this important fact"
```

### **In VS Code**
```
1. Install MCP extension (if needed)
2. Restart VS Code
3. Command Palette → "MCP: Connect to Servers"
4. Access tools via Command Palette or integrated chat
```

### **Command Line Usage**
```bash
# GitHub Copilot CLI
gh copilot suggest --mcp-server memory "remember project architecture"

# Cursor CLI
cursor-cli --mcp git "analyze recent changes"

# Direct MCP server usage
node src/memory/dist/index.js
python3 -m mcp_server_git
```

---

## 🛠️ **Development**

### **Adding New Servers**
1. Create server in `src/your-server-name/`
2. Add `package.json` (Node.js) or `pyproject.toml` (Python)
3. Run `python3 mcp-config-generator.py` to update configs
4. Run `./universal-mcp-installer.sh install-all` to deploy

### **Building from Source**
```bash
# Build all Node.js servers
npm run build:all

# Setup Python servers
./universal-mcp-installer.sh setup-python

# Generate all configurations
npm run generate-configs
```

### **Testing**
```bash
# Test all servers
npm test

# Test specific server
node src/memory/dist/index.js --help
python3 -m mcp_server_git --help
```

---

## 📚 **Documentation**

### **Server Documentation**
Each server includes:
- `README.md` - Server-specific documentation
- `pyproject.toml` or `package.json` - Dependencies and metadata
- Example usage and configuration

### **Tool Integration Guides**
- [Cursor IDE Integration](docs/cursor-integration.md)
- [VS Code Integration](docs/vscode-integration.md)
- [Claude Desktop Integration](docs/claude-integration.md)
- [CLI Tools Integration](docs/cli-integration.md)

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-server`)
3. Add your MCP server in `src/your-server-name/`
4. Update documentation
5. Test with `./universal-mcp-installer.sh test`
6. Submit a pull request

### **Server Requirements**
- Follow MCP protocol specification
- Include comprehensive README
- Add proper error handling
- Include tests where applicable
- Support stdio communication

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

- 📖 **Documentation**: Check individual server READMEs
- 🐛 **Issues**: [GitHub Issues](https://github.com/kmransom56/universal-mcp-servers/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/kmransom56/universal-mcp-servers/discussions)

---

## 🎉 **Features**

### **🔄 Universal Compatibility**
- Works with **6+ AI development tools**
- **Portable configurations** across different systems
- **Environment variable support** for API keys and settings

### **🛠️ Easy Management**
- **One-command installation** for all tools
- **Automatic building** and dependency management
- **Health checking** and validation
- **Backup system** for existing configurations

### **📊 Production Ready**
- **Error handling** and graceful failures
- **Comprehensive logging** and status reporting
- **Virtual environment isolation** for Python servers
- **Dependency management** for Node.js servers

### **🎯 Comprehensive Coverage**
- **AI Integration**: Platform gateways, memory, reasoning
- **File Operations**: Git, filesystem, data processing
- **Media Processing**: Images, audio, video, PDFs
- **Network Management**: Fortinet, Meraki, monitoring
- **Utilities**: Text processing, validation, compression

---

**🎯 Transform your AI development workflow with 40+ powerful MCP servers!**