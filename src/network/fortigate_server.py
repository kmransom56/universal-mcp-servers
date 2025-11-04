from mcp.server.fastmcp import FastMCP, Context
import httpx
import sqlite3
import pandas as pd
import json
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
import time

# Define our application context
@dataclass
class FortimanagerContext:
    api_client: httpx.AsyncClient
    db_connection: sqlite3.Connection
    session_token: str = None

# Lifespan manager to handle connections
@asynccontextmanager
async def fortimanager_lifespan(server: FastMCP) -> AsyncIterator[FortimanagerContext]:
    """Setup and teardown database and API connections"""
    # Initialize database
    db = sqlite3.connect("fortimanager_data.db")
    init_database(db)
    
    # Create API client
    async with httpx.AsyncClient() as client:
        yield FortimanagerContext(api_client=client, db_connection=db)
    
    # Cleanup
    db.close()

# Initialize our server
mcp = FastMCP("FortimanagerTools", lifespan=fortimanager_lifespan)

# Database initialization function
def init_database(conn):
    """Create necessary database tables if they don't exist"""
    cursor = conn.cursor()
    
    # Firewall policies table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS firewall_policies (
        id INTEGER PRIMARY KEY,
        firewall TEXT,
        policy_id INTEGER,
        name TEXT,
        source_interface TEXT,
        destination_interface TEXT,
        source_address TEXT,
        destination_address TEXT,
        service TEXT,
        action TEXT,
        status TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # URL filters table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS url_filters (
        id INTEGER PRIMARY KEY,
        firewall TEXT,
        profile_name TEXT,
        url_category TEXT,
        action TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Interfaces table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interfaces (
        id INTEGER PRIMARY KEY,
        firewall TEXT,
        name TEXT,
        ip TEXT,
        netmask TEXT,
        status TEXT,
        type TEXT,
        vlan_id INTEGER,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Connected devices table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS connected_devices (
        id INTEGER PRIMARY KEY,
        firewall TEXT,
        mac_address TEXT,
        ip_address TEXT,
        hostname TEXT,
        interface TEXT,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Routing table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS routing (
        id INTEGER PRIMARY KEY,
        firewall TEXT,
        destination TEXT,
        gateway TEXT,
        interface TEXT,
        metric INTEGER,
        type TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Packet captures table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS packet_captures (
        id INTEGER PRIMARY KEY,
        firewall TEXT,
        interface TEXT,
        filter TEXT,
        start_time TIMESTAMP,
        duration INTEGER,
        capture_data TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()

#
# Authentication Tools
#
@mcp.tool()
async def authenticate_fortimanager(url: str, username: str, password: str, ctx: Context) -> str:
    """Authenticate to Fortimanager API
    
    Args:
        url: Fortimanager URL (e.g., https://fortimanager.example.com)
        username: API username
        password: API password
    """
    api_client = ctx.request_context.lifespan_context.api_client
    
    # Authentication request payload
    auth_data = {
        "method": "exec",
        "params": [
            {
                "url": "/sys/login/user",
                "data": {
                    "user": username,
                    "passwd": password
                }
            }
        ],
        "session": None,
        "id": 1
    }
    
    try:
        response = await api_client.post(f"{url}/jsonrpc", json=auth_data)
        result = response.json()
        
        if "session" in result and result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            # Store session token in context for future use
            ctx.request_context.lifespan_context.session_token = result["session"]
            return f"Successfully authenticated to Fortimanager at {url}"
        else:
            error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
            return f"Authentication failed: {error_msg}"
    except Exception as e:
        return f"Authentication error: {str(e)}"

#
# Data Collection Tools
#
@mcp.tool()
async def collect_firewall_policies(url: str, device: str, ctx: Context) -> str:
    """Collect firewall policies from a Fortigate device
    
    Args:
        url: Fortimanager URL
        device: Name of the Fortigate device
    """
    api_client = ctx.request_context.lifespan_context.api_client
    db = ctx.request_context.lifespan_context.db_connection
    session = ctx.request_context.lifespan_context.session_token
    
    if not session:
        return "Error: Not authenticated to Fortimanager. Use authenticate_fortimanager tool first."
    
    # API request to get policies
    policy_data = {
        "method": "get",
        "params": [
            {
                "url": f"/pm/config/device/{device}/adom/root/obj/firewall/policy"
            }
        ],
        "session": session,
        "id": 2
    }
    
    try:
        response = await api_client.post(f"{url}/jsonrpc", json=policy_data)
        result = response.json()
        
        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            policies = result.get("result", [{}])[0].get("data", [])
            
            # Store in database
            cursor = db.cursor()
            for policy in policies:
                cursor.execute('''
                INSERT INTO firewall_policies 
                (firewall, policy_id, name, source_interface, destination_interface, 
                source_address, destination_address, service, action, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device, 
                    policy.get("policyid"), 
                    policy.get("name"), 
                    ", ".join(policy.get("srcintf", [])), 
                    ", ".join(policy.get("dstintf", [])),
                    ", ".join(policy.get("srcaddr", [])),
                    ", ".join(policy.get("dstaddr", [])),
                    ", ".join(policy.get("service", [])),
                    policy.get("action"),
                    policy.get("status")
                ))
            
            db.commit()
            return f"Successfully collected {len(policies)} firewall policies from {device}"
        else:
            error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
            return f"Failed to collect firewall policies: {error_msg}"
    except Exception as e:
        return f"Error collecting firewall policies: {str(e)}"

@mcp.tool()
async def collect_url_filters(url: str, device: str, ctx: Context) -> str:
    """Collect webfilter URL filters from a Fortigate device
    
    Args:
        url: Fortimanager URL
        device: Name of the Fortigate device
    """
    api_client = ctx.request_context.lifespan_context.api_client
    db = ctx.request_context.lifespan_context.db_connection
    session = ctx.request_context.lifespan_context.session_token
    
    if not session:
        return "Error: Not authenticated to Fortimanager. Use authenticate_fortimanager tool first."
    
    # API request to get webfilter profiles
    webfilter_data = {
        "method": "get",
        "params": [
            {
                "url": f"/pm/config/device/{device}/adom/root/obj/webfilter/profile"
            }
        ],
        "session": session,
        "id": 3
    }
    
    try:
        response = await api_client.post(f"{url}/jsonrpc", json=webfilter_data)
        result = response.json()
        
        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            profiles = result.get("result", [{}])[0].get("data", [])
            
            # Store in database
            cursor = db.cursor()
            total_filters = 0
            
            for profile in profiles:
                profile_name = profile.get("name")
                
                # Process URL filter categories
                for category in profile.get("ftgd-wf", {}).get("filters", []):
                    cursor.execute('''
                    INSERT INTO url_filters 
                    (firewall, profile_name, url_category, action)
                    VALUES (?, ?, ?, ?)
                    ''', (
                        device,
                        profile_name,
                        category.get("category"),
                        category.get("action")
                    ))
                    total_filters += 1
            
            db.commit()
            return f"Successfully collected URL filters from {len(profiles)} webfilter profiles on {device}"
        else:
            error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
            return f"Failed to collect URL filters: {error_msg}"
    except Exception as e:
        return f"Error collecting URL filters: {str(e)}"

@mcp.tool()
async def collect_interfaces(url: str, device: str, ctx: Context) -> str:
    """Collect interface information from a Fortigate device
    
    Args:
        url: Fortimanager URL
        device: Name of the Fortigate device
    """
    api_client = ctx.request_context.lifespan_context.api_client
    db = ctx.request_context.lifespan_context.db_connection
    session = ctx.request_context.lifespan_context.session_token
    
    if not session:
        return "Error: Not authenticated to Fortimanager. Use authenticate_fortimanager tool first."
    
    # API request to get interfaces
    interface_data = {
        "method": "get",
        "params": [
            {
                "url": f"/pm/config/device/{device}/adom/root/obj/system/interface"
            }
        ],
        "session": session,
        "id": 4
    }
    
    try:
        response = await api_client.post(f"{url}/jsonrpc", json=interface_data)
        result = response.json()
        
        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            interfaces = result.get("result", [{}])[0].get("data", [])
            
            # Store in database
            cursor = db.cursor()
            for interface in interfaces:
                cursor.execute('''
                INSERT INTO interfaces 
                (firewall, name, ip, netmask, status, type, vlan_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device,
                    interface.get("name"),
                    interface.get("ip"),
                    interface.get("netmask"),
                    interface.get("status"),
                    interface.get("type"),
                    interface.get("vlanid")
                ))
            
            db.commit()
            return f"Successfully collected {len(interfaces)} interfaces from {device}"
        else:
            error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
            return f"Failed to collect interfaces: {error_msg}"
    except Exception as e:
        return f"Error collecting interfaces: {str(e)}"

@mcp.tool()
async def collect_connected_devices(url: str, device: str, ctx: Context) -> str:
    """Collect information about devices connected to a Fortigate firewall
    
    Args:
        url: Fortimanager URL
        device: Name of the Fortigate device
    """
    api_client = ctx.request_context.lifespan_context.api_client
    db = ctx.request_context.lifespan_context.db_connection
    session = ctx.request_context.lifespan_context.session_token
    
    if not session:
        return "Error: Not authenticated to Fortimanager. Use authenticate_fortimanager tool first."
    
    # API request to get connected devices
    devices_data = {
        "method": "get",
        "params": [
            {
                "url": f"/dvmdb/device/{device}/vdom/root/user/device/query"
            }
        ],
        "session": session,
        "id": 5
    }
    
    try:
        response = await api_client.post(f"{url}/jsonrpc", json=devices_data)
        result = response.json()
        
        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            devices = result.get("result", [{}])[0].get("data", [])
            
            # Store in database
            cursor = db.cursor()
            for connected_device in devices:
                cursor.execute('''
                INSERT INTO connected_devices 
                (firewall, mac_address, ip_address, hostname, interface, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device,
                    connected_device.get("mac"),
                    connected_device.get("ip"),
                    connected_device.get("hostname"),
                    connected_device.get("interface"),
                    connected_device.get("first_seen"),
                    connected_device.get("last_seen")
                ))
            
            db.commit()
            return f"Successfully collected information about {len(devices)} connected devices from {device}"
        else:
            error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
            return f"Failed to collect connected devices: {error_msg}"
    except Exception as e:
        return f"Error collecting connected devices: {str(e)}"

@mcp.tool()
async def collect_routing_info(url: str, device: str, ctx: Context) -> str:
    """Collect routing information from a Fortigate device
    
    Args:
        url: Fortimanager URL
        device: Name of the Fortigate device
    """
    api_client = ctx.request_context.lifespan_context.api_client
    db = ctx.request_context.lifespan_context.db_connection
    session = ctx.request_context.lifespan_context.session_token
    
    if not session:
        return "Error: Not authenticated to Fortimanager. Use authenticate_fortimanager tool first."
    
    # API request to get routing table
    routing_data = {
        "method": "get",
        "params": [
            {
                "url": f"/pm/config/device/{device}/adom/root/obj/router/static"
            }
        ],
        "session": session,
        "id": 6
    }
    
    try:
        response = await api_client.post(f"{url}/jsonrpc", json=routing_data)
        result = response.json()
        
        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            routes = result.get("result", [{}])[0].get("data", [])
            
            # Store in database
            cursor = db.cursor()
            for route in routes:
                cursor.execute('''
                INSERT INTO routing 
                (firewall, destination, gateway, interface, metric, type)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    device,
                    route.get("dst"),
                    route.get("gateway"),
                    route.get("device"),
                    route.get("distance"),
                    "static"
                ))
            
            db.commit()
            return f"Successfully collected {len(routes)} static routes from {device}"
        else:
            error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
            return f"Failed to collect routing information: {error_msg}"
    except Exception as e:
        return f"Error collecting routing information: {str(e)}"

#
# Debugging Tools
#
@mcp.tool()
async def debug_traffic_flow(url: str, device: str, source_ip: str, destination_ip: str, 
                        destination_port: int, ctx: Context) -> str:
    """Debug traffic flow through a Fortigate firewall
    
    Args:
        url: Fortimanager URL
        device: Name of the Fortigate device
        source_ip: Source IP address
        destination_ip: Destination IP address
        destination_port: Destination port
    """
    api_client = ctx.request_context.lifespan_context.api_client
    session = ctx.request_context.lifespan_context.session_token
    
    if not session:
        return "Error: Not authenticated to Fortimanager. Use authenticate_fortimanager tool first."
    
    # API request to debug traffic flow
    flow_data = {
        "method": "exec",
        "params": [
            {
                "url": f"/dvmdb/device/{device}/exec/firewall/debug/flow",
                "data": {
                    "source": source_ip,
                    "destination": destination_ip,
                    "port": destination_port
                }
            }
        ],
        "session": session,
        "id": 7
    }
    
    try:
        response = await api_client.post(f"{url}/jsonrpc", json=flow_data)
        result = response.json()
        
        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            flow_result = result.get("result", [{}])[0].get("data", {}).get("results", "No flow results")
            return f"Traffic flow analysis from {source_ip} to {destination_ip}:{destination_port} on {device}:\n\n{flow_result}"
        else:
            error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
            return f"Failed to debug traffic flow: {error_msg}"
    except Exception as e:
        return f"Error debugging traffic flow: {str(e)}"

@mcp.tool()
async def capture_packets(url: str, device: str, interface: str, filter_expr: str, 
                     duration: int, ctx: Context) -> str:
    """Perform packet capture on a Fortigate firewall
    
    Args:
        url: Fortimanager URL
        device: Name of the Fortigate device
        interface: Interface to capture on (e.g., port1)
        filter_expr: Capture filter expression (e.g., "host 192.168.1.1")
        duration: Capture duration in seconds
    """
    api_client = ctx.request_context.lifespan_context.api_client
    db = ctx.request_context.lifespan_context.db_connection
    session = ctx.request_context.lifespan_context.session_token
    
    if not session:
        return "Error: Not authenticated to Fortimanager. Use authenticate_fortimanager tool first."
    
    # Start capture API request
    capture_data = {
        "method": "exec",
        "params": [
            {
                "url": f"/dvmdb/device/{device}/exec/system/sniffer",
                "data": {
                    "interface": interface,
                    "filter": filter_expr,
                    "count": "unlimited"
                }
            }
        ],
        "session": session,
        "id": 8
    }
    
    try:
        ctx.info(f"Starting packet capture on {device} interface {interface} for {duration} seconds")
        
        # Start capture
        response = await api_client.post(f"{url}/jsonrpc", json=capture_data)
        result = response.json()
        
        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            # Capture ID needed to stop it later
            capture_id = result.get("result", [{}])[0].get("data", {}).get("taskid")
            
            # Sleep for duration
            for i in range(duration):
                if i % 5 == 0:  # Report progress every 5 seconds
                    await ctx.report_progress(i, duration, f"Capturing packets... {i}/{duration} seconds")
                await asyncio.sleep(1)
            
            # Stop capture API request
            stop_data = {
                "method": "exec",
                "params": [
                    {
                        "url": f"/dvmdb/device/{device}/exec/system/sniffer/stop",
                        "data": {
                            "taskid": capture_id
                        }
                    }
                ],
                "session": session,
                "id": 9
            }
            
            # Stop capture
            stop_response = await api_client.post(f"{url}/jsonrpc", json=stop_data)
            
            # Get capture results
            get_results_data = {
                "method": "exec",
                "params": [
                    {
                        "url": f"/dvmdb/device/{device}/exec/system/sniffer/result",
                        "data": {
                            "taskid": capture_id
                        }
                    }
                ],
                "session": session,
                "id": 10
            }
            
            results_response = await api_client.post(f"{url}/jsonrpc", json=get_results_data)
            results = results_response.json()
            
            if results.get("result", [{}])[0].get("status", {}).get("code") == 0:
                capture_results = results.get("result", [{}])[0].get("data", {}).get("results", "No packets captured")
                
                # Store in database
                cursor = db.cursor()
                cursor.execute('''
                INSERT INTO packet_captures 
                (firewall, interface, filter, start_time, duration, capture_data)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    device,
                    interface,
                    filter_expr,
                    time.strftime('%Y-%m-%d %H:%M:%S'),
                    duration,
                    capture_results
                ))
                
                db.commit()
                
                # Return a preview of the capture
                result_lines = capture_results.split('\n')
                preview = '\n'.join(result_lines[:50])
                total_packets = len(result_lines)
                
                return f"Packet capture completed on {device} interface {interface}\nTotal packets: {total_packets}\nPreview:\n\n{preview}"
            else:
                error_msg = results.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
                return f"Failed to retrieve capture results: {error_msg}"
        else:
            error_msg = result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")
            return f"Failed to start packet capture: {error_msg}"
    except Exception as e:
        return f"Error during packet capture: {str(e)}"

#
# Database Query Tools
#
@mcp.tool()
async def query_database(sql_query: str, ctx: Context) -> str:
    """Run a read-only SQL query against the collected data
    
    Args:
        sql_query: SQL query to execute (must be SELECT only)
    """
    db = ctx.request_context.lifespan_context.db_connection
    
    # Security check - only allow SELECT queries
    sql_lower = sql_query.strip().lower()
    if not sql_lower.startswith("select"):
        return "Error: Only SELECT queries are allowed for security reasons."
    
    for prohibited in ["insert", "update", "delete", "drop", "alter", "create", ";--", "union"]:
        if prohibited in sql_lower:
            return f"Error: Prohibited SQL operation detected: {prohibited}"
    
    try:
        # Execute query and return results
        df = pd.read_sql_query(sql_query, db)
        if len(df) > 100:
            return f"Query returned {len(df)} rows. First 100 shown:\n\n{df.head(100).to_string()}"
        else:
            return f"Query results ({len(df)} rows):\n\n{df.to_string()}"
    except Exception as e:
        return f"SQL query error: {str(e)}"

#
# Resources
#
@mcp.resource("policies://{device}")
async def get_device_policies(device: str, ctx: Context) -> str:
    """Get firewall policies for a specific device"""
    db = ctx.request_context.lifespan_context.db_connection
    
    try:
        # Query the database for policies
        df = pd.read_sql_query(f"SELECT * FROM firewall_policies WHERE firewall = '{device}'", db)
        if len(df) == 0:
            return f"No policies found for device {device}"
        return df.to_string()
    except Exception as e:
        return f"Error retrieving policies: {str(e)}"

@mcp.resource("webfilter://{device}")
async def get_device_webfilter(device: str, ctx: Context) -> str:
    """Get URL filters for a specific device"""
    db = ctx.request_context.lifespan_context.db_connection
    
    try:
        # Query the database for URL filters
        df = pd.read_sql_query(f"SELECT * FROM url_filters WHERE firewall = '{device}'", db)
        if len(df) == 0:
            return f"No URL filters found for device {device}"
        return df.to_string()
    except Exception as e:
        return f"Error retrieving URL filters: {str(e)}"

@mcp.resource("interfaces://{device}")
async def get_device_interfaces(device: str, ctx: Context) -> str:
    """Get interface information for a specific device"""
    db = ctx.request_context.lifespan_context.db_connection
    
    try:
        # Query the database for interfaces
        df = pd.read_sql_query(f"SELECT * FROM interfaces WHERE firewall = '{device}'", db)
        if len(df) == 0:
            return f"No interfaces found for device {device}"
        return df.to_string()
    except Exception as e:
        return f"Error retrieving interfaces: {str(e)}"

@mcp.resource("routing://{device}")
async def get_device_routing(device: str, ctx: Context) -> str:
    """Get routing information for a specific device"""
    db = ctx.request_context.lifespan_context.db_connection
    
    try:
        # Query the database for routing information
        df = pd.read_sql_query(f"SELECT * FROM routing WHERE firewall = '{device}'", db)
        if len(df) == 0:
            return f"No routing information found for device {device}"
        return df.to_string()
    except Exception as e:
        return f"Error retrieving routing information: {str(e)}"

#
# Prompts
#
@mcp.prompt()
def analyze_firewall_policies(device: str) -> str:
    """Create a prompt to analyze firewall policies for potential security issues"""
    return f"""Please analyze the firewall policies for device {device} and identify:
1. Any overly permissive rules that might create security vulnerabilities
2. Any contradictory or redundant rules
3. Rules that might impede legitimate traffic
4. Recommendations for policy improvements

First, retrieve the policies using the policies://{device} resource, then analyze them systematically."""

@mcp.prompt()
def troubleshoot_connection(source_ip: str, destination_ip: str, destination_port: int) -> str:
    """Create a prompt to troubleshoot connection issues between hosts"""
    return f"""I need to troubleshoot a connection issue from {source_ip} to {destination_ip}:{destination_port}. 
    
Please help me by:
1. Checking if any firewall policies would block this traffic
2. Examining the routing information to ensure the traffic can be properly routed
3. Suggesting tools to debug the connection, such as packet capture or traffic flow analysis
4. Providing a systematic troubleshooting plan"""

@mcp.prompt()
def security_audit(device: str) -> str:
    """Create a prompt to perform a security audit of a Fortigate firewall"""
    return f"""Please perform a security audit for the Fortigate firewall {device} by:
1. Examining the firewall policies for security risks
2. Reviewing the URL filters for effectiveness
3. Checking interface configurations for potential vulnerabilities
4. Analyzing the connected devices for unauthorized access
5. Providing a comprehensive security assessment with recommendations"""

@mcp.prompt()
def optimize_performance(device: str) -> str:
    """Create a prompt to optimize the performance of a Fortigate firewall"""
    return f"""Please analyze the configuration of Fortigate firewall {device} and suggest performance optimizations by:
1. Reviewing the policy configuration for efficiency improvements
2. Examining interface settings for potential bottlenecks
3. Analyzing the routing table for optimization opportunities
4. Identifying any performance-impacting features that could be adjusted
5. Providing specific recommendations to enhance throughput and reduce latency"""