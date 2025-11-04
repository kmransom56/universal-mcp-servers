#!/usr/bin/env python3
"""
FortiManager MCP Server - Centralized FortiGate Management
Provides AI-native access to FortiManager JSON-RPC API via MCP protocol

Features:
- Centralized multi-device management
- Device inventory and status
- Policy management across ADOMs
- Configuration templates
- Device provisioning
- Firmware management
- Log and report access
- Restaurant chain support (Arby's, BWW, Sonic)
"""

import os
import httpx
import asyncio
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("FortiManager Centralized Manager")

# FortiManager JSON-RPC API client
class FortiManagerAPI:
    """FortiManager JSON-RPC API client for centralized FortiGate management"""

    def __init__(self, host: str, username: str, password: str, verify_ssl: bool = False):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.base_url = f"https://{self.host}/jsonrpc"
        self.session_id = None
        self.request_id = 1

        self.client = httpx.AsyncClient(
            verify=verify_ssl,
            timeout=60.0,
            headers={"Content-Type": "application/json"}
        )

    async def login(self) -> bool:
        """Login to FortiManager and get session ID"""
        if self.session_id:
            return True

        payload = {
            "id": self.request_id,
            "method": "exec",
            "params": [{
                "url": "/sys/login/user",
                "data": {
                    "user": self.username,
                    "passwd": self.password
                }
            }],
            "session": None
        }

        response = await self.client.post(self.base_url, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
            self.session_id = result.get('session')
            self.request_id += 1
            return True
        return False

    async def logout(self):
        """Logout from FortiManager"""
        if not self.session_id:
            return

        payload = {
            "id": self.request_id,
            "method": "exec",
            "params": [{
                "url": "/sys/logout"
            }],
            "session": self.session_id
        }

        await self.client.post(self.base_url, json=payload)
        self.session_id = None

    async def request(self, method: str, url: str, params: Dict = None) -> Dict:
        """Execute JSON-RPC request to FortiManager"""
        if not self.session_id:
            await self.login()

        payload = {
            "id": self.request_id,
            "method": method,
            "params": [{
                "url": url
            }],
            "session": self.session_id
        }

        if params:
            payload["params"][0].update(params)

        self.request_id += 1

        response = await self.client.post(self.base_url, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get('result', [{}])[0].get('status', {}).get('code') != 0:
            error_msg = result.get('result', [{}])[0].get('status', {}).get('message', 'Unknown error')
            raise Exception(f"FortiManager API error: {error_msg}")

        return result.get('result', [{}])[0].get('data', {})

    async def get(self, url: str, params: Dict = None) -> Dict:
        """Execute GET request"""
        return await self.request("get", url, params)

    async def set(self, url: str, data: Dict) -> Dict:
        """Execute SET request"""
        return await self.request("set", url, {"data": data})

    async def add(self, url: str, data: Dict) -> Dict:
        """Execute ADD request"""
        return await self.request("add", url, {"data": data})

    async def update(self, url: str, data: Dict) -> Dict:
        """Execute UPDATE request"""
        return await self.request("update", url, {"data": data})

    async def delete(self, url: str, params: Dict = None) -> Dict:
        """Execute DELETE request"""
        return await self.request("delete", url, params)

    async def execute(self, url: str, params: Dict = None) -> Dict:
        """Execute EXEC request"""
        return await self.request("exec", url, params)

    async def close(self):
        """Close the HTTP client"""
        await self.logout()
        await self.client.aclose()

# Global FortiManager clients
fortimanager_clients: Dict[str, FortiManagerAPI] = {}

def get_fortimanager_client(device_name: str = "primary") -> FortiManagerAPI:
    """Get or create FortiManager API client"""
    if device_name not in fortimanager_clients:
        host = os.getenv(f"FORTIMANAGER_{device_name.upper()}_HOST")
        username = os.getenv(f"FORTIMANAGER_{device_name.upper()}_USERNAME", "admin")
        password = os.getenv(f"FORTIMANAGER_{device_name.upper()}_PASSWORD")

        if not host or not password:
            raise ValueError(f"Missing configuration for FortiManager: {device_name}")

        fortimanager_clients[device_name] = FortiManagerAPI(host, username, password)

    return fortimanager_clients[device_name]

# ==================== System Information ====================

@mcp.tool()
async def get_fortimanager_status(device: str = "primary") -> str:
    """
    Get FortiManager system status including version, hostname, and license.

    Args:
        device: FortiManager device name (primary, arbys, bww, sonic)

    Returns:
        System status information
    """
    client = get_fortimanager_client(device)
    result = await client.get("/sys/status")

    return f"""FortiManager System Status ({device}):
- Version: {result.get('Version', 'N/A')}
- Serial: {result.get('Serial Number', 'N/A')}
- Hostname: {result.get('Hostname', 'N/A')}
- FIPS Mode: {result.get('FIPS Mode', 'N/A')}
- HA Mode: {result.get('HA Mode', 'N/A')}
- Platform: {result.get('Platform Type', 'N/A')}
"""

@mcp.tool()
async def get_fortimanager_performance(device: str = "primary") -> str:
    """
    Get FortiManager performance metrics.

    Args:
        device: FortiManager device name

    Returns:
        Performance metrics
    """
    client = get_fortimanager_client(device)
    result = await client.get("/sys/performance")

    cpu = result.get('CPU', {})
    memory = result.get('Memory', {})
    disk = result.get('Disk', {})

    return f"""FortiManager Performance ({device}):
- CPU Usage: {cpu.get('Usage', 'N/A')}%
- Memory Usage: {memory.get('Usage', 'N/A')}%
- Disk Usage: {disk.get('Usage', 'N/A')}%
- Logged-in Users: {result.get('Current Sessions', 'N/A')}
"""

# ==================== ADOM Management ====================

@mcp.tool()
async def list_adoms(device: str = "primary") -> str:
    """
    List all Administrative Domains (ADOMs).

    Args:
        device: FortiManager device name

    Returns:
        List of ADOMs
    """
    client = get_fortimanager_client(device)
    result = await client.get("/dvmdb/adom")

    adoms = []
    for adom in result:
        adoms.append(
            f"- {adom.get('name', 'N/A')}: "
            f"Version {adom.get('os_ver', 'N/A')} "
            f"[{adom.get('state', 'N/A')}] "
            f"({adom.get('desc', 'No description')})"
        )

    return f"ADOMs ({len(adoms)} total):\n" + "\n".join(adoms)

@mcp.tool()
async def get_adom_details(device: str, adom_name: str) -> str:
    """
    Get detailed information about an ADOM.

    Args:
        device: FortiManager device name
        adom_name: ADOM name

    Returns:
        ADOM details
    """
    client = get_fortimanager_client(device)
    result = await client.get(f"/dvmdb/adom/{adom_name}")

    return f"""ADOM Details ({device} - {adom_name}):
- Name: {result.get('name', 'N/A')}
- Description: {result.get('desc', 'N/A')}
- OS Version: {result.get('os_ver', 'N/A')}
- Mode: {result.get('mode', 'N/A')}
- State: {result.get('state', 'N/A')}
- Workspace Mode: {result.get('workspace_mode', 'N/A')}
- Created: {result.get('create_time', 'N/A')}
"""

# ==================== Device Management ====================

@mcp.tool()
async def list_managed_devices(device: str = "primary", adom: str = "root") -> str:
    """
    List all managed FortiGate devices.

    Args:
        device: FortiManager device name
        adom: ADOM name (default: root)

    Returns:
        List of managed devices
    """
    client = get_fortimanager_client(device)
    result = await client.get(f"/dvmdb/adom/{adom}/device")

    devices = []
    for dev in result:
        devices.append(
            f"- {dev.get('name', 'N/A')}: "
            f"{dev.get('ip', 'N/A')} "
            f"SN: {dev.get('sn', 'N/A')} "
            f"[{dev.get('conn_status', 'N/A')}] "
            f"Version: {dev.get('os_ver', 'N/A')}"
        )

    return f"Managed Devices in ADOM '{adom}' ({len(devices)} total):\n" + "\n".join(devices)

@mcp.tool()
async def get_device_details(device: str, adom: str, device_name: str) -> str:
    """
    Get detailed information about a managed device.

    Args:
        device: FortiManager device name
        adom: ADOM name
        device_name: FortiGate device name

    Returns:
        Device details
    """
    client = get_fortimanager_client(device)
    result = await client.get(f"/dvmdb/adom/{adom}/device/{device_name}")

    return f"""Device Details ({device} - {adom}/{device_name}):
- Name: {result.get('name', 'N/A')}
- IP Address: {result.get('ip', 'N/A')}
- Serial Number: {result.get('sn', 'N/A')}
- Platform: {result.get('platform_str', 'N/A')}
- OS Version: {result.get('os_ver', 'N/A')}
- Connection Status: {result.get('conn_status', 'N/A')}
- HA Mode: {result.get('ha_mode', 'N/A')}
- Management Mode: {result.get('mgmt_mode', 'N/A')}
- VDOM Status: {result.get('vdom_status', 'N/A')}
"""

@mcp.tool()
async def add_device(
    device: str,
    adom: str,
    device_name: str,
    device_ip: str,
    username: str,
    password: str
) -> str:
    """
    Add a new FortiGate device to FortiManager.

    Args:
        device: FortiManager device name
        adom: ADOM name to add device to
        device_name: FortiGate device name
        device_ip: FortiGate IP address
        username: FortiGate admin username
        password: FortiGate admin password

    Returns:
        Result of device addition
    """
    client = get_fortimanager_client(device)

    device_data = {
        "name": device_name,
        "ip": device_ip,
        "adm_usr": username,
        "adm_pass": password
    }

    await client.add(f"/dvmdb/adom/{adom}/device", device_data)

    return f"✅ Added device '{device_name}' ({device_ip}) to ADOM '{adom}' on {device}"

# ==================== Policy Package Management ====================

@mcp.tool()
async def list_policy_packages(device: str = "primary", adom: str = "root") -> str:
    """
    List all policy packages in an ADOM.

    Args:
        device: FortiManager device name
        adom: ADOM name

    Returns:
        List of policy packages
    """
    client = get_fortimanager_client(device)
    result = await client.get(f"/pm/pkg/adom/{adom}")

    packages = []
    for pkg in result:
        packages.append(
            f"- {pkg.get('name', 'N/A')}: "
            f"Type={pkg.get('type', 'N/A')} "
            f"[{pkg.get('package settings', {}).get('inspection-mode', 'N/A')}]"
        )

    return f"Policy Packages in ADOM '{adom}' ({len(packages)} total):\n" + "\n".join(packages)

@mcp.tool()
async def list_firewall_policies(
    device: str,
    adom: str,
    package: str
) -> str:
    """
    List firewall policies in a policy package.

    Args:
        device: FortiManager device name
        adom: ADOM name
        package: Policy package name

    Returns:
        List of firewall policies
    """
    client = get_fortimanager_client(device)
    result = await client.get(f"/pm/config/adom/{adom}/pkg/{package}/firewall/policy")

    policies = []
    for policy in result[:20]:  # Limit to first 20
        policies.append(
            f"- Policy {policy.get('policyid', 'N/A')}: "
            f"{policy.get('name', 'Unnamed')} "
            f"[{policy.get('status', 'N/A')}] "
            f"Action: {policy.get('action', 'N/A')}"
        )

    return f"Firewall Policies in '{package}' ({len(result)} total, showing 20):\n" + "\n".join(policies)

@mcp.tool()
async def create_firewall_policy(
    device: str,
    adom: str,
    package: str,
    name: str,
    srcintf: List[str],
    dstintf: List[str],
    srcaddr: List[str],
    dstaddr: List[str],
    service: List[str],
    action: str = "accept"
) -> str:
    """
    Create a new firewall policy in a policy package.

    Args:
        device: FortiManager device name
        adom: ADOM name
        package: Policy package name
        name: Policy name
        srcintf: Source interfaces
        dstintf: Destination interfaces
        srcaddr: Source addresses
        dstaddr: Destination addresses
        service: Services
        action: Action (accept/deny)

    Returns:
        Creation result
    """
    client = get_fortimanager_client(device)

    policy_data = {
        "name": name,
        "srcintf": srcintf,
        "dstintf": dstintf,
        "srcaddr": srcaddr,
        "dstaddr": dstaddr,
        "service": service,
        "action": action,
        "schedule": "always",
        "status": "enable"
    }

    await client.add(f"/pm/config/adom/{adom}/pkg/{package}/firewall/policy", policy_data)

    return f"✅ Created firewall policy '{name}' in package '{package}' (ADOM: {adom})"

# ==================== Configuration Installation ====================

@mcp.tool()
async def install_policy_package(
    device: str,
    adom: str,
    package: str,
    scope: List[Dict[str, str]]
) -> str:
    """
    Install policy package to devices.

    Args:
        device: FortiManager device name
        adom: ADOM name
        package: Policy package name
        scope: List of devices to install to (e.g., [{"name": "FG-1", "vdom": "root"}])

    Returns:
        Installation result
    """
    client = get_fortimanager_client(device)

    install_data = {
        "adom": adom,
        "pkg": package,
        "scope": scope
    }

    result = await client.execute("/securityconsole/install/package", install_data)

    return f"✅ Policy package '{package}' installation initiated for {len(scope)} device(s) (Task ID: {result.get('task', 'N/A')})"

# ==================== FortiSwitch Management ====================

@mcp.tool()
async def list_fortiswitches(device: str, adom: str, fortigate_name: str) -> str:
    """
    List FortiSwitches managed by a FortiGate.

    Args:
        device: FortiManager device name
        adom: ADOM name
        fortigate_name: FortiGate device name

    Returns:
        List of managed FortiSwitches
    """
    client = get_fortimanager_client(device)
    result = await client.get(
        f"/pm/config/adom/{adom}/obj/wireless-controller/wtp/{fortigate_name}"
    )

    switches = []
    for switch in result:
        switches.append(
            f"- {switch.get('name', 'N/A')}: "
            f"Serial={switch.get('wtp-id', 'N/A')} "
            f"Status={switch.get('admin', 'N/A')}"
        )

    return f"FortiSwitches on {fortigate_name} ({len(switches)} total):\n" + "\n".join(switches)

# ==================== Logging & Reports ====================

@mcp.tool()
async def get_device_config(device: str, adom: str, device_name: str, vdom: str = "root") -> str:
    """
    Get current running configuration of a device.

    Args:
        device: FortiManager device name
        adom: ADOM name
        device_name: FortiGate device name
        vdom: VDOM name

    Returns:
        Configuration summary
    """
    client = get_fortimanager_client(device)
    result = await client.get(f"/pm/config/adom/{adom}/obj/firewall/address")

    return f"""Device Configuration ({device_name} - {vdom}):
Retrieved {len(result)} firewall address objects
Use specific tools to query individual configuration sections
"""

@mcp.tool()
async def get_task_status(device: str, task_id: str) -> str:
    """
    Get status of a FortiManager task.

    Args:
        device: FortiManager device name
        task_id: Task ID

    Returns:
        Task status
    """
    client = get_fortimanager_client(device)
    result = await client.get(f"/task/task/{task_id}")

    return f"""Task Status (ID: {task_id}):
- Status: {result.get('state', 'N/A')}
- Progress: {result.get('percent', 'N/A')}%
- Start Time: {result.get('start_time', 'N/A')}
- End Time: {result.get('end_time', 'N/A')}
- History: {result.get('history', [])}
"""

# ==================== Restaurant Chain Support ====================

@mcp.tool()
async def get_restaurant_devices(chain: str) -> str:
    """
    Get all devices for a restaurant chain (Arby's, BWW, Sonic).

    Args:
        chain: Restaurant chain name (arbys, bww, sonic)

    Returns:
        List of devices for the chain
    """
    chain_lower = chain.lower()
    device_map = {
        "arbys": "arbys",
        "bww": "bww",
        "buffalowildwings": "bww",
        "sonic": "sonic"
    }

    device_name = device_map.get(chain_lower, chain_lower)

    client = get_fortimanager_client(device_name)
    adoms = await client.get("/dvmdb/adom")

    summary = [f"Restaurant Chain: {chain.upper()}\n"]
    total_devices = 0

    for adom in adoms:
        adom_name = adom.get('name', 'N/A')
        devices = await client.get(f"/dvmdb/adom/{adom_name}/device")
        total_devices += len(devices)
        summary.append(f"- ADOM '{adom_name}': {len(devices)} devices")

    summary.insert(1, f"Total Devices: {total_devices}\n")

    return "\n".join(summary)

# ==================== Server Lifecycle ====================

@mcp.resource("fortimanager://devices")
async def list_configured_fortimanagers() -> str:
    """List all configured FortiManager devices"""
    devices = []
    for key in os.environ:
        if key.startswith("FORTIMANAGER_") and key.endswith("_HOST"):
            device_name = key.replace("FORTIMANAGER_", "").replace("_HOST", "").lower()
            devices.append(device_name)

    return f"Configured FortiManagers: {', '.join(devices) if devices else 'None'}"

async def cleanup():
    """Cleanup all FortiManager API clients"""
    for client in fortimanager_clients.values():
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
