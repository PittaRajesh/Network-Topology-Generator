"""
Intent Validation Engine

Validates whether a generated topology satisfies the user's intent.
Produces detailed reports on constraint satisfaction and provides
recommendations for improvement.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
import networkx as nx

from app.models.topology import Topology
from app.models.intent import (
    IntentRequest, IntentConstraints, IntentValidationResult,
    TopologyType, RedundancyLevel, IntentReport
)
from app.intent.parser import IntentParser
from app.analysis import TopologyAnalyzer

logger = logging.getLogger(__name__)


class IntentValidator:
    """
    Validates topologies against intent specifications.
    
    Checks:
    - Redundancy level satisfaction
    - Path diversity
    - Hop count constraints
    - SPOF elimination
    - Topology pattern matching
    
    Produces a score (0-100) indicating intent satisfaction.
    """
    
    def __init__(self):
        """Initialize the intent validator."""
        self.parser = IntentParser()
        logger.info("Initializing Intent Validator")
    
    def validate(
        self,
        topology: Topology,
        intent: IntentRequest
    ) -> IntentValidationResult:
        """
        Validate whether topology satisfies intent.
        
        Args:
            topology: Generated topology to validate
            intent: Original intent specification
        
        Returns:
            IntentValidationResult with satisfaction details
        """
        logger.info(f"Validating topology against intent: {intent.intent_name}")
        
        # Parse intent into constraints
        constraints = self.parser.parse(intent)
        
        # Check each constraint
        redundancy_score = self._check_redundancy(topology, intent, constraints)
        path_diversity_score = self._check_path_diversity(topology, intent, constraints)
        hop_count_ok = self._check_hop_count(topology, intent, constraints)
        spof_ok = self._check_spof_elimination(topology, intent, constraints)
        topology_ok = self._check_topology_pattern(topology, intent, constraints)
        
        # Get actual metrics for reporting
        analyzer = TopologyAnalyzer(topology)
        analysis = analyzer.analyze()
        
        # Calculate overall score
        overall_score = (redundancy_score + path_diversity_score) / 2
        if not hop_count_ok:
            overall_score -= 20
        if not spof_ok and intent.minimize_spof:
            overall_score -= 30
        if not topology_ok:
            overall_score -= 15
        
        # Clamp score to 0-100
        overall_score = max(0, min(100, overall_score))
        
        # Check intent satisfaction
        intent_satisfied = (
            redundancy_score >= 70 and
            path_diversity_score >= 60 and
            hop_count_ok and
            (spof_ok or not intent.minimize_spof) and
            topology_ok
        )
        
        # Collect violations and warnings
        violations = self._collect_violations(
            redundancy_score, path_diversity_score, hop_count_ok,
            spof_ok, topology_ok, intent
        )
        
        warnings = self._collect_warnings(topology, intent, analysis)
        recommendations = self._generate_recommendations(
            topology, intent, analysis, violations
        )
        
        result = IntentValidationResult(
            intent_satisfied=intent_satisfied,
            overall_score=overall_score,
            redundancy_score=redundancy_score,
            path_diversity_score=path_diversity_score,
            hop_count_satisfaction=hop_count_ok,
            actual_max_hops=self._calculate_max_hops(topology),
            spof_eliminated=spof_ok,
            remaining_spofs=len(analysis.single_points_of_failure),
            topology_pattern_matched=topology_ok,
            constraint_violations=violations,
            warnings=warnings,
            recommendations=recommendations,
        )
        
        logger.info(f"Validation complete: score={overall_score:.1f}, satisfied={intent_satisfied}")
        return result
    
    def _check_redundancy(
        self,
        topology: Topology,
        intent: IntentRequest,
        constraints: IntentConstraints
    ) -> float:
        """
        Check redundancy level satisfaction.
        
        Returns score 0-100 based on how well redundancy is achieved.
        """
        logger.debug("Checking redundancy requirement")
        
        redundancy_map = {
            RedundancyLevel.MINIMUM: 1,
            RedundancyLevel.STANDARD: 2,
            RedundancyLevel.HIGH: 3,
            RedundancyLevel.CRITICAL: 4,
        }
        
        required_paths = redundancy_map[intent.redundancy_level]
        
        # Count average connections per device
        device_counts = {}
        for link in topology.links:
            device_counts[link.source_device] = device_counts.get(link.source_device, 0) + 1
        
        if not device_counts:
            return 0
        
        avg_connections = sum(device_counts.values()) / len(device_counts)
        
        # Score based on how close we are to required minimum
        if avg_connections >= required_paths:
            score = 100
        else:
            # Partial credit for partial redundancy
            score = (avg_connections / required_paths) * 100
        
        logger.debug(f"Redundancy score: {score:.1f} (avg {avg_connections:.1f} connections/device)")
        return score
    
    def _check_path_diversity(
        self,
        topology: Topology,
        intent: IntentRequest,
        constraints: IntentConstraints
    ) -> float:
        """
        Check path diversity between major device groupings.
        
        Score based on how many edge-disjoint paths exist.
        """
        logger.debug("Checking path diversity")
        
        # Build networkx graph
        G = nx.Graph()
        for device in topology.devices:
            G.add_node(device.name)
        for link in topology.links:
            G.add_edge(link.source_device, link.destination_device)
        
        if not G or len(G.nodes) < 2:
            return 0
        
        # Calculate average edge connectivity
        try:
            # Sample pairs due to computational complexity
            sample_size = min(5, len(G.nodes) - 1)
            nodes = list(G.nodes)
            total_connectivity = 0
            samples = 0
            
            for i in range(min(sample_size, len(nodes) - 1)):
                try:
                    src = nodes[i]
                    dst = nodes[i + 1]
                    connectivity = nx.edge_connectivity(G, src, dst)
                    total_connectivity += connectivity
                    samples += 1
                except:
                    pass
            
            if samples > 0:
                avg_connectivity = total_connectivity / samples
                # Expected minimum based on redundancy
                expected_min = {
                    RedundancyLevel.MINIMUM: 1,
                    RedundancyLevel.STANDARD: 2,
                    RedundancyLevel.HIGH: 3,
                    RedundancyLevel.CRITICAL: 4,
                }.get(intent.redundancy_level, 1)
                
                if avg_connectivity >= expected_min:
                    score = 100
                else:
                    score = (avg_connectivity / expected_min) * 100
            else:
                score = 50
        except Exception as e:
            logger.warning(f"Path diversity calculation failed: {e}")
            score = 50
        
        logger.debug(f"Path diversity score: {score:.1f}")
        return score
    
    def _check_hop_count(
        self,
        topology: Topology,
        intent: IntentRequest,
        constraints: IntentConstraints
    ) -> bool:
        """
        Check if topology satisfies max hop constraint.
        """
        logger.debug(f"Checking hop count constraint (max {intent.max_hops})")
        
        actual_max = self._calculate_max_hops(topology)
        satisfied = actual_max <= intent.max_hops
        
        logger.debug(f"Hop count check: actual={actual_max}, max={intent.max_hops}, satisfied={satisfied}")
        return satisfied
    
    def _check_spof_elimination(
        self,
        topology: Topology,
        intent: IntentRequest,
        constraints: IntentConstraints
    ) -> bool:
        """
        Check if single points of failure are eliminated.
        """
        logger.debug(f"Checking SPOF elimination (required={intent.minimize_spof})")
        
        if not intent.minimize_spof:
            return True  # No SPOF elimination required
        
        # Use topology analyzer to find SPOFs
        analyzer = TopologyAnalyzer(topology)
        analysis = analyzer.analyze()
        
        spof_count = len(analysis.single_points_of_failure)
        satisfied = spof_count == 0
        
        logger.debug(f"SPOF check: found {spof_count} SPOFs, satisfied={satisfied}")
        return satisfied
    
    def _check_topology_pattern(
        self,
        topology: Topology,
        intent: IntentRequest,
        constraints: IntentConstraints
    ) -> bool:
        """
        Check if topology matches the requested pattern.
        
        This is a basic check - just verifies the topology name contains the pattern.
        More sophisticated checks could analyze actual structure.
        """
        logger.debug(f"Checking topology pattern match: {intent.topology_type}")
        
        pattern_str = intent.topology_type.value
        match = pattern_str in topology.name.lower()
        
        logger.debug(f"Pattern match: {match}")
        return match
    
    def _calculate_max_hops(self, topology: Topology) -> int:
        """
        Calculate maximum hop count (network diameter).
        """
        # Build networkx graph
        G = nx.Graph()
        for device in topology.devices:
            G.add_node(device.name)
        for link in topology.links:
            G.add_edge(link.source_device, link.destination_device)
        
        if not G or len(G.nodes) < 2:
            return 0
        
        try:
            return nx.diameter(G)
        except nx.NetworkXError:
            # Graph is not connected
            return float('inf')
    
    def _collect_violations(
        self,
        redundancy_score: float,
        path_diversity_score: float,
        hop_count_ok: bool,
        spof_ok: bool,
        topology_ok: bool,
        intent: IntentRequest
    ) -> List[str]:
        """Collect list of constraint violations."""
        violations = []
        
        if redundancy_score < 70:
            violations.append(f"Redundancy score too low: {redundancy_score:.1f}/100")
        
        if path_diversity_score < 60:
            violations.append(f"Path diversity insufficient: {path_diversity_score:.1f}/100")
        
        if not hop_count_ok:
            violations.append(f"Maximum hop constraint violated (max allowed: {intent.max_hops})")
        
        if not spof_ok and intent.minimize_spof:
            violations.append("Single points of failure were not eliminated")
        
        if not topology_ok:
            violations.append(f"Topology pattern {intent.topology_type} not matched")
        
        return violations
    
    def _collect_warnings(
        self,
        topology: Topology,
        intent: IntentRequest,
        analysis: Any
    ) -> List[str]:
        """Collect list of non-critical warnings."""
        warnings = []
        
        # Check for overloaded nodes
        if analysis.overloaded_nodes:
            count = len(analysis.overloaded_nodes)
            warnings.append(f"Found {count} overloaded nodes with high connection degree")
        
        # Check network health
        if analysis.overall_health_score < 70:
            warnings.append(f"Overall network health score is low: {analysis.overall_health_score}/100")
        
        return warnings
    
    def _generate_recommendations(
        self,
        topology: Topology,
        intent: IntentRequest,
        analysis: Any,
        violations: List[str]
    ) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        if violations:
            if "Redundancy" in " ".join(violations):
                recommendations.append(
                    "Add more redundant links between critical nodes to increase redundancy"
                )
            
            if "Path diversity" in " ".join(violations):
                recommendations.append(
                    "Add alternative routing paths to increase path diversity"
                )
            
            if "hop" in " ".join(violations):
                recommendations.append(
                    "Reduce network diameter by adding direct links or changing topology structure"
                )
            
            if "SPOF" in " ".join(violations):
                for spof in analysis.single_points_of_failure:
                    recommendations.append(
                        f"Eliminate SPOF at {spof.device_name} by adding redundant paths"
                    )
        
        if analysis.topology_metrics.get("connectivity_coefficient", 1) < 0.5:
            recommendations.append(
                "Increase network connectivity by adding more inter-device connections"
            )
        
        return recommendations
    
    def generate_report(
        self,
        topology: Topology,
        intent: IntentRequest,
        validation_result: IntentValidationResult
    ) -> IntentReport:
        """
        Generate comprehensive validation report.
        """
        report_id = str(uuid.uuid4())[:8]
        
        requested_properties = {
            "topology_type": intent.topology_type.value,
            "number_of_sites": intent.number_of_sites,
            "redundancy_level": intent.redundancy_level.value,
            "max_hops": intent.max_hops,
            "routing_protocol": intent.routing_protocol.value,
            "design_goal": intent.design_goal.value,
            "minimize_spof": intent.minimize_spof,
        }
        
        generated_stats = {
            "total_devices": len(topology.devices),
            "total_links": len(topology.links),
            "avg_connections_per_device": (len(topology.links) * 2 / len(topology.devices)) if topology.devices else 0,
            "routing_protocol": topology.routing_protocol,
        }
        
        recommendations_text = "\n".join([f"- {rec}" for rec in validation_result.recommendations])
        
        next_steps = []
        if validation_result.intent_satisfied:
            next_steps = [
                "✓ Intent satisfied - proceed with topology deployment",
                "Export topology to Containerlab for testing",
                "Run failure simulation scenarios to validate resilience",
                "Deploy to test environment and validate configurations",
            ]
        else:
            next_steps = [
                "Review constraint violations above",
                "Modify intent or regenerate topology",
                "Implement recommendations for improvement",
                "Re-validate topology against intent",
            ]
        
        return IntentReport(
            report_id=report_id,
            intent_name=intent.intent_name,
            intent_description=intent.intent_description,
            requested_properties=requested_properties,
            generated_topology_stats=generated_stats,
            validation_result=validation_result,
            generation_timestamp=datetime.now().isoformat(),
            recommendations_summary=recommendations_text if recommendations_text else "No specific recommendations",
            next_steps=next_steps,
        )
