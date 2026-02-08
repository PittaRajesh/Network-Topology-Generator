"""Pydantic models for failure simulation."""
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field
from enum import Enum


class FailureType(str, Enum):
    """Types of failures that can be simulated."""
    LINK_FAILURE = "link_failure"
    ROUTER_FAILURE = "router_failure"
    SWITCH_FAILURE = "switch_failure"
    MULTIPLE_LINK_FAILURE = "multiple_link_failures"


class FailureRequest(BaseModel):
    """Request to simulate a failure."""
    failure_type: FailureType = Field(..., description="Type of failure to simulate")
    failed_element: Optional[str] = Field(None, description="Device or link that fails")
    failed_elements: Optional[List[str]] = Field(
        None, 
        description="Multiple devices/links that fail (for multiple failures)"
    )


class AffectedRoute(BaseModel):
    """A route affected by a failure."""
    source_device: str = Field(..., description="Source device")
    destination_device: str = Field(..., description="Destination device")
    original_path: List[str] = Field(..., description="Original routing path")
    rerouted_path: Optional[List[str]] = Field(
        None, 
        description="New path after failure (None if unreachable)"
    )
    original_hops: int = Field(..., description="Hops in original path")
    rerouted_hops: Optional[int] = Field(None, description="Hops in rerouted path")
    path_length_increase: Optional[int] = Field(
        None, 
        description="Increase in hops due to failure"
    )
    reachable_after_failure: bool = Field(
        ..., 
        description="Whether destination is still reachable"
    )


class DisconnectedComponent(BaseModel):
    """A partition of the topology caused by failure."""
    component_id: int = Field(..., description="ID of this component")
    devices: List[str] = Field(..., description="Devices in this component")
    device_count: int = Field(..., description="Number of devices in this component")


class FailureImpact(BaseModel):
    """Impact analysis of a single failure."""
    failed_element: str = Field(..., description="The element that failed")
    failure_type: FailureType = Field(..., description="Type of failure")
    
    # Connectivity
    devices_disconnected: List[str] = Field(
        default_factory=list,
        description="Devices that are disconnected from the network"
    )
    connectivity_lost_percentage: float = Field(
        ..., 
        description="Percentage of network connectivity lost"
    )
    network_partitions: int = Field(
        ..., 
        description="Number of disconnected network partitions"
    )
    isolated_devices: List[str] = Field(
        default_factory=list,
        description="Devices that become isolated"
    )
    
    # Routing
    affected_routes: List[AffectedRoute] = Field(
        default_factory=list,
        description="Routes affected by this failure"
    )
    routes_impacted: int = Field(..., description="Number of routes affected")
    routes_lost: int = Field(..., description="Number of routes that have no alternative")
    
    # Recovery
    recovery_time_estimate: Optional[float] = Field(
        None, 
        description="Estimated time to recover in seconds"
    )
    can_recovery_automatically: bool = Field(
        ..., 
        description="Whether OSPF can automatically recover"
    )
    
    # Severity
    severity: str = Field(..., description="Severity of the failure (critical, high, medium, low)")
    impact_score: float = Field(..., ge=0.0, le=100.0, description="Impact score (0-100)")


class FailureSimulationResult(BaseModel):
    """Result of a failure simulation."""
    topology_name: str = Field(..., description="Name of the topology")
    simulation_timestamp: str = Field(..., description="When the simulation was performed")
    
    # Failure details
    failure_description: str = Field(..., description="Description of the simulated failure")
    failed_elements: List[str] = Field(..., description="Elements that failed")
    
    # Analysis
    impact_analysis: Dict[str, FailureImpact] = Field(
        ..., 
        description="Impact analysis for each failed element"
    )
    combined_impact: FailureImpact = Field(..., description="Combined impact of all failures")
    
    # Scenario information
    scenario_id: str = Field(..., description="Unique ID for this failure scenario")
    scenario_severity: str = Field(..., description="Overall severity of the scenario")


class TestScenario(BaseModel):
    """A failure test scenario."""
    scenario_id: str = Field(..., description="Unique scenario identifier")
    name: str = Field(..., description="Friendly name for the scenario")
    description: str = Field(..., description="Description of what is tested")
    target_resilience_aspect: str = Field(
        ..., 
        description="What aspect of resilience this tests (e.g., 'link redundancy')"
    )
    failures: List[FailureRequest] = Field(
        ..., 
        description="List of failures to simulate in sequence"
    )
    expected_recovery_time: float = Field(
        ..., 
        description="Expected recovery time in seconds"
    )
    critical_success_factors: List[str] = Field(
        ..., 
        description="What defines success for this test scenario"
    )
    severity: str = Field(..., description="Severity of the scenario being tested")


class TestScenarioResult(BaseModel):
    """Result of executing a test scenario."""
    scenario_id: str = Field(..., description="Scenario identifier")
    scenario_name: str = Field(..., description="Friendly name")
    topology_name: str = Field(..., description="Topology tested")
    test_timestamp: str = Field(..., description="When test was run")
    
    # Simulation results
    simulation_results: List[FailureSimulationResult] = Field(
        ..., 
        description="Results from each failure in the scenario"
    )
    
    # Scenario assessment
    total_failures_simulated: int = Field(..., description="Total failures tested")
    network_remained_operational: bool = Field(
        ..., 
        description="Whether network remained operational throughout"
    )
    critical_failures_handled: int = Field(
        ..., 
        description="Number of critical failures the network handled"
    )
    
    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations based on scenario results"
    )
    
    # Overall assessment
    resilience_rating: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Network resilience rating based on test (0-100)"
    )
    resilience_level: str = Field(
        ..., 
        description="Resilience level (excellent, good, fair, poor)"
    )
