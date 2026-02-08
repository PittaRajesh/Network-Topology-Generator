"""
Database models for topology history, simulations, and learning.

This module defines ORM models for storing:
- Topology generation history
- Failure simulation results
- Validation scores
- Performance metrics

Database is designed to be PostgreSQL-ready while supporting SQLite for development.
Can be extended with ML model predictions and autonomous optimization decisions.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TopologyRecord(Base):
    """
    Stores metadata about generated topologies.
    
    Attributes:
        id: Unique identifier
        intent_name: Name of the intent specification
        intent_parameters: JSON of complete intent specification
        topology_type: Type of topology (full_mesh, tree, leaf_spine, etc.)
        number_of_sites: Number of sites in topology
        num_devices: Number of generated devices
        num_links: Number of generated links
        redundancy_level: Redundancy level (minimum, standard, high, critical)
        routing_protocol: Routing protocol (ospf, bgp)
        design_goal: Design goal (cost_optimized, redundancy_focused, etc.)
        created_at: Timestamp of creation
        export_format: Format exported to (containerlab, yaml, etc.)
        notes: User notes about this topology
    """
    __tablename__ = "topology_records"
    
    id = Column(Integer, primary_key=True, index=True)
    intent_name = Column(String(255), nullable=False)
    intent_parameters = Column(JSON, nullable=False)  # Full intent spec for reproducibility
    topology_type = Column(String(50), nullable=False)  # full_mesh, tree, leaf_spine, hub_spoke, ring, hybrid
    number_of_sites = Column(Integer, nullable=False)
    num_devices = Column(Integer, nullable=False)
    num_links = Column(Integer, nullable=False)
    redundancy_level = Column(String(20), nullable=False)  # minimum, standard, high, critical
    routing_protocol = Column(String(20), nullable=False)  # ospf, bgp
    design_goal = Column(String(50), nullable=False)  # cost_optimized, redundancy_focused, latency_optimized, scalability
    minimize_spof = Column(Boolean, default=True)
    avg_connections_per_device = Column(Float, nullable=True)
    graph_diameter = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    export_format = Column(String(50), nullable=True)  # containerlab, yaml, json
    notes = Column(Text, nullable=True)
    
    # Relationships
    validation_records = relationship("ValidationRecord", back_populates="topology", cascade="all, delete-orphan")
    simulation_records = relationship("SimulationRecord", back_populates="topology", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TopologyRecord id={self.id} type={self.topology_type} sites={self.number_of_sites} created={self.created_at}>"


class ValidationRecord(Base):
    """
    Stores validation results for topologies.
    
    Attributes:
        id: Unique identifier
        topology_id: Foreign key to TopologyRecord
        intent_satisfied: Whether intent was satisfied
        overall_score: Overall validation score (0-100)
        redundancy_score: Redundancy component score (0-100)
        path_diversity_score: Path diversity component score (0-100)
        hop_count_satisfied: Whether hop count requirement met
        spof_eliminated: Whether SPOFs eliminated
        topology_matched: Whether topology pattern matched intent
        constraint_violations: JSON of violated constraints
        num_violations: Count of violations
        execution_time_ms: Time taken to validate (milliseconds)
        created_at: Timestamp of validation
    """
    __tablename__ = "validation_records"
    
    id = Column(Integer, primary_key=True, index=True)
    topology_id = Column(Integer, ForeignKey("topology_records.id"), nullable=False)
    intent_satisfied = Column(Boolean, nullable=False)
    overall_score = Column(Float, nullable=False)  # 0-100
    redundancy_score = Column(Float, nullable=False)
    path_diversity_score = Column(Float, nullable=False)
    hop_count_satisfied = Column(Boolean, nullable=False)
    spof_eliminated = Column(Boolean, nullable=False)
    topology_matched = Column(Boolean, nullable=False)
    constraint_violations = Column(JSON, nullable=True)  # List of violations
    num_violations = Column(Integer, default=0)
    execution_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    topology = relationship("TopologyRecord", back_populates="validation_records")
    
    def __repr__(self):
        return f"<ValidationRecord id={self.id} topology_id={self.topology_id} score={self.overall_score}>"


class SimulationRecord(Base):
    """
    Stores failure simulation results.
    
    Attributes:
        id: Unique identifier
        topology_id: Foreign key to TopologyRecord
        failure_scenario: Name/type of failure (node_down, link_down, multiple_failures, etc.)
        failure_details: JSON with specific nodes/links that failed
        network_partitioned: Whether simulation resulted in partitioned network
        isolated_devices: Number of isolated devices
        recovery_time_ms: Time until network converged after failure
        affected_paths: Number of paths affected
        reroutable_paths: Number of paths that had alternative routes
        resilience_impact: Impact score (0-100, higher=worse)
        num_isolated_components: Number of disconnected components
        created_at: Timestamp of simulation
    """
    __tablename__ = "simulation_records"
    
    id = Column(Integer, primary_key=True, index=True)
    topology_id = Column(Integer, ForeignKey("topology_records.id"), nullable=False)
    failure_scenario = Column(String(100), nullable=False)  # node_down, link_down, multi_failure, cascade
    failure_details = Column(JSON, nullable=False)  # {"failed_devices": [...], "failed_links": [...]}
    network_partitioned = Column(Boolean, nullable=False)
    isolated_devices = Column(Integer, default=0)
    recovery_time_ms = Column(Float, nullable=True)
    affected_paths = Column(Integer, nullable=True)
    reroutable_paths = Column(Integer, nullable=True)
    resilience_impact = Column(Float, nullable=True)  # 0-100, higher=worse
    num_isolated_components = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    topology = relationship("TopologyRecord", back_populates="simulation_records")
    
    def __repr__(self):
        return f"<SimulationRecord id={self.id} topology_id={self.topology_id} scenario={self.failure_scenario}>"


class PerformanceMetrics(Base):
    """
    Aggregated performance metrics computed from topology/simulation/validation records.
    
    Used by the learning engine to identify patterns and recommend topologies.
    Updated periodically by the learning analyzer.
    
    Attributes:
        id: Unique identifier
        topology_type: Type of topology (full_mesh, tree, leaf_spine, etc.)
        redundancy_level: Redundancy level
        design_goal: Design goal
        sample_size: Number of topologies in this category
        avg_validation_score: Average validation score
        avg_redundancy_score: Average redundancy score
        avg_path_diversity: Average path diversity score
        failure_resilience: Average resilience across simulations (0-100, lower=better)
        avg_recovery_time: Average recovery time in milliseconds
        spof_elimination_rate: Percentage of topologies that eliminated all SPOFs
        intent_satisfaction_rate: Percentage of topologies satisfying intent
        avg_num_links: Average link count
        avg_cost: Average cost metric (for cost-optimized designs)
        reliability_rank: Rank among peers (1=best)
        last_updated: When metrics were last calculated
        is_recommended: Whether this combination is recommended by learning engine
        confidence_score: Confidence in metrics (0-100, based on sample_size)
    """
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    topology_type = Column(String(50), nullable=False)
    redundancy_level = Column(String(20), nullable=False)
    design_goal = Column(String(50), nullable=False)
    sample_size = Column(Integer, default=0)
    avg_validation_score = Column(Float, nullable=True)
    avg_redundancy_score = Column(Float, nullable=True)
    avg_path_diversity = Column(Float, nullable=True)
    failure_resilience = Column(Float, nullable=True)  # 0-100, lower=more resilient
    avg_recovery_time = Column(Float, nullable=True)
    spof_elimination_rate = Column(Float, nullable=True)  # 0-100
    intent_satisfaction_rate = Column(Float, nullable=True)  # 0-100
    avg_num_links = Column(Float, nullable=True)
    avg_cost = Column(Float, nullable=True)
    reliability_rank = Column(Integer, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_recommended = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)  # 0-100
    
    def __repr__(self):
        return f"<PerformanceMetrics type={self.topology_type} redundancy={self.redundancy_level} score={self.avg_validation_score}>"


class RecommendationHistory(Base):
    """
    Tracks recommendations made by the learning engine.
    
    Used to evaluate recommendation accuracy and improve recommendation logic.
    
    Attributes:
        id: Unique identifier
        requested_intent: Original intent parameters
        recommended_topology_type: Recommended topology type
        recommended_redundancy: Recommended redundancy level
        recommendation_reason: Why this recommendation was made
        confidence_score: Confidence in recommendation (0-100)
        alternative_recommendations: JSON with other options considered
        user_selected: Which recommendation user selected (if any)
        resulted_topology_id: Link to final topology if generated
        feedback_score: User feedback on recommendation (1-5 stars or -1 for not provided)
        created_at: When recommendation was made
    """
    __tablename__ = "recommendation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    requested_intent = Column(JSON, nullable=False)
    recommended_topology_type = Column(String(50), nullable=False)
    recommended_redundancy = Column(String(20), nullable=False)
    recommendation_reason = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=False)  # 0-100
    alternative_recommendations = Column(JSON, nullable=True)  # List of alternatives
    user_selected = Column(String(50), nullable=True)  # Which topology user selected
    resulted_topology_id = Column(Integer, ForeignKey("topology_records.id"), nullable=True)
    feedback_score = Column(Integer, nullable=True)  # 1-5 stars or -1 for no feedback
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<RecommendationHistory id={self.id} recommended={self.recommended_topology_type} confidence={self.confidence_score}>"


class OptimizationLog(Base):
    """
    Tracks autonomous optimization decisions and their outcomes.
    
    Documents how the system adapts based on historical performance.
    
    Attributes:
        id: Unique identifier
        intent_parameters: Intent that triggered optimization
        original_topology_type: Initial topology type chosen
        optimization_applied: What optimization was applied
        adjusted_topology_type: Topology type after optimization
        optimization_reason: Why this optimization was chosen
        historical_advantage: How historical data supported this decision
        expected_improvement: Expected improvement percentage
        actual_improvement: Actual improvement achieved (if measured later)
        created_at: When optimization was applied
    """
    __tablename__ = "optimization_log"
    
    id = Column(Integer, primary_key=True, index=True)
    intent_parameters = Column(JSON, nullable=False)
    original_topology_type = Column(String(50), nullable=False)
    optimization_applied = Column(String(100), nullable=False)
    adjusted_topology_type = Column(String(50), nullable=False)
    optimization_reason = Column(Text, nullable=True)
    historical_advantage = Column(Text, nullable=True)  # Reference to historical data
    expected_improvement = Column(Float, nullable=True)  # Percentage
    actual_improvement = Column(Float, nullable=True)  # Percentage
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<OptimizationLog id={self.id} from={self.original_topology_type} to={self.adjusted_topology_type}>"
