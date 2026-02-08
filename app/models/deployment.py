"""Pydantic models for deployment and export functionality."""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ContainerlabNode(BaseModel):
    """Represents a single node in Containerlab topology."""
    image: str = Field(
        default="golang:latest",
        description="Container image for the node"
    )
    binds: Optional[List[str]] = Field(None, description="Volume binds")

    class Config:
        """Pydantic config."""
        use_enum_values = True


class ContainerlabTopology(BaseModel):
    """Containerlab-compatible topology format."""
    name: str = Field(..., description="Topology name")
    topology: Dict[str, Any] = Field(
        ...,
        description="Containerlab topology structure"
    )

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "name": "test-topology",
                "topology": {
                    "nodes": {},
                    "links": [],
                },
            }
        }
