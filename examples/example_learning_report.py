"""
Example 3: Learning Report & Digital Twin Analysis

Demonstrates how to:
1. Generate comprehensive learning reports
2. Analyze performance trends
3. Understand topology effectiveness
4. Make data-driven optimization decisions
"""

import json
from datetime import datetime

from app.database import Database
from app.models import IntentRequest
from app.generator import IntentBasedTopologyGenerator
from app.validation import IntentValidator
from app.history import HistoryManager
from app.learning import LearningAnalyzer


def example_3_learning_report():
    """
    Demonstrate learning analysis and reporting:
    Transform raw generation data into actionable insights
    """
    print("\n" + "="*80)
    print("Example 3: Learning Report & Digital Twin Analysis")
    print("="*80)
    
    # Initialize
    Database.initialize()
    db = Database.get_session()
    
    try:
        history_mgr = HistoryManager(db)
        generator = IntentBasedTopologyGenerator(seed=456)
        validator = IntentValidator()
        analyzer = LearningAnalyzer(db)
        
        # ============ Step 1: Generate Diverse Topologies ============
        print("\n[Step 1] Generating diverse topologies for comprehensive learning...")
        
        configs = [
            ("tree", 10, "standard", "cost_optimized"),
            ("tree", 20, "standard", "redundancy_focused"),
            ("tree", 15, "high", "redundancy_focused"),
            ("leaf_spine", 8, "critical", "redundancy_focused"),
            ("leaf_spine", 12, "standard", "cost_optimized"),
            ("hub_spoke", 20, "standard", "cost_optimized"),
            ("full_mesh", 6, "critical", "redundancy_focused"),
            ("ring", 10, "standard", "cost_optimized"),
        ]
        
        for topology_type, num_sites, redundancy, design_goal in configs:
            intent = IntentRequest(
                intent_name=f"{topology_type.upper()} {redundancy}",
                intent_description=f"Test topology: {topology_type} with {redundancy} redundancy",
                topology_type=topology_type,
                number_of_sites=num_sites,
                redundancy_level=redundancy,
                routing_protocol="ospf",
                design_goal=design_goal,
                minimize_spof=redundancy == "critical",
                minimum_connections_per_site=1 if redundancy == "minimum" else 2,
                max_hops=5,
                max_links=300,
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
        
        print(f"  Generated {len(configs)} test topologies")
        
        # ============ Step 2: Run Learning Analyzer ============
        print("\n[Step 2] Running comprehensive learning analysis...")
        
        analysis = analyzer.analyze_all()
        
        print(f"\n  Analysis Results:")
        print(f"    Total topologies analyzed: {analysis['total_topologies_analyzed']}")
        print(f"    Unique configuration combinations: {len(analysis['metrics'])}")
        
        # ============ Step 3: Display Key Insights ============
        print("\n[Step 3] Key Insights from Learning Data...")
        
        if analysis['insights']:
            print(f"\n  Top Insights ({len(analysis['insights'])} found):")
            for idx, insight in enumerate(analysis['insights'], 1):
                print(f"\n    {idx}. {insight['title']}")
                print(f"       {insight['insight']}")
                print(f"       (Type: {insight['type']})")
        
        # ============ Step 4: Top Recommendations ============
        print("\n[Step 4] Top Recommended Configurations...")
        
        if analysis['recommendations']:
            print(f"\n  Best Performing Configurations ({len(analysis['recommendations'])} recommendations):")
            for idx, rec in enumerate(analysis['recommendations'], 1):
                print(f"\n    {idx}. {rec['topology_type'].upper()} | {rec['redundancy_level']} | {rec['design_goal']}")
                print(f"       Average Score: {rec['avg_score']:.1f}/100")
                print(f"       Intent Satisfaction Rate: {rec['satisfaction_rate']:.1f}%")
                print(f"       Confidence: {rec['confidence']:.1f}%")
                print(f"       Reason: {rec['reason']}")
        
        # ============ Step 5: Detailed Metrics ============
        print("\n[Step 5] Detailed Performance Metrics by Configuration...")
        
        metric_items = analysis.get('metrics', {})
        if metric_items:
            # Sort by validation score
            sorted_metrics = sorted(
                metric_items.items(),
                key=lambda x: x[1].get('avg_validation_score', 0) if isinstance(x[1], dict) else 0,
                reverse=True
            )
            
            print(f"\n  Top 5 Performing Configurations:")
            for idx, (config_key, metrics) in enumerate(sorted_metrics[:5], 1):
                if isinstance(metrics, dict):
                    print(f"\n    {idx}. {config_key}")
                    print(f"       Validation Score: {metrics.get('avg_validation_score', 'N/A'):.1f}")
                    print(f"       Redundancy Score: {metrics.get('avg_redundancy_score', 'N/A'):.1f}")
                    print(f"       Path Diversity: {metrics.get('avg_path_diversity', 'N/A'):.1f}")
                    print(f"       Failure Resilience: {metrics.get('failure_resilience', 'N/A'):.1f}")
                    print(f"       SPOF Elimination Rate: {metrics.get('spof_elimination_rate', 'N/A'):.1f}%")
                    print(f"       Intent Satisfaction: {metrics.get('intent_satisfaction_rate', 'N/A'):.1f}%")
                    print(f"       Sample Size: {metrics.get('sample_size', 'N/A')}")
                    print(f"       Recommended: {metrics.get('is_recommended', False)}")
        
        # ============ Step 6: Topology Performance Summary ============
        print("\n[Step 6] Topology Type Performance Summary...")
        
        topology_types = set()
        metric_items = analysis.get('metrics', {})
        for config_key in metric_items.keys():
            parts = config_key.split('_')
            if parts:
                topology_types.add(parts[0])
        
        print(f"\n  Performance by Topology Type:")
        for ttype in sorted(topology_types):
            perf_data = analyzer.get_topology_performance(ttype)
            if perf_data:
                print(f"\n    {ttype.upper()}")
                print(f"      Configurations tested: {perf_data['configurations']}")
                print(f"      Avg Validation Score: {perf_data['avg_validation_score']:.1f}/100")
                print(f"      Avg Satisfaction Rate: {perf_data['avg_satisfaction_rate']:.1f}%")
                if perf_data['best_config']:
                    print(f"      Best Config: {perf_data['best_config'].redundancy_level} redundancy, " +
                          f"{perf_data['best_config'].design_goal} goal")
        
        # ============ Summary ============
        print("\n" + "="*80)
        print("Digital Twin Learning Report Summary:")
        print("="*80)
        print("\nWhat This Report Tells Us:")
        print("✓ Best topology types for different requirements")
        print("✓ Performance patterns based on real data")
        print("✓ Confidence levels in recommendations")
        print("✓ Trends and validation effectiveness")
        print("✓ Risk identification (low-performing configs)")
        
        print("\nBusiness Value:")
        print("• Make topology decisions based on proven data")
        print("• Reduce deployment risk through learned patterns")
        print("• Identify and avoid anti-patterns")
        print("• Faster recommendations as confidence improves")
        print("• Measurable ROI from learning system")
        
        print("\nNext Steps:")
        print("• Monitor recommendations vs. user selections")
        print("• Track actual vs. predicted performance")
        print("• Continuously refine learning model")
        print("• Export data for BI/analytics tools")
        
        print("="*80 + "\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    example_3_learning_report()
