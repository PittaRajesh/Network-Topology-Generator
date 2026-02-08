# Pipeline Orchestration - Live Demo Guide

This guide shows how to run and demonstrate the `/run-pipeline` endpoint for an interviewer.

## Quick Start (5 minutes)

### 1. Start the FastAPI Application

```bash
# Navigate to project directory
cd networking-automation-engine

# Option A: Using Python directly
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option B: Using the provided run script
./run.sh  # Linux/Mac
./run.ps1 # Windows PowerShell
./run.bat # Windows CMD
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 2. Open API Documentation

Open your browser and navigate to:
```
http://localhost:8000/docs
```

This opens Swagger UI where you can see all endpoints including `/run-pipeline`.

## Demo Scenario

### Scenario: "Generate a complete network topology and run the full analysis"

#### Option 1: Using Swagger UI (Easiest for Interview)

1. Navigate to `http://localhost:8000/docs`
2. Find the **POST /api/v1/run-pipeline** endpoint
3. Click **"Try it out"**
4. Enter the following JSON in the request body:

```json
{
  "topology_name": "production-network",
  "num_routers": 4,
  "num_switches": 2,
  "seed": 42,
  "container_image": "frrouting/frr:latest",
  "run_analysis": true
}
```

5. Click **"Execute"**
6. Show the response to the interviewer

**Expected Response** (shown in real-time):
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
      "duration_seconds": 0.234
    },
    "configuration_generation": {
      "stage_name": "configuration_generation",
      "status": "success",
      "duration_seconds": 1.567
    },
    "containerlab_export": {
      "stage_name": "containerlab_export",
      "status": "success",
      "duration_seconds": 0.456
    },
    "topology_analysis": {
      "stage_name": "topology_analysis",
      "status": "success",
      "duration_seconds": 2.134
    }
  },
  "summary": {
    "topology_name": "production-network",
    "total_devices": 6,
    "total_links": 8,
    "num_routers": 4,
    "num_switches": 2,
    "containerlab_nodes": 6,
    "analysis_health_score": 87,
    "analysis_issues_found": 1,
    "stages_completed": 4,
    "stages_failed": 0
  }
}
```

#### Option 2: Using cURL (Shows Technical Knowledge)

Open a terminal and run:

```bash
curl -X POST "http://localhost:8000/api/v1/run-pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "topology_name": "demo-topology",
    "num_routers": 5,
    "num_switches": 3,
    "seed": 123,
    "run_analysis": true
  }'
```

#### Option 3: Using Python (Shows Programming Skills)

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def demo_pipeline():
    """Demonstrate the complete pipeline orchestration."""
    
    payload = {
        "topology_name": "interview-demo",
        "num_routers": 4,
        "num_switches": 2,
        "seed": 42,
        "run_analysis": True
    }
    
    print("🚀 Starting Pipeline Orchestration...")
    print(f"Request: {json.dumps(payload, indent=2)}\n")
    
    response = requests.post(f"{BASE_URL}/run-pipeline", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ Pipeline Execution Completed!")
        print(f"\n📊 Results:")
        print(f"  Pipeline ID: {result['pipeline_id']}")
        print(f"  Status: {result['overall_status']}")
        print(f"  Total Duration: {result['total_duration_seconds']:.2f}s")
        
        print(f"\n📈 Generated Topology:")
        summary = result['summary']
        print(f"  Topology Name: {summary['topology_name']}")
        print(f"  Total Devices: {summary['total_devices']}")
        print(f"  Total Links: {summary['total_links']}")
        print(f"  Routers: {summary['num_routers']}")
        print(f"  Switches: {summary['num_switches']}")
        
        print(f"\n🔍 Analysis Results:")
        print(f"  Health Score: {summary['analysis_health_score']}/100")
        print(f"  Issues Found: {summary['analysis_issues_found']}")
        
        print(f"\n⚙️  Pipeline Stages:")
        for stage_name, stage in result['stages'].items():
            status_icon = "✅" if stage['status'] == 'success' else "❌"
            print(f"  {status_icon} {stage_name}: {stage['duration_seconds']:.3f}s")
        
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    demo_pipeline()
```

Run with:
```bash
python demo.py
```

