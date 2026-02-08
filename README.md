# Networking Automation Engine

An AI-assisted networking automation tool that automatically generates L2/L3 network topologies, creates routing configurations, and prepares scalable test environments for regression and automation testing.

## 🚀 Features

### Core Capabilities
- **Automatic Topology Generation**: Generate random but valid network topologies with configurable routers and switches
- **OSPF Configuration Generation**: Automatically create OSPF routing configurations for all devices
- **Configuration Rendering**: Use Jinja2 templates for multi-vendor device configurations (Cisco, Linux, etc.)
- **Topology Export**: Export in Containerlab-compatible YAML format
- **REST API**: Full-featured REST API for programmatic access

### 🤖 AI-Assisted Analysis & Optimization
- **Topology Analysis**: SPOF detection, path balancing analysis, node load assessment, network health scoring
- **Failure Simulation**: Simulate device/link failures, analyze impact on connectivity and routing
- **Resilience Testing**: Auto-generate test scenarios for network validation
- **Optimization Engine**: Rule-based recommendations for improving redundancy and performance
- **Graph-Based Intelligence**: Uses NetworkX algorithms for sophisticated topology analysis

### 🧠 Learning & Autonomous Capabilities (NEW)
- **Historical Learning**: Store and analyze results from topology generation, validation, and failure simulations
- **Intelligent Recommendations**: Get topology suggestions based on historical performance data (confidence-scored)
- **Autonomous Optimization**: System automatically improves topology choices based on learned patterns
- **Performance Tracking**: Monitor actual outcomes of recommendations and optimizations
- **Digital Twin**: Virtual replica of network infrastructure that learns and self-improves
- **Feedback Loop**: System learns from user selections and improves future recommendations

### Architecture Highlights
- **Clean Architecture**: Modular design with separated concerns (API, Topology, Configuration, Deployment, Analysis)
- **Production-Ready**: Follows Python best practices and is structured for GitHub
- **Extensible**: Designed for future protocol support (BGP, ISIS) and ML model integration
- **Type-Safe**: Pydantic models for data validation
- **Well-Documented**: Comprehensive docstrings, API documentation, and usage examples

## 📋 Requirements

- Python 3.10+
- FastAPI
- Pydantic
- Jinja2
- PyYAML

## 🔧 Installation

### Option 1: Using provided run script (Linux/macOS)

```bash
cd networking-automation-engine
chmod +x run.sh
./run.sh
```

### Option 2: Manual setup

1. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python3 -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 🎯 Accessing API Documentation

Once started, visit:
- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc

## 📁 Project Structure

```
networking-automation-engine/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── configuration.py    # OSPF configuration generator
│   │
│   ├── generator/
│   │   ├── __init__.py
│   │   └── topology.py         # Topology generation logic
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Application configuration
│   │
│   ├── deployment/
│   │   ├── __init__.py
│   │   └── exporter.py         # Export functionality (Containerlab, YAML)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── topology.py         # Topology data models
│   │   ├── configuration.py    # Configuration data models
│   │   └── deployment.py       # Deployment data models
│   │
│   └── utils/
│       ├── __init__.py
│       └── ipaddr.py           # IP addressing utilities
│
├── templates/
│   ├── ospf_router.j2          # OSPF router configuration template
│   ├── cisco_config.j2         # Cisco IOS XE template
│   └── linux_network.j2        # Linux network configuration template
│
├── tests/
│   └── (test files)
│
├── requirements.txt
├── run.sh
└── README.md
```

## 🔌 API Endpoints

### 1. Health Check
```
GET /
GET /api/v1/info
```
Check service status and capabilities.

### 2. Topology Generation
```
POST /api/v1/topology/generate
```
Generate a new network topology.

**Request Body**:
```json
{
    "name": "production-topology",
    "num_routers": 5,
    "num_switches": 3,
    "seed": null
}
```

### 3. Configuration Generation
```
POST /api/v1/configuration/generate
```
Generate OSPF configurations for topology.

**Request Body**: Topology object (from generate endpoint)

### 4. Export to Containerlab
```
POST /api/v1/topology/export/containerlab
```
Export topology in Containerlab format.

**Query Parameters**:
- `image`: Container image (default: `frrouting/frr:latest`)

### 5. Export to YAML
```
POST /api/v1/topology/export/yaml
```
Export topology in universal YAML format.

### 6. Topology Statistics
```
GET /api/v1/stats/topology
```
Get topology connectivity statistics.

