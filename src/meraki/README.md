---
title: "README"
date: "2025-11-03"
tags: [chat-copilot, auto-tagged]
source: auto-import
status: imported
---

# Meraki MCP Server

AI-native access to Cisco Meraki Dashboard via Model Context Protocol (MCP).

## Features

### Organization Management
- `list_organizations` - List all accessible organizations
- `get_organization_details` - Get organization information
- `get_organization_inventory` - Get complete device inventory

### Network Management
- `list_networks` - List all networks in an organization
- `get_network_details` - Get detailed network information
- `create_network` - Create a new network

### Device Management
- `list_network_devices` - List all devices in a network
- `get_device_status` - Get current device status
- `claim_device` - Claim a device into a network

### Client Management
- `list_network_clients` - List all clients on a network
- `get_client_details` - Get detailed client information

### Switch Management
- `list_switch_ports` - List all ports on a switch
- `configure_switch_port` - Configure a switch port

### Wireless Management
- `list_wireless_ssids` - List all SSIDs
- `configure_ssid` - Configure a wireless SSID

### Appliance (MX) Management
- `get_appliance_uplink_status` - Get uplink status
- `list_firewall_rules` - List Layer 3 firewall rules

### Camera Management
- `list_camera_quality_profiles` - List camera quality profiles

### Analytics & Monitoring
- `get_network_traffic` - Get network traffic analytics

## Installation

```bash
cd /opt/ai-research-platform/chat-copilot/mcp-servers/src/meraki
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Configuration

Create a `.env` file with your Meraki API key:

```env
# Meraki Dashboard API Key
MERAKI_API_KEY=your-meraki-api-key-here

# Optional: Custom API base URL
# MERAKI_BASE_URL=https://api.meraki.com/api/v1
```

## Running the Server

```bash
# Development
python server.py

# Production with uvicorn
uvicorn server:mcp --host 0.0.0.0 --port 8101
```

## Usage with OpenWebUI

### 1. Add MCP Server to OpenWebUI

In OpenWebUI settings:
1. Go to **Admin Panel** → **Functions**
2. Click **Add Function**
3. Add MCP Server URL: `http://localhost:8101`

### 2. Example Queries

**List organizations:**
```
Show me all Meraki organizations
```

**Get device inventory:**
```
What devices do we have in organization 123456?
```

**Check client connections:**
```
Show me all clients connected to network N_123456 in the last 24 hours
```

**Configure switch port:**
```
Enable PoE on port 12 of switch Q2AB-CDEF-1234
```

**Monitor network traffic:**
```
What are the top applications using bandwidth on network N_123456?
```

## API Key Generation

### Meraki Dashboard

1. Login to Meraki Dashboard
2. Go to **Organization** → **Settings**
3. Scroll to **Dashboard API access**
4. Click **Enable access**
5. Click **Generate new API key**
6. Copy the API key (shown only once!)

### API Key Scope

Meraki API keys have organization-level access. The same key can access all organizations associated with your Meraki account.

### Required Permissions

For full functionality, your account needs:
- **Read access**: View devices, clients, configurations
- **Write access**: Modify configurations, claim devices, create networks
- **API access enabled**: Organization must have API access enabled

## Multi-Organization Support

The server automatically handles multiple organizations:

```python
# List all organizations
orgs = await list_organizations()

# Work with specific organization
devices = await get_organization_inventory(org_id="123456")
```

## Security Considerations

- **API Keys**: Store in `.env` file, never commit to git
- **Rate Limiting**: Meraki enforces rate limits (5 requests per second)
- **Network Access**: Consider restricting MCP server to management network
- **Permissions**: Use least-privilege accounts
- **Audit Logs**: All API calls are logged in Meraki Dashboard

## Troubleshooting

### Connection Errors

```bash
# Test Meraki API access
curl -H "X-Cisco-Meraki-API-Key: YOUR_API_KEY" \
  https://api.meraki.com/api/v1/organizations
```

### Rate Limiting

The Meraki API has rate limits:
- **5 requests per second** per organization
- **429 Too Many Requests** response when exceeded

The server handles rate limiting automatically with retries.

### Organization Access

If you can't see expected organizations:
1. Verify API access is enabled for the organization
2. Check your account has access to the organization
3. Confirm API key is valid and not expired

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Tools

1. Add function with `@mcp.tool()` decorator
2. Include comprehensive docstring
3. Handle errors gracefully
4. Test with real Meraki organization

## Integration Examples

### With Restaurant Network Management

```python
# Monitor all restaurant locations
networks = await list_networks(org_id="restaurant_org")

# Check POS system connectivity
clients = await list_network_clients(network_id="store_123")
```

### With Monitoring Stack

```python
# Export device status to Prometheus
devices = await list_network_devices(network_id="network_id")
# Parse and export metrics
```

## Supported Meraki Products

- **MX** - Security & SD-WAN Appliances
- **MS** - Switches
- **MR** - Wireless Access Points
- **MV** - Smart Cameras
- **MG** - Cellular Gateways
- **MT** - Sensors
- **SM** - Systems Manager (MDM)

## Roadmap

- [ ] Systems Manager (MDM) integration
- [ ] Sensor (MT) data retrieval
- [ ] Cellular Gateway (MG) management
- [ ] Bulk configuration operations
- [ ] Webhook event handling
- [ ] Change management workflows
- [ ] Compliance reporting

## Resources

- **Meraki API Docs**: https://developer.cisco.com/meraki/api-v1/
- **API Explorer**: https://developer.cisco.com/meraki/api-v1/
- **Meraki Community**: https://community.meraki.com/
- **Rate Limits**: https://developer.cisco.com/meraki/api-v1/#!rate-limit

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: https://github.com/your-org/meraki-mcp-server/issues
- Documentation: https://docs.your-org.com/mcp/meraki
