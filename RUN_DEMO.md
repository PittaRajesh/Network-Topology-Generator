# Quick Demo Instructions

## Before Starting

Make sure the FastAPI application is running:

```bash
# Navigate to the project
cd networking-automation-engine

# Start the API
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Then open a **new terminal** window and follow the demo instructions below.

---

## Option 1: Swagger UI (Easiest)

1. Open your browser: http://localhost:8000/docs
2. Scroll down to **POST /api/v1/run-pipeline**
3. Click **"Try it out"**
4. Replace the request body with:

```json
{
  "topology_name": "demo-topology",
  "num_routers": 4,
  "num_switches": 2,
  "run_analysis": true
}
```

5. Click **"Execute"**
6. Watch the response appear in real-time!

---

## Option 2: PowerShell (Windows)

Run the interactive demo:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo.ps1
```

Then select option 1, 2, 3, or 4 from the menu.

**Tip**: If PowerShell opens but doesn't respond, try:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\demo.ps1
```

---

## Option 3: Command Line (Any OS)

### Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/run-pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "topology_name": "my-demo",
    "num_routers": 5,
    "num_switches": 3,
    "run_analysis": true
  }'
```

### Using PowerShell

```powershell
$payload = @{
    topology_name = "demo-topology"
    num_routers = 4
    num_switches = 2
    run_analysis = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/run-pipeline" `
    -Method POST `
    -Headers @{'Content-Type'='application/json'} `
    -Body $payload | ConvertTo-Json
```

---

## Expected Output

The API will return a response like:

```json
{
  "pipeline_id": "pipe_a1b2c3d4e5f6",
  "execution_timestamp": "2026-02-08T10:30:45.123456",
  "total_duration_seconds": 4.567,
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
    "topology_name": "demo-topology",
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

---

## What's Happening

The pipeline executes **4 stages automatically**:

1. **Topology Generation** (0.2-0.3s)
   - Creates a network with specified routers and switches
   - Allocates IP addresses
   - Generates router IDs

2. **Configuration Generation** (1.5-2s)
   - Creates OSPF routing configs
   - Generates device-specific configurations
   - Uses Jinja2 templates

3. **Containerlab Export** (0.4-0.5s)
   - Exports topology in Containerlab format
   - Creates deployment-ready YAML
   - Defines nodes and links

4. **Topology Analysis** (2-3s)
   - Detects single points of failure
   - Analyzes link balancing
   - Calculates health score (0-100)
   - Identifies network issues

---

## Try Different Configurations

### Smaller (faster):
```json
{
  "topology_name": "tiny",
  "num_routers": 2,
  "num_switches": 0,
  "run_analysis": false
}
```

### Larger (more complex):
```json
{
  "topology_name": "enterprise",
  "num_routers": 12,
  "num_switches": 6,
  "run_analysis": true
}
```

### Reproducible (same result every time):
```json
{
  "topology_name": "test",
  "num_routers": 5,
  "num_switches": 3,
  "seed": 42,
  "run_analysis": true
}
```

---

## Troubleshooting

### "Connection refused"
- Make sure the FastAPI app is running in another terminal
- Check that it's on port 8000

### "Can't reach API"
- Make sure you navigated to the project directory first
- The API should output: `Uvicorn running on http://0.0.0.0:8000`

### Response looks wrong
- Check HTTP status code (should be 200)
- Look at `overall_status` - should be "success" or "partial_success"
- Check individual stage status for errors

---

## Next Steps

After seeing the demo:

1. **Explore the code**: Check `app/api/pipeline.py`
2. **Read the docs**: See `PIPELINE_ORCHESTRATION.md`  
3. **Use the API**: Integrate into your own applications
4. **Modify the demos**: Edit the demo files to try different configurations

---

## Resources

- **Full API Documentation**: http://localhost:8000/docs
- **ReDoc Alternative**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Code Implementation**: [app/api/pipeline.py](app/api/pipeline.py)
- **Detailed Guide**: [PIPELINE_ORCHESTRATION.md](PIPELINE_ORCHESTRATION.md)
