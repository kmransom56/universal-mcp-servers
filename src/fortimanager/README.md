---
title: "README"
date: "2025-11-03"
tags: [chat-copilot, auto-tagged]
source: auto-import
status: imported
---

# FortiManager MCP Server

AI-native access to FortiManager for centralized FortiGate management via Model Context Protocol (MCP).

## Why FortiManager Instead of Direct FortiGate Access?

**Use FortiManager when:**
- ✅ You can't access FortiGates directly (need jumpbox)
- ✅ You manage multiple FortiGate devices (10+)
- ✅ You need centralized policy management
- ✅ You want configuration templates
- ✅ You need centralized logging and reporting
- ✅ You manage restaurant chains with many locations

**FortiManager Benefits:**
- **Centralized Management**: Manage 1000+ FortiGates from one console
- **Policy Templates**: Deploy consistent policies across locations
- **ADOM Support**: Separate management domains (per chain, per region)
- **Configuration Backup**: Automatic backup of all device configs
- **Bulk Operations**: Push changes to multiple devices at once
- **Workflow Automation**: Approval workflows for changes

## Features

### System Management
- `get_fortimanager_status` - System information
- `get_fortimanager_performance` - Performance metrics

### ADOM Management
- `list_adoms` - List all administrative domains
- `get_adom_details` - Get ADOM information

### Device Management
- `list_managed_devices` - List all managed FortiGates
- `get_device_details` - Get device information
- `add_device` - Add new FortiGate to management

### Policy Management
- `list_policy_packages` - List policy packages
- `list_firewall_policies` - List policies in package
- `create_firewall_policy` - Create new policy
- `install_policy_package` - Push policies to devices

### FortiSwitch Management
- `list_fortiswitches` - List managed FortiSwitches

### Configuration & Tasks
- `get_device_config` - Get device configuration
- `get_task_status` - Check task status

