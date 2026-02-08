"""
Example 2: Autonomous Optimization Workflow

Demonstrates how to:
1. Generate topologies with autonomous optimization enabled
2. Watch system automatically improve choices based on history
3. Track optimization decisions and outcomes
4. Measure actual improvements
"""

import logging
from sqlalchemy.orm import Session

from app.database import Database
from app.models import IntentRequest
from app.generator import IntentBasedTopologyGenerator
from app.validation import IntentValidator
from app.history import HistoryManager
from app.learning import AutonomousOptimizer
from app.recommendation import RecommendationEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_2_autonomous_optimization():
    """
    Demonstrate autonomous optimization:
    As system learns, it auto-adjusts topology choices for better outcomes
    """
    print("\n" + "="*80)
    print("Example 2: Autonomous Optimization Workflow")
    print("="*80)
    
    # Initialize
    Database.initialize()
    db = Database.get_session()
    
    try:
        history_mgr = HistoryManager(db)
        generator = IntentBasedTopologyGenerator(seed=123)
        validator = IntentValidator()
        optimizer = AutonomousOptimizer(db)
        
        # ============ Step 1: Build Learning History ============
        print("\n[Step 1] Building historical learning data...")
        
        # Generate several hub_spoke and tree topologies to establish patterns
        test_intents = [
            {
                "intent_name": "Test Hub-Spoke 1",
                "topology_type": "hub_spoke",
                "number_of_sites": 10,
                "redundancy_level": "standard"
            },
            {
                "intent_name": "Test Hub-Spoke 2",
                "topology_type": "hub_spoke",
                "number_of_sites": 15,
                "redundancy_level": "standard"
            },
            {
                "intent_name": "Test Tree 1",
                "topology_type": "tree",
                "number_of_sites": 10,
                "redundancy_level": "standard"
            },
            {
                "intent_name": "Test Tree 2",
                "topology_type": "tree",
                "number_of_sites": 15,
                "redundancy_level": "standard"
            }
        ]
        
        for test in test_intents:
            intent = IntentRequest(
                intent_name=test["intent_name"],
                intent_description="Historical data for learning",
                topology_type=test["topology_type"],
                number_of_sites=test["number_of_sites"],
                redundancy_level=test["redundancy_level"],
                routing_protocol="ospf",
                design_goal="cost_optimized",
                minimize_spof=False,
                minimum_connections_per_site=1,
                max_hops=5,
                max_links=200,
                link_speed="1Gbps",
                custom_constraints={}
            )
            
            topology = generator.generate_from_intent(intent)
            topology_id = history_mgr.record_topology_generation(intent, topology)
            
            validation = validator.validate(topology, intent)
            history_mgr.record_validation_result(
                topology_id=topology_id,
                intent_satisfied=validation.intent_satisfied,
                overall_score=validation.overall_score,
                redundancy_score=validation.redundancy_score,
                path_diversity_score=validation.path_diversity_score,
                hop_count_satisfied=validation.hop_count_satisfied,
                spof_eliminated=validation.spof_eliminated,
                topology_matched=validation.topology_matched
            )
            
            print(f"  Created: {test['intent_name']} (Score: {validation.overall_score:.1f})")
        
        # ============ Step 2: Demonstrate Optimization ============
        print("\n[Step 2] Testing autonomous optimization...")
        
        new_intent = IntentRequest(
            intent_name="Critical Branch Network",
            intent_description="10-site branch network needing reliability",
            topology_type="hub_spoke",  # User chose hub_spoke
            number_of_sites=10,
            redundancy_level="standard",
            routing_protocol="ospf",
            design_goal="cost_optimized",
            minimize_spof=False,
            minimum_connections_per_site=1,
            max_hops=5,
            max_links=200,
            link_speed="1Gbps",
            custom_constraints={}
        )
        
        print(f"\n  User's request:")
        print(f"    Intent: {new_intent.intent_name}")
        print(f"    Sites: {new_intent.number_of_sites}")
        print(f"    Redundancy: {new_intent.redundancy_level.value}")
        print(f"    Initial topology choice: {new_intent.topology_type.value}")
        
        # Apply optimization
        optimized_topology_type, optimization_data = optimizer.optimize_generation(
            new_intent,
            new_intent.topology_type.value
        )
        
        if optimization_data:
            print(f"\n  ✓ Optimizer recommended change!")
            print(f"    Original: {optimization_data['original_topology_type']}")
            print(f"    Optimized: {optimization_data['optimized_topology_type']}")
            print(f"    Reason: {optimization_data['reason']}")
            print(f"    Expected improvement: {optimization_data['expected_improvement']:.1f}%")
            print(f"    Historical advantage: {optimization_data['historical_advantage']}")
        else:
            print(f"\n  No optimization recommended")
            print(f"  Reason: Insufficient historical data for topology type")
        
        # Generate with optimized selection
        print(f"\n  Generating topology with recommendation...")
        topology = generator.generate_from_intent(new_intent, topology_type=optimized_topology_type)
        topology_id = history_mgr.record_topology_generation(new_intent, topology)
        
        # Validate optimized topology
        validation = validator.validate(topology, new_intent)
        history_mgr.record_validation_result(
            topology_id=topology_id,
            intent_satisfied=validation.intent_satisfied,
            overall_score=validation.overall_score,
            redundancy_score=validation.redundancy_score,
            path_diversity_score=validation.path_diversity_score,
            hop_count_satisfied=validation.hop_count_satisfied,
            spof_eliminated=validation.spof_eliminated,
            topology_matched=validation.topology_matched
        )
        
        print(f"\n  Optimized topology validation:")
        print(f"    Type: {optimized_topology_type}")
        print(f"    Score: {validation.overall_score:.1f}/100")
        print(f"    Satisfied: {validation.intent_satisfied}")
        
        # ============ Step 3: Show Optimization Summary ============
        print("\n[Step 3] Showing optimization summary...")
        
        summary = optimizer.get_optimization_summary()
        
        print(f"\n  Total optimizations performed: {summary['total_optimizations']}")
        if summary['changes_made']:
            print(f"  Changes made:")
            for change, count in sorted(summary['changes_made'].items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"    • {change}: {count} times")
        
        if summary['measured_improvements']:
            print(f"\n  Measured improvements:")
            for imp in summary['measured_improvements'][:3]:
                print(f"    • {imp['original']} → {imp['optimized']}: +{imp['actual_improvement_percent']:.1f}%")
            print(f"  Average improvement: {summary['avg_improvement']:.1f}%")
        
        # ============ Summary ============
        print("\n" + "="*80)
        print("Autonomous Optimization Summary:")
        print("="*80)
        print("Key Capabilities Demonstrated:")
        print("✓ System analyzes historical performance data")
        print("✓ Automatically identifies better topology choices")
        print("✓ Logs optimization decisions with rationale")
        print("✓ Tracks expected vs actual improvements")
        print("✓ Continuously learns and refines recommendations")
        print("\nBusiness Impact:")
        print("• Better topology choices without manual design")
        print("• Measurable improvement in validation scores")
        print("• Reduced time to deploy networks")
        print("• Documented audit trail of decisions")
        print("="*80 + "\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    example_2_autonomous_optimization()
