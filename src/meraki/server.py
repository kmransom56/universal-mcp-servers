#!/usr/bin/env python3
"""
Meraki MCP Server - Cisco Meraki Dashboard API Management
Provides AI-native access to Meraki networks via MCP protocol

Features:
- Organization management
- Network management
- Device inventory and status
- Client tracking
- Switch port configuration
- Wireless configuration
- Appliance (MX) configuration
- Camera management
- Multi-organization support
"""

import os
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("Meraki Dashboard Manager")

# Meraki Dashboard API client
class MerakiAPI:
    """Meraki Dashboard API client with comprehensive network management"""

    def __init__(self, api_key: str, base_url: str = "https://api.meraki.com/api/v1"):
        self.api_key = api_key
        self.base_url = base_url

        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "X-Cisco-Meraki-API-Key": api_key,
                "Content-Type": "application/json"
            }
        )

    async def get(self, endpoint: str, params: Dict = None) -> Any:
        """Execute GET request to Meraki API"""
        url = urljoin(self.base_url, endpoint)
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, endpoint: str, data: Dict) -> Any:
        """Execute POST request to Meraki API"""
        url = urljoin(self.base_url, endpoint)
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()

    async def put(self, endpoint: str, data: Dict) -> Any:
        """Execute PUT request to Meraki API"""
        url = urljoin(self.base_url, endpoint)
        response = await self.client.put(url, json=data)
        response.raise_for_status()
        return response.json()

    async def delete(self, endpoint: str) -> Any:
        """Execute DELETE request to Meraki API"""
        url = urljoin(self.base_url, endpoint)
        response = await self.client.delete(url)
        response.raise_for_status()
        return response.json() if response.content else {}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global Meraki client
meraki_client: Optional[MerakiAPI] = None

def get_meraki_client() -> MerakiAPI:
    """Get or create Meraki API client"""
    global meraki_client
    if meraki_client is None:
        api_key = os.getenv("MERAKI_API_KEY")
        if not api_key:
            raise ValueError("MERAKI_API_KEY environment variable not set")
        meraki_client = MerakiAPI(api_key)
    return meraki_client

# ==================== Organization Management ====================

@mcp.tool()
async def list_organizations() -> str:
    """
    List all organizations accessible with the API key.

    Returns:
        List of organizations with IDs and names
    """
    client = get_meraki_client()
    orgs = await client.get("organizations")

    org_list = []
    for org in orgs:
        org_list.append(
            f"- {org['name']} (ID: {org['id']})\n"
            f"  URL: {org.get('url', 'N/A')}"
        )

    return f"Meraki Organizations ({len(orgs)} total):\n" + "\n".join(org_list)

@mcp.tool()
async def get_organization_details(org_id: str) -> str:
    """
    Get detailed information about an organization.

    Args:
        org_id: Organization ID

    Returns:
        Organization details
    """
    client = get_meraki_client()
    org = await client.get(f"organizations/{org_id}")

    return f"""Organization Details:
- Name: {org['name']}
- ID: {org['id']}
- URL: {org.get('url', 'N/A')}
- API Enabled: {org.get('api', {}).get('enabled', False)}
- Licensing Model: {org.get('licensing', {}).get('model', 'N/A')}
"""

@mcp.tool()
async def get_organization_inventory(org_id: str) -> str:
    """
    Get complete device inventory for an organization.

    Args:
        org_id: Organization ID

    Returns:
        Device inventory summary
    """
    client = get_meraki_client()
    devices = await client.get(f"organizations/{org_id}/devices")

    # Count devices by product type
    device_types = {}
    for device in devices:
        product = device.get('model', 'Unknown')
        device_types[product] = device_types.get(product, 0) + 1

    summary = [f"Total Devices: {len(devices)}\n"]
    summary.append("Device Breakdown:")
    for product, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True):
        summary.append(f"  - {product}: {count}")

    return "\n".join(summary)

# ==================== Network Management ====================

@mcp.tool()
async def list_networks(org_id: str) -> str:
    """
    List all networks in an organization.

    Args:
        org_id: Organization ID

    Returns:
        List of networks
    """
    client = get_meraki_client()
    networks = await client.get(f"organizations/{org_id}/networks")

    net_list = []
    for net in networks:
        net_list.append(
            f"- {net['name']} ({net['id']})\n"
            f"  Type: {', '.join(net.get('productTypes', []))}\n"
            f"  Timezone: {net.get('timeZone', 'N/A')}\n"
            f"  Tags: {', '.join(net.get('tags', [])) or 'None'}"
        )

    return f"Meraki Networks ({len(networks)} total):\n" + "\n".join(net_list)

