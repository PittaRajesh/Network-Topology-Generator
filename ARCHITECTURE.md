# Architecture & Design Patterns

## Overview

The Networking Automation Engine uses a **clean, layered architecture** with clear separation of concerns. This design ensures the codebase is:
- **Maintainable**: Each component has a single responsibility
- **Testable**: Components can be tested in isolation
- **Extensible**: New features can be added without modifying existing code
- **Scalable**: Ready for enterprise deployment

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   API Layer (/api)                      │ │
│  │  - REST Endpoints                                       │ │
│  │  - Request/Response Validation                          │ │
│  │  - HTTP Status Codes                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ▲                                    │
│                           │                                    │
│  ┌────────────────────────┴────────────────────────────────┐ │
│  │              Business Logic Layer (/core, /generator)   │ │
│  │  ┌──────────────────────┬────────────────────────────┐  │ │
│  │  │ TopologyGenerator    │ ConfigurationGenerator     │  │ │
│  │  │ - Networks creation  │ - OSPF configs            │  │ │
│  │  │ - Link allocation    │ - Interface configs       │  │ │
│  │  │ - Validation         │ - Network statements      │  │ │
│  │  └──────────────────────┴────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ▲                                    │
│                           │                                    │
│  ┌────────────────────────┴────────────────────────────────┐ │
│  │          Data Access & Export Layer (/deployment)       │ │
│  │  - Containerlab YAML Export                             │ │
│  │  - Configuration Rendering with Jinja2                  │ │
│  │  - File I/O Operations                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ▲                                    │
│                           │                                    │
│  ┌────────────────────────┴────────────────────────────────┐ │
│  │            Data Models Layer (/models)                  │ │
│  │  - Pydantic Models                                      │ │
│  │  - Data Validation                                      │ │
│  │  - Type Safety                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ▲                                    │
│                           │                                    │
│  ┌────────────────────────┴────────────────────────────────┐ │
│  │           Utilities Layer (/utils)                      │ │
│  │  - IP Address Calculations                              │ │
│  │  - Network Math                                         │ │
│  │  - Helper Functions                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ▲                                    │
│                           │                                    │
│  ┌────────────────────────┴────────────────────────────────┐ │
│  │         Configuration Layer (/config)                   │ │
│  │  - Settings Management (Pydantic Settings)              │ │
│  │  - Environment Variables                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. API Layer (`app/api/routes.py`)

**Responsibility**: Handle HTTP request/response, routing, and basic validation

**Key Components**:
- REST endpoint definitions
- Request body parsing (with Pydantic)
- Response formatting
- HTTP status codes
- Error handling

**Example**:
```python
@router.post("/topology/generate", response_model=Topology)
async def generate_topology(request: TopologyRequest) -> Topology:
    # Validation already done by Pydantic
    # Call business logic
    generator = TopologyGenerator(seed=request.seed)
    return generator.generate(request.name, request.num_routers, request.num_switches)
```

### 2. Business Logic Layer (`app/generator/`, `app/core/`)

**Responsibility**: Core algorithms and business rules

**Key Components**:

#### TopologyGenerator (`app/generator/topology.py`)
```
Input: Configuration (num_routers, num_switches)
    ↓
Create Routers
Create Switches
    ↓
Create Backbone Links
Add Redundancy Links
Connect Switches
    ↓
Output: Topology Object
```

#### ConfigurationGenerator (`app/core/configuration.py`)
```
Input: Topology
    ↓
Extract Routers
For each Router:
  - Get Connected Links
  - Create Interface Configs
  - Generate OSPF Networks
    ↓
Output: RoutingConfig
```

### 3. Data Access & Export Layer (`app/deployment/exporter.py`)

**Responsibility**: Format conversion and file I/O

**Capabilities**:
- **Containerlab Export**: Convert topology to Containerlab YAML
- **YAML Export**: Universal topology representation
- **Configuration Rendering**: Jinja2 template processing

**Example Flow**:
```
Topology → Containerlab Format
        → YAML Format
        → Configuration Text (via Jinja2)
```

### 4. Data Models Layer (`app/models/`)

**Responsibility**: Data validation and type safety

**Key Models**:
```python
Device          # Router or Switch
Link            # Connection between devices
Topology        # Complete network definition
OSPFConfiguration  # Routing config
```

**Validation Examples**:
```python
# Automatic validation by Pydantic
Device(name="R1", device_type="router")  ✓
Device(name="R1" * 20, device_type="router")  ✗ (too long)
Device(name="R#$%", device_type="router")  ✗ (invalid chars)
```

