"""
Autonomous optimizer - Automatically adjusts topology generation strategies based on historical performance.

Key functions:
1. Compare new intent with historical data
2. Identify topology choices with better historical performance
3. Auto-adjust generation parameters
4. Log optimization decisions for audit trail
5. Track improvement outcomes
"""

from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import OptimizationRepository, PerformanceMetricsRepository, DatabaseRepository
from app.database.models import PerformanceMetrics
from app.models import IntentRequest


class AutonomousOptimizer:
    """
    Automatically optimizes topology generation based on learned historical patterns.
    
    Integration point:
    - Called during topology generation after initial topology type is selected
    - Can recommend adjustment to topology type or parameters
    - Logs all optimization decisions for audit
    - Tracks actual improvements achieved
    """
    
    def __init__(self, db: Session):
        """Initialize optimizer with database session."""
        self.db = db
        self.repo = DatabaseRepository(db)
    
    def optimize_generation(
        self,
        intent: IntentRequest,
        initial_topology_type: str
    ) -> Tuple[str, Optional[Dict]]:
        """
        Analyze intent and potentially recommend optimized topology type.
        
        Args:
            intent: The IntentRequest to optimize
            initial_topology_type: Initially selected topology type
        
        Returns:
            Tuple of (recommended_topology_type, optimization_data)
            - recommended_topology_type: Type to use (may differ from initial)
            - optimization_data: Dict with optimization metadata if changed, None if no change
        """
        # Check if we have sufficient historical data
        historical_data = self._get_historical_performance(
            intent.redundancy_level.value,
            intent.design_goal.value
        )
        
        if not historical_data or len(historical_data) == 0:
            # No historical data to optimize from
            return initial_topology_type, None
        
        # Find best performer for this intent configuration
        best_topology = self._find_best_topology(historical_data)
        
        if best_topology is None:
            # No strong recommendations from history
            return initial_topology_type, None
        
        # Check if recommendation differs from initial
        if best_topology["topology_type"] == initial_topology_type:
            # Already chose the best option
            return initial_topology_type, None
        
        # We have a better option - log the optimization and return it
        optimization_data = {
            "original_topology_type": initial_topology_type,
            "optimized_topology_type": best_topology["topology_type"],
            "reason": best_topology["reason"],
            "historical_advantage": best_topology["advantage_description"],
            "expected_improvement": best_topology["expected_improvement"],
            "confidence_score": best_topology["confidence"]
        }
        
        # Log this optimization decision
        self._log_optimization(intent, initial_topology_type, optimization_data)
        
        return best_topology["topology_type"], optimization_data
    
    def _get_historical_performance(
        self,
        redundancy_level: str,
        design_goal: str
    ) -> list:
        """
        Get historical performance data for topology combinations matching these parameters.
        """
        metrics = self.db.query(PerformanceMetrics).filter(
            and_(
                PerformanceMetrics.redundancy_level == redundancy_level,
                PerformanceMetrics.design_goal == design_goal,
                PerformanceMetrics.sample_size > 0
            )
        ).all()
        
        return metrics
    
    def _find_best_topology(self, metrics_list: list) -> Optional[Dict]:
        """
        Find the best performing topology type from metrics list.
        
        Scoring logic:
        - Validation score (70% weight)
        - Intent satisfaction rate (20% weight)
        - Resilience (10% weight, lower=better)
        """
        if not metrics_list:
            return None
        
        scored_options = []
        
        for metrics in metrics_list:
            # Skip if not enough confidence
            if metrics.confidence_score < 40:
                continue
            
            # Calculate composite score
            validation_score = metrics.avg_validation_score or 0
            satisfaction_score = metrics.intent_satisfaction_rate or 0
            resilience_score = 100 - (metrics.failure_resilience or 0) if metrics.failure_resilience else 50
            
            composite_score = (
                validation_score * 0.70 +
                satisfaction_score * 0.20 +
                resilience_score * 0.10
            )
            
            scored_options.append({
                "topology_type": metrics.topology_type,
                "composite_score": composite_score,
                "validation_score": validation_score,
                "satisfaction_rate": satisfaction_score,
                "resilience_score": resilience_score,
                "confidence": metrics.confidence_score,
                "sample_size": metrics.sample_size
            })
        
        if not scored_options:
            return None
        
        # Sort by composite score
        scored_options.sort(key=lambda x: x["composite_score"], reverse=True)
        best = scored_options[0]
        
        # Build recommendation data
        return {
            "topology_type": best["topology_type"],
            "confidence": best["confidence"],
            "reason": f"Better validation score ({best['validation_score']:.1f}) and "
                     f"satisfaction rate ({best['satisfaction_rate']:.1f}%)",
            "advantage_description": (
                f"Historical data from {best['sample_size']} topologies shows "
                f"{best['topology_type']} achieves {best['composite_score']:.1f} "
                f"composite performance score"
            ),
            "expected_improvement": best["composite_score"]
        }
    
    def _log_optimization(
        self,
        intent: IntentRequest,
        original_topology: str,
        optimization_data: Dict
    ):
        """Log the optimization decision for audit trail."""
        intent_params = {
            "intent_name": intent.intent_name,
            "number_of_sites": intent.number_of_sites,
            "redundancy_level": intent.redundancy_level.value,
            "design_goal": intent.design_goal.value,
            "max_hops": intent.max_hops,
            "minimize_spof": intent.minimize_spof
        }
        
        self.repo.optimization.log_optimization(
            db=self.db,
            intent_parameters=intent_params,
            original_topology_type=original_topology,
            optimization_applied="topology_type_selection",
            adjusted_topology_type=optimization_data["optimized_topology_type"],
            reason=optimization_data["reason"],
            historical_advantage=optimization_data["historical_advantage"],
            expected_improvement=optimization_data["expected_improvement"]
        )
    
    def get_optimization_summary(self) -> Dict:
        """Get summary of optimization activities."""
        all_optimizations = self.repo.optimization.get_recent(self.db, limit=1000)
        
        # Count by original and adjusted types
        changes = {}
        total = len(all_optimizations)
        
        for opt in all_optimizations:
            key = f"{opt.original_topology_type} → {opt.adjusted_topology_type}"
            changes[key] = changes.get(key, 0) + 1
        
        # Get improvements
        improvements = self.repo.optimization.get_improvements(self.db, limit=20)
        
        return {
            "total_optimizations": total,
            "changes_made": changes,
            "measured_improvements": [
                {
                    "original": opt.original_topology_type,
                    "optimized": opt.adjusted_topology_type,
                    "actual_improvement_percent": opt.actual_improvement
                }
                for opt in improvements
            ],
            "avg_improvement": (
                sum(opt.actual_improvement or 0 for opt in improvements) / len(improvements)
                if improvements else 0
            )
        }
    
    def evaluate_optimization_outcome(
        self,
        optimization_id: int,
        original_validation_score: float,
        new_validation_score: float
    ):
        """Evaluate the outcome of an optimization decision."""
        optimization = self.db.query(
            __import__('app.database.models', fromlist=['OptimizationLog']).OptimizationLog
        ).filter(
            __import__('app.database.models', fromlist=['OptimizationLog']).OptimizationLog.id == optimization_id
        ).first()
        
        if optimization:
            improvement = ((new_validation_score - original_validation_score) / 
                          original_validation_score * 100) if original_validation_score > 0 else 0
            
            optimization.actual_improvement = improvement
            self.db.commit()


