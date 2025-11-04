#!/usr/bin/env python3
"""
Fortinet MCP Server - FortiGate and FortiSwitch Management
Provides AI-native access to Fortinet devices via MCP protocol

Features:
- FortiGate firewall management
- Security policy operations
- System information and monitoring
- Interface management
- VPN configuration
- Security Fabric topology
- FortiSwitch management
- Multi-device support
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
mcp = FastMCP("Fortinet Device Manager")

# FortiGate API client
class FortiGateAPI:
    """FortiGate REST API client with comprehensive device management"""

    def __init__(self, host: str, api_key: str, verify_ssl: bool = False):
        self.host = host.rstrip('/')
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.base_url = f"https://{self.host}/api/v2"

        self.client = httpx.AsyncClient(
            verify=verify_ssl,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

    async def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Execute GET request to FortiGate API"""
        url = urljoin(self.base_url, endpoint)
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, endpoint: str, data: Dict) -> Dict:
        """Execute POST request to FortiGate API"""
        url = urljoin(self.base_url, endpoint)
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()

    async def put(self, endpoint: str, data: Dict) -> Dict:
        """Execute PUT request to FortiGate API"""
        url = urljoin(self.base_url, endpoint)
        response = await self.client.put(url, json=data)
        response.raise_for_status()
        return response.json()

    async def delete(self, endpoint: str) -> Dict:
        """Execute DELETE request to FortiGate API"""
        url = urljoin(self.base_url, endpoint)
        response = await self.client.delete(url)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global FortiGate clients (supports multiple devices)
fortigate_clients: Dict[str, FortiGateAPI] = {}

def get_fortigate_client(device_name: str = "primary") -> FortiGateAPI:
    """Get or create FortiGate API client for specified device"""
    if device_name not in fortigate_clients:
        host = os.getenv(f"FORTIGATE_{device_name.upper()}_HOST")
        api_key = os.getenv(f"FORTIGATE_{device_name.upper()}_API_KEY")

        if not host or not api_key:
            raise ValueError(f"Missing configuration for FortiGate device: {device_name}")

        fortigate_clients[device_name] = FortiGateAPI(host, api_key)

    return fortigate_clients[device_name]

# ==================== System Information ====================

@mcp.tool()
async def get_system_status(device: str = "primary") -> str:
    """
    Get FortiGate system status including version, hostname, and uptime.

    Args:
        device: Device name (primary, secondary, etc.)

    Returns:
        System status information
    """
    client = get_fortigate_client(device)
    result = await client.get("monitor/system/status")

    return f"""FortiGate System Status ({device}):
- Hostname: {result['results']['hostname']}
- Version: {result['results']['version']}
- Serial: {result['results']['serial']}
- Uptime: {result['results'].get('uptime', 'N/A')}
- HA Mode: {result['results'].get('ha-mode', 'standalone')}
- Operation Mode: {result['results'].get('operation-mode', 'N/A')}
"""

@mcp.tool()
async def get_system_performance(device: str = "primary") -> str:
    """
    Get FortiGate system performance metrics (CPU, memory, sessions).

    Args:
        device: Device name

    Returns:
        Performance metrics
    """
    client = get_fortigate_client(device)
    perf = await client.get("monitor/system/resource/usage")

    cpu = perf['results']['cpu'][0] if 'cpu' in perf['results'] else {}
    memory = perf['results'].get('memory', {})
    sessions = perf['results'].get('session', {})

    return f"""FortiGate Performance ({device}):
- CPU Usage: {cpu.get('usage', 'N/A')}%
- Memory Usage: {memory.get('used_percent', 'N/A')}%
- Active Sessions: {sessions.get('current', 'N/A')}
- Total Disk: {perf['results'].get('disk', {}).get('total', 'N/A')} GB
"""

# ==================== Interface Management ====================

@mcp.tool()
async def list_interfaces(device: str = "primary") -> str:
    """
    List all network interfaces on FortiGate.

    Args:
        device: Device name

    Returns:
        List of interfaces with status
    """
    client = get_fortigate_client(device)
    result = await client.get("cmdb/system/interface")

    interfaces = []
    for intf in result.get('results', []):
        interfaces.append(
            f"- {intf['name']}: {intf.get('ip', 'N/A')} "
            f"[{intf.get('status', 'unknown')}] "
            f"({intf.get('type', 'physical')})"
        )

    return f"FortiGate Interfaces ({device}):\n" + "\n".join(interfaces)

@mcp.tool()
async def get_interface_details(device: str, interface_name: str) -> str:
    """
    Get detailed information about a specific interface.

    Args:
        device: Device name
        interface_name: Name of the interface

    Returns:
        Interface details
    """
    client = get_fortigate_client(device)
    result = await client.get(f"cmdb/system/interface/{interface_name}")

    intf = result.get('results', [{}])[0]
    return f"""Interface Details ({device} - {interface_name}):
- IP: {intf.get('ip', 'N/A')}
- Status: {intf.get('status', 'N/A')}
- Type: {intf.get('type', 'N/A')}
- VLAN ID: {intf.get('vlanid', 'N/A')}
- MTU: {intf.get('mtu', 'N/A')}
- Speed: {intf.get('speed', 'N/A')}
- Mode: {intf.get('mode', 'N/A')}
"""

