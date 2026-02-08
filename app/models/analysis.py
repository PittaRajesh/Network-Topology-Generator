"""Pydantic models for topology analysis."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SinglePointOfFailure(BaseModel):
    """Represents a single point of failure in the topology."""
    device_name: str = Field(..., description="Name of the device that is a SPOF")
    risk_level: RiskLevel = Field(..., description="Severity of the risk")
    dependent_devices: List[str] = Field(
        ..., 
        description="List of devices that would be disconnected if this device fails"
    )
    total_affected_nodes: int = Field(
        ..., 
        description="Number of devices affected by this failure"
    )
    remedy: str = Field(..., description="Suggested fix for this SPOF")


class UnbalancedPath(BaseModel):
    """Represents an unbalanced routing path."""
    source_device: str = Field(..., description="Source device")
    destination_device: str = Field(..., description="Destination device")
    path_length: int = Field(..., description="Number of hops in the path")
    alternative_paths: List[List[str]] = Field(
        ..., 
        description="Alternative paths through the topology"
    )
    balance_score: float = Field(
        ..., 
        description="Score indicating path balance (0-1, higher is better)"
    )
    recommendation: str = Field(..., description="Recommendation for balancing")


class OverloadedNode(BaseModel):
    """Represents a node with high link concentration."""
    device_name: str = Field(..., description="Name of the device")
    link_count: int = Field(..., description="Number of links connected to this device")
    average_device_links: float = Field(..., description="Average links per device")
    load_percentage: float = Field(
        ..., 
        description="Load as percentage of average (100 = average)"
    )
    risk_level: RiskLevel = Field(..., description="Risk level due to overload")
    recommendation: str = Field(..., description="Recommendation to reduce load")


class TopologyIssue(BaseModel):
    """Represents a detected issue in the topology."""
    issue_type: str = Field(..., description="Type of issue (e.g., spof, redundancy)")
    severity: RiskLevel = Field(..., description="Severity level")
    description: str = Field(..., description="Detailed description of the issue")
    affected_elements: List[str] = Field(..., description="Elements affected by this issue")
    recommendation: str = Field(..., description="Recommendation to fix the issue")


class TopologyMetrics(BaseModel):
    """Metrics about the topology structure."""
    total_devices: int = Field(..., description="Total number of devices")
    total_links: int = Field(..., description="Total number of links")
    network_diameter: int = Field(
        ..., 
        description="Maximum shortest path between any two devices"
    )
    average_connectivity: float = Field(
        ..., 
        description="Average links per device"
    )
    connectivity_coefficient: float = Field(
        ..., 
        description="Measure of how well-connected devices are (0-1)"
    )
    redundancy_factor: float = Field(
        ..., 
        description="How many disjoint paths exist on average"
    )
    spof_count: int = Field(..., description="Number of single points of failure")


class TopologyAnalysisResult(BaseModel):
    """Complete topology analysis result."""
    topology_name: str = Field(..., description="Name of the analyzed topology")
    analysis_timestamp: str = Field(..., description="When the analysis was performed")
    
    # Metrics
    metrics: TopologyMetrics = Field(..., description="Topology metrics and statistics")
    
    # Issues found
    single_points_of_failure: List[SinglePointOfFailure] = Field(
        default_factory=list,
        description="Detected single points of failure"
    )
    unbalanced_paths: List[UnbalancedPath] = Field(
        default_factory=list,
        description="Unbalanced routing paths"
    )
    overloaded_nodes: List[OverloadedNode] = Field(
        default_factory=list,
        description="Nodes with high link concentration"
    )
    other_issues: List[TopologyIssue] = Field(
        default_factory=list,
        description="Other detected issues"
    )
    
    # Overall assessment
    overall_health_score: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Overall topology health score (0-100)"
    )
    health_status: str = Field(..., description="Overall health status (excellent, good, fair, poor)")
    total_issues: int = Field(..., description="Total number of issues detected")
    critical_issues: int = Field(..., description="Number of critical issues")
    
    # Recommendations summary
    summary: str = Field(..., description="Summary of findings and recommendations")


class VisualizationNode(BaseModel):
    """Node data for visualization."""
    id: str = Field(..., description="Node identifier")
    label: str = Field(..., description="Display label")
    device_type: str = Field(..., description="Type of device (router, switch)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class VisualizationEdge(BaseModel):
    """Edge data for visualization."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str = Field(..., description="Display label")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class TopologyVisualization(BaseModel):
    """Topology data formatted for visualization."""
    topology_name: str = Field(..., description="Name of the topology")
    nodes: List[VisualizationNode] = Field(..., description="Nodes in the topology")
    edges: List[VisualizationEdge] = Field(..., description="Edges/links in the topology")
    layout_hints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Layout hints for visualization tools"
    )
