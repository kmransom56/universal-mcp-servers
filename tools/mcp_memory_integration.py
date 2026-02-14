#!/usr/bin/env python3
"""
MCP Memory Integration - Shared memory persistence for all MCP servers
Provides memory manager wrapper and utility functions
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import memory manager - use absolute import to avoid relative import errors
import importlib.util
spec = importlib.util.spec_from_file_location(
    "manager",
    Path(__file__).parent.parent / ".mcp" / "memory" / "manager.py"
)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)

MCPMemoryManager = manager.MCPMemoryManager
ContextCategory = manager.ContextCategory

class NetworkMemoryManager:
    """
    Memory manager specialized for network device management
    Provides caching and persistence for device configurations, queries, and results
    """

    def __init__(self, server_name: str):
        """Initialize memory manager for specific MCP server"""
        self.server_name = server_name
        self.memory = MCPMemoryManager()

    def cache_device_query(
        self,
        query_id: str,
        device_type: str,
        data: Dict[str, Any],
        tags: List[str] = None
    ) -> None:
        """
        Cache device query results to avoid re-querying APIs

        Args:
            query_id: Unique identifier for this query (e.g., "arbys_devices_2025")
            device_type: Type of device (fortigate, fortiswitch, meraki_ap, etc.)
            data: Query results to cache
            tags: Optional tags for searching
        """
        all_tags = [self.server_name, device_type]
        if tags:
            all_tags.extend(tags)

        self.memory.save_context(
            context_id=f"{self.server_name}_{query_id}",
            category=ContextCategory.DEVICE_CONFIG,
            title=f"{device_type.upper()} Query: {query_id}",
            data=data,
            tags=all_tags
        )

    def get_cached_query(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached query results

        Args:
            query_id: Query identifier

        Returns:
            Cached data or None if not found
        """
        context = self.memory.load_context(f"{self.server_name}_{query_id}")
        return context.data if context else None

    def cache_adom_list(self, adoms: List[Dict], chain: str = None) -> None:
        """Cache FortiManager ADOM list"""
        tags = ["adom_list"]
        if chain:
            tags.append(chain)

        self.cache_device_query(
            query_id=f"adoms_{chain}" if chain else "adoms_all",
            device_type="fortimanager",
            data={"adoms": adoms, "count": len(adoms), "timestamp": datetime.now().isoformat()},
            tags=tags
        )

    def cache_device_list(self, devices: List[Dict], adom: str, chain: str = None) -> None:
        """Cache FortiManager device list for specific ADOM"""
        tags = ["device_list", adom]
        if chain:
            tags.append(chain)

        self.cache_device_query(
            query_id=f"devices_{adom}_{chain}" if chain else f"devices_{adom}",
            device_type="fortimanager",
            data={
                "devices": devices,
                "count": len(devices),
                "adom": adom,
                "timestamp": datetime.now().isoformat()
            },
            tags=tags
        )

    def cache_policy_package(self, package_name: str, policies: List[Dict], adom: str) -> None:
        """Cache FortiManager policy package"""
        self.cache_device_query(
            query_id=f"policies_{adom}_{package_name}",
            device_type="fortimanager",
            data={
                "package": package_name,
                "policies": policies,
                "count": len(policies),
                "adom": adom,
                "timestamp": datetime.now().isoformat()
            },
            tags=["policy_package", adom, package_name]
        )

    def cache_network_scan(self, scan_id: str, results: Dict[str, Any], organization: str = None) -> None:
        """Cache network scan results"""
        tags = ["network_scan"]
        if organization:
            tags.append(organization)

        self.cache_device_query(
            query_id=f"scan_{scan_id}",
            device_type="network_scan",
            data={
                **results,
                "scan_id": scan_id,
                "timestamp": datetime.now().isoformat()
            },
            tags=tags
        )

    def search_devices(self, device_type: str = None, tags: List[str] = None) -> List[Dict]:
        """
        Search cached device configurations

        Args:
            device_type: Filter by device type
            tags: Filter by tags

        Returns:
            List of matching contexts
        """
        search_tags = [self.server_name]
        if device_type:
            search_tags.append(device_type)
        if tags:
            search_tags.extend(tags)

        results = self.memory.search_contexts(
            category=ContextCategory.DEVICE_CONFIG,
            tags=search_tags
        )

        return [r.data for r in results]

    def save_automation_state(
        self,
        automation_id: str,
        state: Dict[str, Any],
        tags: List[str] = None
    ) -> None:
        """Save automation workflow state"""
        all_tags = [self.server_name, "automation"]
        if tags:
            all_tags.extend(tags)

        self.memory.save_context(
            context_id=f"{self.server_name}_automation_{automation_id}",
            category=ContextCategory.AUTOMATION_FLOW,
            title=f"Automation: {automation_id}",
            data=state,
            tags=all_tags
        )

    def load_automation_state(self, automation_id: str) -> Optional[Dict[str, Any]]:
        """Load automation workflow state"""
        context = self.memory.load_context(f"{self.server_name}_automation_{automation_id}")
        return context.data if context else None


def create_memory_manager(server_name: str) -> NetworkMemoryManager:
    """
    Factory function to create memory manager for MCP server

    Args:
        server_name: Name of MCP server (fortinet, fortimanager, meraki)

    Returns:
        Configured NetworkMemoryManager instance
    """
    return NetworkMemoryManager(server_name)