# ==================== Firewall Policy Management ====================

@mcp.tool()
async def list_firewall_policies(device: str = "primary", vdom: str = "root") -> str:
    """
    List all firewall policies.

    Args:
        device: Device name
        vdom: Virtual domain (default: root)

    Returns:
        List of firewall policies
    """
    client = get_fortigate_client(device)
    result = await client.get(f"cmdb/firewall/policy", params={"vdom": vdom})

    policies = []
    for policy in result.get('results', []):
        policies.append(
            f"- Policy {policy['policyid']}: "
            f"{policy.get('name', 'Unnamed')} "
            f"[{policy.get('status', 'enabled')}] "
            f"{policy.get('srcintf', [])} -> {policy.get('dstintf', [])} "
            f"(Action: {policy.get('action', 'N/A')})"
        )

    return f"Firewall Policies ({device}/{vdom}):\n" + "\n".join(policies[:20])

@mcp.tool()
async def get_policy_details(device: str, policy_id: int, vdom: str = "root") -> str:
    """
    Get detailed information about a specific firewall policy.

    Args:
        device: Device name
        policy_id: Policy ID number
        vdom: Virtual domain

    Returns:
        Policy details
    """
    client = get_fortigate_client(device)
    result = await client.get(f"cmdb/firewall/policy/{policy_id}", params={"vdom": vdom})

    policy = result.get('results', [{}])[0]
    return f"""Firewall Policy Details ({device} - Policy {policy_id}):
- Name: {policy.get('name', 'N/A')}
- Status: {policy.get('status', 'N/A')}
- Source Interface: {', '.join(policy.get('srcintf', []))}
- Destination Interface: {', '.join(policy.get('dstintf', []))}
- Source Address: {', '.join([a['name'] for a in policy.get('srcaddr', [])])}
- Destination Address: {', '.join([a['name'] for a in policy.get('dstaddr', [])])}
- Service: {', '.join([s['name'] for s in policy.get('service', [])])}
- Action: {policy.get('action', 'N/A')}
- NAT: {policy.get('nat', 'disabled')}
- Log Traffic: {policy.get('logtraffic', 'disabled')}
"""

@mcp.tool()
async def create_firewall_policy(
    device: str,
    name: str,
    srcintf: List[str],
    dstintf: List[str],
    srcaddr: List[str],
    dstaddr: List[str],
    service: List[str],
    action: str = "accept",
    vdom: str = "root"
) -> str:
    """
    Create a new firewall policy.

    Args:
        device: Device name
        name: Policy name
        srcintf: Source interfaces
        dstintf: Destination interfaces
        srcaddr: Source addresses
        dstaddr: Destination addresses
        service: Services
        action: Action (accept/deny)
        vdom: Virtual domain

    Returns:
        Creation result
    """
    client = get_fortigate_client(device)

    policy_data = {
        "name": name,
        "srcintf": [{"name": i} for i in srcintf],
        "dstintf": [{"name": i} for i in dstintf],
        "srcaddr": [{"name": a} for a in srcaddr],
        "dstaddr": [{"name": a} for a in dstaddr],
        "service": [{"name": s} for s in service],
        "action": action,
        "schedule": "always",
        "status": "enable"
    }

    result = await client.post(f"cmdb/firewall/policy", data=policy_data)
    return f"✅ Created firewall policy '{name}' on {device} (VDOM: {vdom})"

# ==================== VPN Management ====================

@mcp.tool()
async def list_ipsec_tunnels(device: str = "primary") -> str:
    """
    List all IPsec VPN tunnels.

    Args:
        device: Device name

    Returns:
        List of IPsec tunnels with status
    """
    client = get_fortigate_client(device)
    result = await client.get("monitor/vpn/ipsec")

    tunnels = []
    for tunnel in result.get('results', []):
        tunnels.append(
            f"- {tunnel.get('name', 'N/A')}: "
            f"Status={tunnel.get('status', 'N/A')} "
            f"Remote={tunnel.get('remote-gw', 'N/A')} "
            f"Type={tunnel.get('type', 'N/A')}"
        )

    return f"IPsec VPN Tunnels ({device}):\n" + "\n".join(tunnels)

