"""Pydantic models for configuration data structures."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class InterfaceConfig(BaseModel):
    """Configuration for a single interface."""
    interface_name: str = Field(..., description="Interface name (e.g., eth0)")
    ip_address: str = Field(..., description="IP address with CIDR notation")
    description: Optional[str] = Field(None, description="Interface description")

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "interface_name": "eth0",
                "ip_address": "10.1.1.1/24",
                "description": "Link to R2",
            }
        }


class OSPFConfiguration(BaseModel):
    """OSPF routing configuration for a device."""
    device_name: str = Field(..., description="Device name")
    router_id: str = Field(..., description="OSPF Router ID")
    ospf_process_id: int = Field(1, description="OSPF Process ID")
    networks: List[Dict[str, str]] = Field(
        ...,
        description="List of networks to advertise in OSPF"
    )
    interfaces: List[InterfaceConfig] = Field(..., description="Interface configurations")

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "device_name": "R1",
                "router_id": "10.0.0.1",
                "ospf_process_id": 1,
                "networks": [{"network": "10.1.1.0", "netmask": "0.0.0.255"}],
                "interfaces": [],
            }
        }


class RoutingConfig(BaseModel):
    """Complete routing configuration for the topology."""
    topology_name: str = Field(..., description="Name of the topology")
    routing_protocol: str = Field("ospf", description="Routing protocol")
    ospf_configs: List[OSPFConfiguration] = Field(
        ...,
        description="OSPF configurations for all routers"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "topology_name": "test-topology",
                "routing_protocol": "ospf",
                "ospf_configs": [],
                "metadata": {},
            }
        }