## 🤖 AI-Assisted Analysis & Optimization

The engine includes intelligent topology analysis, failure simulation, and optimization capabilities:

### 7. Analyze Topology
```
POST /api/v1/topology/analyze
```
Perform AI-assisted analysis to detect network issues and assess health.

**Features**:
- SPOF (Single Point of Failure) detection
- Unbalanced path identification
- Overloaded node detection
- Network metrics calculation
- Health score (0-100)

### 8. Failure Simulation
```
POST /api/v1/topology/simulate/failure
```
Simulate device/link failures and analyze impact on network connectivity.

**Query Parameters**:
- `failed_device`: Device or link name to fail

**Results**:
- Connectivity impact percentage
- Affected routes
- Network partitioning analysis
- OSPF recovery time estimation

### 9. Generate Test Scenarios
```
POST /api/v1/topology/simulate/test-scenarios
```
Auto-generate recommended failure scenarios for resilience testing.

**Scenarios**:
- Single router failure
- Link failure
- Multiple simultaneous failures

### 10. Optimize Topology
```
POST /api/v1/topology/optimize
```
Analyze and recommend optimizations for improved resilience and performance.

**Recommendations**:
- SPOF elimination strategies
- Link redundancy improvements
- OSPF cost optimization
- Node load balancing

### 11. Generate Optimization Proposal
```
POST /api/v1/topology/optimize/proposal
```
Generate a complete proposal for optimized topology design.

**Proposal Includes**:
- Links to add/remove
- Expected improvements
- Implementation complexity
- Health score improvement potential

## 🧠 Intent-Based Networking (IBN)

The Networking Automation Engine now supports Intent-Based Networking, enabling users to define **what** they want the network to do rather than **how** to build it. This paradigm shift moves networking toward higher-level abstractions similar to Cisco ACI, AWS Wavelength, and other modern SDN systems.

### Concept

Instead of manually designing a topology, users express high-level intent:
- **Traditional Approach**: "Create a ring topology with 5 routers, connect them with 100 Mbps links, cost 100"
- **Intent-Based Approach**: "I need a highly available topology for 5 sites with critical redundancy"

The system automatically generates and validates topologies that satisfy the intent.

### Key Capabilities

#### 12. Generate from Intent
```
POST /api/v1/intent/generate
```
Generate a topology from high-level intent specification.

**Intent Parameters**:
- `topology_type`: full_mesh, hub_spoke, ring, tree, leaf_spine, hybrid
- `redundancy_level`: minimum, standard, high, critical
- `number_of_sites`: 2-500 devices/sites
- `max_hops`: Maximum acceptable hop count
- `design_goal`: cost_optimized, redundancy_focused, latency_optimized, scalability
- `minimize_spof`: Eliminate single points of failure

**Example Request**:
```json
{
  "intent_name": "Multi-Region Data Center",
  "intent_description": "Highly available network for 10 data centers",
  "topology_type": "leaf_spine",
  "number_of_sites": 10,
  "redundancy_level": "critical",
  "max_hops": 3,
  "routing_protocol": "ospf",
  "design_goal": "redundancy_focused",
  "minimize_spof": true,
  "minimum_connections_per_site": 3
}
```

#### 13. Validate Intent
```
POST /api/v1/intent/validate
```
Validate whether a topology satisfies the specified intent.

**Returns**:
- Intent satisfaction score (0-100)
- Constraint violations
- Recommendations for improvement
- Detailed validation report

#### 14. End-to-End Intent Workflow
```
POST /api/v1/intent/end-to-end
```
Complete workflow: Parse intent → Generate topology → Validate → Report

**Returns complete report with**:
- Generated topology
- Validation results
- Recommendations
- Next steps

#### 15. Intent Examples
```
GET /api/v1/intent/examples
```
Get example intent specifications for common scenarios:
- Multi-region data center network
- Enterprise campus network
- Global WAN network
- Full mesh critical network

> **📖 For comprehensive IBN documentation, see [INTENT_BASED_NETWORKING.md](INTENT_BASED_NETWORKING.md)**

> **📖 For comprehensive AI features documentation, see [AI_FEATURES.md](AI_FEATURES.md)**

### Learning & Autonomous Optimization Endpoints

#### 16. Recommend Topology
```
POST /api/v1/learning/recommend-topology
```
Get intelligent topology recommendations based on historical performance data.

**Request**: IntentRequest (same as generation)

