"""Pydantic models for topology data structures."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class DeviceType(str, Enum):
    """Device types supported in the topology."""
    ROUTER = "router"
    SWITCH = "switch"


class Device(BaseModel):
    """Represents a network device (router or switch)."""
    name: str = Field(..., description="Device name (e.g., R1, SW1)")
    device_type: DeviceType = Field(..., description="Type of device")
    router_id: Optional[str] = Field(None, description="Router ID for OSPF")
    asn: Optional[int] = Field(65000, description="AS Number for BGP (future)")

    @validator("name")
    def validate_name(cls, v):
        """Ensure device name follows networking conventions."""
        if not v or len(v) > 20:
            raise ValueError("Device name must be between 1 and 20 characters")
        return v

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "name": "R1",
                "device_type": "router",
                "router_id": "10.0.0.1",
                "asn": 65000,
            }
        }


class Link(BaseModel):
    """Represents a connection between two devices."""
    source_device: str = Field(..., description="Source device name")
    source_interface: str = Field(..., description="Source interface (e.g., eth0, gi0/0)")
    destination_device: str = Field(..., description="Destination device name")
    destination_interface: str = Field(..., description="Destination interface")
    source_ip: str = Field(..., description="Source IP address")
    destination_ip: str = Field(..., description="Destination IP address")
    subnet_mask: str = Field("255.255.255.0", description="Subnet mask for the link")
    cost: int = Field(1, description="OSPF cost")

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "source_device": "R1",
                "source_interface": "eth0",
                "destination_device": "R2",
                "destination_interface": "eth0",
                "source_ip": "10.1.1.1",
                "destination_ip": "10.1.1.2",
                "subnet_mask": "255.255.255.0",
                "cost": 1,
            }
        }


class Topology(BaseModel):
    """Complete network topology with devices and links."""
    name: str = Field(..., description="Topology name")
    num_routers: int = Field(..., description="Number of routers in topology")
    num_switches: int = Field(..., description="Number of switches in topology")
    devices: List[Device] = Field(..., description="List of all devices")
    links: List[Link] = Field(..., description="List of all links between devices")
    routing_protocol: str = Field("ospf", description="Routing protocol used")

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "name": "test-topology",
                "num_routers": 3,
                "num_switches": 2,
                "devices": [],
                "links": [],
                "routing_protocol": "ospf",
            }
        }


class TopologyRequest(BaseModel):
    """Request model for topology generation."""
    name: str = Field(..., description="Name for the generated topology")
    num_routers: int = Field(
        default=3,
        ge=2,
        le=20,
        description="Number of routers (2-20)"
    )
    num_switches: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Number of switches (0-10)"
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducible topology generation"
    )

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "name": "production-topology",
                "num_routers": 5,
                "num_switches": 3,
                "seed": None,
            }
        }
