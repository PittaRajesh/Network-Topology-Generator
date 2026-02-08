"""
Example 1: Learning-Based Recommendation Workflow

Demonstrates how to:
1. Generate topologies and record in history
2. Validate and record results
3. Run learning analyzer
4. Get recommendations based on history
5. Track improvements
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import Database, get_db
from app.models import IntentRequest
from app.generator import IntentBasedTopologyGenerator
from app.validation import IntentValidator
from app.history import HistoryManager
from app.learning import LearningAnalyzer
from app.recommendation import RecommendationEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_learning_workflow():
    """
    Demonstrate complete learning workflow:
    Multiple topology generations → Learn patterns → Recommend for new intent
    """
    print("\n" + "="*80)
    print("Example 1: Learning-Based Topology Recommendation Workflow")
    print("="*80)
    
    # Initialize database and components
    Database.initialize()
    db = Database.get_session()
    
    try:
        history_mgr = HistoryManager(db)
        generator = IntentBasedTopologyGenerator(seed=42)
        validator = IntentValidator()
        
        # ============ Phase 1: Generate Multiple Topologies (Learning Data) ============
        print("\n[Phase 1] Generating 3 tree-based topologies for learning...")
        
        topology_ids = []
        base_intent = {
            "intent_name": "Campus Network Variant",
            "intent_description": "Build campus network with varying sizes",
            "number_of_sites": 15,
            "redundancy_level": "standard",
            "routing_protocol": "ospf",
            "design_goal": "redundancy_focused",
            "minimize_spof": True,
            "minimum_connections_per_site": 2,
            "max_hops": 4,
            "max_links": 150,
            "link_speed": "1Gbps",
            "custom_constraints": {}
        }
        
        for i in range(3):
            # Create slight variation of intent
            intent_dict = base_intent.copy()
            intent_dict["intent_name"] = f"Campus Variant {i+1}"
            intent_dict["number_of_sites"] = 10 + (i * 5)  # 10, 15, 20 sites
            
            intent = IntentRequest(**intent_dict)
            
            # Generate topology
            print(f"\n  Generating topology {i+1}: {intent.intent_name} with {intent.number_of_sites} sites")
            topology = generator.generate_from_intent(intent)
            
            # Record in history
            topology_id = history_mgr.record_topology_generation(intent, topology, intent_dict)
            topology_ids.append(topology_id)
            
            # Validate
            validation = validator.validate(topology, intent)
            history_mgr.record_validation_result(
                topology_id=topology_id,
                intent_satisfied=validation.intent_satisfied,
                overall_score=validation.overall_score,
                redundancy_score=validation.redundancy_score,
                path_diversity_score=validation.path_diversity_score,
                hop_count_satisfied=validation.hop_count_satisfied,
                spof_eliminated=validation.spof_eliminated,
                topology_matched=validation.topology_matched,
                constraint_violations=validation.constraint_violations
            )
            
            print(f"    ✓ Topology recorded (ID: {topology_id})")
            print(f"    ✓ Validation score: {validation.overall_score:.1f}/100")
            print(f"    ✓ Intent satisfied: {validation.intent_satisfied}")
        
        # ============ Phase 2: Run Learning Analyzer ============
        print("\n[Phase 2] Running learning analyzer on historical data...")
        
        analyzer = LearningAnalyzer(db)
        analysis = analyzer.analyze_all()
        
        print(f"  Total topologies analyzed: {analysis['total_topologies_analyzed']}")
        print(f"  Unique configurations: {len(analysis['metrics'])}")
        
        if analysis['insights']:
            print("\n  Top Insights:")
            for insight in analysis['insights'][:3]:
                print(f"    • {insight['title']}: {insight['insight']}")
        
        # ============ Phase 3: Get Recommendations for New Intent ============
        print("\n[Phase 3] Getting recommendations for new intent (based on learned patterns)...")
        
        rec_engine = RecommendationEngine(db)
        
        # New intent similar to learned patterns
        new_intent = IntentRequest(
            intent_name="New Campus Network",
            intent_description="Another campus with 18 sites needing standard redundancy",
            number_of_sites=18,
            redundancy_level="standard",
            routing_protocol="ospf",
            design_goal="redundancy_focused",
            minimize_spof=True,
            minimum_connections_per_site=2,
            max_hops=4,
            max_links=150,
            topology_type="tree",  # Will be overridden by recommendation
            link_speed="1Gbps",
            custom_constraints={}
        )
        
        recommendations = rec_engine.recommend_topologies(new_intent, top_k=3)
        
        print(f"\n  Top 3 Recommendations for '{new_intent.intent_name}':")
        for idx, rec in enumerate(recommendations, 1):
            print(f"\n  {idx}. {rec['topology_type'].upper()}")
            print(f"     Score: {rec['overall_score']:.1f}/100")
            print(f"     Confidence: {rec['confidence']:.1f}%")
            print(f"     Suitability: {rec['suitability']:.1f}%")
            print(f"     Rationale: {rec['recommendation_reason']}")
            print(f"     Based on history: {rec['based_on_history']}")
        
        # ============ Phase 4: Show History ============
        print("\n[Phase 4] Retrieving generated topology history...")
        
        history = history_mgr.get_recent_history(days=1, limit=10)
        print(f"\n  Recent topologies generated:")
        for item in history:
            print(f"    • {item['intent_name']}")
            print(f"      Type: {item['topology_type']}, Validation Score: {item['validation_score']:.1f}")
        
        # ============ Summary ============
        print("\n" + "="*80)
        print("Learning Workflow Summary:")
        print("="*80)
        print(f"✓ Generated {len(topology_ids)} topologies")
        print(f"✓ Stored in database with full validation data")
        print(f"✓ Learning analyzer identified {len(analysis['metrics'])} configuration patterns")
        print(f"✓ Generated {len(recommendations)} recommendations for new intent")
        print(f"✓ Confidence scores based on {analysis['total_topologies_analyzed']} historical records")
        print("\nKey Learning Insight:")
        print(f"  The system can now recommend topologies automatically based on")
        print(f"  proven historical performance. Confidence improves with more data.")
        print("="*80 + "\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    example_1_learning_workflow()