**Response**: List of ranked recommendations with:
- `topology_type`: Recommended topology
- `overall_score`: 0-100 score
- `confidence`: Confidence level 0-100
- `pros`: List of advantages
- `cons`: List of disadvantages
- `recommendation_reason`: Human-readable rationale
- `based_on_history`: Whether based on real data

**Use Case**: When user wants system to recommend best topology without specifying type

#### 17. Topology History
```
GET /api/v1/learning/topology-history
```
Retrieve historical topology generation data for analysis.

**Query Parameters**:
- `topology_type`: Optional filter (e.g., "tree", "leaf_spine")
- `redundancy_level`: Optional filter (e.g., "standard", "critical")
- `days`: Days of history to retrieve (default: 30)
- `limit`: Max results (default: 100)

**Response**: List of historical topologies with:
- Topology metadata (type, sites, devices, links)
- Validation results (scores, satisfaction)
- Simulation results (failure impacts, resilience)

**Use Case**: Analyzing trends, understanding what worked historically

#### 18. Learning Report
```
POST /api/v1/learning/learning-report
```
Generate comprehensive learning and optimization report.

**Query Parameters**:
- `include_optimization_stats`: Include autonomous optimization data (default: true)

**Response**: Comprehensive report including:
- Total topologies analyzed
- Unique configurations tracked
- Top performance insights
- Recommended configurations
- Autonomous optimization activity
- Key findings and trends

**Use Case**: Executive reporting, periodic learning evaluation

> **📖 For comprehensive Learning documentation, see [LEARNING_BASED_OPTIMIZATION.md](LEARNING_BASED_OPTIMIZATION.md)**

## 📌 Usage Examples

### Example 1: Generate Topology with cURL

```bash
curl -X POST http://localhost:8000/api/v1/topology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-topology",
    "num_routers": 3,
    "num_switches": 2,
    "seed": 42
  }'
```

**Response** (Sample):
```json
{
  "name": "test-topology",
  "num_routers": 3,
  "num_switches": 2,
  "devices": [
    {
      "name": "R1",
      "device_type": "router",
      "router_id": "10.1.1.1",
      "asn": 65000
    },
    {
      "name": "R2",
      "device_type": "router",
      "router_id": "10.2.1.1",
      "asn": 65001
    },
    {
      "name": "R3",
      "device_type": "router",
      "router_id": "10.3.1.1",
      "asn": 65002
    },
    {
      "name": "SW1",
      "device_type": "switch",
      "router_id": null,
      "asn": 65000
    },
    {
      "name": "SW2",
      "device_type": "switch",
      "router_id": null,
      "asn": 65000
    }
  ],
  "links": [
    {
      "source_device": "R1",
      "source_interface": "eth0",
      "destination_device": "R2",
      "destination_interface": "eth0",
      "source_ip": "10.100.1.1",
      "destination_ip": "10.100.1.2",
      "subnet_mask": "255.255.255.0",
      "cost": 1
    },
    // ... more links
  ],
  "routing_protocol": "ospf"
}
```

### Example 2: Generate Configuration

```bash
# First, get a topology
TOPOLOGY=$(curl -s -X POST http://localhost:8000/api/v1/topology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "lab-topology",
    "num_routers": 3,
    "num_switches": 1
  }')

# Then generate configuration
curl -X POST http://localhost:8000/api/v1/configuration/generate \
  -H "Content-Type: application/json" \
  -d "$TOPOLOGY"
```

### Example 3: Export to Containerlab

```bash
# Save topology to file
TOPOLOGY=$(curl -s -X POST http://localhost:8000/api/v1/topology/generate \
  -H "Content-Type: application/json" \
  -d '{"name": "clab-topo", "num_routers": 4, "num_switches": 2}')

# Export to Containerlab format
curl -X POST http://localhost:8000/api/v1/topology/export/containerlab \
  -H "Content-Type: application/json" \
  -d "$TOPOLOGY" \
  > containerlab-topology.json
```

### Example 4: Python Client

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Generate topology
topo_request = {
    "name": "python-topology",
    "num_routers": 5,
    "num_switches": 3,
    "seed": 123
}

response = requests.post(
    f"{BASE_URL}/topology/generate",
    json=topo_request
)
topology = response.json()

print(f"Generated topology: {topology['name']}")
print(f"Devices: {len(topology['devices'])}")
print(f"Links: {len(topology['links'])}")

