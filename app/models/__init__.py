"""Models package for networking automation engine."""
from .topology import Device, Link, Topology, TopologyRequest, DeviceType
from .configuration import OSPFConfiguration, InterfaceConfig, RoutingConfig
from .deployment import ContainerlabTopology, ContainerlabNode
from .analysis import (
    TopologyAnalysisResult, TopologyMetrics, SinglePointOfFailure,
    UnbalancedPath, OverloadedNode, TopologyIssue, RiskLevel,
    VisualizationNode, VisualizationEdge, TopologyVisualization
)
from .simulation import (
    FailureType, FailureRequest, FailureSimulationResult, FailureImpact,
    AffectedRoute, TestScenario, TestScenarioResult
)
from .optimization import (
    TopologyOptimizationResult, OptimizationRecommendation,
    RoutingOptimization, CapacityOptimization, RedundancyOptimization,
    OptimizedTopologyProposal
)
from .intent import (
    TopologyType, RedundancyLevel, RoutingProtocol, DesignGoal,
    IntentRequest, TopologyConstraint, IntentConstraints,
    IntentValidationResult, IntentReport, IntentGenerationRequest,
    IntentValidationRequest, IntentGenerationResponse
)

__all__ = [
    # Topology models
    "Device",
    "DeviceType",
    "Link",
    "Topology",
    "TopologyRequest",
    # Configuration models
    "OSPFConfiguration",
    "InterfaceConfig",
    "RoutingConfig",
    # Deployment models
    "ContainerlabTopology",
    "ContainerlabNode",
    # Analysis models
    "TopologyAnalysisResult",
    "TopologyMetrics",
    "SinglePointOfFailure",
    "UnbalancedPath",
    "OverloadedNode",
    "TopologyIssue",
    "RiskLevel",
    "VisualizationNode",
    "VisualizationEdge",
    "TopologyVisualization",
    # Simulation models
    "FailureType",
    "FailureRequest",
    "FailureSimulationResult",
    "FailureImpact",
    "AffectedRoute",
    "TestScenario",
    "TestScenarioResult",
    # Optimization models
    "TopologyOptimizationResult",
    "OptimizationRecommendation",
    "RoutingOptimization",
    "CapacityOptimization",
    "RedundancyOptimization",
    "OptimizedTopologyProposal",
    # Intent-based networking models
    "TopologyType",
    "RedundancyLevel",
    "RoutingProtocol",
    "DesignGoal",
    "IntentRequest",
    "TopologyConstraint",
    "IntentConstraints",
    "IntentValidationResult",
    "IntentReport",
    "IntentGenerationRequest",
    "IntentValidationRequest",
    "IntentGenerationResponse",
]
