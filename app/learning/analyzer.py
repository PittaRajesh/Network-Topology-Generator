"""
Learning analyzer - Analyzes historical topology generation, validation, and simulation data.

Key functions:
1. Analyze performance metrics across topology types and configurations
2. Identify best-performing topology/redundancy/goal combinations
3. Detect patterns in fault tolerance and resilience
4. Generate insights for recommendation engine
5. Track improvements over time
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.database import (
    TopologyRepository, ValidationRepository, SimulationRepository,
    PerformanceMetricsRepository, DatabaseRepository
)
from app.database.models import (
    TopologyRecord, ValidationRecord, SimulationRecord, PerformanceMetrics
)


class LearningAnalyzer:
    """
    Analyzes historical data to identify patterns and best-performing configurations.
    
    This engine learns:
    - Which topology types produce highest satisfaction with given constraints
    - Which redundancy levels are necessary for certain requirements
    - How different design goals affect validation scores
    - Which configurations are most resilient to failures
    - Trends over time (improving or degrading)
    """
    
    def __init__(self, db: Session):
        """Initialize analyzer with database session."""
        self.db = db
        self.repo = DatabaseRepository(db)
    
    def analyze_all(self) -> Dict[str, any]:
        """
        Run complete analysis on all historical data.
        
        Returns:
            Analysis results including metrics, recommendations, insights
        """
        print("[Analyzer] Starting comprehensive analysis...")
        
        # Get all unique combinations of topology_type, redundancy_level, design_goal
        combinations = self._get_topology_combinations()
        
        analysis_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_topologies_analyzed": self.repo.topology.count(self.db),
            "metrics": {},
            "recommendations": [],
            "insights": []
        }
        
        # Analyze each combination
        for topology_type, redundancy_level, design_goal in combinations:
            metrics = self._analyze_combination(
                topology_type, redundancy_level, design_goal
            )
            
            if metrics:
                key = f"{topology_type}_{redundancy_level}_{design_goal}"
                analysis_results["metrics"][key] = metrics
        
        # Generate insights
        analysis_results["insights"] = self._generate_insights()
        
        # Get top recommendations
        analysis_results["recommendations"] = self._get_top_recommendations(limit=5)
        
        print(f"[Analyzer] Analysis complete: {len(analysis_results['metrics'])} combinations analyzed")
        
        return analysis_results
    
    def _get_topology_combinations(self) -> List[Tuple[str, str, str]]:
        """Get all unique combinations of topology/redundancy/goal from history."""
        # Query unique combinations
        query = self.db.query(
            TopologyRecord.topology_type,
            TopologyRecord.redundancy_level,
            TopologyRecord.design_goal
        ).distinct()
        
        return [(row[0], row[1], row[2]) for row in query.all()]
    
    def _analyze_combination(
        self,
        topology_type: str,
        redundancy_level: str,
        design_goal: str
    ) -> Optional[Dict]:
        """
        Deep analysis of a specific topology/redundancy/goal combination.
        
        Returns:
            Metrics dictionary or None if insufficient data
        """
        # Get all topologies matching this combination
        topologies = self.db.query(TopologyRecord).filter(
            and_(
                TopologyRecord.topology_type == topology_type,
                TopologyRecord.redundancy_level == redundancy_level,
                TopologyRecord.design_goal == design_goal
            )
        ).all()
        
        if not topologies:
            return None
        
        sample_size = len(topologies)
        
        # Get validation data
        validation_scores = []
        redundancy_scores = []
        path_diversity_scores = []
        intent_satisfied_count = 0
        spof_eliminated_count = 0
        
        for topology in topologies:
            validation = self.repo.validation.get_by_topology_id(self.db, topology.id)
            if validation:
                validation_scores.append(validation.overall_score)
                redundancy_scores.append(validation.redundancy_score)
                path_diversity_scores.append(validation.path_diversity_score)
                
                if validation.intent_satisfied:
                    intent_satisfied_count += 1
                if validation.spof_eliminated:
                    spof_eliminated_count += 1
        
        # Get failure simulation data
        resilience_impacts = []
        partition_count = 0
        
        for topology in topologies:
            simulations = self.repo.simulation.get_by_topology_id(self.db, topology.id)
            for sim in simulations:
                if sim.resilience_impact is not None:
                    resilience_impacts.append(sim.resilience_impact)
                if sim.network_partitioned:
                    partition_count += 1
        
        # Calculate metrics
        avg_validation_score = (
            sum(validation_scores) / len(validation_scores)
            if validation_scores else 0
        )
        
        avg_redundancy_score = (
            sum(redundancy_scores) / len(redundancy_scores)
            if redundancy_scores else 0
        )
        
        avg_path_diversity = (
            sum(path_diversity_scores) / len(path_diversity_scores)
            if path_diversity_scores else 0
        )
        
        avg_resilience = (
            sum(resilience_impacts) / len(resilience_impacts)
            if resilience_impacts else 0
        )
        
        avg_links = sum(t.num_links for t in topologies) / len(topologies)
        
        intent_satisfaction_rate = (intent_satisfied_count / sample_size) * 100
        spof_elimination_rate = (spof_eliminated_count / len(validation_scores)) * 100 if validation_scores else 0
        partition_rate = (partition_count / len(resilience_impacts)) * 100 if resilience_impacts else 0
        
        # Determine if recommended
        is_recommended = (
            avg_validation_score >= 80 and
            avg_redundancy_score >= 75 and
            intent_satisfaction_rate >= 80
        )
        
        # Calculate confidence (higher sample size = higher confidence)
        confidence_score = min(100, (sample_size / 10) * 100)
        
        metrics = {
            "topology_type": topology_type,
            "redundancy_level": redundancy_level,
            "design_goal": design_goal,
            "sample_size": sample_size,
            "avg_validation_score": round(avg_validation_score, 2),
            "avg_redundancy_score": round(avg_redundancy_score, 2),
            "avg_path_diversity": round(avg_path_diversity, 2),
            "failure_resilience": round(avg_resilience, 2),  # Lower=better
            "avg_num_links": round(avg_links, 2),
            "intent_satisfaction_rate": round(intent_satisfaction_rate, 2),
            "spof_elimination_rate": round(spof_elimination_rate, 2),
            "partition_rate": round(partition_rate, 2),
            "is_recommended": is_recommended,
            "confidence_score": round(confidence_score, 2)
        }
        
        # Update performance metrics in database
        self.repo.metrics.update(
            self.db,
            topology_type=topology_type,
            redundancy_level=redundancy_level,
            design_goal=design_goal,
            sample_size=sample_size,
            avg_validation_score=avg_validation_score,
            avg_redundancy_score=avg_redundancy_score,
            avg_path_diversity=avg_path_diversity,
            failure_resilience=avg_resilience,
            spof_elimination_rate=spof_elimination_rate,
            intent_satisfaction_rate=intent_satisfaction_rate,
            avg_num_links=avg_links,
            is_recommended=is_recommended,
            confidence_score=confidence_score
        )
        
        return metrics
    
    def _generate_insights(self) -> List[Dict[str, str]]:
        """Generate insights from analysis."""
        insights = []
        
        # Find best overall performer
        best = self.db.query(PerformanceMetrics).order_by(
            PerformanceMetrics.avg_validation_score.desc()
        ).first()
        
        if best:
            insights.append({
                "type": "best_performer",
                "title": "Best Overall Performer",
                "insight": (
                    f"{best.topology_type} with {best.redundancy_level} redundancy "
                    f"achieves {best.avg_validation_score:.1f} average score"
                )
            })
        
        # Find most resilient
        most_resilient = self.db.query(PerformanceMetrics).filter(
            PerformanceMetrics.failure_resilience.isnot(None)
        ).order_by(
            PerformanceMetrics.failure_resilience.asc()  # Lower=better
        ).first()
        
        if most_resilient:
            insights.append({
                "type": "resilience_leader",
                "title": "Most Resilient Configuration",
                "insight": (
                    f"{most_resilient.topology_type} configuration shows best "
                    f"resilience to failures (impact score: {most_resilient.failure_resilience:.1f})"
                )
            })
        
        # Find most reliable
        most_reliable = self.db.query(PerformanceMetrics).order_by(
            PerformanceMetrics.intent_satisfaction_rate.desc()
        ).first()
        
        if most_reliable:
            insights.append({
                "type": "reliability_leader",
                "title": "Most Reliable Intent Satisfaction",
                "insight": (
                    f"{most_reliable.topology_type} achieves {most_reliable.intent_satisfaction_rate:.1f}% "
                    f"intent satisfaction rate"
                )
            })
        
        # Find trending improvement
        recent_better = self.db.query(TopologyRecord).filter(
            TopologyRecord.created_at >= func.date_sub(
                func.now(), {'days': 7}
            )
        ).count()
        
        if recent_better > 0:
            insights.append({
                "type": "trend",
                "title": "Recent Topologies Generated",
                "insight": f"{recent_better} topologies generated in last 7 days"
            })
        
        return insights
    
    def _get_top_recommendations(self, limit: int = 5) -> List[Dict]:
        """Get top recommended configurations."""
        top_performers = self.repo.metrics.get_best_performers(self.db, limit=limit)
        
        recommendations = []
        for perf in top_performers:
            recommendations.append({
                "topology_type": perf.topology_type,
                "redundancy_level": perf.redundancy_level,
                "design_goal": perf.design_goal,
                "avg_score": perf.avg_validation_score,
                "satisfaction_rate": perf.intent_satisfaction_rate,
                "confidence": perf.confidence_score,
                "reason": self._build_recommendation_reason(perf)
            })
        
        return recommendations
    
    @staticmethod
    def _build_recommendation_reason(metrics: PerformanceMetrics) -> str:
        """Build human-readable reason for recommendation."""
        parts = []
        
        if metrics.avg_validation_score >= 85:
            parts.append("excellent validation scores")
        elif metrics.avg_validation_score >= 75:
            parts.append("good validation scores")
        
        if metrics.intent_satisfaction_rate >= 90:
            parts.append("high intent satisfaction")
        
        if metrics.failure_resilience is not None and metrics.failure_resilience <= 25:
            parts.append("strong failure resilience")
        
        if metrics.spof_elimination_rate >= 85:
            parts.append("effective SPOF elimination")
        
        if not parts:
            parts.append("solid overall performance")
        
        return "Recommended due to " + ", ".join(parts)
    
    def get_topology_performance(self, topology_type: str) -> Optional[Dict]:
        """Get performance summary for specific topology type."""
        metrics = self.repo.metrics.get_by_type(self.db, topology_type)
        
        if not metrics:
            return None
        
        return {
            "topology_type": topology_type,
            "configurations": len(metrics),
            "avg_satisfaction_rate": sum(
                m.intent_satisfaction_rate for m in metrics if m.intent_satisfaction_rate
            ) / len([m for m in metrics if m.intent_satisfaction_rate]),
            "avg_validation_score": sum(
                m.avg_validation_score for m in metrics if m.avg_validation_score
            ) / len([m for m in metrics if m.avg_validation_score]),
            "best_config": max(
                metrics,
                key=lambda m: m.avg_validation_score or 0
            ) if metrics else None
        }
    
    def get_recommendations_for_intent(
        self,
        number_of_sites: int,
        redundancy_level: str,
        design_goal: str
    ) -> List[Dict]:
        """
        Get recommended topology types for specific intent parameters.
        
        This is used by the recommendation engine to suggest topologies.
        """
        # Query metrics matching these parameters
        matching_metrics = self.db.query(PerformanceMetrics).filter(
            and_(
                PerformanceMetrics.redundancy_level == redundancy_level,
                PerformanceMetrics.design_goal == design_goal,
                PerformanceMetrics.is_recommended == True
            )
        ).order_by(
            PerformanceMetrics.avg_validation_score.desc()
        ).all()
        
        recommendations = []
        for metric in matching_metrics:
            # Check if topology is suitable for number of sites
            if metric.sample_size > 0:  # Have data on this combination
                recommendations.append({
                    "topology_type": metric.topology_type,
                    "confidence": metric.confidence_score,
                    "validation_score": metric.avg_validation_score,
                    "satisfaction_rate": metric.intent_satisfaction_rate,
                    "reason": self._build_recommendation_reason(metric)
                })
        
        return recommendations
