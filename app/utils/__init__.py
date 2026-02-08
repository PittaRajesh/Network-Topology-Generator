"""Utility functions module."""
from .ipaddr import (
    generate_ip_subnet,
    allocate_ips_for_link,
    get_network_address,
    get_subnet_mask,
    get_wildcard_mask,
    validate_ip_address,
    generate_router_id,
    is_valid_interface_name,
)

__all__ = [
    "generate_ip_subnet",
    "allocate_ips_for_link",
    "get_network_address",
    "get_subnet_mask",
    "get_wildcard_mask",
    "validate_ip_address",
    "generate_router_id",
    "is_valid_interface_name",
]