@mcp.tool()
async def get_network_details(network_id: str) -> str:
    """
    Get detailed information about a network.

    Args:
        network_id: Network ID

    Returns:
        Network details
    """
    client = get_meraki_client()
    network = await client.get(f"networks/{network_id}")

    return f"""Network Details:
- Name: {network['name']}
- ID: {network['id']}
- Organization ID: {network['organizationId']}
- Product Types: {', '.join(network.get('productTypes', []))}
- Timezone: {network.get('timeZone', 'N/A')}
- Tags: {', '.join(network.get('tags', [])) or 'None'}
- Notes: {network.get('notes', 'None')}
"""

@mcp.tool()
async def create_network(
    org_id: str,
    name: str,
    product_types: List[str],
    timezone: str = "America/Los_Angeles",
    tags: List[str] = None
) -> str:
    """
    Create a new network in an organization.

    Args:
        org_id: Organization ID
        name: Network name
        product_types: Product types (appliance, switch, wireless, camera, cellularGateway)
        timezone: Timezone name
        tags: Optional tags

    Returns:
        Created network details
    """
    client = get_meraki_client()

    network_data = {
        "name": name,
        "productTypes": product_types,
        "timeZone": timezone
    }
    if tags:
        network_data["tags"] = tags

    network = await client.post(f"organizations/{org_id}/networks", data=network_data)

    return f"✅ Created network '{name}' (ID: {network['id']})"

# ==================== Device Management ====================

@mcp.tool()
async def list_network_devices(network_id: str) -> str:
    """
    List all devices in a network.

    Args:
        network_id: Network ID

    Returns:
        List of devices with status
    """
    client = get_meraki_client()
    devices = await client.get(f"networks/{network_id}/devices")

    device_list = []
    for device in devices:
        device_list.append(
            f"- {device.get('name', 'Unnamed')} ({device['model']})\n"
            f"  Serial: {device['serial']}\n"
            f"  MAC: {device.get('mac', 'N/A')}\n"
            f"  Status: {device.get('status', 'N/A')}\n"
            f"  IP: {device.get('lanIp', 'N/A')}"
        )

    return f"Network Devices ({len(devices)} total):\n" + "\n".join(device_list)

@mcp.tool()
async def get_device_status(serial: str) -> str:
    """
    Get current status of a device.

    Args:
        serial: Device serial number

    Returns:
        Device status information
    """
    client = get_meraki_client()
    status = await client.get(f"devices/{serial}/status")

    return f"""Device Status (Serial: {serial}):
- Status: {status.get('status', 'N/A')}
- Public IP: {status.get('publicIp', 'N/A')}
- LAN IP: {status.get('lanIp', 'N/A')}
- Gateway: {status.get('gateway', 'N/A')}
- DNS: {status.get('dns', 'N/A')}
- Last Reported: {status.get('lastReportedAt', 'N/A')}
"""

@mcp.tool()
async def claim_device(network_id: str, serial: str) -> str:
    """
    Claim a device into a network.

    Args:
        network_id: Network ID
        serial: Device serial number

    Returns:
        Claim result
    """
    client = get_meraki_client()
    await client.post(f"networks/{network_id}/devices/claim", data={"serials": [serial]})

    return f"✅ Claimed device {serial} into network {network_id}"

# ==================== Client Management ====================

@mcp.tool()
async def list_network_clients(network_id: str, timespan: int = 86400) -> str:
    """
    List all clients seen on a network.

    Args:
        network_id: Network ID
        timespan: Timespan in seconds (default: 86400 = 24 hours)

    Returns:
        List of clients
    """
    client = get_meraki_client()
    clients = await client.get(f"networks/{network_id}/clients", params={"timespan": timespan})

    client_list = []
    for c in clients[:20]:  # Limit to first 20
        client_list.append(
            f"- {c.get('description', c.get('mac', 'Unknown'))}\n"
            f"  MAC: {c['mac']}\n"
            f"  IP: {c.get('ip', 'N/A')}\n"
            f"  VLAN: {c.get('vlan', 'N/A')}\n"
            f"  Usage: {c.get('usage', {}).get('sent', 0) + c.get('usage', {}).get('recv', 0')} bytes"
        )

    return f"Network Clients ({len(clients)} total, showing first 20):\n" + "\n".join(client_list)