### 5. Utilities Layer (`app/utils/`)

**Responsibility**: Common operations

**Utilities**:
- IP address calculations
- Network math (CIDR, wildcard masks)
- Router ID generation
- Validation helpers

## Design Patterns Used

### 1. Factory Pattern
**Location**: `TopologyGenerator`

```python
class TopologyGenerator:
    def generate(self, name, num_routers, num_switches) -> Topology:
        # Creates Topology objects
        devices = self._create_routers(num_routers)
        devices.extend(self._create_switches(num_switches))
        links = self._create_links(devices)
        return Topology(...)
```

### 2. Strategy Pattern
**Location**: Configuration Generation

Different strategies for different protocols:
```python
class ConfigurationGenerator:
    def generate_ospf_configs(topology) -> RoutingConfig: ...

class BGPConfigurationGenerator:  # Future
    def generate_bgp_configs(topology) -> BGPRoutingConfig: ...

class ISISConfigurationGenerator:  # Future
    def generate_isis_configs(topology) -> ISISRoutingConfig: ...
```

### 3. Template Method Pattern
**Location**: `DeploymentExporter`

```python
class DeploymentExporter:
    def export_containerlab_topology(topology) -> Dict:
        nodes = self._create_nodes(topology)
        links = self._create_links(topology)
        return {"name": topology.name, "topology": {...}}
    
    def export_to_yaml(topology) -> str:
        data = self._prepare_data(topology)
        return yaml.dump(data)
```

### 4. Builder Pattern
**Location**: Models/Schemas

```python
# Pydantic automatically provides builder-like functionality
topology = Topology(
    name="test",
    num_routers=5,
    num_switches=2,
    devices=[...],
    links=[...],
    routing_protocol="ospf"
)
```

### 5. Dependency Injection
**Location**: FastAPI routes

```python
@router.post("/topology/generate")
async def generate_topology(request: TopologyRequest) -> Topology:
    # Dependencies injected by FastAPI/Pydantic
    generator = TopologyGenerator(seed=request.seed)
    return generator.generate(...)
```

## Data Flow Examples

### Topology Generation Flow

```
User Request (POST /topology/generate)
    ↓
TopologyRequest (Pydantic validation)
    ↓
TopologyGenerator
  ├─ Create devices
  ├─ Generate backbone links
  ├─ Add redundancy
  └─ Connect switches
    ↓
Topology Object (Pydantic validation)
    ↓
HTTP Response (JSON serialization)
    ↓
User Receives Topology
```

### Configuration Generation Flow

```
Topology Object
    ↓
ConfigurationGenerator.generate_ospf_configs()
  ├─ For each router:
  │  ├─ Get connected links
  │  ├─ Create interface configs
  │  └─ Generate OSPF networks
  └─ Create RoutingConfig
    ↓
RoutingConfig Object
    ↓
DeploymentExporter.generate_all_device_configs()
  ├─ Load Jinja2 templates
  ├─ Render for each device
  └─ Return configurations
    ↓
Device Configuration Strings
```

### Full Pipeline Flow

```
User Request
    ↓
Generate Topology
    ├─ TopologyGenerator
    └─ Returns Topology
    ↓
Generate Configuration
    ├─ ConfigurationGenerator
    └─ Returns RoutingConfig
    ↓
Export to Containerlab
    ├─ DeploymentExporter
    └─ Returns YAML structure
    ↓
Render Device Configs
    ├─ Jinja2 template processing
    └─ Returns configuration text
    ↓
User Gets Results
```

## Extending the System

### Adding New Routing Protocol

**Step 1**: Create configuration generator

```python
# app/core/bgp.py
class BGPConfigurationGenerator:
    def generate_bgp_configs(self, topology: Topology) -> BGPRoutingConfig:
        """Generate BGP configs from topology"""
        pass
```

**Step 2**: Create Pydantic models

```python
# app/models/bgp.py
class BGPPeer(BaseModel):
    neighbor_ip: str
    remote_asn: int
    local_asn: int

class BGPConfiguration(BaseModel):
    device_name: str
    local_asn: int
    peers: List[BGPPeer]

class BGPRoutingConfig(BaseModel):
    topology_name: str
    bgp_configs: List[BGPConfiguration]
```

**Step 3**: Create Jinja2 template

```jinja2
! BGP Configuration
router bgp {{ local_asn }}
  router-id {{ router_id }}
{% for peer in peers %}
  neighbor {{ peer.neighbor_ip }} remote-as {{ peer.remote_asn }}
{% endfor %}
```

