"""
Recommendation engine - Generates topology recommendations based on historical learning data.

Key functions:
1. Score topology options based on historical performance
2. Generate ranked list of recommendations
3. Provide confidence scores and reasoning
4. Track recommendation accuracy
5. Adapt recommendations based on feedback
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.database import RecommendationRepository, PerformanceMetricsRepository, DatabaseRepository
from app.database.models import PerformanceMetrics
from app.models import IntentRequest
from app.learning.analyzer import LearningAnalyzer


class RecommendationEngine:
    """
    Generates intelligent topology recommendations for user intents.
    
    Recommendations are based on:
    - Historical validation scores
    - Previous intent satisfaction rates
    - Failure resilience data
    - Design goal optimization history
    
    Integration point:
    - Called when user requests recommendations without specifying topology type
    - Returns ranked list of options with confidence scores
    - Tracks user feedback to improve future recommendations
    """
    
    def __init__(self, db: Session):
        """Initialize recommendation engine with database session."""
        self.db = db
        self.repo = DatabaseRepository(db)
        self.analyzer = LearningAnalyzer(db)
    
    def recommend_topologies(
        self,
        intent: IntentRequest,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Generate topology recommendations for a given intent.
        
        Args:
            intent: User's IntentRequest
            top_k: Number of recommendations to return
        
        Returns:
            List of recommendations with scores and reasoning
        """
        print(f"[Recommender] Generating recommendations for intent: {intent.intent_name}")
        
        # Get all known topology types
        all_topologies = self._get_all_topology_types()
        
        scored_recommendations = []
        
        for topology_type in all_topologies:
            # Score this topology for the given intent
            score_data = self._score_topology_for_intent(
                topology_type,
                intent.redundancy_level.value,
                intent.design_goal.value,
                intent.number_of_sites
            )
            
            if score_data:
                scored_recommendations.append(score_data)
        
        # Sort by overall score
        scored_recommendations.sort(
            key=lambda x: x["overall_score"],
            reverse=True
        )
        
        # Take top K
        top_recommendations = scored_recommendations[:top_k]
        
        print(f"[Recommender] Generated {len(top_recommendations)} recommendations")
        
        return top_recommendations
    
    def _get_all_topology_types(self) -> List[str]:
        """Get all known topology types from database."""
        query = self.db.query(
            __import__('app.database.models', fromlist=['TopologyRecord']).TopologyRecord.topology_type
        ).distinct()
        
        types = [row[0] for row in query.all()]
        
        # Ensure common types are included even if no history
        common_types = [
            "full_mesh", "hub_spoke", "ring", "tree", "leaf_spine", "hybrid"
        ]
        
        for ttype in common_types:
            if ttype not in types:
                types.append(ttype)
        
        return types
    
    def _score_topology_for_intent(
        self,
        topology_type: str,
        redundancy_level: str,
        design_goal: str,
        number_of_sites: int
    ) -> Optional[Dict]:
        """
        Score a specific topology for the given intent parameters.
        
        Returns:
            Scoring dictionary or None if not applicable
        """
        # Get performance metrics for this combination
        metrics = self.db.query(PerformanceMetrics).filter(
            __import__('sqlalchemy', fromlist=['and_']).and_(
                PerformanceMetrics.topology_type == topology_type,
                PerformanceMetrics.redundancy_level == redundancy_level,
                PerformanceMetrics.design_goal == design_goal
            )
        ).first()
        
        # Check if topology is suitable for site count
        suitability = self._check_topology_suitability(topology_type, number_of_sites)
        
        if not suitability["suitable"]:
            return None
        
        # Build score from metrics if available
        if metrics and metrics.sample_size > 0:
            overall_score = self._calculate_overall_score(metrics)
            confidence = metrics.confidence_score
            reason = self._build_recommendation_reason(metrics, topology_type, design_goal)
        else:
            # No historical data - use heuristic scoring
            overall_score = self._heuristic_score(topology_type, redundancy_level, design_goal)
            confidence = 30.0  # Low confidence without data
            reason = self._build_heuristic_reason(topology_type, redundancy_level)
        
        # Apply suitability factor
        overall_score *= suitability["suitability_factor"]
        
        return {
            "topology_type": topology_type,
            "overall_score": round(overall_score, 2),
            "confidence": round(confidence, 2),
            "suitability": round(suitability["suitability_factor"] * 100, 1),
            "pros": self._get_topology_pros(topology_type, metrics),
            "cons": self._get_topology_cons(topology_type, metrics),
            "recommendation_reason": reason,
            "based_on_history": metrics is not None and metrics.sample_size > 0,
            "estimated_links": self._estimate_link_count(topology_type, number_of_sites),
            "typical_diameter": self._get_typical_diameter(topology_type)
        }
    
    def _check_topology_suitability(
        self,
        topology_type: str,
        number_of_sites: int
    ) -> Dict:
        """
        Check if topology is suitable for number of sites.
        
        Returns dict with 'suitable' (bool) and 'suitability_factor' (0.5-1.0)
        """
        suitability_ranges = {
            "full_mesh": {"min": 3, "max": 10, "ideal": 6},
            "hub_spoke": {"min": 3, "max": 500, "ideal": 20},
            "ring": {"min": 3, "max": 100, "ideal": 10},
            "tree": {"min": 5, "max": 500, "ideal": 50},
            "leaf_spine": {"min": 4, "max": 500, "ideal": 30},
            "hybrid": {"min": 5, "max": 500, "ideal": 100}
        }
        
        ranges = suitability_ranges.get(topology_type)
        if not ranges:
            return {"suitable": True, "suitability_factor": 1.0}
        
        # Check if within range
        if number_of_sites < ranges["min"] or number_of_sites > ranges["max"]:
            return {"suitable": False, "suitability_factor": 0.0}
        
        # Calculate suitability factor (closer to ideal = higher)
        ideal = ranges["ideal"]
        distance_from_ideal = abs(number_of_sites - ideal)
        max_distance = max(ideal - ranges["min"], ranges["max"] - ideal)
        
        suitability_factor = 1.0 - (distance_from_ideal / max_distance * 0.5)
        
        return {"suitable": True, "suitability_factor": max(0.5, suitability_factor)}
    
    def _calculate_overall_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate overall recommendation score from metrics."""
        # Weighted combination of metrics
        validation_score = (metrics.avg_validation_score or 0) * 0.40  # 40%
        satisfaction_score = (metrics.intent_satisfaction_rate or 0) * 0.35  # 35%
        resilience_score = (100 - (metrics.failure_resilience or 50)) * 0.25  # 25% (inverted, lower=better)
        
        overall = validation_score + satisfaction_score + resilience_score
        
        return min(100, overall)  # Cap at 100
    
    def _heuristic_score(
        self,
        topology_type: str,
        redundancy_level: str,
        design_goal: str
    ) -> float:
        """
        Calculate score using heuristics when no historical data available.
        Base compatibility scoring.
        """
        base_scores = {
            "full_mesh": 85,
            "leaf_spine": 82,
            "tree": 78,
            "ring": 75,
            "hub_spoke": 65,
            "hybrid": 80
        }
        
        score = base_scores.get(topology_type, 70)
        
        # Adjust for redundancy level match
        redundancy_bonuses = {
            "critical": {"full_mesh": 10, "leaf_spine": 12, "tree": 5, "ring": 8},
            "high": {"full_mesh": 8, "leaf_spine": 10, "tree": 5, "ring": 6},
            "standard": {"tree": 10, "leaf_spine": 8, "hybrid": 8},
            "minimum": {"hub_spoke": 10, "ring": 5}
        }
        
        bonus = redundancy_bonuses.get(redundancy_level, {}).get(topology_type, 0)
        score += bonus
        
        return min(100, score)
    
    def _build_recommendation_reason(
        self,
        metrics: PerformanceMetrics,
        topology_type: str,
        design_goal: str
    ) -> str:
        """Build human-readable recommendation reason."""
        parts = []
        
        # Validation score
        if metrics.avg_validation_score:
            if metrics.avg_validation_score >= 85:
                parts.append(f"excellent validation ({metrics.avg_validation_score:.0f})")
            elif metrics.avg_validation_score >= 75:
                parts.append(f"good validation ({metrics.avg_validation_score:.0f})")
        
        # Intent satisfaction
        if metrics.intent_satisfaction_rate:
            if metrics.intent_satisfaction_rate >= 90:
                parts.append(f"high intent satisfaction ({metrics.intent_satisfaction_rate:.0f}%)")
            elif metrics.intent_satisfaction_rate >= 75:
                parts.append(f"reliable intent satisfaction ({metrics.intent_satisfaction_rate:.0f}%)")
        
        # Resilience
        if metrics.failure_resilience is not None:
            if metrics.failure_resilience <= 20:
                parts.append("strong failure resilience")
            elif metrics.failure_resilience <= 35:
                parts.append("good resilience")
        
        # SPOF
        if metrics.spof_elimination_rate and metrics.spof_elimination_rate >= 80:
            parts.append("effective SPOF elimination")
        
        if not parts:
            parts.append("proven performance")
        
        return f"Recommended based on {', and '.join(parts)}"
    
    def _build_heuristic_reason(self, topology_type: str, redundancy_level: str) -> str:
        """Build reason when using heuristic scoring."""
        return f"Standard recommendation for {redundancy_level} redundancy with {topology_type} topology"
    
    def _get_topology_pros(
        self,
        topology_type: str,
        metrics: Optional[PerformanceMetrics] = None
    ) -> List[str]:
        """Get list of pros for topology type."""
        base_pros = {
            "full_mesh": [
                "Maximum redundancy and path diversity",
                "Minimal hop count (always 2 or less)",
                "No single points of failure"
            ],
            "hub_spoke": [
                "Low link count and cost",
                "Easy to manage and expand",
                "Suitable for large branch networks"
            ],
            "ring": [
                "Moderate redundancy with minimal links",
                "Scalable to hundreds of devices",
                "Low cost compared to mesh"
            ],
            "tree": [
                "Hierarchical and organized structure",
                "Scalable to thousands of devices",
                "Core can be mesh for redundancy while access is simple"
            ],
            "leaf_spine": [
                "Data center optimized",
                "Predictable latency (always 3 hops max)",
                "High throughput for East-West traffic",
                "Excellent for large-scale deployments"
            ],
            "hybrid": [
                "Flexible topology combining multiple patterns",
                "Optimizable per layer",
                "Suitable for complex organizations"
            ]
        }
        
        pros = base_pros.get(topology_type, [])
        
        # Add metrics-based pros if available
        if metrics:
            if metrics.intent_satisfaction_rate and metrics.intent_satisfaction_rate >= 85:
                pros.append(f"Historically satisfies user intents {metrics.intent_satisfaction_rate:.0f}% of the time")
            if metrics.failure_resilience and metrics.failure_resilience <= 25:
                pros.append("Proven resilience to common failure scenarios")
        
        return pros
    
    def _get_topology_cons(
        self,
        topology_type: str,
        metrics: Optional[PerformanceMetrics] = None
    ) -> List[str]:
        """Get list of cons for topology type."""
        base_cons = {
            "full_mesh": [
                "High link count and cost",
                "Not suitable for networks >15 devices",
                "Complex configuration management"
            ],
            "hub_spoke": [
                "Central hub is single point of failure",
                "All traffic must pass through hub",
                "Hub becomes bottleneck at scale"
            ],
            "ring": [
                "Limited path diversity for non-adjacent devices",
                "Not ideal for critical applications",
                "Failure creates larger impact zones"
            ],
            "tree": [
                "Potential SPOFs at aggregation layer",
                "More complex than simpler topologies",
                "May require careful redundancy design"
            ],
            "leaf_spine": [
                "Higher link count than hierarchical designs",
                "Requires equal-cost multipath routing",
                "More complex switch configuration"
            ],
            "hybrid": [
                "More complex to manage",
                "Harder to optimize uniformly",
                "Requires expertise to balance correctly"
            ]
        }
        
        cons = base_cons.get(topology_type, [])
        
        # Add metrics-based cons if available
        if metrics:
            if metrics.failure_resilience and metrics.failure_resilience > 50:
                cons.append("Shows lower resilience to failures in historical data")
            if metrics.spof_elimination_rate and metrics.spof_elimination_rate < 50:
                cons.append("Often contains hard-to-eliminate SPOFs")
        
        return cons
    
    @staticmethod
    def _estimate_link_count(topology_type: str, number_of_sites: int) -> str:
        """Estimate expected link count for topology."""
        if topology_type == "full_mesh":
            estimate = (number_of_sites * (number_of_sites - 1)) // 2
        elif topology_type == "hub_spoke":
            estimate = number_of_sites - 1
        elif topology_type == "ring":
            estimate = number_of_sites
        elif topology_type == "tree":
            estimate = number_of_sites - 1  # For tree structure
        elif topology_type == "leaf_spine":
            leaves = int(number_of_sites * 0.6)
            spines = int(number_of_sites * 0.4)
            estimate = leaves * spines
        else:  # hybrid
            estimate = int(number_of_sites * 1.5)
        
        return f"~{estimate} links"
    
    @staticmethod
    def _get_typical_diameter(topology_type: str) -> str:
        """Get typical maximum hop count for topology."""
        diameters = {
            "full_mesh": "2",
            "hub_spoke": "3",
            "ring": "varies (N/2 max)",
            "tree": "varies (5-7 typical)",
            "leaf_spine": "3",
            "hybrid": "varies"
        }
        return diameters.get(topology_type, "varies")
    
    def record_recommendation_feedback(
        self,
        recommendation_id: int,
        feedback_score: int,
        user_selected_topology: Optional[str] = None,
        resulted_topology_id: Optional[int] = None
    ):
        """
        Record user feedback on recommendation.
        
        Args:
            recommendation_id: ID of recommendation
            feedback_score: User rating (1-5 stars, or -1 for no feedback)
            user_selected_topology: Which topology user selected
            resulted_topology_id: ID of resulting topology record
        """
        self.repo.recommendation.update_feedback(
            db=self.db,
            recommendation_id=recommendation_id,
            feedback_score=feedback_score,
            user_selected=user_selected_topology,
            topology_id=resulted_topology_id
        )
