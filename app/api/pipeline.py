"""Pipeline orchestration module for executing complete networking workflows."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models import TopologyRequest, Topology
from app.generator import TopologyGenerator
from app.core import ConfigurationGenerator
from app.deployment import DeploymentExporter
from app.analysis import TopologyAnalyzer

logger = logging.getLogger(__name__)


class PipelineRequest(BaseModel):
    """Request model for pipeline orchestration."""
    topology_name: str = Field(..., description="Name for the generated topology")
    num_routers: int = Field(
        default=3,
        ge=2,
        le=20,
        description="Number of routers (2-20)"
    )
    num_switches: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Number of switches (0-10)"
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducible topology generation"
    )
    container_image: str = Field(
        "frrouting/frr:latest",
        description="Container image for Containerlab nodes"
    )
    run_analysis: bool = Field(
        True,
        description="Whether to run topology analysis as final stage"
    )


class PipelineStageResult(BaseModel):
    """Result from a single pipeline stage."""
    stage_name: str
    status: str = "success"  # success, failed, skipped
    duration_seconds: float
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class PipelineResponse(BaseModel):
    """Complete response from pipeline execution."""
    pipeline_id: str
    execution_timestamp: str
    total_duration_seconds: float
    overall_status: str  # success, partial_success, failed
    stages: Dict[str, PipelineStageResult]
    summary: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class PipelineOrchestrator:
    """
    Orchestrates the complete network automation workflow.
    
    Manages the following stages:
    1. Topology generation
    2. Configuration generation (OSPF routing)
    3. Containerlab export
    4. Topology analysis
    
    Each stage builds on the output of the previous stage.
    """

    def __init__(self):
        """Initialize the pipeline orchestrator with service modules."""
        self.topology_generator = TopologyGenerator()
        self.config_generator = ConfigurationGenerator()
        self.deployment_exporter = DeploymentExporter()
    
    def run(self, request: PipelineRequest) -> PipelineResponse:
        """
        Execute the complete networking automation pipeline.
        
        Args:
            request: PipelineRequest with topology and deployment parameters
        
        Returns:
            PipelineResponse with results from all stages
        """
        pipeline_id = self._generate_pipeline_id()
        start_time = datetime.now()
        stages = {}
        overall_status = "success"
        topology = None
        routing_config = None
        containerlab_config = None
        analysis_result = None
        
        try:
            # Stage 1: Generate Topology
            logger.info(f"[Pipeline {pipeline_id}] Starting stage: topology generation")
            try:
                topology, stage_result = self._run_stage(
                    "topology_generation",
                    self._generate_topology,
                    request
                )
                stages["topology_generation"] = stage_result
                logger.info(f"[Pipeline {pipeline_id}] Topology generated successfully with "
                           f"{len(topology.devices)} devices and {len(topology.links)} links")
            except Exception as e:
                logger.error(f"[Pipeline {pipeline_id}] Topology generation failed: {str(e)}")
                stages["topology_generation"] = PipelineStageResult(
                    stage_name="topology_generation",
                    status="failed",
                    duration_seconds=0,
                    error_message=str(e)
                )
                overall_status = "failed"
                return self._build_response(pipeline_id, start_time, stages, overall_status)
            
            # Stage 2: Generate Configurations (OSPF and device configs)
            logger.info(f"[Pipeline {pipeline_id}] Starting stage: configuration generation")
            try:
                routing_config, device_configs, stage_result = self._run_stage(
                    "configuration_generation",
                    self._generate_configurations,
                    topology
                )
                stages["configuration_generation"] = stage_result
                logger.info(f"[Pipeline {pipeline_id}] Configuration generated for "
                           f"{len(device_configs)} devices")
            except Exception as e:
                logger.error(f"[Pipeline {pipeline_id}] Configuration generation failed: {str(e)}")
                stages["configuration_generation"] = PipelineStageResult(
                    stage_name="configuration_generation",
                    status="failed",
                    duration_seconds=0,
                    error_message=str(e)
                )
                overall_status = "partial_success"
            
            # Stage 3: Export to Containerlab format
            logger.info(f"[Pipeline {pipeline_id}] Starting stage: containerlab export")
            try:
                containerlab_config, stage_result = self._run_stage(
                    "containerlab_export",
                    self._export_containerlab,
                    topology,
                    request.container_image
                )
                stages["containerlab_export"] = stage_result
                logger.info(f"[Pipeline {pipeline_id}] Containerlab export completed with "
                           f"{len(containerlab_config.get('topology', {}).get('nodes', {}))} nodes")
            except Exception as e:
                logger.error(f"[Pipeline {pipeline_id}] Containerlab export failed: {str(e)}")
                stages["containerlab_export"] = PipelineStageResult(
                    stage_name="containerlab_export",
                    status="failed",
                    duration_seconds=0,
                    error_message=str(e)
                )
                overall_status = "partial_success"
            
            # Stage 4: Run Topology Analysis
            if request.run_analysis:
                logger.info(f"[Pipeline {pipeline_id}] Starting stage: topology analysis")
                try:
                    analysis_result, stage_result = self._run_stage(
                        "topology_analysis",
                        self._analyze_topology,
                        topology
                    )
                    stages["topology_analysis"] = stage_result
                    logger.info(f"[Pipeline {pipeline_id}] Analysis complete: "
                               f"health_score={analysis_result.overall_health_score}, "
                               f"issues_found={analysis_result.total_issues}")
                except Exception as e:
                    logger.error(f"[Pipeline {pipeline_id}] Topology analysis failed: {str(e)}")
                    stages["topology_analysis"] = PipelineStageResult(
                        stage_name="topology_analysis",
                        status="failed",
                        duration_seconds=0,
                        error_message=str(e)
                    )
                    overall_status = "partial_success"
            
        except Exception as e:
            logger.error(f"[Pipeline {pipeline_id}] Unexpected error in pipeline: {str(e)}")
            overall_status = "failed"
        
        return self._build_response(
            pipeline_id, 
            start_time, 
            stages, 
            overall_status,
            topology=topology,
            routing_config=routing_config,
            containerlab_config=containerlab_config,
            analysis_result=analysis_result
        )
    
    def _generate_topology(self, request: PipelineRequest) -> Topology:
        """Generate network topology."""
        generator = TopologyGenerator(seed=request.seed)
        return generator.generate(
            topology_name=request.topology_name,
            num_routers=request.num_routers,
            num_switches=request.num_switches
        )
    
    def _generate_configurations(self, topology: Topology) -> tuple:
        """Generate OSPF and device-specific configurations."""
        routing_config = self.config_generator.generate_ospf_configs(topology)
        device_configs = self.deployment_exporter.generate_all_device_configs(routing_config)
        return routing_config, device_configs
    
    def _export_containerlab(self, topology: Topology, image: str) -> dict:
        """Export topology in Containerlab format."""
        return self.deployment_exporter.export_containerlab_topology(
            topology=topology,
            image=image
        )
    
    def _analyze_topology(self, topology: Topology):
        """Perform comprehensive topology analysis."""
        analyzer = TopologyAnalyzer(topology)
        return analyzer.analyze()
    
    def _run_stage(self, stage_name: str, func, *args) -> tuple:
        """
        Execute a pipeline stage and measure execution time.
        
        Args:
            stage_name: Name of the stage
            func: Function to execute
            *args: Arguments to pass to the function
        
        Returns:
            Tuple of (result, stage_result)
        """
        start_time = datetime.now()
        try:
            result = func(*args)
            duration = (datetime.now() - start_time).total_seconds()
            
            stage_result = PipelineStageResult(
                stage_name=stage_name,
                status="success",
                duration_seconds=duration
            )
            
            return result, stage_result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            raise Exception(f"Stage {stage_name} failed: {str(e)}")
    
    def _generate_pipeline_id(self) -> str:
        """Generate a unique pipeline execution ID."""
        from uuid import uuid4
        return f"pipe_{uuid4().hex[:12]}"
    
    def _build_response(
        self,
        pipeline_id: str,
        start_time: datetime,
        stages: Dict[str, PipelineStageResult],
        overall_status: str,
        topology: Optional[Topology] = None,
        routing_config: Optional[Any] = None,
        containerlab_config: Optional[dict] = None,
        analysis_result: Optional[Any] = None
    ) -> PipelineResponse:
        """
        Build the final pipeline response.
        
        Args:
            pipeline_id: Unique pipeline execution ID
            start_time: Pipeline start time
            stages: Dictionary of stage results
            overall_status: Overall execution status
            topology: Generated topology object
            routing_config: Generated routing configuration
            containerlab_config: Containerlab export configuration
            analysis_result: Topology analysis result
        
        Returns:
            PipelineResponse with complete execution summary
        """
        total_duration = (datetime.now() - start_time).total_seconds()
        
        # Build summary with stage success counts
        summary = {
            "topology_name": topology.name if topology else None,
            "total_devices": len(topology.devices) if topology else 0,
            "total_links": len(topology.links) if topology else 0,
            "num_routers": topology.num_routers if topology else 0,
            "num_switches": topology.num_switches if topology else 0,
            "containerlab_nodes": len(
                containerlab_config.get("topology", {}).get("nodes", {})
            ) if containerlab_config else 0,
            "analysis_health_score": (
                analysis_result.overall_health_score if analysis_result else None
            ),
            "analysis_issues_found": (
                analysis_result.total_issues if analysis_result else None
            ),
            "stages_completed": sum(
                1 for s in stages.values() if s.status == "success"
            ),
            "stages_failed": sum(
                1 for s in stages.values() if s.status == "failed"
            ),
        }
        
        return PipelineResponse(
            pipeline_id=pipeline_id,
            execution_timestamp=start_time.isoformat(),
            total_duration_seconds=total_duration,
            overall_status=overall_status,
            stages=stages,
            summary=summary
        )
