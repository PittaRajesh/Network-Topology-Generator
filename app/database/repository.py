"""
Data access layer (repository pattern) for database operations.

Provides abstraction for:
- Storing topology generation results
- Querying historical data
- Analyzing performance metrics
- Managing recommendations and optimizations

This abstraction allows easy switching between SQLite/PostgreSQL/other databases.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.database.models import (
    TopologyRecord, ValidationRecord, SimulationRecord,
    PerformanceMetrics, RecommendationHistory, OptimizationLog
)


class TopologyRepository:
    """Repository for TopologyRecord operations."""
    
    @staticmethod
    def create(db: Session, intent_name: str, intent_parameters: Dict,
               topology_type: str, number_of_sites: int, num_devices: int,
               num_links: int, redundancy_level: str, routing_protocol: str,
               design_goal: str, minimize_spof: bool = True,
               avg_connections: Optional[float] = None,
               diameter: Optional[int] = None,
               notes: Optional[str] = None) -> TopologyRecord:
        """Create new topology record."""
        topology = TopologyRecord(
            intent_name=intent_name,
            intent_parameters=intent_parameters,
            topology_type=topology_type,
            number_of_sites=number_of_sites,
            num_devices=num_devices,
            num_links=num_links,
            redundancy_level=redundancy_level,
            routing_protocol=routing_protocol,
            design_goal=design_goal,
            minimize_spof=minimize_spof,
            avg_connections_per_device=avg_connections,
            graph_diameter=diameter,
            notes=notes
        )
        db.add(topology)
        db.commit()
        db.refresh(topology)
        return topology
    
    @staticmethod
    def get_by_id(db: Session, topology_id: int) -> Optional[TopologyRecord]:
        """Get topology by ID."""
        return db.query(TopologyRecord).filter(TopologyRecord.id == topology_id).first()
    
    @staticmethod
    def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[TopologyRecord]:
        """Get all topologies with pagination."""
        return db.query(TopologyRecord).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_by_type(db: Session, topology_type: str) -> List[TopologyRecord]:
        """Get topologies by type."""
        return db.query(TopologyRecord).filter(TopologyRecord.topology_type == topology_type).all()
    
    @staticmethod
    def get_by_redundancy(db: Session, redundancy_level: str) -> List[TopologyRecord]:
        """Get topologies by redundancy level."""
        return db.query(TopologyRecord).filter(TopologyRecord.redundancy_level == redundancy_level).all()
    
    @staticmethod
    def get_recent(db: Session, days: int = 30, limit: int = 100) -> List[TopologyRecord]:
        """Get topologies created in last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.query(TopologyRecord).filter(
            TopologyRecord.created_at >= cutoff
        ).order_by(desc(TopologyRecord.created_at)).limit(limit).all()
    
    @staticmethod
    def count(db: Session) -> int:
        """Count all topologies."""
        return db.query(TopologyRecord).count()


class ValidationRepository:
    """Repository for ValidationRecord operations."""
    
    @staticmethod
    def create(db: Session, topology_id: int, intent_satisfied: bool,
               overall_score: float, redundancy_score: float,
               path_diversity_score: float, hop_count_satisfied: bool,
               spof_eliminated: bool, topology_matched: bool,
               constraint_violations: Optional[List] = None,
               execution_time_ms: Optional[float] = None) -> ValidationRecord:
        """Create validation record."""
        validation = ValidationRecord(
            topology_id=topology_id,
            intent_satisfied=intent_satisfied,
            overall_score=overall_score,
            redundancy_score=redundancy_score,
            path_diversity_score=path_diversity_score,
            hop_count_satisfied=hop_count_satisfied,
            spof_eliminated=spof_eliminated,
            topology_matched=topology_matched,
            constraint_violations=constraint_violations,
            num_violations=len(constraint_violations) if constraint_violations else 0,
            execution_time_ms=execution_time_ms
        )
        db.add(validation)
        db.commit()
        db.refresh(validation)
        return validation
    
    @staticmethod
    def get_by_topology_id(db: Session, topology_id: int) -> Optional[ValidationRecord]:
        """Get validation for specific topology."""
        return db.query(ValidationRecord).filter(
            ValidationRecord.topology_id == topology_id
        ).order_by(desc(ValidationRecord.created_at)).first()
    
    @staticmethod
    def get_avg_score_by_type(db: Session, topology_type: str) -> Optional[float]:
        """Get average validation score for topology type."""
        result = db.query(func.avg(ValidationRecord.overall_score)).join(
            TopologyRecord
        ).filter(
            TopologyRecord.topology_type == topology_type
        ).scalar()
        return result
    
    @staticmethod
    def count_satisfied_intents(db: Session, topology_type: str) -> Tuple[int, int]:
        """Get count of satisfied vs total intents for topology type."""
        total = db.query(ValidationRecord).join(TopologyRecord).filter(
            TopologyRecord.topology_type == topology_type
        ).count()
        satisfied = db.query(ValidationRecord).join(TopologyRecord).filter(
            and_(TopologyRecord.topology_type == topology_type,
                 ValidationRecord.intent_satisfied == True)
        ).count()
        return satisfied, total


