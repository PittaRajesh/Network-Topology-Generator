"""FastAPI routes for topology generation and configuration."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import TopologyRequest, Topology, IntentRequest
from app.generator import TopologyGenerator
from app.core import ConfigurationGenerator
from app.deployment import DeploymentExporter
from app.database import get_db
from app.api.pipeline import PipelineOrchestrator, PipelineRequest, PipelineResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["topology"])

# Initialize generators and exporters
topology_generator = TopologyGenerator()
config_generator = ConfigurationGenerator()
deployment_exporter = DeploymentExporter()
pipeline_orchestrator = PipelineOrchestrator()


# ============================================================================
# Pipeline Orchestration Endpoints
# ============================================================================

@router.post(
    "/run-pipeline",
    response_model=PipelineResponse,
    summary="Execute Complete Networking Automation Pipeline",
    description="Automatically execute the full workflow: topology generation, configuration generation, "
                "Containerlab export, and topology analysis",
    tags=["pipeline"]
)
async def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    """
    Execute the complete networking automation pipeline.
    
    This endpoint orchestrates the entire workflow:
    1. Generate Network Topology - Creates a random but valid network topology
    2. Generate Configurations - Creates OSPF routing configs using Jinja2 templates
    3. Export Containerlab YAML - Exports topology in Containerlab format for deployment
    4. Run Analysis - Performs comprehensive topology analysis
    
    Args:
        request: PipelineRequest with topology generation and deployment parameters
            - topology_name: Name for the generated topology
            - num_routers: Number of routers (2-20)
            - num_switches: Number of switches (0-10)
            - seed: Optional seed for reproducible generation
            - container_image: Container image for Containerlab nodes
            - run_analysis: Whether to perform topology analysis
    
    Returns:
        PipelineResponse containing:
        - pipeline_id: Unique execution identifier
        - execution_timestamp: When the pipeline started
        - total_duration_seconds: Total execution time
        - overall_status: success, partial_success, or failed
        - stages: Results from each pipeline stage
        - summary: High-level summary of generated topology and analysis results
    
    Raises:
        HTTPException: If pipeline execution fails
    
    Example:
        POST /api/v1/run-pipeline
        {
            "topology_name": "production-topology",
            "num_routers": 5,
            "num_switches": 3,
            "run_analysis": true
        }
    """
    try:
        logger.info(f"Starting pipeline execution for topology '{request.topology_name}'")
        
        # Execute the pipeline
        pipeline_result = pipeline_orchestrator.run(request)
        
        logger.info(
            f"Pipeline execution completed with status '{pipeline_result.overall_status}' "
            f"in {pipeline_result.total_duration_seconds:.2f} seconds"
        )
        
        return pipeline_result
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@router.post(
    "/topology/generate",
    response_model=Topology,
    summary="Generate Network Topology",
    description="Generate a random but valid network topology with routers and switches"
)
async def generate_topology(request: TopologyRequest) -> Topology:
    """
    Generate a new network topology.
    
    Args:
        request: TopologyRequest with configuration parameters
    
    Returns:
        Generated Topology object
    
    Raises:
        HTTPException: If topology generation fails
    """
    try:
        logger.info(
            f"Generating topology '{request.name}' with "
            f"{request.num_routers} routers and {request.num_switches} switches"
        )
        
        generator = TopologyGenerator(seed=request.seed)
        topology = generator.generate(
            topology_name=request.name,
            num_routers=request.num_routers,
            num_switches=request.num_switches
        )
        
        logger.info(f"Successfully generated topology with {len(topology.devices)} devices "
                   f"and {len(topology.links)} links")
        
        return topology
        
    except ValueError as e:
        logger.error(f"Validation error during topology generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during topology generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate topology")


@router.post(
    "/configuration/generate",
    summary="Generate OSPF Configuration",
    description="Generate OSPF routing configurations for a topology"
)
async def generate_configuration(topology: Topology) -> dict:
    """
    Generate routing configuration for a topology.
    
    Args:
        topology: Topology object
    
    Returns:
        Dictionary with OSPF configurations and device configs
    
    Raises:
        HTTPException: If configuration generation fails
    """
    try:
        logger.info(f"Generating OSPF configuration for topology '{topology.name}'")
        
        # Generate routing configuration
        routing_config = config_generator.generate_ospf_configs(topology)
        
        # Generate device-specific configurations
        device_configs = deployment_exporter.generate_all_device_configs(routing_config)
        
        logger.info(f"Generated configurations for {len(device_configs)} devices")
        
        return {
            "topology_name": topology.name,
            "routing_protocol": "ospf",
            "num_devices": len(topology.devices),
            "device_configurations": {
                name: {
                    "device_name": name,
                    "config_preview": config[:500] + "..." if len(config) > 500 else config
                }
                for name, config in device_configs.items()
            },
            "full_configurations": device_configs
        }
        
    except Exception as e:
        logger.error(f"Error generating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate configuration")


@router.post(
    "/topology/export/containerlab",
    summary="Export Containerlab Topology",
    description="Export topology in Containerlab-compatible YAML format"
)
async def export_containerlab(
    topology: Topology,
    image: str = Query("frrouting/frr:latest", description="Container image")
) -> dict:
    """
    Export topology for Containerlab deployment.
    
    Args:
        topology: Topology object
        image: Container image to use
    
    Returns:
        Containerlab topology configuration
    
    Raises:
        HTTPException: If export fails
    """
    try:
        logger.info(f"Exporting topology '{topology.name}' to Containerlab format")
        
        containerlab_config = deployment_exporter.export_containerlab_topology(
            topology,
            image=image
        )
        
        logger.info(f"Successfully exported topology with {len(containerlab_config['topology']['nodes'])} nodes")
        
        return containerlab_config
        
    except Exception as e:
        logger.error(f"Error exporting topology: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export topology")


@router.post(
    "/topology/export/yaml",
    summary="Export Topology YAML",
    description="Export topology in universal YAML format"
)
async def export_topology_yaml(topology: Topology) -> dict:
    """
    Export topology as YAML.
    
    Args:
        topology: Topology object
    
    Returns:
        YAML content as dictionary
    """
    try:
        logger.info(f"Exporting topology '{topology.name}' to YAML format")
        
        yaml_content = deployment_exporter.export_to_yaml(topology)
        
        return {
            "topology_name": topology.name,
            "yaml_content": yaml_content,
            "format": "yaml"
        }
        
    except Exception as e:
        logger.error(f"Error exporting YAML: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export YAML")


@router.get(
    "/stats/topology",
    summary="Get Topology Statistics",
    description="Get statistics about a topology"
)
async def get_topology_stats(topology: Topology) -> dict:
    """
    Get statistics about topology connectivity.
    
    Args:
        topology: Topology object
    
    Returns:
        Dictionary with topology statistics
    """
    from app.models import DeviceType
    
    routers = [d for d in topology.devices if d.device_type == DeviceType.ROUTER]
    switches = [d for d in topology.devices if d.device_type == DeviceType.SWITCH]
    
    # Count link types
    router_links = sum(
        1 for l in topology.links
        if l.source_device in [r.name for r in routers] and
           l.destination_device in [r.name for r in routers]
    )
    
    return {
        "topology_name": topology.name,
        "total_devices": len(topology.devices),
        "routers": len(routers),
        "switches": len(switches),
        "total_links": len(topology.links),
        "router_to_router_links": router_links,
        "average_links_per_device": len(topology.links) * 2 / len(topology.devices) if topology.devices else 0,
    }


# ============================================================================
# AI-Assisted Analysis, Simulation, and Optimization Endpoints
# ============================================================================

@router.post(
    "/analyze/topology",
    summary="Analyze Network Topology",
    description="Perform AI-assisted analysis to detect issues and assess topology health",
    tags=["analysis"]
)
async def analyze_topology(topology: Topology):
    """
    Perform comprehensive topology analysis.
    
    Detects:
    - Single points of failure
    - Unbalanced routing paths
    - Overloaded nodes
    - Network metrics and health score
    
    Args:
        topology: Topology object to analyze
    
    Returns:
        TopologyAnalysisResult with findings and recommendations
    
    Raises:
        HTTPException: If analysis fails
    """
    try:
        from app.analysis import TopologyAnalyzer
        
        logger.info(f"Analyzing topology '{topology.name}'")
        
        analyzer = TopologyAnalyzer(topology)
        result = analyzer.analyze()
        
        logger.info(f"Analysis complete: {result.total_issues} issues found, "
                   f"health score {result.overall_health_score}/100")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing topology: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze topology")


@router.post(
    "/analyze/topology/visualize",
    summary="Visualize Network Topology",
    description="Generate visualization data for the topology graph",
    tags=["analysis"]
)
async def visualize_topology(topology: Topology):
    """
    Generate visualization data for a topology.
    
    Returns graph nodes and edges suitable for frontend visualization.
    
    Args:
        topology: Topology object
    
    Returns:
        TopologyVisualization with nodes, edges, and layout hints
    """
    try:
        from app.analysis import TopologyAnalyzer
        
        logger.info(f"Generating visualization for topology '{topology.name}'")
        
        analyzer = TopologyAnalyzer(topology)
        visualization = analyzer.visualize()
        
        return visualization
        
    except Exception as e:
        logger.error(f"Error visualizing topology: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to visualize topology")


@router.post(
    "/simulate/failure",
    summary="Simulate Network Failure",
    description="Simulate network failures and analyze their impact",
    tags=["simulation"]
)
async def simulate_failure(
    topology: Topology,
    failed_device: str = Query(..., description="Device/link name to fail"),
):
    """
    Simulate the failure of a network device or link.
    
    Analyzes:
    - Impact on connectivity
    - Affected routes
    - Recovery possibilities
    - Severity assessment
    
    Args:
        topology: Topology object
        failed_device: Device or link to simulate failure of
    
    Returns:
        FailureSimulationResult with impact analysis
    
    Raises:
        HTTPException: If simulation fails
    """
    try:
        from app.simulation import FailureSimulator
        from app.models.simulation import FailureRequest, FailureType
        
        logger.info(f"Simulating failure of {failed_device}")
        
        simulator = FailureSimulator(topology)
        
        # Determine failure type
        device_names = {d.name for d in topology.devices}
        if failed_device in device_names:
            failure_type = FailureType.ROUTER_FAILURE
        else:
            failure_type = FailureType.LINK_FAILURE
        
        failure_request = FailureRequest(
            failure_type=failure_type,
            failed_element=failed_device
        )
        
        result = simulator.simulate_failure([failure_request])
        
        logger.info(f"Simulation complete: {result.scenario_severity} severity")
        
        return result
        
    except Exception as e:
        logger.error(f"Error simulating failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to simulate failure")


@router.post(
    "/simulate/test-scenarios",
    summary="Generate Test Scenarios",
    description="Generate recommended failure test scenarios for topology",
    tags=["simulation"]
)
async def generate_test_scenarios(topology: Topology):
    """
    Generate recommended failure test scenarios.
    
    Creates scenarios to validate:
    - Resilience to single device failures
    - Multiple failure scenarios
    - Recovery time expectations
    
    Args:
        topology: Topology object
    
    Returns:
        List of TestScenario objects
    """
    try:
        from app.simulation import FailureSimulator
        
        logger.info(f"Generating test scenarios for topology '{topology.name}'")
        
        simulator = FailureSimulator(topology)
        scenarios = simulator.generate_test_scenarios()
        
        logger.info(f"Generated {len(scenarios)} test scenarios")
        
        return {
            "topology_name": topology.name,
            "scenarios": scenarios,
            "count": len(scenarios),
            "description": "Test scenarios to validate network resilience"
        }
        
    except Exception as e:
        logger.error(f"Error generating scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate test scenarios")


@router.post(
    "/optimize/topology",
    summary="Optimize Network Topology",
    description="Analyze topology and provide optimization recommendations",
    tags=["optimization"]
)
async def optimize_topology(topology: Topology):
    """
    Analyze topology and recommend optimizations.
    
    Provides recommendations for:
    - Eliminating single points of failure
    - Improving redundancy
    - Optimizing routing costs
    - Balancing node capacity
    
    Args:
        topology: Topology object to optimize
    
    Returns:
        TopologyOptimizationResult with recommendations
    
    Raises:
        HTTPException: If optimization analysis fails
    """
    try:
        from app.optimization import TopologyOptimizer
        
        logger.info(f"Optimizing topology '{topology.name}'")
        
        optimizer = TopologyOptimizer(topology)
        result = optimizer.optimize()
        
        logger.info(f"Optimization analysis complete: "
                   f"{result.total_recommendations} recommendations, "
                   f"{result.optimization_potential:.1f}% improvement potential")
        
        return result
        
    except Exception as e:
        logger.error(f"Error optimizing topology: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to optimize topology")


@router.post(
    "/optimize/proposal",
    summary="Generate Optimized Topology Proposal",
    description="Generate a complete proposal for an optimized topology design",
    tags=["optimization"]
)
async def generate_optimization_proposal(topology: Topology):
    """
    Create a proposal for optimizing the topology.
    
    Includes:
    - Links to add/remove
    - Cost changes
    - Expected improvements
    - Implementation complexity
    
    Args:
        topology: Topology object
    
    Returns:
        OptimizedTopologyProposal with detailed changes
    """
    try:
        from app.optimization import TopologyOptimizer
        
        logger.info(f"Generating optimization proposal for '{topology.name}'")
        
        optimizer = TopologyOptimizer(topology)
        proposal = optimizer.propose_optimized_topology()
        
        logger.info(f"Proposal generated: {len(proposal.links_to_add)} links to add")
        
        return proposal
        
    except Exception as e:
        logger.error(f"Error generating proposal: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate proposal")


# ============================================================================
# Intent-Based Networking (IBN) Endpoints
# ============================================================================

@router.post(
    "/intent/generate",
    summary="Generate Topology from Intent",
    description="Generate network topology from high-level intent specification",
    tags=["intent"]
)
async def generate_from_intent(request: dict):
    """
    Generate a network topology from user intent.
    
    Users specify high-level networking goals (e.g., "highly available topology for 10 sites")
    rather than explicitly designing the network. The system automatically generates a
    topology that satisfies the intent requirements.
    
    Args:
        request: Dict containing IntentRequest with the following structure:
            {
                "intent_name": "string",
                "intent_description": "string",
                "topology_type": "full_mesh|hub_spoke|ring|tree|leaf_spine|hybrid",
                "number_of_sites": int (2-500),
                "redundancy_level": "minimum|standard|high|critical",
                "max_hops": int (2-10),
                "routing_protocol": "ospf|bgp",
                "design_goal": "cost_optimized|redundancy_focused|latency_optimized|scalability",
                "minimize_spof": bool,
                "minimum_connections_per_site": int (1-5)
            }
    
    Returns:
        Generated Topology that satisfies the intent
    
    Raises:
        HTTPException: If generation fails
    """
    try:
        from app.models.intent import IntentRequest
        from app.generator.intent_generator import IntentBasedTopologyGenerator
        from app.validation import IntentValidator
        
        # Parse request into IntentRequest
        intent = IntentRequest(**request)
        
        logger.info(f"Intent-based generation requested: {intent.intent_name}")
        
        # Generate topology from intent
        generator = IntentBasedTopologyGenerator()
        topology = generator.generate_from_intent(intent)
        
        # Validate the generated topology
        validator = IntentValidator()
        validation_result = validator.validate(topology, intent)
        
        logger.info(
            f"Generated topology from intent: {len(topology.devices)} devices, "
            f"{len(topology.links)} links, validation score: {validation_result.overall_score:.1f}/100"
        )
        
        return {
            "success": True,
            "message": "Topology generated from intent",
            "generated_topology": topology.dict(),
            "validation_result": validation_result.dict(),
        }
        
    except Exception as e:
        logger.error(f"Error generating topology from intent: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to generate from intent: {str(e)}")


@router.post(
    "/intent/validate",
    summary="Validate Intent Satisfaction",
    description="Validate whether a topology satisfies the specified intent",
    tags=["intent"]
)
async def validate_intent(intent_request: dict, topology_dict: dict):
    """
    Validate a topology against intent requirements.
    
    Args:
        intent_request: IntentRequest specification
        topology_dict: Generated topology to validate
    
    Returns:
        Validation result with constraint satisfaction details
    """
    try:
        from app.models.intent import IntentRequest
        from app.validation import IntentValidator
        
        # Parse inputs
        intent = IntentRequest(**intent_request)
        # Reconstruct topology from dict
        devices_data = topology_dict.get("devices", [])
        links_data = topology_dict.get("links", [])
        
        from app.models.topology import Device, Link
        devices = [Device(**d) for d in devices_data]
        links = [Link(**l) for l in links_data]
        
        topology = Topology(
            name=topology_dict.get("name", "topology"),
            devices=devices,
            links=links,
            routing_protocol=topology_dict.get("routing_protocol", "ospf")
        )
        
        # Validate
        validator = IntentValidator()
        validation_result = validator.validate(topology, intent)
        
        # Generate report
        report = validator.generate_report(topology, intent, validation_result)
        
        logger.info(f"Validation complete: satisfied={validation_result.intent_satisfied}")
        
        return {
            "validation_result": validation_result.dict(),
            "report": report.dict()
        }
        
    except Exception as e:
        logger.error(f"Error validating intent: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@router.post(
    "/intent/end-to-end",
    summary="Intent-Based Topology Generation with Validation",
    description="Complete end-to-end workflow: parse intent → generate topology → validate → report",
    tags=["intent"]
)
async def intent_end_to_end(request: dict):
    """
    Complete intent-based topology workflow in one call.
    
    This endpoint combines generation and validation, returning both the
    generated topology and the validation report in a single response.
    
    Args:
        request: IntentRequest specification
    
    Returns:
        Complete workflow result with topology and validation report
    """
    try:
        from app.models.intent import IntentRequest
        from app.generator.intent_generator import IntentBasedTopologyGenerator
        from app.validation import IntentValidator
        
        intent = IntentRequest(**request)
        
        logger.info(f"Starting intent end-to-end workflow: {intent.intent_name}")
        
        # Step 1: Generate topology
        generator = IntentBasedTopologyGenerator()
        topology = generator.generate_from_intent(intent)
        logger.info(f"Step 1 complete: Generated topology with {len(topology.devices)} devices")
        
        # Step 2: Validate topology
        validator = IntentValidator()
        validation_result = validator.validate(topology, intent)
        logger.info(f"Step 2 complete: Validation score {validation_result.overall_score:.1f}/100")
        
        # Step 3: Generate report
        report = validator.generate_report(topology, intent, validation_result)
        logger.info(f"Step 3 complete: Generated report {report.report_id}")
        
        return {
            "success": True,
            "workflow_stages": {
                "generation": "✓ Complete",
                "validation": "✓ Complete",
                "reporting": "✓ Complete"
            },
            "topology": topology.dict(),
            "validation_result": validation_result.dict(),
            "report": report.dict(),
            "summary": {
                "intent_satisfied": validation_result.intent_satisfied,
                "overall_score": validation_result.overall_score,
                "devices_generated": len(topology.devices),
                "links_generated": len(topology.links),
                "violations": validation_result.constraint_violations,
                "recommendations": validation_result.recommendations[:3],  # Top 3 recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Error in intent workflow: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Workflow failed: {str(e)}")


@router.get(
    "/intent/examples",
    summary="Get Intent Examples",
    description="Get example intent specifications for different scenarios",
    tags=["intent"]
)
async def get_intent_examples():
    """
    Return example intent specifications for common network scenarios.
    
    Returns:
        Dict with multiple example intents
    """
    examples = {
        "example_1_datacenter": {
            "intent_name": "Multi-Region Data Center Network",
            "intent_description": "Highly available network connecting 5 regional data centers with critical resilience",
            "topology_type": "leaf_spine",
            "number_of_sites": 5,
            "redundancy_level": "critical",
            "max_hops": 3,
            "routing_protocol": "ospf",
            "design_goal": "redundancy_focused",
            "minimize_spof": True,
            "minimum_connections_per_site": 4
        },
        "example_2_campus": {
            "intent_name": "Enterprise Campus Network",
            "intent_description": "Campus network with hierarchical design, balanced redundancy and cost",
            "topology_type": "tree",
            "number_of_sites": 15,
            "redundancy_level": "standard",
            "max_hops": 4,
            "routing_protocol": "ospf",
            "design_goal": "redundancy_focused",
            "minimize_spof": True,
            "minimum_connections_per_site": 2
        },
        "example_3_wan": {
            "intent_name": "Global WAN Network",
            "intent_description": "Wide-area network connecting 20 branch offices with optimized latency",
            "topology_type": "hub_spoke",
            "number_of_sites": 20,
            "redundancy_level": "standard",
            "max_hops": 5,
            "routing_protocol": "ospf",
            "design_goal": "latency_optimized",
            "minimize_spof": False,
            "minimum_connections_per_site": 1
        },
        "example_4_mesh": {
            "intent_name": "Full Mesh Critical Network",
            "intent_description": "Fully meshed network for maximum redundancy and low latency",
            "topology_type": "full_mesh",
            "number_of_sites": 8,
            "redundancy_level": "critical",
            "max_hops": 2,
            "routing_protocol": "ospf",
            "design_goal": "redundancy_focused",
            "minimize_spof": True,
            "minimum_connections_per_site": 7
        },
    }
    
    logger.info("Returning intent examples")
    return {"examples": examples}


# ==================== Learning & Recommendation Endpoints ====================

@router.post(
    "/learning/recommend-topology",
    summary="Recommend Topology Based on Historical Learning",
    description="Get intelligent topology recommendations based on historical performance data"
)
async def recommend_topology(intent: IntentRequest, db: Session = Depends(get_db)) -> dict:
    """
    Get topology recommendations based on historical learning data.
    
    This endpoint uses the learning engine to analyze historical topology generations,
    validations, and simulations to recommend the best topology type for the given intent.
    
    Args:
        intent: IntentRequest with high-level requirements
        db: Database session
    
    Returns:
        Dictionary with ranked topology recommendations and rationale
    
    Raises:
        HTTPException: If recommendation generation fails
    """
    try:
        logger.info(f"[API] Getting topology recommendations for intent: {intent.intent_name}")
        
        from app.history import HistoryManager
        from app.recommendation import RecommendationEngine
        
        # Initialize recommendation engine
        rec_engine = RecommendationEngine(db)
        
        # Get recommendations
        recommendations = rec_engine.recommend_topologies(intent, top_k=5)
        
        logger.info(f"[API] Generated {len(recommendations)} recommendations")
        
        return {
            "success": True,
            "intent_name": intent.intent_name,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[API] Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.get(
    "/learning/topology-history",
    summary="Get Topology Generation History",
    description="Retrieve historical topology generation data for analysis"
)
async def get_topology_history(
    topology_type: Optional[str] = Query(None, description="Filter by topology type"),
    redundancy_level: Optional[str] = Query(None, description="Filter by redundancy level"),
    days: int = Query(30, description="Days of history to retrieve"),
    limit: int = Query(100, description="Maximum results"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get historical topology generation data.
    
    Useful for analyzing patterns and understanding how topology recommendations
    have changed over time.
    
    Args:
        topology_type: Optional filter by topology type
        redundancy_level: Optional filter by redundancy level
        days: Number of days of history (default 30)
        limit: Maximum number of records
        db: Database session
    
    Returns:
        List of historical topology records with metadata and validation scores
    """
    try:
        logger.info(f"[API] Retrieving topology history (type={topology_type}, redundancy={redundancy_level})")
        
        from app.history import HistoryManager
        
        history_manager = HistoryManager(db)
        
        # Get appropriate history
        if topology_type or redundancy_level:
            history = history_manager.get_topology_history(
                topology_type=topology_type,
                redundancy_level=redundancy_level,
                limit=limit
            )
        else:
            history = history_manager.get_recent_history(days=days, limit=limit)
        
        # Get record counts
        counts = history_manager.get_total_records()
        
        logger.info(f"[API] Retrieved {len(history)} history records")
        
        return {
            "success": True,
            "history": history,
            "total_records": counts,
            "filters": {
                "topology_type": topology_type,
                "redundancy_level": redundancy_level,
                "days": days if not topology_type and not redundancy_level else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[API] Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.post(
    "/learning/learning-report",
    summary="Generate Learning & Optimization Report",
    description="Analyze all historical data and generate insights"
)
async def generate_learning_report(
    include_optimization_stats: bool = Query(True),
    db: Session = Depends(get_db)
) -> dict:
    """
    Generate comprehensive learning and optimization report.
    
    This endpoint:
    1. Analyzes all historical topology data
    2. Identifies best-performing configurations
    3. Tracks autonomous optimization decisions
    4. Provides recommendations for improvement
    
    Args:
        include_optimization_stats: Whether to include optimization log analysis
        db: Database session
    
    Returns:
        Comprehensive report with metrics, insights, and recommendations
    """
    try:
        logger.info("[API] Generating comprehensive learning report")
        
        from app.learning import LearningAnalyzer, AutonomousOptimizer
        
        # Initialize analyzers
        analyzer = LearningAnalyzer(db)
        optimizer = AutonomousOptimizer(db)
        
        # Run comprehensive analysis
        analysis = analyzer.analyze_all()
        
        # Get optimization summary if requested
        optimization_summary = None
        if include_optimization_stats:
            optimization_summary = optimizer.get_optimization_summary()
        
        # Build comprehensive report
        report = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "learning_analysis": {
                "total_topologies_analyzed": analysis["total_topologies_analyzed"],
                "unique_configurations": len(analysis["metrics"]),
                "top_insights": analysis["insights"][:3],  # Top 3 insights
                "recommended_configurations": analysis["recommendations"]
            },
            "optimization_activity": optimization_summary if optimization_summary else "No optimization data",
            "key_findings": _extract_key_findings(analysis, optimization_summary),
            "recommendations_for_future_generations": analyze["recommendations"]
        }
        
        logger.info(f"[API] Report generated with {len(analysis['metrics'])} analyzed configurations")
        
        return report
        
    except Exception as e:
        logger.error(f"[API] Error generating learning report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


def _extract_key_findings(analysis: dict, optimization_summary: Optional[dict]) -> dict:
    """Extract key findings from analysis data."""
    findings = {
        "most_analyzed_topologies": [],
        "highest_satisfaction_configs": [],
        "autonomic_optimizations_performed": 0
    }
    
    # Get top metrics by validation score
    metric_items = analysis.get("metrics", {}).items()
    sorted_metrics = sorted(
        metric_items,
        key=lambda x: x[1].get("avg_validation_score", 0) if isinstance(x[1], dict) else 0,
        reverse=True
    )
    
    # Top 3 highest satisfaction
    findings["highest_satisfaction_configs"] = [
        {
            "config": item[0],
            "score": item[1].get("avg_validation_score", 0) if isinstance(item[1], dict) else 0
        }
        for item in sorted_metrics[:3]
    ]
    
    # Optimization count
    if optimization_summary:
        findings["autonomic_optimizations_performed"] = optimization_summary.get("total_optimizations", 0)
    
    return findings