@mcp.tool()
async def get_client_details(network_id: str, client_id: str) -> str:
    """
    Get detailed information about a specific client.

    Args:
        network_id: Network ID
        client_id: Client ID or MAC address

    Returns:
        Client details
    """
    client = get_meraki_client()
    c = await client.get(f"networks/{network_id}/clients/{client_id}")

    return f"""Client Details:
- Description: {c.get('description', 'N/A')}
- MAC: {c['mac']}
- IP: {c.get('ip', 'N/A')}
- User: {c.get('user', 'N/A')}
- VLAN: {c.get('vlan', 'N/A')}
- SSID: {c.get('ssid', 'N/A')}
- Manufacturer: {c.get('manufacturer', 'N/A')}
- OS: {c.get('os', 'N/A')}
- First Seen: {c.get('firstSeen', 'N/A')}
- Last Seen: {c.get('lastSeen', 'N/A')}
"""

# ==================== Switch Management ====================

@mcp.tool()
async def list_switch_ports(serial: str) -> str:
    """
    List all ports on a switch.

    Args:
        serial: Switch serial number

    Returns:
        List of switch ports with configuration
    """
    client = get_meraki_client()
    ports = await client.get(f"devices/{serial}/switch/ports")

    port_list = []
    for port in ports:
        port_list.append(
            f"- Port {port['portId']}: {port.get('name', 'Unnamed')}\n"
            f"  Enabled: {port.get('enabled', False)}\n"
            f"  Type: {port.get('type', 'N/A')}\n"
            f"  VLAN: {port.get('vlan', 'N/A')}\n"
            f"  PoE: {port.get('poeEnabled', False)}"
        )

    return f"Switch Ports ({len(ports)} total):\n" + "\n".join(port_list)

@mcp.tool()
async def configure_switch_port(
    serial: str,
    port_id: str,
    name: str = None,
    enabled: bool = True,
    port_type: str = "access",
    vlan: int = None,
    poe_enabled: bool = None
) -> str:
    """
    Configure a switch port.

    Args:
        serial: Switch serial number
        port_id: Port number
        name: Port name
        enabled: Enable/disable port
        port_type: Port type (access/trunk)
        vlan: VLAN ID
        poe_enabled: Enable/disable PoE

    Returns:
        Configuration result
    """
    client = get_meraki_client()

    config = {"enabled": enabled, "type": port_type}
    if name:
        config["name"] = name
    if vlan:
        config["vlan"] = vlan
    if poe_enabled is not None:
        config["poeEnabled"] = poe_enabled

    await client.put(f"devices/{serial}/switch/ports/{port_id}", data=config)

    return f"✅ Configured port {port_id} on switch {serial}"

# ==================== Wireless Management ====================

@mcp.tool()
async def list_wireless_ssids(network_id: str) -> str:
    """
    List all SSIDs configured on a network.

    Args:
        network_id: Network ID

    Returns:
        List of SSIDs
    """
    client = get_meraki_client()
    ssids = await client.get(f"networks/{network_id}/wireless/ssids")

    ssid_list = []
    for ssid in ssids:
        if ssid.get('name'):  # Only show configured SSIDs
            ssid_list.append(
                f"- SSID {ssid['number']}: {ssid['name']}\n"
                f"  Enabled: {ssid.get('enabled', False)}\n"
                f"  Auth: {ssid.get('authMode', 'N/A')}\n"
                f"  Encryption: {ssid.get('encryptionMode', 'N/A')}\n"
                f"  Visible: {not ssid.get('hideSsid', False)}"
            )

    return f"Wireless SSIDs:\n" + "\n".join(ssid_list)

@mcp.tool()
async def configure_ssid(
    network_id: str,
    number: int,
    name: str,
    enabled: bool = True,
    auth_mode: str = "psk",
    psk: str = None
) -> str:
    """
    Configure a wireless SSID.

    Args:
        network_id: Network ID
        number: SSID number (0-14)
        name: SSID name
        enabled: Enable/disable SSID
        auth_mode: Authentication mode (open/psk/8021x-meraki/etc)
        psk: Pre-shared key (for WPA/WPA2)

    Returns:
        Configuration result
    """
    client = get_meraki_client()

    config = {
        "name": name,
        "enabled": enabled,
        "authMode": auth_mode
    }
    if psk:
        config["psk"] = psk

    await client.put(f"networks/{network_id}/wireless/ssids/{number}", data=config)

    return f"✅ Configured SSID {number} '{name}' on network {network_id}"

