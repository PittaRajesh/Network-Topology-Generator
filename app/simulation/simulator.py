"""
Failure simulation engine for testing network resilience.

Simulates various failure scenarios including:
- Single link failures
- Device failures
- Multiple simultaneous failures
- Automatic OSPF path recalculation
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
import networkx as nx
from app.models import Topology
from app.models.simulation import (
    FailureType, FailureRequest, FailureSimulationResult, FailureImpact,
    AffectedRoute, DisconnectedComponent, TestScenario, TestScenarioResult
)

logger = logging.getLogger(__name__)


class FailureSimulator:
    """
    Simulates network failures and analyzes their impact.
    
    Features:
    - Single and multiple failure simulation
    - Automatic OSPF path recalculation
    - Impact analysis on connectivity and routing
    - Recovery time estimation
    """

    def __init__(self, topology: Topology):
        """
        Initialize the failure simulator.
        
        Args:
            topology: Topology to simulate failures on
        """
        self.topology = topology
        self.graph = self._build_graph()
        logger.info(f"Simulator initialized for topology '{topology.name}'")

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

    def simulate_failure(
        self,
        failure_requests: List[FailureRequest]
    ) -> FailureSimulationResult:
        """
        Simulate one or more failures.
        
        Args:
            failure_requests: List of failures to simulate
        
        Returns:
            FailureSimulationResult with impact analysis
        """
        logger.info(f"Simulating {len(failure_requests)} failure(s)")
        
        # Identify failed elements
        failed_elements = []
        for req in failure_requests:
            if req.failed_element:
                failed_elements.append(req.failed_element)
            elif req.failed_elements:
                failed_elements.extend(req.failed_elements)
        
        # Create a copy of the graph and remove failed elements
        simulation_graph = self.graph.copy()
        for element in failed_elements:
            if element in simulation_graph:
                simulation_graph.remove_node(element)
            else:
                # It might be a link, try removing adjacent nodes
                logger.warning(f"Element {element} not found in graph")
        
        # Build impact analysis for each failure
        impact_analyses = {}
        for element in set(failed_elements):
            impact_analyses[element] = self._analyze_failure_impact(element, simulation_graph)
        
        # Calculate combined impact
        combined_impact = self._calculate_combined_impact(impact_analyses)
        
        # Determine scenario severity
        if combined_impact.severity == "critical":
            scenario_severity = "critical"
        elif combined_impact.severity == "high":
            scenario_severity = "high"
        elif combined_impact.severity == "medium":
            scenario_severity = "medium"
        else:
            scenario_severity = "low"
        
        result = FailureSimulationResult(
            topology_name=self.topology.name,
            simulation_timestamp=datetime.now().isoformat(),
            failure_description=self._generate_failure_description(failure_requests),
            failed_elements=failed_elements,
            impact_analysis=impact_analyses,
            combined_impact=combined_impact,
            scenario_id=self._generate_scenario_id(),
            scenario_severity=scenario_severity
        )
        
        logger.info(f"Simulation complete: {combined_impact.severity.upper()} severity, "
                   f"{combined_impact.connectivity_lost_percentage:.1f}% connectivity lost")
        
        return result

    def _analyze_failure_impact(
        self,
        failed_element: str,
        simulation_graph: nx.Graph
    ) -> FailureImpact:
        """
        Analyze the impact of a single failure.
        
        Returns:
            FailureImpact with detailed analysis
        """
        # Determine failure type
        failure_type = self._determine_failure_type(failed_element)
        
        # Check connectivity before/after
        original_graph = self.graph
        affected_devices = []
        if failed_element in original_graph:
            # Find devices that lose connectivity
            original_components = list(nx.connected_components(original_graph))
            failed_components = list(nx.connected_components(simulation_graph))
            
            if len(failed_components) > len(original_components):
                # Network became partitioned
                largest_component = max(failed_components, key=len) if failed_components else set()
                affected_devices = [d for d in original_graph.nodes()
                                  if d not in largest_component and d != failed_element]
        
        # Calculate connectivity loss
        original_connectivity = original_graph.number_of_edges()
        new_connectivity = simulation_graph.number_of_edges()
        connectivity_lost = original_connectivity - new_connectivity
        connectivity_lost_percentage = (connectivity_lost / original_connectivity * 100) \
            if original_connectivity > 0 else 0
        
        # Analyze routing impact
        affected_routes = self._calculate_affected_routes(failed_element)
        
        # Determine severity
        if len(affected_devices) > original_graph.number_of_nodes() / 2:
            severity = "critical"
        elif len(affected_devices) > original_graph.number_of_nodes() / 4:
            severity = "high"
        elif affected_routes:
            severity = "medium"
        else:
            severity = "low"
        
        # Calculate impact score
        impact_score = (
            (len(affected_devices) / original_graph.number_of_nodes() * 50) if original_graph.number_of_nodes() > 0 else 0 +
            (min(len(affected_routes), 10) / 10 * 50)
        )
        
        return FailureImpact(
            failed_element=failed_element,
            failure_type=failure_type,
            devices_disconnected=affected_devices,
            connectivity_lost_percentage=round(connectivity_lost_percentage, 1),
            network_partitions=len(list(nx.connected_components(simulation_graph))),
            isolated_devices=affected_devices,
            affected_routes=affected_routes,
            routes_impacted=len(affected_routes),
            routes_lost=sum(1 for r in affected_routes if not r.rerouted_path),
            recovery_time_estimate=30.0,  # OSPF convergence time ~30 seconds
            can_recovery_automatically=True,
            severity=severity,
            impact_score=min(100, round(impact_score, 1))
        )

    def _determine_failure_type(self, element: str) -> FailureType:
        """Determine the type of failure for an element."""
        # Check if it's a device
        device_names = {d.name for d in self.topology.devices}
        if element in device_names:
            # Determine device type
            device_type = next((d.device_type for d in self.topology.devices 
                              if d.name == element), None)
            if device_type and "router" in device_type.value:
                return FailureType.ROUTER_FAILURE
            else:
                return FailureType.SWITCH_FAILURE
        else:
            return FailureType.LINK_FAILURE

    def _calculate_affected_routes(self, failed_element: str) -> List[AffectedRoute]:
        """
        Calculate routes affected by a failure.
        
        Returns:
            List of affected routes
        """
        affected = []
        nodes = list(self.graph.nodes())
        
        # Sample pairs to avoid O(n²) computation
        sampled_pairs = [(nodes[i], nodes[j]) for i in range(min(5, len(nodes)))
                        for j in range(i + 1, min(i + 3, len(nodes)))]
        
        for source, dest in sampled_pairs:
            if source == failed_element or dest == failed_element:
                continue
            
            try:
                # Check if path exists before failure
                if nx.has_path(self.graph, source, dest):
                    original_path = nx.shortest_path(
                        self.graph, source, dest, weight='weight'
                    )
                    original_hops = len(original_path) - 1
                    
                    # Check for path after failure
                    temp_graph = self.graph.copy()
                    if failed_element in temp_graph:
                        temp_graph.remove_node(failed_element)
                    
                    if nx.has_path(temp_graph, source, dest):
                        new_path = nx.shortest_path(
                            temp_graph, source, dest, weight='weight'
                        )
                        new_hops = len(new_path) - 1
                        hop_increase = new_hops - original_hops
                    else:
                        new_path = None
                        new_hops = None
                        hop_increase = None
                    
                    affected.append(AffectedRoute(
                        source_device=source,
                        destination_device=dest,
                        original_path=original_path,
                        rerouted_path=new_path,
                        original_hops=original_hops,
                        rerouted_hops=new_hops,
                        path_length_increase=hop_increase,
                        reachable_after_failure=new_path is not None
                    ))
            except (nx.NetworkXNoPath, nx.NetworkXError):
                continue
        
        return affected

    def _calculate_combined_impact(
        self,
        impact_analyses: Dict[str, FailureImpact]
    ) -> FailureImpact:
        """Calculate combined impact of multiple failures."""
        if not impact_analyses:
            return FailureImpact(
                failed_element="unknown",
                failure_type=FailureType.LINK_FAILURE,
                connectivity_lost_percentage=0,
                network_partitions=1,
                routes_impacted=0,
                routes_lost=0,
                can_recovery_automatically=True,
                severity="low",
                impact_score=0
            )
        
        # Aggregate impacts
        all_disconnected = set()
        for impact in impact_analyses.values():
            all_disconnected.update(impact.devices_disconnected)
        
        max_connectivity_loss = max(
            (i.connectivity_lost_percentage for i in impact_analyses.values()),
            default=0
        )
        
        total_routes_impacted = sum(i.routes_impacted for i in impact_analyses.values())
        total_routes_lost = sum(i.routes_lost for i in impact_analyses.values())
        
        # Determine severity
        if len(all_disconnected) > 5 or max_connectivity_loss > 50:
            severity = "critical"
        elif len(all_disconnected) > 2 or max_connectivity_loss > 25:
            severity = "high"
        elif total_routes_impacted > 0:
            severity = "medium"
        else:
            severity = "low"
        
        return FailureImpact(
            failed_element=", ".join(impact_analyses.keys()),
            failure_type=FailureType.MULTIPLE_LINK_FAILURE,
            devices_disconnected=list(all_disconnected),
            connectivity_lost_percentage=round(max_connectivity_loss, 1),
            network_partitions=sum(i.network_partitions for i in impact_analyses.values()),
            routes_impacted=total_routes_impacted,
            routes_lost=total_routes_lost,
            can_recovery_automatically=all(i.can_recovery_automatically 
                                         for i in impact_analyses.values()),
            severity=severity,
            impact_score=min(100, sum(i.impact_score for i in impact_analyses.values()))
        )

    def _generate_failure_description(self, requests: List[FailureRequest]) -> str:
        """Generate a textual description of the failure scenario."""
        if len(requests) == 1:
            req = requests[0]
            element = req.failed_element or (req.failed_elements[0] if req.failed_elements else "unknown")
            return f"Simulating {req.failure_type.value}: {element}"
        else:
            elements = []
            for req in requests:
                if req.failed_element:
                    elements.append(req.failed_element)
                elif req.failed_elements:
                    elements.extend(req.failed_elements)
            return f"Simulating multiple failures: {', '.join(set(elements))}"

    def _generate_scenario_id(self) -> str:
        """Generate a unique scenario ID."""
        import time
        return f"scenario_{int(time.time() * 1000)}"

    def generate_test_scenarios(self) -> List[TestScenario]:
        """
        Generate recommended test scenarios.
        
        Returns:
            List of test scenarios to validate topology resilience
        """
        logger.info("Generating recommended test scenarios")
        scenarios = []
        
        # Scenario 1: Single router failure
        routers = [d.name for d in self.topology.devices 
                 if "router" in d.device_type.value]
        if routers:
            scenarios.append(TestScenario(
                scenario_id="scenario_single_router",
                name="Single Router Failure",
                description="Tests network behavior when one router fails",
                target_resilience_aspect="Core router redundancy",
                failures=[FailureRequest(
                    failure_type=FailureType.ROUTER_FAILURE,
                    failed_element=routers[0]
                )],
                expected_recovery_time=30.0,
                critical_success_factors=[
                    "Network remains connected",
                    "Traffic reroutes within 30 seconds",
                    "No permanent link loss"
                ],
                severity="high"
            ))
        
        # Scenario 2: Link failure
        if self.topology.links:
            link = self.topology.links[0]
            link_id = f"{link.source_device}-{link.destination_device}"
            scenarios.append(TestScenario(
                scenario_id="scenario_link_failure",
                name="Single Link Failure",
                description="Tests network behavior when one link fails",
                target_resilience_aspect="Link redundancy",
                failures=[FailureRequest(
                    failure_type=FailureType.LINK_FAILURE,
                    failed_element=link_id
                )],
                expected_recovery_time=30.0,
                critical_success_factors=[
                    "Alternate path exists",
                    "Path converges quickly"
                ],
                severity="medium"
            ))
        
        # Scenario 3: Multiple link failures
        if len(self.topology.links) > 2:
            links = self.topology.links[:2]
            link_ids = [f"{l.source_device}-{l.destination_device}" for l in links]
            scenarios.append(TestScenario(
                scenario_id="scenario_multiple_links",
                name="Multiple Link Failures",
                description="Tests network behavior under multiple simultaneous link failures",
                target_resilience_aspect="Multiple link redundancy",
                failures=[FailureRequest(
                    failure_type=FailureType.LINK_FAILURE,
                    failed_elements=link_ids
                )],
                expected_recovery_time=45.0,
                critical_success_factors=[
                    "Network remains mostly connected",
                    "Core services remain available"
                ],
                severity="high"
            ))
        
        logger.info(f"Generated {len(scenarios)} test scenarios")
        return scenarios