### Restaurant Chain Support
- `get_restaurant_devices` - Get all devices for a chain (Arby's, BWW, Sonic)

## Installation

```bash
cd /opt/ai-research-platform/chat-copilot/mcp-servers/src/fortimanager
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Configuration

Create a `.env` file:

```env
# Primary FortiManager
FORTIMANAGER_PRIMARY_HOST=192.168.1.100
FORTIMANAGER_PRIMARY_USERNAME=admin
FORTIMANAGER_PRIMARY_PASSWORD=your-password-here

# Restaurant Chain FortiManagers
FORTIMANAGER_ARBYS_HOST=10.128.144.132
FORTIMANAGER_ARBYS_USERNAME=admin
FORTIMANAGER_ARBYS_PASSWORD=your-password-here

FORTIMANAGER_BWW_HOST=10.128.145.4
FORTIMANAGER_BWW_USERNAME=admin
FORTIMANAGER_BWW_PASSWORD=your-password-here

FORTIMANAGER_SONIC_HOST=10.128.156.36
FORTIMANAGER_SONIC_USERNAME=admin
FORTIMANAGER_SONIC_PASSWORD=your-password-here
```

## Running the Server

```bash
# Development
python server.py

# Production with uvicorn
uvicorn server:mcp --host 0.0.0.0 --port 8102
```

## Usage with OpenWebUI

### Example Queries

**System Monitoring:**
```
Show me the FortiManager status
What's the performance of our FortiManager?
```

**Device Management:**
```
List all managed FortiGates in Arby's ADOM
Show me devices in the root ADOM
Get details for device FG-STORE-001
Add FortiGate 192.168.1.50 to the BWW ADOM
```

**Policy Management:**
```
List all policy packages in the Sonic ADOM
Show firewall policies in the default package
Create a policy allowing HTTPS from LAN to WAN
Install the updated policy package to all Arby's devices
```

**Restaurant Operations:**
```
How many devices do we have across all Arby's locations?
Show me all FortiGates for Buffalo Wild Wings
Get device inventory for Sonic restaurants
```

**Configuration Management:**
```
Get the configuration for device FG-STORE-042
Check the status of task 12345
What ADOMs do we have configured?
```

## FortiManager JSON-RPC API

FortiManager uses JSON-RPC instead of REST API. The MCP server handles this automatically.

### API Methods
- **get**: Retrieve configuration
- **set**: Replace configuration
- **add**: Add new object
- **update**: Update existing object
- **delete**: Delete object
- **exec**: Execute command

### Authentication
- Session-based authentication
- Automatic session management
- Session timeout handling

## Multi-Device Support

The server supports multiple FortiManagers. Use the `device` parameter:

```python
# Primary FortiManager
get_fortimanager_status(device="primary")

# Arby's FortiManager
list_managed_devices(device="arbys", adom="root")

# BWW FortiManager
get_restaurant_devices(chain="bww")
```

## ADOM (Administrative Domain)

ADOMs allow you to separate management domains:

**Use Cases:**
- **Per Restaurant Chain**: Separate ADOM for Arby's, BWW, Sonic
- **Per Region**: East Coast, West Coast, Central
- **Per Environment**: Production, Staging, Development
- **Per Customer**: If managing multiple customers

**Benefits:**
- **Isolation**: Changes in one ADOM don't affect others
- **RBAC**: Different admins for different ADOMs
- **Separate Policies**: Different firewall rules per ADOM
- **Independent Upgrades**: Upgrade one ADOM at a time

## Workflow Example: Adding New Restaurant Location

```bash
# 1. Add the FortiGate to FortiManager
"Add device FG-RESTAURANT-NEW at IP 10.1.50.1 to the Arby's ADOM"

# 2. Verify device added
"Show me all devices in Arby's ADOM"

# 3. Install policy package to new device
"Install the Arby's-Standard policy package to FG-RESTAURANT-NEW"

# 4. Check installation status
"Check the status of task 67890"

# 5. Verify configuration
"Get configuration for FG-RESTAURANT-NEW"
```

## API Documentation

API documentation is available in `/home/keith/chat-copilot/api/`:
- FortiOS Monitor API for switch-controller operations
- Comprehensive Swagger 2.0 specifications

## Security Considerations

- **Credentials**: Store username/password in `.env`, never commit
- **Session Management**: Automatic login/logout
- **SSL Verification**: Disabled by default for self-signed certs
- **RBAC**: Use least-privilege FortiManager accounts
- **Change Control**: Use ADOM workflow approvals

## Troubleshooting

### Connection Errors

```bash
# Test FortiManager access
curl -k -X POST https://FORTIMANAGER_IP/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"id":1,"method":"exec","params":[{"url":"/sys/login/user","data":{"user":"admin","passwd":"PASSWORD"}}],"session":null}'
```

### Session Timeout

The server automatically handles session timeouts by re-authenticating.

### Permission Denied

Ensure your FortiManager user has required permissions:
- **Read**: View configurations
- **Read-Write**: Modify configurations
- **Execute**: Install policies

## Comparison: FortiGate Direct vs FortiManager

| Feature | FortiGate Direct | FortiManager |
|---------|------------------|--------------|
| **Access** | Direct device access | Centralized access |
| **Scale** | 1-10 devices | 1-10,000 devices |
| **Policies** | Per-device | Centralized templates |
| **Deployment** | Manual per device | Bulk operations |
| **Backup** | Manual | Automatic |
| **Reporting** | Per-device logs | Centralized logs |
| **Best For** | Small deployments | Enterprise, multi-site |

## Restaurant Chain Deployment

### Arby's (~2,000-3,000 devices)
- FortiManager: 10.128.144.132
- ADOM: arbys-production
- Policy Packages: arbys-standard, arbys-kiosk, arbys-pos

### Buffalo Wild Wings (~2,500-3,500 devices)
- FortiManager: 10.128.145.4
- ADOM: bww-production
- Policy Packages: bww-standard, bww-gaming, bww-sports

### Sonic (~7,000-10,000 devices)
- FortiManager: 10.128.156.36
- ADOM: sonic-production
- Policy Packages: sonic-standard, sonic-drive-thru, sonic-pos

## Roadmap

- [ ] Configuration templates management
- [ ] Firmware upgrade orchestration
- [ ] Log query and analysis
- [ ] Report generation
- [ ] Device discovery and provisioning
- [ ] Script execution
- [ ] FortiAnalyzer integration

## Resources

- **FortiManager Documentation**: https://docs.fortinet.com/product/fortimanager
- **JSON-RPC API Guide**: https://fndn.fortinet.net/
- **FortiManager Admin Guide**: https://docs.fortinet.com/document/fortimanager/

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: https://github.com/your-org/fortimanager-mcp-server/issues
- FortiManager API Docs: https://fndn.fortinet.net/
