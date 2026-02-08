"""
Topology analysis module for detecting issues and assessing network health.

Uses networkx for graph-based analysis to:
- Detect single points of failure
- Identify unbalanced routing paths
- Find overloaded nodes
- Calculate network metrics
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
import networkx as nx
from app.models import Topology, Device, Link
from app.models.analysis import (
    TopologyAnalysisResult, TopologyMetrics, SinglePointOfFailure,
    UnbalancedPath, OverloadedNode, TopologyIssue, RiskLevel, VisualizationNode,
    VisualizationEdge, TopologyVisualization
)

logger = logging.getLogger(__name__)


class TopologyAnalyzer:
    """
    Analyzes network topologies to detect issues and provide insights.
    
    Uses graph theory to identify:
    - Single points of failure (articulation points)
    - Unbalanced routing paths
    - Overloaded nodes (high link concentration)
    - Network metrics and statistics
    """

    def __init__(self, topology: Topology):
        """
        Initialize the analyzer with a topology.
        
        Args:
            topology: Topology object to analyze
        """
        self.topology = topology
        self.graph = self._build_graph()
        logger.info(f"Analyzer initialized for topology '{topology.name}' with "
                   f"{len(topology.devices)} devices and {len(topology.links)} links")

    def _build_graph(self) -> nx.Graph:
        """
        Build a networkx graph from the topology.
        
        Returns:
            Undirected graph representation of the topology
        """
        graph = nx.Graph()
        
        # Add all devices as nodes
        for device in self.topology.devices:
            graph.add_node(device.name, device_type=device.device_type)
        
        # Add links as edges with weights (OSPF cost)
        for link in self.topology.links:
            graph.add_edge(
                link.source_device,
                link.destination_device,
                weight=link.cost,
                source_ip=link.source_ip,
                destination_ip=link.destination_ip
            )
        
        return graph

    def analyze(self) -> TopologyAnalysisResult:
        """
        Perform complete topology analysis.
        
        Returns:
            TopologyAnalysisResult with all findings
        """
        logger.info(f"Starting analysis of topology '{self.topology.name}'")
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        # Detect issues
        spofs = self._detect_single_points_of_failure()
        unbalanced = self._detect_unbalanced_paths()
        overloaded = self._detect_overloaded_nodes()
        other_issues = self._detect_other_issues()
        
        # Calculate health score
        health_score, health_status = self._calculate_health_score(
            metrics, spofs, unbalanced, overloaded, other_issues
        )
        
        # Generate summary
        summary = self._generate_summary(
            metrics, spofs, unbalanced, overloaded, other_issues, health_score
        )
        
        result = TopologyAnalysisResult(
            topology_name=self.topology.name,
            analysis_timestamp=datetime.now().isoformat(),
            metrics=metrics,
            single_points_of_failure=spofs,
            unbalanced_paths=unbalanced,
            overloaded_nodes=overloaded,
            other_issues=other_issues,
            overall_health_score=health_score,
            health_status=health_status,
            total_issues=len(spofs) + len(unbalanced) + len(overloaded) + len(other_issues),
            critical_issues=sum(
                1 for issue in spofs + other_issues 
                if issue.risk_level == RiskLevel.CRITICAL
            ),
            summary=summary
        )
        
        logger.info(f"Analysis complete: Health score {health_score:.1f}/100, "
                   f"{result.total_issues} issues found")
        return result

    def _calculate_metrics(self) -> TopologyMetrics:
        """Calculate overall topology metrics."""
        logger.debug("Calculating topology metrics")
        
        num_devices = self.graph.number_of_nodes()
        num_links = self.graph.number_of_edges()
        
        # Network diameter (longest shortest path)
        if nx.is_connected(self.graph):
            diameter = nx.diameter(self.graph)
        else:
            # For disconnected graphs, use largest component diameter
            largest_cc = max(nx.connected_components(self.graph), key=len)
            subgraph = self.graph.subgraph(largest_cc)
            diameter = nx.diameter(subgraph) if len(subgraph) > 1 else 0
        
        # Average connectivity
        avg_connectivity = 2 * num_links / num_devices if num_devices > 0 else 0
        
        # Connectivity coefficient (density)
        connectivity_coefficient = nx.density(self.graph)
        
        # Redundancy factor (average number of edge-disjoint paths)
        redundancy_factor = self._calculate_redundancy_factor()
        
        # Count SPOFs
        articulation_points = list(nx.articulation_points(self.graph))
        spof_count = len(articulation_points)
        
        return TopologyMetrics(
            total_devices=num_devices,
            total_links=num_links,
            network_diameter=diameter,
            average_connectivity=round(avg_connectivity, 2),
            connectivity_coefficient=round(connectivity_coefficient, 3),
            redundancy_factor=round(redundancy_factor, 2),
            spof_count=spof_count
        )

    def _calculate_redundancy_factor(self) -> float:
        """
        Calculate average number of edge-disjoint paths.
        
        Returns:
            Average redundancy factor across device pairs
        """
        if self.graph.number_of_nodes() < 2:
            return 0.0
        
        redundancy_values = []
        nodes = list(self.graph.nodes())
        
        # Sample pairs to avoid O(n²) computation for large graphs
        sample_size = min(10, len(nodes) * (len(nodes) - 1) // 2)
        sampled_pairs = []
        
        for i in range(min(5, len(nodes))):
            for j in range(i + 1, min(i + 3, len(nodes))):
                sampled_pairs.append((nodes[i], nodes[j]))
        
        for source, target in sampled_pairs:
            if nx.has_path(self.graph, source, target):
                try:
                    # Get edge connectivity (number of edge-disjoint paths)
                    connectivity = nx.edge_connectivity(self.graph, source, target)
                    redundancy_values.append(connectivity)
                except nx.NetworkXError:
                    redundancy_values.append(1)
        
        return sum(redundancy_values) / len(redundancy_values) if redundancy_values else 1.0

    def _detect_single_points_of_failure(self) -> List[SinglePointOfFailure]:
        """
        Detect single points of failure (articulation points).
        
        Returns:
            List of detected SPOFs
        """
        logger.debug("Detecting single points of failure")
        spofs = []
        
        # Find articulation points
        articulation_points = list(nx.articulation_points(self.graph))
        
        for device_name in articulation_points:
            # Get devices that would be disconnected if this device fails
            temp_graph = self.graph.copy()
            temp_graph.remove_node(device_name)
            
            # Find disconnected nodes
            if nx.is_connected(temp_graph) or temp_graph.number_of_nodes() == 0:
                dependent_devices = []
            else:
                # Get all nodes not in the largest component
                largest_cc = max(nx.connected_components(temp_graph), key=len)
                other_nodes = set(temp_graph.nodes()) - largest_cc
                dependent_devices = sorted(list(other_nodes))
            
            # Determine risk level based on number of affected devices
            affected_count = len(dependent_devices)
            total_devices = self.graph.number_of_nodes()
            affected_percentage = (affected_count / total_devices * 100) if total_devices > 0 else 0
            
            if affected_percentage >= 50:
                risk_level = RiskLevel.CRITICAL
            elif affected_percentage >= 25:
                risk_level = RiskLevel.HIGH
            elif affected_percentage >= 10:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
            
            # Generate remedy
            degree = self.graph.degree(device_name)
            remedy = (f"Add redundant links to {device_name} (currently {degree} links). "
                     f"Consider backup connections to devices: {', '.join(dependent_devices[:3])}")
            
            spofs.append(SinglePointOfFailure(
                device_name=device_name,
                risk_level=risk_level,
                dependent_devices=dependent_devices,
                total_affected_nodes=affected_count,
                remedy=remedy
            ))
        
        return spofs

    def _detect_unbalanced_paths(self) -> List[UnbalancedPath]:
        """
        Detect unbalanced routing paths.
        
        Returns:
            List of unbalanced path issues
        """
        logger.debug("Detecting unbalanced paths")
        unbalanced = []
        
        nodes = list(self.graph.nodes())
        device_pairs = [(nodes[i], nodes[j]) for i in range(len(nodes)) 
                       for j in range(i + 1, min(i + 3, len(nodes)))]  # Sample for performance
        
        for source, dest in device_pairs:
            if not nx.has_path(self.graph, source, dest):
                continue
            
            try:
                # Find shortest path
                shortest_path = nx.shortest_path(
                    self.graph, source, dest, weight='weight'
                )
                path_length = len(shortest_path) - 1
                
                # Find all simple paths (limit to prevent explosion)
                all_paths = []
                try:
                    for path in nx.all_simple_paths(self.graph, source, dest, cutoff=5):
                        all_paths.append(path)
                        if len(all_paths) >= 5:
                            break
                except nx.NetworkXNoPath:
                    pass
                
                if len(all_paths) > 1:
                    # Calculate path balance
                    path_lengths = [len(p) - 1 for p in all_paths]
                    min_length = min(path_lengths)
                    max_length = max(path_lengths)
                    balance_score = 1.0 - (max_length - min_length) / (max_length + 1)
                    
                    if balance_score < 0.8:
                        alternative_paths = [p for p in all_paths if p != shortest_path]
                        recommendation = (
                            f"Paths between {source} and {dest} have varying lengths "
                            f"({min_length}-{max_length} hops). Consider adjusting OSPF costs "
                            f"for better load balancing."
                        )
                        
                        unbalanced.append(UnbalancedPath(
                            source_device=source,
                            destination_device=dest,
                            path_length=path_length,
                            alternative_paths=alternative_paths,
                            balance_score=round(balance_score, 3),
                            recommendation=recommendation
                        ))
            except nx.NetworkXError:
                continue
        
        return unbalanced

    def _detect_overloaded_nodes(self) -> List[OverloadedNode]:
        """
        Detect nodes with high link concentration.
        
        Returns:
            List of overloaded nodes
        """
        logger.debug("Detecting overloaded nodes")
        overloaded = []
        
        degrees = dict(self.graph.degree())
        avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0
        
        for device_name, degree in degrees.items():
            if degree == 0:
                continue
            
            load_percentage = (degree / avg_degree * 100) if avg_degree > 0 else 0
            
            # Flag as overloaded if significantly above average
            if load_percentage > 150:  # 1.5x average
                if load_percentage > 250:
                    risk_level = RiskLevel.HIGH
                else:
                    risk_level = RiskLevel.MEDIUM
                
                recommendation = (
                    f"Device {device_name} has {degree} connections (average is {avg_degree:.1f}). "
                    f"Consider adding an additional aggregation point to distribute load."
                )
                
                overloaded.append(OverloadedNode(
                    device_name=device_name,
                    link_count=degree,
                    average_device_links=round(avg_degree, 2),
                    load_percentage=round(load_percentage, 1),
                    risk_level=risk_level,
                    recommendation=recommendation
                ))
        
        return overloaded

    def _detect_other_issues(self) -> List[TopologyIssue]:
        """
        Detect other topology issues.
        
        Returns:
            List of other issues
        """
        issues = []
        
        # Check for isolated devices (devices with no links)
        isolated = [node for node in self.graph.nodes() if self.graph.degree(node) == 0]
        if isolated:
            issues.append(TopologyIssue(
                issue_type="isolated_devices",
                severity=RiskLevel.CRITICAL,
                description=f"Found {len(isolated)} isolated device(s)",
                affected_elements=isolated,
                recommendation=f"Connect isolated devices: {', '.join(isolated)}"
            ))
        
        # Check network connectivity
        if not nx.is_connected(self.graph):
            num_components = nx.number_connected_components(self.graph)
            issues.append(TopologyIssue(
                issue_type="disconnected_network",
                severity=RiskLevel.CRITICAL,
                description=f"Network has {num_components} disconnected components",
                affected_elements=list(self.graph.nodes()),
                recommendation="Connect all network components to form a single connected graph"
            ))
        
        return issues

    def _calculate_health_score(
        self,
        metrics: TopologyMetrics,
        spofs: List[SinglePointOfFailure],
        unbalanced: List[UnbalancedPath],
        overloaded: List[OverloadedNode],
        other_issues: List[TopologyIssue]
    ) -> Tuple[float, str]:
        """
        Calculate overall topology health score.
        
        Returns:
            Tuple of (health_score, health_status)
        """
        score = 100.0
        
        # Deduct for critical issues
        critical_count = len([s for s in spofs if s.risk_level == RiskLevel.CRITICAL])
        score -= critical_count * 20
        
        # Deduct for high-risk SPOFs
        high_risk_spofs = len([s for s in spofs if s.risk_level == RiskLevel.HIGH])
        score -= high_risk_spofs * 10
        
        # Deduct for unbalanced paths
        score -= len(unbalanced) * 3
        
        # Deduct for overloaded nodes
        score -= len(overloaded) * 5
        
        # Deduct for other issues
        score -= len(other_issues) * 15
        
        # Increase for good redundancy
        if metrics.redundancy_factor >= 2.0:
            score += 10
        
        # Increase for good connectivity
        if metrics.connectivity_coefficient > 0.3:
            score += 5
        
        score = max(0, min(100, score))
        
        if score >= 80:
            status = "excellent"
        elif score >= 60:
            status = "good"
        elif score >= 40:
            status = "fair"
        else:
            status = "poor"
        
        return round(score, 1), status

    def _generate_summary(
        self,
        metrics: TopologyMetrics,
        spofs: List[SinglePointOfFailure],
        unbalanced: List[UnbalancedPath],
        overloaded: List[OverloadedNode],
        other_issues: List[TopologyIssue],
        health_score: float
    ) -> str:
        """Generate a text summary of the analysis."""
        summary_parts = [
            f"Topology '{self.topology.name}' analysis complete.",
            f"Health Score: {health_score}/100",
            f"Devices: {metrics.total_devices}, Links: {metrics.total_links}",
            f"Network Diameter: {metrics.network_diameter} hops",
        ]
        
        if spofs:
            critical_spofs = [s for s in spofs if s.risk_level == RiskLevel.CRITICAL]
            summary_parts.append(
                f"⚠️  Found {len(spofs)} single points of failure "
                f"({len(critical_spofs)} critical)"
            )
        
        if unbalanced:
            summary_parts.append(
                f"⚠️  Found {len(unbalanced)} unbalanced routing paths"
            )
        
        if overloaded:
            summary_parts.append(
                f"⚠️  Found {len(overloaded)} overloaded nodes"
            )
        
        if metrics.redundancy_factor < 1.5:
            summary_parts.append(
                "💡 Low redundancy detected. Consider adding backup links."
            )
        
        summary_parts.append(
            "✅ Review recommendations above to improve topology resilience."
        )
        
        return " ".join(summary_parts)

    def visualize(self) -> TopologyVisualization:
        """
        Generate visualization data for the topology.
        
        Returns:
            TopologyVisualization with nodes and edges
        """
        logger.debug("Generating visualization data")
        
        nodes = []
        for device in self.topology.devices:
            nodes.append(VisualizationNode(
                id=device.name,
                label=device.name,
                device_type=device.device_type.value,
                properties={
                    "router_id": device.router_id,
                    "asn": device.asn,
                }
            ))
        
        edges = []
        for link in self.topology.links:
            edges.append(VisualizationEdge(
                source=link.source_device,
                target=link.destination_device,
                label=f"Cost: {link.cost}",
                properties={
                    "source_ip": link.source_ip,
                    "destination_ip": link.destination_ip,
                    "cost": link.cost,
                }
            ))
        
        return TopologyVisualization(
            topology_name=self.topology.name,
            nodes=nodes,
            edges=edges,
            layout_hints={
                "algorithm": "force-directed",
                "charge": -300,
                "link_strength": 0.5,
            }
        )