class AdaptiveGenerationRules:
    """
    Encapsulates rules for adaptive topology generation based on learning.
    
    Can be extended to modify generation parameters without changing topology type.
    """
    
    @staticmethod
    def get_link_budget_adjustment(
        topology_type: str,
        intent_redundancy: str,
        historical_data: Optional[Dict] = None
    ) -> float:
        """
        Determine optimal link budget multiplier based on topology type and history.
        
        Returns float multiplier (e.g., 1.1 for +10% more links)
        """
        base_multipliers = {
            "full_mesh": 1.0,      # Already optimal
            "leaf_spine": 1.0,     # Fixed pattern
            "tree": 0.95,          # Can be slightly reduced
            "ring": 1.05,          # May need extra links for redundancy
            "hub_spoke": 0.9,      # Minimal links
            "hybrid": 1.0
        }
        
        redundancy_adjustments = {
            "minimum": 0.85,
            "standard": 1.0,
            "high": 1.15,
            "critical": 1.30
        }
        
        base = base_multipliers.get(topology_type, 1.0)
        adjustment = redundancy_adjustments.get(intent_redundancy, 1.0)
        
        return base * adjustment
    
    @staticmethod
    def get_spof_elimination_aggressive(
        topology_type: str,
        intent_minimize_spof: bool,
        historical_spof_rate: Optional[float] = None
    ) -> bool:
        """
        Determine if aggressive SPOF elimination should be applied.
        
        Returns True if should be aggressive in eliminating SPOFs.
        """
        # If user explicitly wants SPOF minimization
        if intent_minimize_spof:
            return True
        
        # If history shows this topology has SPOF issues (>30% rate)
        if historical_spof_rate and historical_spof_rate > 30:
            return True
        
        return False