## Key Points to Emphasize to Interviewer

### 1. **Complete Workflow Execution**
```
Show how one endpoint executes the entire pipeline:
- Topology Generation ✓
- Configuration Generation (OSPF + device configs) ✓
- Containerlab Export (production-ready format) ✓
- Topology Analysis (health metrics + findings) ✓
```

### 2. **Modular Architecture**
Point out in the code:
- Uses existing service modules (no duplication)
- Each stage is independent and can fail gracefully
- `PipelineOrchestrator` in `app/api/pipeline.py`

### 3. **Error Handling**
Demonstrate partial success handling:

```json
{
  "overall_status": "partial_success",
  "stages": {
    "topology_generation": {"status": "success"},
    "configuration_generation": {"status": "failed", "error_message": "..."}
  }
}
```

### 4. **Production-Ready Features**
- Unique pipeline ID for tracking (`pipeline_id`)
- Execution timing for each stage (performance monitoring)
- Detailed summary statistics
- Comprehensive logging at each stage
- HTTP status codes (200 for successful execution, 500 for critical failure)

### 5. **Code Reusability**
Open `app/api/pipeline.py` and show:
- `TopologyGenerator.generate()` - Existing module
- `ConfigurationGenerator.generate_ospf_configs()` - Existing module
- `DeploymentExporter.export_containerlab_topology()` - Existing module
- `TopologyAnalyzer.analyze()` - Existing module

## Common Interview Questions & Answers

### Q: "Why did you create this endpoint?"
**A:** The pipeline endpoint simplifies the workflow by orchestrating all stages in a single request. Previously, users would need 4 separate API calls. Now they get a complete topology with configurations and analysis in one operation.

### Q: "What happens if one stage fails?"
**A:** We use graceful degradation:
- If **topology generation fails**: Pipeline stops (status: `failed`)
- If **config/export fails**: Pipeline continues (status: `partial_success`)
- If **analysis fails**: Pipeline continues (status: `partial_success`)
- Each failure includes error details for debugging

### Q: "How do you avoid code duplication?"
**A:** We reuse existing service modules instead of reimplementing logic. The `PipelineOrchestrator` orchestrates, not duplicates.

### Q: "How does this scale?"
**A:** Currently sequential, but the structure supports future enhancements:
- Async/parallel execution for independent stages
- Pipeline templates and replay
- Webhook callbacks
- Execution history storage

### Q: "What's the response time?"
**A:** Show the `total_duration_seconds` in the response. Each stage's timing is included for optimization analysis.

## Testing Different Scenarios

### Scenario 1: Large Topology
```json
{
  "topology_name": "enterprise-network",
  "num_routers": 15,
  "num_switches": 8
}
```

### Scenario 2: Reproducible Results (Same Seed)
```json
{
  "topology_name": "test-1",
  "num_routers": 4,
  "num_switches": 2,
  "seed": 999
}
```

### Scenario 3: Skip Analysis for Speed
```json
{
  "topology_name": "quick-test",
  "num_routers": 3,
  "num_switches": 1,
  "run_analysis": false
}
```

## Showing the Code

If asked to show implementation, open:
- **Endpoint Definition**: `app/api/routes.py` (lines 30-100)
- **Orchestrator Logic**: `app/api/pipeline.py` (lines 60-200)
- **Error Handling**: `app/api/pipeline.py` (lines 120-180)
- **Response Building**: `app/api/pipeline.py` (lines 270-330)

## API Documentation

Show the interactive API docs:
```
http://localhost:8000/docs          (Swagger UI)
http://localhost:8000/redoc         (ReDoc)
http://localhost:8000/openapi.json  (OpenAPI JSON)
```

The `/run-pipeline` endpoint is fully documented with:
- Request/response schemas
- Parameter descriptions
- Example usage
- Error handling

## Summary

**What you're demonstrating:**
1. ✅ Complete networking automation workflow in one call
2. ✅ Reusable existing modules (good architecture)
3. ✅ Comprehensive error handling
4. ✅ Production-ready implementation
5. ✅ Well-documented API

This shows you can:
- Design clean APIs
- Handle errors gracefully
- Reuse code effectively
- Build production-ready features