# ==================== Appliance (MX) Management ====================

@mcp.tool()
async def get_appliance_uplink_status(network_id: str) -> str:
    """
    Get uplink status for MX appliances.

    Args:
        network_id: Network ID

    Returns:
        Uplink status information
    """
    client = get_meraki_client()
    uplinks = await client.get(f"networks/{network_id}/appliance/uplink/statuses")

    uplink_list = []
    for uplink in uplinks:
        uplink_list.append(
            f"- {uplink.get('interface', 'Unknown')}\n"
            f"  Status: {uplink.get('status', 'N/A')}\n"
            f"  IP: {uplink.get('ip', 'N/A')}\n"
            f"  Gateway: {uplink.get('gateway', 'N/A')}\n"
            f"  DNS: {', '.join(uplink.get('dns', []))}"
        )

    return f"Appliance Uplinks:\n" + "\n".join(uplink_list)

@mcp.tool()
async def list_firewall_rules(network_id: str) -> str:
    """
    List Layer 3 firewall rules on an MX appliance.

    Args:
        network_id: Network ID

    Returns:
        List of firewall rules
    """
    client = get_meraki_client()
    rules = await client.get(f"networks/{network_id}/appliance/firewall/l3FirewallRules")

    rule_list = []
    for idx, rule in enumerate(rules.get('rules', []), 1):
        rule_list.append(
            f"- Rule {idx}: {rule.get('comment', 'Unnamed')}\n"
            f"  Policy: {rule.get('policy', 'N/A')}\n"
            f"  Protocol: {rule.get('protocol', 'any')}\n"
            f"  Src: {rule.get('srcCidr', 'any')} Port: {rule.get('srcPort', 'any')}\n"
            f"  Dst: {rule.get('destCidr', 'any')} Port: {rule.get('destPort', 'any')}"
        )

    return f"Firewall Rules ({len(rule_list)} total):\n" + "\n".join(rule_list[:20])

# ==================== Camera Management ====================

@mcp.tool()
async def list_camera_quality_profiles(network_id: str) -> str:
    """
    List camera quality and retention profiles.

    Args:
        network_id: Network ID

    Returns:
        List of quality profiles
    """
    client = get_meraki_client()
    profiles = await client.get(f"networks/{network_id}/camera/qualityRetentionProfiles")

    profile_list = []
    for profile in profiles:
        profile_list.append(
            f"- {profile.get('name', 'Unnamed')} (ID: {profile['id']})\n"
            f"  Motion Detection: {profile.get('motionBasedRetentionEnabled', False)}\n"
            f"  Resolution: {profile.get('videoSettings', {}).get('MV12/MV22/MV72', {}).get('quality', 'N/A')}"
        )

    return f"Camera Quality Profiles:\n" + "\n".join(profile_list)

# ==================== Analytics & Monitoring ====================

@mcp.tool()
async def get_network_traffic(network_id: str, timespan: int = 3600) -> str:
    """
    Get network traffic analytics.

    Args:
        network_id: Network ID
        timespan: Timespan in seconds (default: 3600 = 1 hour)

    Returns:
        Traffic analytics summary
    """
    client = get_meraki_client()
    traffic = await client.get(
        f"networks/{network_id}/traffic",
        params={"timespan": timespan}
    )

    # Summarize top applications
    if traffic:
        top_apps = sorted(traffic, key=lambda x: x.get('sent', 0) + x.get('recv', 0), reverse=True)[:10]

        traffic_list = []
        for app in top_apps:
            total = app.get('sent', 0) + app.get('recv', 0)
            traffic_list.append(
                f"- {app.get('application', 'Unknown')}: {total / 1024 / 1024:.2f} MB"
            )

        return f"Top 10 Applications (Last {timespan}s):\n" + "\n".join(traffic_list)
    else:
        return "No traffic data available"

# ==================== Server Lifecycle ====================

@mcp.resource("meraki://organizations")
async def list_meraki_organizations() -> str:
    """List all accessible Meraki organizations"""
    client = get_meraki_client()
    orgs = await client.get("organizations")
    return f"Accessible organizations: {', '.join([org['name'] for org in orgs])}"

async def cleanup():
    """Cleanup Meraki API client"""
    if meraki_client:
        await meraki_client.close()

if __name__ == "__main__":
    import signal

    # Register cleanup on shutdown
    def signal_handler(sig, frame):
        asyncio.run(cleanup())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the MCP server
    mcp.run()
