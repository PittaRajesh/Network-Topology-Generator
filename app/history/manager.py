"""
History management system for storing topology generation and validation results.

Provides methods to:
- Store topology generation metadata
- Record validation results
- Store failure simulation results
- Retrieve historical data for learning
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.repository import DatabaseRepository
from app.models import Topology, IntentRequest, TopologyConstraint


class HistoryManager:
    """
    Manages all history recording for learning and recommendation.
    
    Integration points:
    - Called after topology generation
    - Called after validation
    - Called after failure simulation
    - Accessed by learning analyzer
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.repo = DatabaseRepository(db)
    
    def record_topology_generation(
        self,
        intent: IntentRequest,
        topology: Topology,
        intent_parameters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Record a generated topology.
        
        Args:
            intent: The IntentRequest that was used
            topology: The generated Topology object
            intent_parameters: Optional serialized intent parameters
        
        Returns:
            topology_record_id for later reference
        """
        # Build intent parameters dict
        if intent_parameters is None:
            intent_parameters = {
                "intent_name": intent.intent_name,
                "intent_description": intent.intent_description,
                "topology_type": intent.topology_type.value,
                "number_of_sites": intent.number_of_sites,
                "redundancy_level": intent.redundancy_level.value,
                "routing_protocol": intent.routing_protocol.value,
                "design_goal": intent.design_goal.value,
                "max_hops": intent.max_hops,
                "minimize_spof": intent.minimize_spof,
                "minimum_connections_per_site": intent.minimum_connections_per_site,
                "max_links": intent.max_links,
                "link_speed": intent.link_speed,
                "custom_constraints": intent.custom_constraints
            }
        
        # Calculate topology metrics
        avg_connections = self._calculate_avg_connections(topology)
        diameter = self._calculate_diameter(topology)
        
        # Create record
        topology_record = self.repo.topology.create(
            db=self.db,
            intent_name=intent.intent_name,
            intent_parameters=intent_parameters,
            topology_type=intent.topology_type.value,
            number_of_sites=intent.number_of_sites,
            num_devices=len(topology.devices),
            num_links=len(topology.links),
            redundancy_level=intent.redundancy_level.value,
            routing_protocol=intent.routing_protocol.value,
            design_goal=intent.design_goal.value,
            minimize_spof=intent.minimize_spof,
            avg_connections=avg_connections,
            diameter=diameter,
            notes=f"Auto-generated from intent '{intent.intent_name}'"
        )
        
        return topology_record.id
    
    def record_validation_result(
        self,
        topology_id: int,
        intent_satisfied: bool,
        overall_score: float,
        redundancy_score: float,
        path_diversity_score: float,
        hop_count_satisfied: bool,
        spof_eliminated: bool,
        topology_matched: bool,
        constraint_violations: Optional[List[str]] = None,
        execution_time_ms: Optional[float] = None
    ) -> int:
        """
        Record validation result for a topology.
        
        Args:
            topology_id: ID of topology being validated
            intent_satisfied: Whether intent was satisfied
            overall_score: Overall validation score (0-100)
            redundancy_score: Redundancy component score
            path_diversity_score: Path diversity score
            hop_count_satisfied: Hop count requirement met
            spof_eliminated: SPOFs eliminated
            topology_matched: Pattern matched
            constraint_violations: List of violated constraints
            execution_time_ms: Validation execution time
        
        Returns:
            validation_record_id
        """
        validation_record = self.repo.validation.create(
            db=self.db,
            topology_id=topology_id,
            intent_satisfied=intent_satisfied,
            overall_score=overall_score,
            redundancy_score=redundancy_score,
            path_diversity_score=path_diversity_score,
            hop_count_satisfied=hop_count_satisfied,
            spof_eliminated=spof_eliminated,
            topology_matched=topology_matched,
            constraint_violations=constraint_violations,
            execution_time_ms=execution_time_ms
        )
        
        return validation_record.id
    
    def record_failure_simulation(
        self,
        topology_id: int,
        failure_scenario: str,
        failure_details: Dict[str, Any],
        network_partitioned: bool,
        isolated_devices: int = 0,
        recovery_time_ms: Optional[float] = None,
        affected_paths: Optional[int] = None,
        reroutable_paths: Optional[int] = None,
        resilience_impact: Optional[float] = None,
        num_isolated_components: int = 1
    ) -> int:
        """
        Record failure simulation result.
        
        Args:
            topology_id: ID of simulated topology
            failure_scenario: Type of failure (node_down, link_down, etc.)
            failure_details: Dict with failed devices/links
            network_partitioned: Whether network was partitioned
            isolated_devices: Number of isolated devices
            recovery_time_ms: Time to recovery
            affected_paths: Number of affected paths
            reroutable_paths: Number of reroutable paths
            resilience_impact: Impact score (0-100, higher=worse)
            num_isolated_components: Number of disconnected components
        
        Returns:
            simulation_record_id
        """
        simulation_record = self.repo.simulation.create(
            db=self.db,
            topology_id=topology_id,
            failure_scenario=failure_scenario,
            failure_details=failure_details,
            network_partitioned=network_partitioned,
            isolated_devices=isolated_devices,
            recovery_time_ms=recovery_time_ms,
            affected_paths=affected_paths,
            reroutable_paths=reroutable_paths,
            resilience_impact=resilience_impact,
            num_isolated_components=num_isolated_components
        )
        
        return simulation_record.id
    
    def get_topology_history(
        self,
        topology_type: Optional[str] = None,
        redundancy_level: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get history of topologies with optional filtering.
        
        Args:
            topology_type: Filter by topology type
            redundancy_level: Filter by redundancy level
            limit: Maximum results
        
        Returns:
            List of topology records with validation data
        """
        if topology_type:
            topologies = self.repo.topology.get_by_type(self.db, topology_type)
        elif redundancy_level:
            topologies = self.repo.topology.get_by_redundancy(self.db, redundancy_level)
        else:
            topologies = self.repo.topology.get_all(self.db, limit=limit)
        
        result = []
        for topology in topologies[:limit]:
            validation = self.repo.validation.get_by_topology_id(self.db, topology.id)
            simulations = self.repo.simulation.get_by_topology_id(self.db, topology.id)
            
            result.append({
                "topology": {
                    "id": topology.id,
                    "intent_name": topology.intent_name,
                    "topology_type": topology.topology_type,
                    "num_sites": topology.number_of_sites,
                    "num_devices": topology.num_devices,
                    "num_links": topology.num_links,
                    "avg_connections": topology.avg_connections_per_device,
                    "created_at": topology.created_at.isoformat() if topology.created_at else None
                },
                "validation": {
                    "overall_score": validation.overall_score if validation else None,
                    "intent_satisfied": validation.intent_satisfied if validation else None,
                    "redundancy_score": validation.redundancy_score if validation else None,
                    "path_diversity_score": validation.path_diversity_score if validation else None
                } if validation else None,
                "simulations": [
                    {
                        "scenario": sim.failure_scenario,
                        "network_partitioned": sim.network_partitioned,
                        "resilience_impact": sim.resilience_impact
                    }
                    for sim in simulations
                ]
            })
        
        return result
    
    def get_recent_history(self, days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently generated topologies."""
        topologies = self.repo.topology.get_recent(self.db, days=days, limit=limit)
        
        result = []
        for topology in topologies:
            validation = self.repo.validation.get_by_topology_id(self.db, topology.id)
            result.append({
                "id": topology.id,
                "intent_name": topology.intent_name,
                "topology_type": topology.topology_type,
                "validation_score": validation.overall_score if validation else None,
                "created_at": topology.created_at.isoformat() if topology.created_at else None
            })
        
        return result
    
    def get_total_records(self) -> Dict[str, int]:
        """Get count of all records."""
        return {
            "total_topologies": self.repo.topology.count(self.db),
            "validations": self.db.query(
                __import__('app.database.models', fromlist=['ValidationRecord']).ValidationRecord
            ).count(),
            "simulations": self.db.query(
                __import__('app.database.models', fromlist=['SimulationRecord']).SimulationRecord
            ).count()
        }
    
    @staticmethod
    def _calculate_avg_connections(topology: Topology) -> float:
        """Calculate average connections per device."""
        if not topology.devices:
            return 0.0
        
        total_connections = 0
        for device in topology.devices:
            # Count links where this device is one end
            connections = sum(
                1 for link in topology.links
                if link.source_device == device.device_id or
                link.destination_device == device.device_id
            )
            total_connections += connections
        
        return total_connections / len(topology.devices)
    
    @staticmethod
    def _calculate_diameter(topology: Topology) -> Optional[int]:
        """Calculate network diameter using networkx."""
        try:
            import networkx as nx
            
            # Build graph
            G = nx.Graph()
            for device in topology.devices:
                G.add_node(device.device_id)
            
            for link in topology.links:
                G.add_edge(link.source_device, link.destination_device)
            
            # Calculate diameter
            if nx.is_connected(G):
                return nx.diameter(G)
            return None
        except Exception:
            return None