@mcp.tool()
async def list_ssl_vpn_users(device: str = "primary") -> str:
    """
    List active SSL VPN users.

    Args:
        device: Device name

    Returns:
        List of active SSL VPN sessions
    """
    client = get_fortigate_client(device)
    result = await client.get("monitor/vpn/ssl")

    users = []
    for user in result.get('results', []):
        users.append(
            f"- {user.get('user_name', 'N/A')}: "
            f"IP={user.get('remote_host', 'N/A')} "
            f"Duration={user.get('duration', 'N/A')}s "
            f"RX/TX={user.get('bytes_rx', 0)}/{user.get('bytes_tx', 0)}"
        )

    return f"SSL VPN Users ({device}):\n" + ("\n".join(users) if users else "No active sessions")

# ==================== Security Fabric & HA ====================

@mcp.tool()
async def get_security_fabric_status(device: str = "primary") -> str:
    """
    Get Security Fabric topology and status.

    Args:
        device: Device name

    Returns:
        Security Fabric information
    """
    client = get_fortigate_client(device)
    result = await client.get("monitor/system/csf")

    fabric = result.get('results', {})
    return f"""Security Fabric Status ({device}):
- Status: {fabric.get('status', 'N/A')}
- Root: {fabric.get('is-root', False)}
- Upstream: {fabric.get('upstream', 'N/A')}
- Downstream Devices: {len(fabric.get('downstream', []))}
"""

@mcp.tool()
async def get_ha_status(device: str = "primary") -> str:
    """
    Get High Availability (HA) cluster status.

    Args:
        device: Device name

    Returns:
        HA cluster information
    """
    client = get_fortigate_client(device)
    result = await client.get("monitor/system/ha-peer")

    ha_info = []
    for peer in result.get('results', []):
        ha_info.append(
            f"- {peer.get('hostname', 'N/A')}: "
            f"Priority={peer.get('priority', 'N/A')} "
            f"Status={peer.get('status', 'N/A')} "
            f"Serial={peer.get('serial_no', 'N/A')}"
        )

    return f"HA Cluster Status ({device}):\n" + "\n".join(ha_info)

# ==================== Logging & Monitoring ====================

@mcp.tool()
async def get_recent_logs(
    device: str = "primary",
    log_type: str = "traffic",
    count: int = 10
) -> str:
    """
    Get recent logs from FortiGate.

    Args:
        device: Device name
        log_type: Type of logs (traffic, event, virus, etc.)
        count: Number of logs to retrieve

    Returns:
        Recent log entries
    """
    client = get_fortigate_client(device)
    result = await client.get(
        f"monitor/log/{log_type}/select",
        params={"rows": count}
    )

    logs = []
    for log in result.get('results', [])[:count]:
        logs.append(
            f"- [{log.get('date', 'N/A')} {log.get('time', 'N/A')}] "
            f"{log.get('type', 'N/A')}: {log.get('msg', log.get('action', 'N/A'))}"
        )

    return f"Recent {log_type.title()} Logs ({device}):\n" + "\n".join(logs)

@mcp.tool()
async def get_top_applications(device: str = "primary", count: int = 10) -> str:
    """
    Get top applications by bandwidth usage.

    Args:
        device: Device name
        count: Number of top applications

    Returns:
        Top applications by bandwidth
    """
    client = get_fortigate_client(device)
    result = await client.get("monitor/firewall/app-ctrl/stats")

    apps = []
    for app in result.get('results', [])[:count]:
        apps.append(
            f"- {app.get('application', 'N/A')}: "
            f"Bandwidth={app.get('bytes', 0)} bytes "
            f"Sessions={app.get('sessions', 0)}"
        )

    return f"Top Applications ({device}):\n" + "\n".join(apps)

# ==================== FortiSwitch Management ====================

@mcp.tool()
async def list_fortiswitches(device: str = "primary") -> str:
    """
    List all FortiSwitches managed by this FortiGate.

    Args:
        device: Device name

    Returns:
        List of managed FortiSwitches
    """
    client = get_fortigate_client(device)
    result = await client.get("monitor/switch-controller/managed-switch")

    switches = []
    for switch in result.get('results', []):
        switches.append(
            f"- {switch.get('name', 'N/A')}: "
            f"Model={switch.get('model', 'N/A')} "
            f"Status={switch.get('status', 'N/A')} "
            f"Ports={switch.get('ports', 'N/A')}"
        )

    return f"FortiSwitches ({device}):\n" + "\n".join(switches)

# ==================== Server Lifecycle ====================

@mcp.resource("fortinet://devices")
async def list_configured_devices() -> str:
    """List all configured FortiGate devices"""
    devices = []
    for key in os.environ:
        if key.startswith("FORTIGATE_") and key.endswith("_HOST"):
            device_name = key.replace("FORTIGATE_", "").replace("_HOST", "").lower()
            devices.append(device_name)

    return f"Configured FortiGate devices: {', '.join(devices) if devices else 'None'}"

async def cleanup():
    """Cleanup all FortiGate API clients"""
    for client in fortigate_clients.values():
        await client.close()

if __name__ == "__main__":
    import signal

    # Register cleanup on shutdown
    def signal_handler(sig, frame):
        asyncio.run(cleanup())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the MCP server
    mcp.run()
