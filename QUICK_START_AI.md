# Quick Start: AI-Assisted Network Analysis

This is a quick reference for using the new AI features. For comprehensive documentation, see [AI_FEATURES.md](AI_FEATURES.md).

## 1. Start the Application

```bash
# Option A: Using Python directly
python -m uvicorn app.main:app --reload

# Option B: Using run script
./run.sh  # Linux/macOS
./run.bat # Windows
```

Server will start at `http://localhost:8000`

## 2. Basic Workflow

### Step A: Generate a Test Topology

```bash
curl -X POST http://localhost:8000/api/v1/topology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-network",
    "num_routers": 5,
    "num_switches": 2
  }' > topology.json
```

### Step B: Analyze It

```bash
curl -X POST http://localhost:8000/api/v1/topology/analyze \
  -H "Content-Type: application/json" \
  -d @topology.json | jq '.overall_health_score'
```

Output: Health score (0-100)

### Step C: Check for Issues

```bash
curl -X POST http://localhost:8000/api/v1/topology/analyze \
  -H "Content-Type: application/json" \
  -d @topology.json | jq '.single_points_of_failure'
```

### Step D: Simulate a Failure

```bash
# Get first router name
ROUTER=$(jq -r '.devices[0].name' topology.json)

# Simulate its failure
curl -X POST "http://localhost:8000/api/v1/topology/simulate/failure?failed_device=$ROUTER" \
  -H "Content-Type: application/json" \
  -d @topology.json | jq '.connectivity_impact'
```

### Step E: Get Recommendations

```bash
curl -X POST http://localhost:8000/api/v1/topology/optimize \
  -H "Content-Type: application/json" \
  -d @topology.json | jq '.general_recommendations'
```

## 3. Python Examples

### Quick Analysis

```python
import requests
import json

BASE = "http://localhost:8000/api/v1"

# Generate topology
topology = requests.post(
    f"{BASE}/topology/generate",
    json={"name": "test", "num_routers": 5, "num_switches": 2}
).json()

# Analyze it
analysis = requests.post(
    f"{BASE}/topology/analyze",
    json=topology
).json()

print(f"Health: {analysis['overall_health_score']}/100")
print(f"Issues: {analysis['total_issues']}")
print(f"SPOFs: {len(analysis['single_points_of_failure'])}")
```

### Failure Simulation

```python
import requests

BASE = "http://localhost:8000/api/v1"
topology = {...}  # Your topology

# Get device to fail
device = topology['devices'][0]['name']

# Simulate failure
result = requests.post(
    f"{BASE}/topology/simulate/failure",
    json=topology,
    params={"failed_device": device}
).json()

print(f"Severity: {result['scenario_severity']}")
print(f"Loss: {result['connectivity_impact']['connectivity_loss_percentage']:.1f}%")
```

### Get Recommendations

```python
import requests

BASE = "http://localhost:8000/api/v1"
topology = {...}

# Get optimization recommendations
opt = requests.post(f"{BASE}/topology/optimize", json=topology).json()

print(f"Potential: +{opt['optimization_potential']:.1f}%")
for rec in opt['general_recommendations']:
    print(f"- [{rec['priority']}] {rec['title']}")
```

## 4. Health Score Guide

| Score | Meaning | Action |
|-------|---------|--------|
| 80-100 | Excellent | No immediate action needed |
| 60-79 | Good | Monitor and plan improvements |
| 40-59 | Fair | Schedule optimization work |
| 0-39 | Poor | Urgent: Address critical issues |

## 5. Interpreting Results

### Severity Levels
- **CRITICAL**: >50% connectivity loss
- **HIGH**: 25-50% connectivity loss
- **MEDIUM**: 10-25% connectivity loss
- **LOW**: <10% connectivity loss

### Risk Levels (SPOFs)
- **CRITICAL**: >50% of network affected
- **HIGH**: 25-50% of network affected
- **MEDIUM**: 10-25% of network affected
- **LOW**: <10% of network affected

## 6. API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation

## 7. Common Tasks

### Find SPOFs

```bash
curl -X POST http://localhost:8000/api/v1/topology/analyze \
  -H "Content-Type: application/json" \
  -d @topology.json | jq '.single_points_of_failure[] | \
  select(.risk_level=="CRITICAL") | .device_name'
```

### Get Network Metrics

```bash
curl -X POST http://localhost:8000/api/v1/topology/analyze \
  -H "Content-Type: application/json" \
  -d @topology.json | jq '.topology_metrics'
```

### Generate Test Plan

```bash
curl -X POST http://localhost:8000/api/v1/topology/simulate/test-scenarios \
  -H "Content-Type: application/json" \
  -d @topology.json | jq '.scenarios[] | .scenario_name'
```

### Get Optimization Plan

```bash
curl -X POST http://localhost:8000/api/v1/topology/optimize/proposal \
  -H "Content-Type: application/json" \
  -d @topology.json | jq '{
    links_to_add: (.links_to_add | length),
    links_to_remove: (.links_to_remove | length),
    health_improvement: .expected_improvements
  }'
```

## 8. Troubleshooting

**Q: Getting empty analysis results?**
A: Ensure topology has at least 2 devices and valid links between them

**Q: Failure simulation shows unexpected results?**
A: Use analysis first to understand topology structure, device names are case-sensitive

**Q: Performance issues on large topologies?**
A: API uses sampling for >100 device topologies, results are still accurate for major issues

## 9. Advanced Usage

See [AI_FEATURES.md](AI_FEATURES.md) for:
- Detailed algorithm explanations
- Enterprise implementation patterns
- CI/CD integration examples
- ML-ready architecture

See [ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) for:
- Network resilience validation
- Change management patterns
- Capacity planning
- Disaster recovery testing

## 10. Support

For issues or questions:
1. Check [AI_FEATURES.md](AI_FEATURES.md) troubleshooting section
2. Review [ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) patterns
3. Check API docs at `http://localhost:8000/docs`
4. File an issue in the repository
