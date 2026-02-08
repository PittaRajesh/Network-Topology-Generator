# Pipeline Orchestration Endpoint

## Overview

The `/run-pipeline` endpoint provides a unified interface to execute the entire networking automation workflow in a single request. This endpoint seamlessly orchestrates all stages of the automation process and returns comprehensive results.

## Endpoint Details

### Route
```
POST /api/v1/run-pipeline
```

### Request Model: `PipelineRequest`

```json
{
  "topology_name": "production-topology",
  "num_routers": 5,
  "num_switches": 3,
  "seed": null,
  "container_image": "frrouting/frr:latest",
  "run_analysis": true
}
```

#### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `topology_name` | string | Required | - | Name for the generated topology |
| `num_routers` | integer | 3 | 2-20 | Number of routers in the topology |
| `num_switches` | integer | 2 | 0-10 | Number of switches in the topology |
| `seed` | integer/null | null | - | Optional seed for reproducible generation |
| `container_image` | string | "frrouting/frr:latest" | - | Container image for Containerlab nodes |
| `run_analysis` | boolean | true | - | Whether to run topology analysis as final stage |

## Pipeline Stages

The orchestration executes the following stages sequentially:

### Stage 1: Topology Generation
- **Module**: `app.generator.TopologyGenerator`
- **What it does**:
  - Creates a valid network topology with specified routers and switches
  - Automatically allocates IP addresses
  - Generates OSPF router IDs
  - Ensures topological connectivity
- **Output**: `Topology` object with devices and links
- **Failure Handling**: Pipeline stops if this stage fails

### Stage 2: Configuration Generation
- **Module**: `app.core.ConfigurationGenerator` + `app.deployment.DeploymentExporter`
- **What it does**:
  - Generates OSPF routing configurations for all routers
  - Creates Jinja2-rendered device-specific configurations
  - Sets up interface IPs and OSPF networks
- **Output**: `RoutingConfig` and device-specific configurations
- **Failure Handling**: Pipeline continues with partial success status

### Stage 3: Containerlab Export
- **Module**: `app.deployment.DeploymentExporter`
- **What it does**:
  - Exports topology in Containerlab-compatible YAML format
  - Creates node definitions with container images
  - Defines inter-device links
- **Output**: Containerlab topology configuration dictionary
- **Failure Handling**: Pipeline continues with partial success status

### Stage 4: Topology Analysis
- **Module**: `app.analysis.TopologyAnalyzer`
- **What it does**:
  - Detects single points of failure (SPOFs)
  - Identifies unbalanced routing paths
  - Detects overloaded nodes
  - Calculates network health metrics
  - Generates comprehensive findings and recommendations
- **Output**: `TopologyAnalysisResult` with detailed analysis
- **Failure Handling**: Pipeline continues with partial success status (can be skipped with `run_analysis: false`)

## Response Model: `PipelineResponse`

```json
{
  "pipeline_id": "pipe_a1b2c3d4e5f6",
  "execution_timestamp": "2026-02-08T10:30:45.123456",
  "total_duration_seconds": 12.345,
  "overall_status": "success",
  "stages": {
    "topology_generation": {
      "stage_name": "topology_generation",
      "status": "success",
      "duration_seconds": 0.234,
      "data": null,
      "error_message": null
    },
    "configuration_generation": {
      "stage_name": "configuration_generation",
      "status": "success",
      "duration_seconds": 1.567,
      "data": null,
      "error_message": null
    },
    "containerlab_export": {
      "stage_name": "containerlab_export",
      "status": "success",
      "duration_seconds": 0.456,
      "data": null,
      "error_message": null
    },
    "topology_analysis": {
      "stage_name": "topology_analysis",
      "status": "success",
      "duration_seconds": 2.134,
      "data": null,
      "error_message": null
    }
  },
  "summary": {
    "topology_name": "production-topology",
    "total_devices": 8,
    "total_links": 12,
    "num_routers": 5,
    "num_switches": 3,
    "containerlab_nodes": 8,
    "analysis_health_score": 85,
    "analysis_issues_found": 2,
    "stages_completed": 4,
    "stages_failed": 0
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `pipeline_id` | string | Unique identifier for this pipeline execution |
| `execution_timestamp` | string | ISO 8601 timestamp when pipeline started |
| `total_duration_seconds` | float | Total execution time in seconds |
| `overall_status` | string | One of: `success`, `partial_success`, `failed` |
| `stages` | object | Results from each pipeline stage |
| `summary` | object | High-level summary of topology and analysis results |

#### Overall Status Values

- **`success`**: All requested stages completed successfully
- **`partial_success`**: Some stages failed but topology generation succeeded
- **`failed`**: Critical stage (topology generation) failed; pipeline stopped

## Usage Examples

### Example 1: Basic Topology with Full Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/run-pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "topology_name": "sample-network",
    "num_routers": 4,
    "num_switches": 2
  }'
```

### Example 2: Reproducible Generation with Custom Image

