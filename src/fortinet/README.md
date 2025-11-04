---
title: "README"
date: "2025-11-03"
tags: [chat-copilot, auto-tagged]
source: auto-import
status: imported
---

# Fortinet MCP Server

AI-native access to Fortinet FortiGate and FortiSwitch devices via Model Context Protocol (MCP).

## Features

### System Management
- `get_system_status` - Get system information (version, hostname, uptime, HA mode)
- `get_system_performance` - Get performance metrics (CPU, memory, sessions)

### Interface Management
- `list_interfaces` - List all network interfaces
- `get_interface_details` - Get detailed interface information

### Firewall Policy Management
- `list_firewall_policies` - List all firewall policies
- `get_policy_details` - Get detailed policy information
- `create_firewall_policy` - Create new firewall policy

### VPN Management
- `list_ipsec_tunnels` - List IPsec VPN tunnels with status
- `list_ssl_vpn_users` - List active SSL VPN sessions

### High Availability & Security Fabric
- `get_security_fabric_status` - Get Security Fabric topology
- `get_ha_status` - Get HA cluster status

### Logging & Monitoring
- `get_recent_logs` - Get recent logs (traffic, event, virus)
- `get_top_applications` - Get top applications by bandwidth

### FortiSwitch Management
- `list_fortiswitches` - List managed FortiSwitches

## Installation

```bash
cd /opt/ai-research-platform/chat-copilot/mcp-servers/src/fortinet
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Configuration

Create a `.env` file with your FortiGate credentials:

```env
# Primary FortiGate
FORTIGATE_PRIMARY_HOST=192.168.1.1
FORTIGATE_PRIMARY_API_KEY=your-api-key-here

# Secondary FortiGate (optional)
FORTIGATE_SECONDARY_HOST=192.168.1.2
FORTIGATE_SECONDARY_API_KEY=your-api-key-here

# FortiManager (optional)
FORTIGATE_FORTIMANAGER_HOST=10.128.144.132
FORTIGATE_FORTIMANAGER_API_KEY=your-fortimanager-key
```

## Running the Server

```bash
# Development
python server.py

# Production with uvicorn
uvicorn server:mcp --host 0.0.0.0 --port 8100
```

## Usage with OpenWebUI

### 1. Add MCP Server to OpenWebUI

In OpenWebUI settings:
1. Go to **Admin Panel** → **Functions**
2. Click **Add Function**
3. Add MCP Server URL: `http://localhost:8100`

### 2. Example Queries

**Get system status:**
```
Show me the status of our primary FortiGate
```

**List firewall policies:**
```
What firewall policies do we have on the primary FortiGate?
```

**Check VPN tunnels:**
```
Show me all IPsec VPN tunnels and their status
```

**Monitor performance:**
```
What's the current CPU and memory usage on our FortiGate?
```

**Create firewall policy:**
```
Create a firewall policy allowing HTTP from LAN to WAN
```

## API Key Generation

### FortiGate/FortiManager

1. Login to FortiGate web interface
2. Go to **System** → **Administrators**
3. Create a new **REST API Admin**
4. Set profile to `super_admin` (or custom with required permissions)
5. Generate API key
6. Copy the API key (shown only once!)

### Required Permissions

For full functionality, the API user needs:
- `fwpolicy` - Firewall policy management
- `system` - System configuration
- `vpn` - VPN management
- `log` - Log access
- `monitor` - Monitoring data

## Multi-Device Support

The server supports multiple FortiGate devices. Use the `device` parameter:

```python
# Primary device
get_system_status(device="primary")

# Secondary device
get_system_status(device="secondary")

# FortiManager
get_system_status(device="fortimanager")
```

## Security Considerations

- **SSL Verification**: Disabled by default for self-signed certificates
- **API Keys**: Store in `.env` file, never commit to git
- **Network Access**: Server should be on management network
- **Permissions**: Use least-privilege API users
- **Firewall**: Restrict MCP server access to authorized users

## Troubleshooting

### Connection Errors

```bash
# Test FortiGate API access
curl -k -H "Authorization: Bearer YOUR_API_KEY" \
  https://192.168.1.1/api/v2/monitor/system/status
```

### SSL Certificate Issues

If you have trusted certificates, enable SSL verification in `server.py`:

```python
self.verify_ssl = True  # Change from False
```

### Permission Denied

Ensure API user has required permissions. Check FortiGate logs:

```bash
# Get recent event logs
get_recent_logs(device="primary", log_type="event", count=50)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Tools

1. Add function with `@mcp.tool()` decorator
2. Include comprehensive docstring
3. Handle errors gracefully
4. Test with real FortiGate device

## Integration Examples

### With Restaurant Network Management

```python
# Check all Arby's FortiGates
devices = ["arbys-fw-01", "arbys-fw-02", "arbys-fw-03"]
for device in devices:
    status = await get_system_status(device=device)
    print(status)
```

### With Monitoring Stack

```python
# Export metrics to Prometheus
performance = await get_system_performance(device="primary")
# Parse and export metrics
```

## Roadmap

- [ ] FortiAnalyzer integration
- [ ] FortiManager device provisioning
- [ ] SD-WAN management
- [ ] FortiSwitch port configuration
- [ ] Bulk policy operations
- [ ] Webhook notifications
- [ ] Policy compliance checking

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: https://github.com/your-org/fortinet-mcp-server/issues
- Documentation: https://docs.your-org.com/mcp/fortinet
- FortiGate API Docs: https://docs.fortinet.com/document/fortigate/latest/rest-api
