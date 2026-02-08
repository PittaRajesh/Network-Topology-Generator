"""
Topology optimization engine for recommending improvements.

Features:
- Identifies redundancy opportunities
- Suggests routing cost optimizations
- Recommends capacity balancing
- Proposes topology redesigns
"""

import logging
from typing import Dict, List, Set, Tuple
from datetime import datetime
import networkx as nx
from app.models import Topology
from app.models.optimization import (
    TopologyOptimizationResult, OptimizationRecommendation,
    RoutingOptimization, CapacityOptimization, RedundancyOptimization,
    OptimizedTopologyProposal
)
from app.analysis import TopologyAnalyzer

logger = logging.getLogger(__name__)


class TopologyOptimizer:
    """
    Recommends topology optimizations and improvements.
    
    Features:
    - Cost optimization for routing
    - Redundancy improvements
    - Capacity balancing
    - Alternative topology proposals
    """

    def __init__(self, topology: Topology):
        """
        Initialize the optimizer.
        
        Args:
            topology: Topology to optimize
        """
        self.topology = topology
        self.graph = self._build_graph()
        self.analyzer = TopologyAnalyzer(topology)
        logger.info(f"Optimizer initialized for topology '{topology.name}'")

    def _build_graph(self) -> nx.Graph:
        """Build networkx graph from topology."""
        graph = nx.Graph()
        
        for device in self.topology.devices:
            graph.add_node(device.name, device_type=device.device_type)
        
        for link in self.topology.links:
            graph.add_edge(
                link.source_device,
                link.destination_device,
                weight=link.cost,
                source_ip=link.source_ip,
                destination_ip=link.destination_ip
            )
        
        return graph

    def optimize(self) -> TopologyOptimizationResult:
        """
        Perform complete topology optimization analysis.
        
        Returns:
            TopologyOptimizationResult with recommendations
        """
        logger.info(f"Starting optimization of topology '{self.topology.name}'")
        
        # Get analysis for baseline
        analysis = self.analyzer.analyze()
        
        # Generate recommendations
        general_recs = self._generate_general_recommendations(analysis)
        routing_opts = self._generate_routing_optimizations()
        capacity_opts = self._generate_capacity_optimizations(analysis)
        redundancy_opts = self._generate_redundancy_optimizations(analysis)
        
        # Calculate optimization potential
        current_score = analysis.overall_health_score
        potential_score = min(100.0, current_score + 30)  # Estimate potential improvement
        optimization_potential = ((potential_score - current_score) / 100.0 * 100) \
            if current_score > 0 else 0
        
        # Calculate implementation effort
        total_recs = (
            len(general_recs) + len(routing_opts) +
            len(capacity_opts) + len(redundancy_opts)
        )
        if total_recs > 5:
            effort = "high"
        elif total_recs > 2:
            effort = "medium"
        else:
            effort = "low"
        
        # Generate summary
        summary = self._generate_optimization_summary(
            analysis, general_recs, routing_opts, capacity_opts, redundancy_opts
        )
        
        result = TopologyOptimizationResult(
            topology_name=self.topology.name,
            optimization_timestamp=datetime.now().isoformat(),
            general_recommendations=general_recs,
            routing_optimizations=routing_opts,
            capacity_optimizations=capacity_opts,
            redundancy_optimizations=redundancy_opts,
            current_optimization_score=round(current_score, 1),
            potential_optimization_score=round(potential_score, 1),
            optimization_potential=round(optimization_potential, 1),
            total_recommendations=total_recs,
            high_priority_recommendations=sum(
                1 for r in general_recs if r.priority <= 2
            ),
            implementation_effort=effort,
            summary=summary
        )
        
        logger.info(f"Optimization complete: {total_recs} recommendations generated, "
                   f"{optimization_potential:.1f}% potential improvement")
        return result

    def _generate_general_recommendations(
        self,
        analysis
    ) -> List[OptimizationRecommendation]:
        """Generate general topology optimization recommendations."""
        recommendations = []
        
        # Check for SPOFs
        if analysis.single_points_of_failure:
            for spof in analysis.single_points_of_failure[:3]:
                recommendations.append(OptimizationRecommendation(
                    priority=1,
                    category="redundancy",
                    title=f"Eliminate SPOF: {spof.device_name}",
                    description=(
                        f"Device {spof.device_name} is a single point of failure "
                        f"affecting {spof.total_affected_nodes} devices"
                    ),
                    expected_benefit="Improved network resilience and availability",
                    estimated_effort="high",
                    affected_elements=spof.dependent_devices,
                    implementation_steps=[
                        f"Add redundant links to {spof.device_name}",
                        "Configure link aggregation if applicable",
                        "Test failover scenarios",
                        "Update OSPF costs for balanced paths"
                    ]
                ))
        
        # Check for low connectivity
        if analysis.metrics.connectivity_coefficient < 0.3:
            recommendations.append(OptimizationRecommendation(
                priority=2,
                category="redundancy",
                title="Increase Network Connectivity",
                description=(
                    f"Low network connectivity ({analysis.metrics.connectivity_coefficient:.1%}). "
                    "Consider adding more links for better resilience."
                ),
                expected_benefit="Improved path diversity and redundancy",
                estimated_effort="medium",
                affected_elements=list(set([d.name for d in self.topology.devices])),
                implementation_steps=[
                    "Identify candidates for additional links",
                    "Add mesh links between core devices",
                    "Recalculate OSPF metrics",
                    "Validate new paths"
                ]
            ))
        
        # Check for low redundancy
        if analysis.metrics.redundancy_factor < 1.5:
            recommendations.append(OptimizationRecommendation(
                priority=2,
                category="redundancy",
                title="Improve Path Redundancy",
                description=(
                    f"Path redundancy factor is low ({analysis.metrics.redundancy_factor:.1f}x). "
                    "Most device pairs have limited alternative paths."
                ),
                expected_benefit="Reduced impact of link failures",
                estimated_effort="medium",
                affected_elements=list(set([d.name for d in self.topology.devices])),
                implementation_steps=[
                    "Add cross-links between distribution devices",
                    "Create mesh in access layer",
                    "Test multiple failures",
                    "Document new redundancy paths"
                ]
            ))
        
        # Check for high diameter
        if analysis.metrics.network_diameter > 6:
            recommendations.append(OptimizationRecommendation(
                priority=3,
                category="performance",
                title="Reduce Network Diameter",
                description=(
                    f"Wide network diameter ({analysis.metrics.network_diameter} hops) "
                    "may cause increased latency."
                ),
                expected_benefit="Reduced latency and convergence time",
                estimated_effort="medium",
                affected_elements=list(set([d.name for d in self.topology.devices])),
                implementation_steps=[
                    "Add shortcut links",
                    "Create more direct paths between core devices",
                    "Optimize routing hierarchy",
                    "Test latency improvements"
                ]
            ))
        
        return recommendations

    def _generate_routing_optimizations(self) -> List[RoutingOptimization]:
        """Generate OSPF cost optimization recommendations."""
        optimizations = []
        
        nodes = list(self.graph.nodes())
        # Sample pairs to avoid O(n²) computation
        for i in range(min(5, len(nodes))):
            for j in range(i + 1, min(i + 3, len(nodes))):
                source, dest = nodes[i], nodes[j]
                
                try:
                    if nx.has_path(self.graph, source, dest):
                        current_path = nx.shortest_path(
                            self.graph, source, dest, weight='weight'
                        )
                        current_metric = nx.shortest_path_length(
                            self.graph, source, dest, weight='weight'
                        )
                        
                        # Check if there are alternative paths with different costs
                        alternative_paths = []
                        try:
                            for path in nx.all_simple_paths(
                                self.graph, source, dest, cutoff=6
                            ):
                                if path != current_path:
                                    alternative_paths.append(path)
                                    if len(alternative_paths) >= 2:
                                        break
                        except nx.NetworkXNoPath:
                            pass
                        
                        if alternative_paths:
                            alt_metric = min(
                                nx.shortest_path_length(
                                    self.graph,
                                    source, dest, weight='weight'
                                ) for _ in [alternative_paths[0]]
                            )
                            
                            if current_metric > alt_metric:
                                optimizations.append(RoutingOptimization(
                                    device_pair=(source, dest),
                                    current_metric=current_metric,
                                    suggested_metric=alt_metric,
                                    benefit="Better load balancing and traffic distribution",
                                    reasoning=(
                                        f"Current metric is {current_metric}, "
                                        f"but metric {alt_metric} would use shorter path"
                                    )
                                ))
                except (nx.NetworkXNoPath, nx.NetworkXError):
                    continue
        
        return optimizations[:5]  # Return top 5

    def _generate_capacity_optimizations(
        self,
        analysis
    ) -> List[CapacityOptimization]:
        """Generate capacity optimization recommendations."""
        optimizations = []
        
        # Check overloaded nodes
        for overloaded in analysis.overloaded_nodes:
            optimizations.append(CapacityOptimization(
                device_name=overloaded.device_name,
                current_link_count=overloaded.link_count,
                recommended_action="Distribute load to new aggregation point",
                target_link_count=max(
                    overloaded.link_count // 2,
                    int(overloaded.average_device_links)
                ),
                benefit="Reduced device load, improved scalability"
            ))
        
        return optimizations

    def _generate_redundancy_optimizations(
        self,
        analysis
    ) -> List[RedundancyOptimization]:
        """Generate redundancy improvement recommendations."""
        optimizations = []
        
        # For each SPOF, recommend redundancy improvements
        for spof in analysis.single_points_of_failure:
            optimizations.append(RedundancyOptimization(
                failure_scenario=f"Loss of {spof.device_name}",
                current_state="Single point of failure",
                recommended_state="Multiple independent paths",
                required_links=[
                    f"Add-backup-link-to-{spof.device_name}",
                    f"Add-diversa-path-via-alternate-device"
                ],
                failure_modes_addressed=[
                    f"Failure of {spof.device_name}",
                    "Links to dependent devices"
                ]
            ))
        
        return optimizations[:3]  # Return top 3

    def _generate_optimization_summary(
        self,
        analysis,
        general_recs: List[OptimizationRecommendation],
        routing_opts: List[RoutingOptimization],
        capacity_opts: List[CapacityOptimization],
        redundancy_opts: List[RedundancyOptimization]
    ) -> str:
        """Generate a summary of optimization opportunities."""
        summary_parts = [
            f"Topology '{self.topology.name}' optimization analysis complete.",
        ]
        
        if general_recs:
            summary_parts.append(f"Found {len(general_recs)} general recommendations")
        
        if routing_opts:
            summary_parts.append(f"Identified {len(routing_opts)} routing optimizations")
        
        if capacity_opts:
            summary_parts.append(f"Detected {len(capacity_opts)} capacity concerns")
        
        if redundancy_opts:
            summary_parts.append(f"Proposed {len(redundancy_opts)} redundancy improvements")
        
        summary_parts.append(
            "Focus first on eliminating single points of failure (priority 1)."
        )
        
        return " ".join(summary_parts)

    def propose_optimized_topology(self) -> OptimizedTopologyProposal:
        """
        Create a proposal for an optimized topology.
        
        Returns:
            OptimizedTopologyProposal with suggested changes
        """
        analysis = self.analyzer.analyze()
        
        # Identify SPOFs to eliminate
        spof_devices = [s.device_name for s in analysis.single_points_of_failure]
        
        # Propose links to add for redundancy
        links_to_add = []
        for spof in analysis.single_points_of_failure[:3]:
            links_to_add.append({
                "source": spof.device_name,
                "target": spof.dependent_devices[0] if spof.dependent_devices else "backup_device"
            })
        
        # Calculate improvements
        improved_metrics = {
            "diameter_reduction": f"{max(0, analysis.metrics.network_diameter - 4)} hops",
            "redundancy_increase": f"{analysis.metrics.redundancy_factor * 1.5:.1f}x",
            "connectivity_improvement": f"{(1 - analysis.metrics.connectivity_coefficient) * 100:.1f}%"
        }
        
        return OptimizedTopologyProposal(
            proposal_id="proposal_optimal_v1",
            base_topology_name=self.topology.name,
            proposal_name=f"Optimized {self.topology.name}",
            description="Enhanced topology with improved redundancy and resilience",
            links_to_add=links_to_add,
            links_to_remove=[],
            cost_changes={},
            improved_metrics=improved_metrics,
            eliminated_spofs=spof_devices,
            resilience_improvement=25.0,
            implementation_complexity="medium",
            estimated_deployment_time=8.0,
            estimated_cost_impact="increase"  # More links = more cost
        )