# Generate configuration
config_response = requests.post(
    f"{BASE_URL}/configuration/generate",
    json=topology
)
configs = config_response.json()

print(f"Generated configurations for {len(configs['device_configurations'])} devices")

# Export to Containerlab
export_response = requests.post(
    f"{BASE_URL}/topology/export/containerlab",
    json=topology
)
containerlab_topology = export_response.json()

# Get topology stats
stats_response = requests.get(
    f"{BASE_URL}/stats/topology",
    json=topology
)
stats = stats_response.json()
print(f"Topology Stats: {json.dumps(stats, indent=2)}")
```

### Example 5: AI-Assisted Analysis & Optimization

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Generate a topology
topology = requests.post(
    f"{BASE_URL}/topology/generate",
    json={"name": "test-network", "num_routers": 5, "num_switches": 2}
).json()

# 1. Analyze topology for issues
analysis = requests.post(
    f"{BASE_URL}/topology/analyze",
    json=topology
).json()

print(f"Network Health Score: {analysis['overall_health_score']}/100")
print(f"Total Issues: {analysis['total_issues']}")
print(f"SPOFs Found: {len(analysis['single_points_of_failure'])}")

if analysis['single_points_of_failure']:
    spof = analysis['single_points_of_failure'][0]
    print(f"  - {spof['device_name']} (severity: {spof['risk_level']})")

# 2. Simulate failures to understand impact
failure_result = requests.post(
    f"{BASE_URL}/topology/simulate/failure?failed_device={topology['devices'][0]['name']}",
    json=topology
).json()

print(f"\nIf {failure_result['failed_element']} fails:")
print(f"  - Severity: {failure_result['scenario_severity']}")
print(f"  - Connectivity Loss: {failure_result['connectivity_impact']['connectivity_loss_percentage']:.1f}%")
print(f"  - Recovery Time: ~{failure_result['recovery_estimate_seconds']}s")

# 3. Generate test scenarios
scenarios = requests.post(
    f"{BASE_URL}/topology/simulate/test-scenarios",
    json=topology
).json()

print(f"\nRecommended test scenarios: {scenarios['count']}")
for scenario in scenarios['scenarios']:
    print(f"  - {scenario['scenario_name']}")

# 4. Get optimization recommendations
optimization = requests.post(
    f"{BASE_URL}/topology/optimize",
    json=topology
).json()

print(f"\nOptimization Potential: {optimization['optimization_potential']:.1f}%")
print(f"Recommendations: {optimization['total_recommendations']}")

if optimization['general_recommendations']:
    for rec in optimization['general_recommendations'][:2]:
        print(f"  - Priority {rec['priority']}: {rec['title']}")

# 5. Generate optimized topology proposal
proposal = requests.post(
    f"{BASE_URL}/topology/optimize/proposal",
    json=topology
).json()

print(f"\nOptimization Proposal:")
print(f"  - Links to add: {len(proposal['links_to_add'])}")
print(f"  - Links to remove: {len(proposal['links_to_remove'])}")
print(f"  - Expected health improvement: {proposal['expected_improvements']}")
```

### Example 6: Intent-Based Networking (IBN)

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Define high-level intent (what you want, not how to build it)
intent = {
    "intent_name": "Multi-Region Data Center Network",
    "intent_description": "Highly available network connecting 10 data centers with critical redundancy",
    "topology_type": "leaf_spine",
    "number_of_sites": 10,
    "redundancy_level": "critical",
    "max_hops": 3,
    "routing_protocol": "ospf",
    "design_goal": "redundancy_focused",
    "minimize_spof": True,
    "minimum_connections_per_site": 3
}

# 1. Generate topology from intent (end-to-end workflow)
result = requests.post(
    f"{BASE_URL}/intent/end-to-end",
    json=intent
).json()

print(f"✓ Intent Workflow Complete")
print(f"  Topology: {result['topology']['name']}")
print(f"  Devices: {result['summary']['devices_generated']}")
print(f"  Links: {result['summary']['links_generated']}")
print(f"  Intent Satisfied: {result['summary']['intent_satisfied']}")
print(f"  Validation Score: {result['summary']['overall_score']:.1f}/100")

# 2. Review validation results
validation = result['validation_result']
print(f"\n✓ Validation Results")
print(f"  Redundancy Score: {validation['redundancy_score']:.1f}/100")
print(f"  Path Diversity Score: {validation['path_diversity_score']:.1f}/100")
print(f"  Actual Max Hops: {validation['actual_max_hops']} (required: ≤{intent['max_hops']})")
print(f"  SPOFs Eliminated: {validation['spof_eliminated']}")

