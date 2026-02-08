"""
Intent-Based Networking (IBN) Models

Pydantic models for representing user intent, constraints, and validation results.
These models enable users to express high-level networking goals that the system
translates into concrete topology configurations.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class TopologyType(str, Enum):
    """
    Types of network topologies that can be generated from intent.
    
    - FULL_MESH: Every device connects to every other device
    - HUB_SPOKE: Central hub with spokes radiating outward
    - RING: Devices arranged in a ring topology
    - TREE: Hierarchical tree structure (core, aggregation, edge)
    - LEAF_SPINE: Data center topology with leaves and spines
    - HYBRID: Mix of topology types
    """
    FULL_MESH = "full_mesh"
    HUB_SPOKE = "hub_spoke"
    RING = "ring"
    TREE = "tree"
    LEAF_SPINE = "leaf_spine"
    HYBRID = "hybrid"


class RedundancyLevel(str, Enum):
    """
    Redundancy requirements for the network.
    
    - MINIMUM: Single path between devices (not recommended for production)
    - STANDARD: At least 2 diverse paths (recommended)
    - HIGH: At least 3 diverse paths with smart routing
    - CRITICAL: At least 4 diverse paths with active-active
    """
    MINIMUM = "minimum"    # 1 path
    STANDARD = "standard"  # 2+ paths
    HIGH = "high"          # 3+ paths
    CRITICAL = "critical"  # 4+ paths


class RoutingProtocol(str, Enum):
    """Supported routing protocols for intent-generated topologies."""
    OSPF = "ospf"
    BGP = "bgp"


class DesignGoal(str, Enum):
    """Primary design goals that guide topology generation."""
    COST_OPTIMIZED = "cost_optimized"      # Minimize links and devices
    REDUNDANCY_FOCUSED = "redundancy_focused"  # Maximize diverse paths
    LATENCY_OPTIMIZED = "latency_optimized"   # Minimize hop counts
    SCALABILITY = "scalability"            # Support growth


class IntentRequest(BaseModel):
    """
    High-level user intent for network topology generation.
    
    This is the primary interface where users specify what they want,
    rather than how to build it. The system converts this into actual topology.
    
    Attributes:
        intent_name: Human-readable name for this intent
        intent_description: Detailed description of the desired network
        topology_type: Desired topology pattern (hub-spoke, mesh, tree, etc.)
        number_of_sites: Number of network sites or routers needed
        redundancy_level: Required redundancy (minimum, standard, high, critical)
        max_hops: Maximum acceptable hop count between any two devices
        routing_protocol: Routing protocol to use (OSPF, BGP)
        design_goal: Primary optimization goal
        minimize_spof: If True, eliminates single points of failure
        minimum_connections_per_site: Minimum links per device (redundancy)
        max_links: Optional maximum total links allowed
        link_speed: Optional specification of link bandwidth
        custom_constraints: Optional dict for implementation-specific requirements
    """
    intent_name: str = Field(..., description="Name of the intent (e.g., 'Production Core Network')")
    intent_description: str = Field(..., description="Detailed intent description")
    topology_type: TopologyType = Field(
        default=TopologyType.FULL_MESH,
        description="Desired network topology pattern"
    )
    number_of_sites: int = Field(
        default=10,
        ge=2,
        le=500,
        description="Number of sites/devices in the network"
    )
    redundancy_level: RedundancyLevel = Field(
        default=RedundancyLevel.STANDARD,
        description="Required redundancy level"
    )
    max_hops: int = Field(
        default=4,
        ge=2,
        le=10,
        description="Maximum hops between any two devices"
    )
    routing_protocol: RoutingProtocol = Field(
        default=RoutingProtocol.OSPF,
        description="Routing protocol for configuration"
    )
    design_goal: DesignGoal = Field(
        default=DesignGoal.REDUNDANCY_FOCUSED,
        description="Primary design optimization goal"
    )
    minimize_spof: bool = Field(
        default=True,
        description="Eliminate single points of failure"
    )
    minimum_connections_per_site: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Minimum redundant connections per device"
    )
    max_links: Optional[int] = Field(
        default=None,
        description="Maximum total links allowed in topology"
    )
    link_speed: Optional[str] = Field(
        default="1Gbps",
        description="Link speed specification (1Gbps, 10Gbps, etc.)"
    )
    custom_constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom implementation-specific constraints"
    )
    
    @validator('number_of_sites')
    def validate_sites(cls, v):
        """Validate number of sites is reasonable."""
        if v < 2:
            raise ValueError('Must have at least 2 sites')
        if v > 500:
            raise ValueError('Cannot exceed 500 sites with this generator')
        return v
    
    @validator('max_hops')
    def validate_hops(cls, v):
        """Validate hop count is reasonable."""
        if v < 2:
            raise ValueError('Max hops must be at least 2')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "intent_name": "Global Data Center Network",
                "intent_description": "Highly available topology connecting 10 regional data centers",
                "topology_type": "full_mesh",
                "number_of_sites": 10,
                "redundancy_level": "critical",
                "max_hops": 3,
                "routing_protocol": "ospf",
                "design_goal": "redundancy_focused",
                "minimize_spof": True,
                "minimum_connections_per_site": 3
            }
        }


class TopologyConstraint(BaseModel):
    """
    Internal representation of constraints extracted from intent.
    
    These constraints guide the topology generator and validator.
    """
    constraint_name: str
    constraint_type: str  # "redundancy", "path_diversity", "hop_count", "spof", etc.
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    required: bool = True
    description: str = ""
    severity: str = Field(default="high")  # high, medium, low


class IntentConstraints(BaseModel):
    """
    Complete set of constraints parsed from user intent.
    """
    redundancy_constraint: TopologyConstraint
    path_diversity_constraint: TopologyConstraint
    hop_count_constraint: TopologyConstraint
    spof_constraint: TopologyConstraint
    topology_pattern_constraint: TopologyConstraint
    scalability_constraint: Optional[TopologyConstraint] = None
    custom_constraints: List[TopologyConstraint] = Field(default_factory=list)
    
    def get_all_constraints(self) -> List[TopologyConstraint]:
        """Get all constraints as a flat list."""
        constraints = [
            self.redundancy_constraint,
            self.path_diversity_constraint,
            self.hop_count_constraint,
            self.spof_constraint,
            self.topology_pattern_constraint,
        ]
        if self.scalability_constraint:
            constraints.append(self.scalability_constraint)
        constraints.extend(self.custom_constraints)
        return constraints


class IntentValidationResult(BaseModel):
    """
    Result of validating whether a generated topology satisfies the intent.
    """
    intent_satisfied: bool
    overall_score: float = Field(ge=0, le=100, description="Overall satisfaction score 0-100")
    redundancy_score: float = Field(ge=0, le=100, description="Redundancy requirement satisfaction 0-100")
    path_diversity_score: float = Field(ge=0, le=100, description="Path diversity score 0-100")
    hop_count_satisfaction: bool = Field(description="Whether max hops constraint is met")
    actual_max_hops: int = Field(description="Actual maximum hops in generated topology")
    spof_eliminated: bool = Field(description="Whether all SPOFs were eliminated")
    remaining_spofs: int = Field(default=0, description="Number of remaining SPOFs if any")
    topology_pattern_matched: bool = Field(description="Whether topology matches requested pattern")
    constraint_violations: List[str] = Field(default_factory=list, description="List of violated constraints")
    warnings: List[str] = Field(default_factory=list, description="Non-critical issues")
    recommendations: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    
    class Config:
        schema_extra = {
            "example": {
                "intent_satisfied": True,
                "overall_score": 92.5,
                "redundancy_score": 95,
                "path_diversity_score": 88,
                "hop_count_satisfaction": True,
                "actual_max_hops": 3,
                "spof_eliminated": True,
                "remaining_spofs": 0,
                "topology_pattern_matched": True,
                "constraint_violations": [],
                "warnings": ["One link has high degree (5 connections)"],
                "recommendations": ["Consider adding one more link for better load distribution"]
            }
        }


class IntentReport(BaseModel):
    """
    Complete report on intent-based topology generation and validation.
    """
    report_id: str
    intent_name: str
    intent_description: str
    requested_properties: Dict[str, Any]  # Original intent parameters
    generated_topology_stats: Dict[str, Any]  # Stats about generated topology
    validation_result: IntentValidationResult
    generation_timestamp: str
    recommendations_summary: str
    next_steps: List[str]


class IntentGenerationRequest(BaseModel):
    """Request to generate a topology from intent."""
    intent: IntentRequest


class IntentValidationRequest(BaseModel):
    """Request to validate a topology against intent."""
    intent: IntentRequest
    topology_json: Dict[str, Any]  # The topology to validate


class IntentGenerationResponse(BaseModel):
    """Response from intent-based topology generation."""
    success: bool
    message: str
    generated_topology: Optional[Dict[str, Any]] = None
    validation_result: Optional[IntentValidationResult] = None
    report_id: Optional[str] = None
