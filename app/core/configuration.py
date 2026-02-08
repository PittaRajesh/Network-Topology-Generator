"""Configuration generator module for creating routing configurations."""
from typing import List, Dict, Any
from app.models import Topology, RoutingConfig, OSPFConfiguration, InterfaceConfig
from app.utils import get_wildcard_mask, get_network_address


class ConfigurationGenerator:
    """
    Generates routing configurations for network devices.
    
    Features:
    - OSPF configuration generation
    - Automatic interface configuration
    - Support for future protocols (BGP, ISIS)
    """

    def __init__(self):
        """Initialize the configuration generator."""
        self.prefix_length = 24  # Default prefix length for point-to-point links

    def generate_ospf_configs(self, topology: Topology) -> RoutingConfig:
        """
        Generate OSPF configurations for all routers in topology.
        
        Args:
            topology: Topology object containing devices and links
        
        Returns:
            RoutingConfig object with OSPF configurations
        """
        ospf_configs = []
        
        # Extract routers from topology
        routers = [d for d in topology.devices if d.device_type.value == "router"]
        
        for router in routers:
            # Get all links connected to this router
            connected_links = [
                link for link in topology.links
                if link.source_device == router.name or link.destination_device == router.name
            ]
            
            # Generate interface configurations
            interfaces = self._create_interface_configs(router.name, connected_links)
            
            # Generate OSPF networks
            networks = self._create_ospf_networks(interfaces)
            
            # Create OSPF configuration
            ospf_config = OSPFConfiguration(
                device_name=router.name,
                router_id=router.router_id,
                ospf_process_id=1,
                networks=networks,
                interfaces=interfaces
            )
            
            ospf_configs.append(ospf_config)
        
        # Create complete routing configuration
        routing_config = RoutingConfig(
            topology_name=topology.name,
            routing_protocol="ospf",
            ospf_configs=ospf_configs,
            metadata={
                "num_routers": topology.num_routers,
                "num_switches": topology.num_switches,
                "total_devices": len(topology.devices),
                "total_links": len(topology.links),
            }
        )
        
        return routing_config

    def _create_interface_configs(
        self,
        device_name: str,
        links: List
    ) -> List[InterfaceConfig]:
        """
        Create interface configurations for a device.
        
        Args:
            device_name: Name of the device
            links: List of links connected to the device
        
        Returns:
            List of InterfaceConfig objects
        """
        interfaces = []
        
        for link in links:
            # Determine which end of the link is our device
            if link.source_device == device_name:
                interface_name = link.source_interface
                ip_address = link.source_ip
                description = f"Link to {link.destination_device}"
            else:
                interface_name = link.destination_interface
                ip_address = link.destination_ip
                description = f"Link to {link.source_device}"
            
            # Create interface config with CIDR notation
            ip_with_prefix = f"{ip_address}/{self.prefix_length}"
            
            interface_config = InterfaceConfig(
                interface_name=interface_name,
                ip_address=ip_with_prefix,
                description=description
            )
            
            interfaces.append(interface_config)
        
        return interfaces

    def _create_ospf_networks(
        self,
        interfaces: List[InterfaceConfig]
    ) -> List[Dict[str, str]]:
        """
        Create OSPF network statements from interfaces.
        
        Args:
            interfaces: List of interface configurations
        
        Returns:
            List of OSPF network dictionaries
        """
        networks = []
        seen_networks = set()
        
        for interface in interfaces:
            # Extract network from CIDR notation
            ip_with_prefix = interface.ip_address
            ip_addr, prefix = ip_with_prefix.split("/")
            prefix_len = int(prefix)
            
            # Get network address
            network_addr = get_network_address(ip_addr, prefix_len)
            
            # Skip if we've already added this network
            if network_addr in seen_networks:
                continue
            
            seen_networks.add(network_addr)
            
            # Get wildcard mask for OSPF
            wildcard = get_wildcard_mask(prefix_len)
            
            network_entry = {
                "network": network_addr,
                "netmask": wildcard,
                "area": "0"  # OSPF backbone area
            }
            
            networks.append(network_entry)
        
        return networks