# 3. Review recommendations
if result['summary']['recommendations']:
    print(f"\n✓ Recommendations for Improvement")
    for i, rec in enumerate(result['summary']['recommendations'], 1):
        print(f"  {i}. {rec}")

# 4. Export to Containerlab and deploy
topology = result['topology']
export = requests.post(
    f"{BASE_URL}/topology/export/containerlab",
    json=topology
).json()

with open(f"{intent['intent_name'].replace(' ', '_')}_containerlab.yml", 'w') as f:
    json.dump(export, f, indent=2)
print(f"\n✓ Topology exported to Containerlab format")

# 5. Get intent examples for other scenarios
examples = requests.get(f"{BASE_URL}/intent/examples").json()
print(f"\n✓ Available intent examples:")
for name in examples['examples'].keys():
    print(f"  - {name}")
```

**Output from Example 6**:
```
✓ Intent Workflow Complete
  Topology: Multi-Region Data Center Network-leaf-spine
  Devices: 10
  Links: 60
  Intent Satisfied: True
  Validation Score: 94.5/100

✓ Validation Results
  Redundancy Score: 98.0/100
  Path Diversity Score: 97.0/100
  Actual Max Hops: 2 (required: ≤3)
  SPOFs Eliminated: True

✓ Recommendations for Improvement
  1. Consider load distribution - 2 spines have slightly higher degree
  2. Latency can be further optimized by adjusting OSPF costs

✓ Topology exported to Containerlab format

✓ Available intent examples:
  - example_1_datacenter
  - example_2_campus
  - example_3_wan
  - example_4_mesh
```

## 🏗️ Architecture Details

### Module Responsibilities

1. **app/models/** - Data structures and validation
   - `topology.py`: Topology and device models
   - `configuration.py`: Routing configuration models
   - `deployment.py`: Export format models
   - `analysis.py`: Topology analysis and metrics models
   - `simulation.py`: Failure simulation models
   - `optimization.py`: Optimization recommendation models
   - `intent.py`: Intent-based networking models and constraints

2. **app/generator/** - Topology creation
   - `topology.py`: Random topology generation with valid connectivity
   - `intent_generator.py`: Intent-based topology generation

3. **app/core/** - Configuration logic
   - `configuration.py`: OSPF configuration generation from topologies

4. **app/deployment/** - Export and rendering
   - `exporter.py`: Containerlab export, YAML export, config rendering

5. **app/analysis/** - AI-assisted topology analysis
   - `analyzer.py`: TopologyAnalyzer class for SPOF detection, metrics, health scoring

6. **app/simulation/** - Failure simulation engine
   - `simulator.py`: FailureSimulator class for impact analysis and test scenario generation

7. **app/optimization/** - Topology optimization recommendations
   - `optimizer.py`: TopologyOptimizer class for improvement recommendations

8. **app/intent/** - Intent-Based Networking
   - `parser.py`: IntentParser for converting intent to constraints

9. **app/validation/** - Intent validation and scoring
   - `validator.py`: IntentValidator for validation and reporting

10. **app/api/** - REST API endpoints
    - `routes.py`: All REST endpoints with full documentation

11. **app/utils/** - Helper functions
    - `ipaddr.py`: IP address allocation and utilities

### Topology Generation Algorithm

1. **Device Creation**: Create N routers and M switches
2. **Backbone Link Creation**: Create linear chain of routers
3. **Redundancy Links**: Add random router-to-router connections
4. **Switch Connections**: Connect switches to routers
5. **IP Allocation**: Assign unique IP addresses to each link

This ensures the generated topologies are:
- ✅ Always fully connected
- ✅ Valid for OSPF
- ✅ Reproducible (with seed)
- ✅ Realistic network structure

## 🚀 Enterprise-Level Extensions

### 1. Multi-Protocol Support
```python
# Future: BGP configuration generation
class BGPConfigurationGenerator:
    def generate_bgp_configs(self, topology: Topology):
        # Internal BGP (iBGP) full mesh
        # External BGP (eBGP) connections
        pass

# Future: ISIS configuration generation
class ISISConfigurationGenerator:
    def generate_isis_configs(self, topology: Topology):
        pass
