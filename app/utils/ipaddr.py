"""Utility functions for IP address and networking operations."""
from ipaddress import IPv4Network, IPv4Address
from typing import Tuple, List
import random


def generate_ip_subnet(base_network: str = "10.0.0.0/8", size: int = 24) -> Tuple[str, str]:
    """
    Generate an IP subnet from a base network.
    
    Args:
        base_network: Base network CIDR (default: 10.0.0.0/8)
        size: Subnet size in bits (default: 24)
    
    Returns:
        Tuple of (network_address, broadcast_address)
    """
    base = IPv4Network(base_network)
    # Generate random subnet within base network
    random_offset = random.randint(0, (2 ** (base.prefixlen - size)) - 1)
    subnet = list(base.subnets(new_prefix=size))[random_offset]
    return str(subnet.network_address), str(subnet.broadcast_address)


def allocate_ips_for_link(base_subnet: str) -> Tuple[str, str]:
    """
    Allocate two IPs for a point-to-point link.
    
    Args:
        base_subnet: Network CIDR (e.g., 10.1.1.0/24)
    
    Returns:
        Tuple of (source_ip, destination_ip)
    """
    network = IPv4Network(base_subnet)
    hosts = list(network.hosts())
    
    if len(hosts) < 2:
        raise ValueError(f"Subnet {base_subnet} has insufficient hosts for a link")
    
    source_ip = str(hosts[0])
    dest_ip = str(hosts[1])
    
    return source_ip, dest_ip


def get_network_address(ip: str, prefix_length: int) -> str:
    """
    Get network address from IP and prefix length.
    
    Args:
        ip: IP address
        prefix_length: Prefix length (e.g., 24 for /24)
    
    Returns:
        Network address as string
    """
    addr = IPv4Address(ip)
    network = IPv4Network(f"{addr}/{prefix_length}", strict=False)
    return str(network.network_address)


def get_subnet_mask(prefix_length: int) -> str:
    """
    Convert prefix length to subnet mask.
    
    Args:
        prefix_length: Prefix length (e.g., 24 for /24)
    
    Returns:
        Subnet mask (e.g., 255.255.255.0)
    """
    network = IPv4Network(f"0.0.0.0/{prefix_length}")
    return str(network.netmask)


def get_wildcard_mask(prefix_length: int) -> str:
    """
    Convert prefix length to wildcard (inverse) mask.
    Used for OSPF network statements.
    
    Args:
        prefix_length: Prefix length (e.g., 24 for /24)
    
    Returns:
        Wildcard mask (e.g., 0.0.0.255)
    """
    subnet_mask = IPv4Network(f"0.0.0.0/{prefix_length}").netmask
    # Wildcard is bitwise NOT of subnet mask
    wildcard = IPv4Address(int(IPv4Address("255.255.255.255")) ^ int(subnet_mask))
    return str(wildcard)


def validate_ip_address(ip: str) -> bool:
    """
    Validate if a string is a valid IP address.
    
    Args:
        ip: IP address string
    
    Returns:
        True if valid, False otherwise
    """
    try:
        IPv4Address(ip)
        return True
    except ValueError:
        return False


def generate_router_id(router_index: int, base_octet: int = 10) -> str:
    """
    Generate a unique router ID in OSPF format.
    
    Args:
        router_index: Router index (0, 1, 2, ...)
        base_octet: Base for the first octet (default: 10)
    
    Returns:
        Router ID in format X.X.X.X
    """
    second = (router_index // 254) + 1
    third = (router_index % 254) + 1
    return f"{base_octet}.{second}.{third}.1"


def is_valid_interface_name(name: str) -> bool:
    """
    Validate interface name format.
    
    Args:
        name: Interface name
    
    Returns:
        True if valid format
    """
    valid_prefixes = ["eth", "gi", "fa", "ge", "xe", "en"]
    return any(name.startswith(prefix) for prefix in valid_prefixes)
