"""Pydantic models for topology optimization."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OptimizationRecommendation(BaseModel):
    """A specific optimization recommendation."""
    priority: int = Field(..., ge=1, le=5, description="Priority (1=highest, 5=lowest)")
    category: str = Field(
        ..., 
        description="Category (e.g., 'redundancy', 'performance', 'cost')"
    )
    title: str = Field(..., description="Short title of the recommendation")
    description: str = Field(..., description="Detailed description")
    expected_benefit: str = Field(..., description="Expected benefit if implemented")
    estimated_effort: str = Field(
        ..., 
        description="Effort to implement (low, medium, high)"
    )
    affected_elements: List[str] = Field(..., description="Elements affected by this change")
    implementation_steps: List[str] = Field(..., description="Steps to implement")


class RoutingOptimization(BaseModel):
    """Recommendation for routing optimization."""
    device_pair: tuple = Field(..., description="Source and destination device")
    current_metric: float = Field(..., description="Current OSPF metric")
    suggested_metric: float = Field(..., description="Suggested metric")
    benefit: str = Field(..., description="Benefit of this change")
    reasoning: str = Field(..., description="Why this change is beneficial")


class CapacityOptimization(BaseModel):
    """Recommendation for capacity optimization."""
    device_name: str = Field(..., description="Device to optimize")
    current_link_count: int = Field(..., description="Current number of links")
    recommended_action: str = Field(
        ..., 
        description="Recommended action (e.g., 'add link', 'redistribute load')"
    )
    target_link_count: int = Field(..., description="Target number of links")
    benefit: str = Field(..., description="Expected benefit")


class RedundancyOptimization(BaseModel):
    """Recommendation for redundancy improvements."""
    failure_scenario: str = Field(..., description="Failure scenario being addressed")
    current_state: str = Field(..., description="Current redundancy state")
    recommended_state: str = Field(..., description="Recommended redundancy state")
    required_links: List[str] = Field(..., description="Links to add for redundancy")
    failure_modes_addressed: List[str] = Field(
        ..., 
        description="Failure modes that would be addressed"
    )


class TopologyOptimizationResult(BaseModel):
    """Complete topology optimization result."""
    topology_name: str = Field(..., description="Name of the topology")
    optimization_timestamp: str = Field(..., description="When optimization was performed")
    
    # Optimization recommendations
    general_recommendations: List[OptimizationRecommendation] = Field(
        default_factory=list,
        description="General optimization recommendations"
    )
    routing_optimizations: List[RoutingOptimization] = Field(
        default_factory=list,
        description="Routing-specific optimizations"
    )
    capacity_optimizations: List[CapacityOptimization] = Field(
        default_factory=list,
        description="Capacity-related optimizations"
    )
    redundancy_optimizations: List[RedundancyOptimization] = Field(
        default_factory=list,
        description="Redundancy improvements"
    )
    
    # Overall assessment
    current_optimization_score: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Current optimization score (0-100)"
    )
    potential_optimization_score: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Score after implementing all recommendations"
    )
    optimization_potential: float = Field(
        ..., 
        ge=0.0,
        description="Improvement potential as percentage"
    )
    
    # Summary
    total_recommendations: int = Field(..., description="Total recommendations")
    high_priority_recommendations: int = Field(..., description="High priority recommendations")
    implementation_effort: str = Field(
        ..., 
        description="Overall effort to implement all recommendations"
    )
    
    summary: str = Field(..., description="Summary of optimization opportunities")


class OptimizedTopologyProposal(BaseModel):
    """A proposed optimized version of the topology."""
    proposal_id: str = Field(..., description="Unique proposal identifier")
    base_topology_name: str = Field(..., description="Name of the base topology")
    proposal_name: str = Field(..., description="Name of this proposal")
    description: str = Field(..., description="Description of the proposed changes")
    
    # Changes
    links_to_add: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Links to add in the format {source, target}"
    )
    links_to_remove: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Links to remove"
    )
    cost_changes: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="OSPF cost changes for links"
    )
    
    # Benefits
    improved_metrics: Dict[str, float] = Field(
        ..., 
        description="Improved topology metrics (e.g., diameter, redundancy)"
    )
    eliminated_spofs: List[str] = Field(..., description="SPOFs that would be eliminated")
    resilience_improvement: float = Field(
        ..., 
        description="Improvement in resilience score (%)"
    )
    
    # Implementation details
    implementation_complexity: str = Field(
        ..., 
        description="Complexity to implement (low, medium, high)"
    )
    estimated_deployment_time: float = Field(
        ..., 
        description="Estimated deployment time in hours"
    )
    estimated_cost_impact: str = Field(
        ..., 
        description="Impact on operational costs (increase, same, decrease)"
    )