```bash
curl -X POST "http://localhost:8000/api/v1/run-pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "topology_name": "production-topology",
    "num_routers": 8,
    "num_switches": 4,
    "seed": 42,
    "container_image": "custom-frr:v8.0",
    "run_analysis": true
  }'
```

### Example 3: Skip Analysis for Faster Execution

```bash
curl -X POST "http://localhost:8000/api/v1/run-pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "topology_name": "quick-topology",
    "num_routers": 3,
    "num_switches": 1,
    "run_analysis": false
  }'
```

### Python Example

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def execute_pipeline(topology_name, num_routers, num_switches):
    """Execute the networking automation pipeline."""
    
    payload = {
        "topology_name": topology_name,
        "num_routers": num_routers,
        "num_switches": num_switches,
        "run_analysis": True
    }
    
    response = requests.post(
        f"{BASE_URL}/run-pipeline",
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Pipeline ID: {result['pipeline_id']}")
        print(f"Status: {result['overall_status']}")
        print(f"Duration: {result['total_duration_seconds']:.2f}s")
        print(f"Topology Summary:")
        print(f"  - Total Devices: {result['summary']['total_devices']}")
        print(f"  - Total Links: {result['summary']['total_links']}")
        print(f"  - Health Score: {result['summary']['analysis_health_score']}")
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Execute pipeline
result = execute_pipeline("my-topology", 5, 3)
```

## Error Handling

### Pipeline Failure Scenarios

1. **Invalid Request Parameters**
   - HTTP 400: Parameter validation fails
   - Check: num_routers (2-20), num_switches (0-10)

2. **Topology Generation Failure**
   - HTTP 500: Pipeline stops immediately
   - Overall status: `failed`
   - Check logs for topology generation issues

3. **Configuration/Export Stage Failures**
   - HTTP 200: Pipeline continues
   - Overall status: `partial_success`
   - Individual stage shows error_message
   - Topology is still available for inspection

4. **Analysis Stage Failure**
   - HTTP 200: Pipeline continues
   - Overall status: `partial_success`
   - All previous stages results available

### Debugging Failed Stages

Each stage result includes:
- `stage_name`: Which stage failed
- `status`: "failed"
- `error_message`: Specific error details
- `duration_seconds`: How long it ran before failing

Use these fields to identify and troubleshoot issues:

```json
{
  "stage_name": "containerlab_export",
  "status": "failed",
  "duration_seconds": 0.123,
  "error_message": "Invalid topology structure: missing device interfaces"
}
```

## Features and Design

### Production-Ready Implementation

1. **Modular Architecture**
   - Each stage uses existing service modules
   - No code duplication
   - Single responsibility per module

2. **Comprehensive Error Handling**
   - Graceful failure at each stage
   - Detailed error messages
   - Pipeline continues when possible

3. **Performance Monitoring**
   - Execution time per stage
   - Total pipeline duration
   - Useful for optimization and debugging

4. **Unique Pipeline Identification**
   - Each execution gets a unique `pipeline_id`
   - Enables tracking and auditing
   - Timestamp for temporal correlation

5. **Summary Statistics**
   - High-level topology metrics
   - Analysis results summary
   - Success/failure counts

### Reusability

The pipeline orchestrator internally reuses:
- `TopologyGenerator.generate()` - Topology generation
- `ConfigurationGenerator.generate_ospf_configs()` - Routing configuration
- `DeploymentExporter.export_containerlab_topology()` - Containerlab export
- `DeploymentExporter.generate_all_device_configs()` - Device configuration rendering
- `TopologyAnalyzer.analyze()` - Topology analysis

## Integration with Existing Endpoints

While the pipeline endpoint orchestrates the complete workflow, individual endpoints remain available for:

- **Incremental workflows**: Generate topology, then perform custom analysis
- **Custom configurations**: Generate topology, then use different routing protocols
- **Testing individual stages**: Verify each component independently

Example workflow comparison:

```
Individual Requests (3 calls):
1. POST /api/v1/topology/generate
2. POST /api/v1/configuration/generate
3. POST /api/v1/analyze/topology

Pipeline Request (1 call):
POST /api/v1/run-pipeline
```

## Monitoring and Logging

The pipeline uses comprehensive logging at each stage:

```
[Pipeline pipe_a1b2c3d4] Starting stage: topology generation
[Pipeline pipe_a1b2c3d4] Topology generated successfully with 8 devices and 12 links
[Pipeline pipe_a1b2c3d4] Starting stage: configuration generation
[Pipeline pipe_a1b2c3d4] Configuration generated for 5 devices
[Pipeline pipe_a1b2c3d4] Pipeline execution completed with status 'success' in 12.34 seconds
```

Configure logging level in `app/config/settings.py` to adjust verbosity.

## Future Enhancements

Potential improvements for future versions:

1. **Async Execution**: Run compatible stages in parallel
2. **Pipeline Templates**: Save and replay successful configurations
3. **Dynamic Stage Management**: Enable/disable specific stages
4. **Advanced Analytics**: Store pipeline execution history
5. **Notifications**: Webhook callbacks on stage completion
6. **Rollback Support**: Revert to previous topology state
7. **Custom Hooks**: Execute user code before/after stages