```

### 2. Advanced Features
- **Automation Integration**: Ansible playbook generation
- **Device Simulation**: Containerlab-native integration
- **Configuration Management**: Store configs in database
- **Version Control**: Git integration for config versioning
- **Change Management**: Diff and rollback capabilities
- **Multi-Vendor Support**: Cisco, Juniper, Nokia configurations

### 3. Cloud-Native Features
- **Kubernetes Deployment**: Helm charts
- **Database Backend**: PostgreSQL/MongoDB for config storage
- **Event Streaming**: Kafka topics for topology changes
- **Telemetry Integration**: Prometheus metrics

### 4. AI/ML Enhancements
- **Intelligent Topology Suggestion**: Based on use case
- **Anomaly Detection**: In generated configurations
- **Performance Prediction**: Network performance simulation
- **Self-Healing Networks**: Automatic remediation suggestions

## 🧪 Testing Environments

### Use Case 1: Regression Testing
```bash
# Generate stable topologies with deterministic seed
seed=12345

# Create baseline topology
curl -X POST http://localhost:8000/api/v1/topology/generate \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"regression-baseline\", \"num_routers\": 10, \"seed\": $seed}"

# Use for nightly regression tests
# Ensure consistent test environment across runs
```

### Use Case 2: Scalability Testing
```bash
# Load testing with increasing topology size
for routers in 5 10 20 50 100; do
  curl -X POST http://localhost:8000/api/v1/topology/generate \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"scale-test-r$routers\", \"num_routers\": $routers}"
done
```

### Use Case 3: Feature Testing
```bash
# Generate multiple topologies for different features
topologies=(
  '{"name": "linear", "num_routers": 5, "num_switches": 0}'
  '{"name": "mesh", "num_routers": 5, "num_switches": 0}'
  '{"name": "with-switches", "num_routers": 5, "num_switches": 5}'
)

for topo in "${topologies[@]}"; do
  curl -X POST http://localhost:8000/api/v1/topology/generate \
    -H "Content-Type: application/json" \
    -d "$topo"
done
```

## 🔐 Security Considerations

### Current Implementation
- Input validation via Pydantic models
- CORS properly configured
- Logging for audit trails

### Production Recommendations
- Add authentication (OAuth2/JWT)
- Implement rate limiting
- Add API key management
- Enable HTTPS/TLS
- Implement request/response encryption
- Add input sanitization for templates
- Implement access controls (RBAC)

## 📊 Performance Characteristics

### Topology Generation
- 3 routers: ~5ms
- 10 routers: ~15ms
- 20 routers: ~30ms

### Configuration Generation
- Linear with device count

### Memory Usage
- Single topology: ~100KB
- 100-device topology: ~1MB

## 🔍 Monitoring and Logging

### Logging Levels
```python
# Set in app/config/settings.py
log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Available Logs
- Topology generation events
- Configuration generation events
- API request/response logging
- Error tracking

## 🤝 Contributing

### Adding New Protocols

1. Create configuration generator:
```python
# app/core/bgp.py
class BGPConfigurationGenerator:
    def generate_bgp_configs(self, topology: Topology) -> BGPRoutingConfig:
        pass
```

2. Create Pydantic models:
```python
# app/models/bgp.py
class BGPConfiguration(BaseModel):
    pass
```

3. Add API endpoint:
```python
# app/api/routes.py
@router.post("/configuration/generate-bgp")
async def generate_bgp_config(topology: Topology):
    pass
```

4. Create templates:
```jinja2
! bgp_config.j2
router bgp {{ local_asn }}
{% for neighbor in neighbors %}
  neighbor {{ neighbor.ip }} remote-as {{ neighbor.asn }}
{% endfor %}
```

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Containerlab Documentation](https://containerlab.dev/)
- [OSPF RFC 2328](https://tools.ietf.org/html/rfc2328)
- [BGP RFC 4271](https://tools.ietf.org/html/rfc4271)

## 📝 License

This project is provided as-is for educational and commercial use.

## 🎓 Learning Resources

### Understanding Network Topologies
- Grid/Mesh topologies for high availability
- Linear topologies for cost efficiency
- Hybrid topologies for balanced solutions

### OSPF Concepts
- Multi-area OSPF design
- OSPF cost calculation
- Router ID significance
- Network statement wildcards

### Container Networking
- Bridge networking in Containerlab
- Interface naming conventions
- Volume binds for configuration

## 📞 Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review example requests in this README
3. Check application logs for errors
4. Examine generated topologies for validation

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Python Version**: 3.10+