**Step 4**: Add API endpoint

```python
# In app/api/routes.py
@router.post("/configuration/generate-bgp")
async def generate_bgp_config(topology: Topology) -> dict:
    bgp_gen = BGPConfigurationGenerator()
    bgp_config = bgp_gen.generate_bgp_configs(topology)
    return {"bgp_configs": bgp_config}
```

**Step 5**: Update configuration generator (optional)

```python
# Make ConfigurationGenerator extensible
class ConfigurationGenerator:
    def __init__(self):
        self.protocol_generators = {
            "ospf": OSPFConfigurationGenerator(),
            "bgp": BGPConfigurationGenerator(),
            "isis": ISISConfigurationGenerator(),
        }
    
    def generate(self, topology, protocol="ospf"):
        generator = self.protocol_generators[protocol]
        return generator.generate(topology)
```

### Adding New Export Format

**Example**: Export to Ansible inventory

```python
# In app/deployment/exporter.py
def export_to_ansible_inventory(
    self,
    topology: Topology
) -> Dict[str, List]:
    """Export as Ansible inventory"""
    inventory = {
        "routers": [
            {
                "name": device.name,
                "router_id": device.router_id,
                "asn": device.asn
            }
            for device in topology.devices
            if device.device_type == DeviceType.ROUTER
        ],
        "switches": [
            {"name": device.name}
            for device in topology.devices
            if device.device_type == DeviceType.SWITCH
        ]
    }
    return inventory
```

**Add API endpoint**:

```python
@router.post("/topology/export/ansible")
async def export_ansible_inventory(topology: Topology) -> dict:
    exporter = DeploymentExporter()
    inventory = exporter.export_to_ansible_inventory(topology)
    return inventory
```

### Adding Device Validation

**In models**:

```python
class Device(BaseModel):
    name: str
    device_type: DeviceType
    
    @validator("name")
    def validate_naming_convention(cls, v, values):
        """Enforce naming conventions"""
        if values.get("device_type") == DeviceType.ROUTER:
            if not v.startswith("R"):
                raise ValueError("Router names must start with 'R'")
        return v
```

### Adding Topology Constraints

**In generator**:

```python
class TopologyGenerator:
    def validate_topology(self, topology: Topology) -> bool:
        """Validate generated topology"""
        # All routers must be reachable from each other
        # No isolated switches
        # Minimum link count
        return True
```

## Performance Considerations

### 1. Topology Generation

**Current**: O(n²) for n devices
- Linear backbone: O(n)
- Random links: O(n*m) where m is connections per device
- Overall: O(n²) worst case

**Optimization**:
```python
# Cache computed values
@lru_cache(maxsize=256)
def get_network_address(ip, prefix):
    ...

# Use generators for large datasets
def generate_topologies(count):
    for i in range(count):
        yield self.generate(f"topo-{i}")
```

### 2. Configuration Generation

**Current**: Linear with device count
- For each device: O(links)
- Template rendering: O(config_size)

**Optimization**:
```python
# Batch process
configs = {
    device.name: render_template(ospf_config)
    for ospf_config in routing_config.ospf_configs
}

# Use async processing
async def generate_all_configs(routing_config):
    tasks = [
        render_config_async(config)
        for config in routing_config.ospf_configs
    ]
    return await asyncio.gather(*tasks)
```

### 3. Memory Usage

**Typical**:
- 1 topology (5 routers + 2 switches): ~100 KB
- Configuration (15 devices): ~50 KB
- YAML export: ~200 KB

**For scaling**: Use streaming/chunking for very large topologies

## Testing Strategy

### Unit Tests
```python
# Test individual components
test_topology_generator()
test_configuration_generator()
test_deployment_exporter()
```

### Integration Tests
```python
# Test complete pipelines
test_topology_generation_and_export()
test_configuration_generation_with_templates()
```

### API Tests
```python
# Test endpoints
test_endpoint_topology_generate()
test_endpoint_configuration_generate()
test_endpoint_export_containerlab()
```

## Security Architecture

### Input Validation
- Pydantic models validate all inputs
- Maximum values enforced (20 routers, 10 switches)
- String length validated

### Output Sanitization
- Jinja2 auto-escaping for templates
- YAML safe serialization
- No code injection possible

### Future Enhancements
- Add authentication layer
- Implement rate limiting per user
- Add audit logging
- Encrypted configuration storage

---

**For updating flows and patterns, refer to:**
- [Design Patterns Reference](https://refactoring.guru/design-patterns)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Design Philosophy](https://fastapi.tiangolo.com/)