class SimulationRepository:
    """Repository for SimulationRecord operations."""
    
    @staticmethod
    def create(db: Session, topology_id: int, failure_scenario: str,
               failure_details: Dict, network_partitioned: bool,
               isolated_devices: int = 0, recovery_time_ms: Optional[float] = None,
               affected_paths: Optional[int] = None, reroutable_paths: Optional[int] = None,
               resilience_impact: Optional[float] = None,
               num_isolated_components: int = 1) -> SimulationRecord:
        """Create simulation record."""
        simulation = SimulationRecord(
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
        db.add(simulation)
        db.commit()
        db.refresh(simulation)
        return simulation
    
    @staticmethod
    def get_by_topology_id(db: Session, topology_id: int) -> List[SimulationRecord]:
        """Get all simulations for topology."""
        return db.query(SimulationRecord).filter(
            SimulationRecord.topology_id == topology_id
        ).all()
    
    @staticmethod
    def get_avg_resilience_impact(db: Session, topology_type: str) -> Optional[float]:
        """Get average failure resilience for topology type (lower=better)."""
        result = db.query(func.avg(SimulationRecord.resilience_impact)).join(
            TopologyRecord
        ).filter(
            TopologyRecord.topology_type == topology_type
        ).scalar()
        return result
    
    @staticmethod
    def get_partitioning_rate(db: Session, topology_type: str) -> Optional[float]:
        """Get percentage of failures causing network partitioning."""
        total = db.query(SimulationRecord).join(TopologyRecord).filter(
            TopologyRecord.topology_type == topology_type
        ).count()
        
        if total == 0:
            return None
        
        partitioned = db.query(SimulationRecord).join(TopologyRecord).filter(
            and_(TopologyRecord.topology_type == topology_type,
                 SimulationRecord.network_partitioned == True)
        ).count()
        
        return (partitioned / total) * 100


class PerformanceMetricsRepository:
    """Repository for PerformanceMetrics operations."""
    
    @staticmethod
    def get_or_create(db: Session, topology_type: str, redundancy_level: str,
                      design_goal: str) -> PerformanceMetrics:
        """Get metric record or create if not exists."""
        metrics = db.query(PerformanceMetrics).filter(
            and_(PerformanceMetrics.topology_type == topology_type,
                 PerformanceMetrics.redundancy_level == redundancy_level,
                 PerformanceMetrics.design_goal == design_goal)
        ).first()
        
        if not metrics:
            metrics = PerformanceMetrics(
                topology_type=topology_type,
                redundancy_level=redundancy_level,
                design_goal=design_goal,
                sample_size=0,
                confidence_score=0.0
            )
            db.add(metrics)
            db.commit()
            db.refresh(metrics)
        
        return metrics
    
    @staticmethod
    def update(db: Session, topology_type: str, redundancy_level: str,
               design_goal: str, **kwargs) -> PerformanceMetrics:
        """Update metrics for topology combination."""
        metrics = PerformanceMetricsRepository.get_or_create(
            db, topology_type, redundancy_level, design_goal
        )
        
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
        
        metrics.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(metrics)
        return metrics
    
    @staticmethod
    def get_best_performers(db: Session, limit: int = 10) -> List[PerformanceMetrics]:
        """Get best performing topology/redundancy/goal combinations."""
        return db.query(PerformanceMetrics).filter(
            PerformanceMetrics.is_recommended == True
        ).order_by(
            desc(PerformanceMetrics.avg_validation_score)
        ).limit(limit).all()
    
    @staticmethod
    def get_by_type(db: Session, topology_type: str) -> List[PerformanceMetrics]:
        """Get metrics for specific topology type."""
        return db.query(PerformanceMetrics).filter(
            PerformanceMetrics.topology_type == topology_type
        ).all()


class RecommendationRepository:
    """Repository for RecommendationHistory operations."""
    
    @staticmethod
    def create(db: Session, requested_intent: Dict, recommended_topology_type: str,
               recommended_redundancy: str, confidence_score: float,
               reason: Optional[str] = None,
               alternatives: Optional[List] = None) -> RecommendationHistory:
        """Create recommendation record."""
        recommendation = RecommendationHistory(
            requested_intent=requested_intent,
            recommended_topology_type=recommended_topology_type,
            recommended_redundancy=recommended_redundancy,
            confidence_score=confidence_score,
            recommendation_reason=reason,
            alternative_recommendations=alternatives
        )
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        return recommendation
    
    @staticmethod
    def update_feedback(db: Session, recommendation_id: int, feedback_score: int,
                       user_selected: Optional[str] = None,
                       topology_id: Optional[int] = None) -> RecommendationHistory:
        """Update recommendation with user feedback."""
        recommendation = db.query(RecommendationHistory).filter(
            RecommendationHistory.id == recommendation_id
        ).first()
        
        if recommendation:
            recommendation.feedback_score = feedback_score
            recommendation.user_selected = user_selected
            recommendation.resulted_topology_id = topology_id
            db.commit()
            db.refresh(recommendation)
        
        return recommendation
    
    @staticmethod
    def get_accuracy_by_topology_type(db: Session, topology_type: str) -> Optional[float]:
        """Get recommendation accuracy (feedback > 3 stars) for topology type."""
        total = db.query(RecommendationHistory).filter(
            and_(RecommendationHistory.recommended_topology_type == topology_type,
                 RecommendationHistory.feedback_score >= 0)
        ).count()
        
        if total == 0:
            return None
        
        accurate = db.query(RecommendationHistory).filter(
            and_(RecommendationHistory.recommended_topology_type == topology_type,
                 RecommendationHistory.feedback_score >= 3)
        ).count()
        
        return (accurate / total) * 100


class OptimizationRepository:
    """Repository for OptimizationLog operations."""
    
    @staticmethod
    def log_optimization(db: Session, intent_parameters: Dict,
                        original_topology_type: str, optimization_applied: str,
                        adjusted_topology_type: str, reason: Optional[str] = None,
                        historical_advantage: Optional[str] = None,
                        expected_improvement: Optional[float] = None) -> OptimizationLog:
        """Log an autonomous optimization decision."""
        log_entry = OptimizationLog(
            intent_parameters=intent_parameters,
            original_topology_type=original_topology_type,
            optimization_applied=optimization_applied,
            adjusted_topology_type=adjusted_topology_type,
            optimization_reason=reason,
            historical_advantage=historical_advantage,
            expected_improvement=expected_improvement
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    
    @staticmethod
    def get_recent(db: Session, limit: int = 50) -> List[OptimizationLog]:
        """Get recent optimization decisions."""
        return db.query(OptimizationLog).order_by(
            desc(OptimizationLog.created_at)
        ).limit(limit).all()
    
    @staticmethod
    def get_improvements(db: Session, limit: int = 10) -> List[OptimizationLog]:
        """Get optimizations where actual improvement was measured."""
        return db.query(OptimizationLog).filter(
            OptimizationLog.actual_improvement.isnot(None)
        ).order_by(
            desc(OptimizationLog.actual_improvement)
        ).limit(limit).all()


class DatabaseRepository:
    """
    Facade providing unified access to all repositories.
    
    Usage:
        repo = DatabaseRepository(db_session)
        topology = repo.topology.create(...)
        validation = repo.validation.create(...)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.topology = TopologyRepository()
        self.validation = ValidationRepository()
        self.simulation = SimulationRepository()
        self.metrics = PerformanceMetricsRepository()
        self.recommendation = RecommendationRepository()
        self.optimization = OptimizationRepository()
    
    def close(self):
        """Close database session."""
        self.db.close()
