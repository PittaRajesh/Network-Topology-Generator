# Networking Automation Engine - Complete User Guide

A comprehensive guide to understanding and using the Networking Automation Engine, from basic setup to advanced features.

---

## Table of Contents

1. [What is This Project?](#what-is-this-project)
2. [Key Features](#key-features)
3. [Installation & Setup](#installation--setup)
4. [Quick Start (5 Minutes)](#quick-start-5-minutes)
5. [How to Use the System](#how-to-use-the-system)
6. [API Endpoints Reference](#api-endpoints-reference)
7. [Learning & Recommendation System](#learning--recommendation-system)
8. [Configuration Guide](#configuration-guide)
9. [Practical Examples](#practical-examples)
10. [Understanding the Architecture](#understanding-the-architecture)
11. [Advanced Usage](#advanced-usage)
12. [Troubleshooting](#troubleshooting)
13. [FAQ](#faq)
14. [Getting Help](#getting-help)

---

## What is This Project?

The **Networking Automation Engine** is an intelligent platform that automatically generates, analyzes, and optimizes computer network topologies using AI and machine learning.

### Purpose

This tool solves the common problem of **designing and testing network infrastructures**:

- **Network Engineers**: Quickly generate valid network topologies for testing
- **QA Teams**: Create consistent test environments for regression testing
- **Researchers**: Study network behavior under various configurations
- **System Architects**: Validate architecture decisions before implementation

### Real-World Scenario

Imagine you're a network engineer who needs to:
1. Design a network for a bank's 50 branch offices
2. Test how the network handles router failures
3. Optimize the design for cost and reliability
4. Quickly iterate on multiple design options

The Networking Automation Engine does all of this automatically.

---

## Key Features

### 🏗️ Core Capabilities

| Feature | What It Does |
|---------|-------------|
| **Topology Generation** | Automatically creates network diagrams with routers, switches, and connections |
| **OSPF Configuration** | Generates routing protocol configurations automatically |
| **Multi-Vendor Support** | Creates configs for Cisco, Linux, and other networking devices |
| **Containerlab Export** | Prepares networks to run in Docker containers for testing |
| **REST API** | Full API for programmatic access (no manual config needed) |

### 🧠 AI-Powered Analysis

| Feature | What It Does |
|---------|-------------|
| **SPOF Detection** | Finds "single points of failure" that could crash your network |
| **Failure Simulation** | Tests what happens when devices fail without affecting real networks |
| **Path Analysis** | Shows how data takes different routes through the network |
| **Health Scoring** | Ranks networks on a quality scale (0-100) |
| **Smart Optimization** | Suggests improvements to network design |

### 🤖 Learning System (NEW)

| Feature | What It Does |
|---------|-------------|
| **History Storage** | Remembers all topologies and their performance results |
| **Pattern Learning** | Identifies which network designs work best |
| **Smart Recommendations** | Suggests appropriate designs for your specific needs |
| **Autonomous Optimization** | Automatically improves design choices over time |
| **Performance Tracking** | Measures how well recommendations work |
| **Feedback Loop** | Gets smarter with each network you generate |

---

## Installation & Setup

### Prerequisites

- **Python 3.10 or higher** - Download from [python.org](https://www.python.org/)
- **pip** - Usually comes with Python
- **5-10 minutes** for setup

### Step 1: Check Python Installation

```bash
python --version
# Should show: Python 3.10.x or higher
```

### Step 2: Set Up Virtual Environment

**On Windows:**
```bash
cd networking-automation-engine
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
cd networking-automation-engine
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **NetworkX** - Graph algorithms for topology analysis
- **Jinja2** - Template engine for configs
- **SQLAlchemy** - Database ORM

### Step 4: Run the Application

```bash
python -m uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 5: Access the System

Open your browser and go to:

```
http://localhost:8000/docs
```

You'll see an interactive interface with all available API endpoints.

---

## Quick Start (5 Minutes)

### The Simplest Workflow

```bash
# 1. Start the server (from project directory)
python -m uvicorn app.main:app --reload

# 2. Open browser: http://localhost:8000/docs

# 3. Click on: POST /api/v1/topology/generate

# 4. Click "Try it out" and modify the JSON:
{
  "intent_name": "my_first_network",
  "sites": 5,
  "routers_per_site": 2,
  "switches_per_site": 3
}

# 5. Click "Execute" and you'll get a generated topology

# 6. Copy the topology ID returned, then go to:
# GET /api/v1/topology/{id}/export

# 7. You now have a network ready to deploy!
```

### What Just Happened?

1. You defined what you wanted (intent: a network with 5 sites)
2. The system generated a valid network design
3. The system created routing configurations
4. The system validated the design
5. You received a network ready to test

---

## How to Use the System

### Understanding the Basic Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Define Intent: "I need a 10-site network"           │
├─────────────────────────────────────────────────────────┤
│ 2. Generate Topology: System creates network design    │
├─────────────────────────────────────────────────────────┤
│ 3. Analyze: System checks for weaknesses               │
├─────────────────────────────────────────────────────────┤
│ 4. Recommend: System suggests improvements             │
├─────────────────────────────────────────────────────────┤
│ 5. Export: System creates deployment files             │
├─────────────────────────────────────────────────────────┤
│ 6. Learn: System stores results for future use         │
└─────────────────────────────────────────────────────────┘
```

### Three Main Use Cases

#### Use Case 1: Generate a Single Network

**What You Want**: A quick network topology for testing

**How to Do It**:
```python
import requests
import json

response = requests.post(
    "http://localhost:8000/api/v1/topology/generate",
    json={
        "intent_name": "quick_test",
        "sites": 5,
        "routers_per_site": 2,
        "switches_per_site": 3
    }
)

topology = response.json()
print(f"Network created with ID: {topology['id']}")
```

**What You Get**:
- A complete network topology
- List of devices and connections
- OSPF routing configuration
- Validation score (quality rating)

#### Use Case 2: Analyze Network Resilience

**What You Want**: To understand how your network handles failures

**How to Do It**:
```python
response = requests.post(
    "http://localhost:8000/api/v1/simulation/failure",
    json={
        "topology_id": "your_network_id",
        "failure_scenario": "node_down",
        "devices_to_fail": ["router1"]
    }
)

result = response.json()
print(f"Network impact: {result['resilience_impact']}%")
```

**What You Get**:
- Impact on network connectivity
- Which devices get isolated
- Recovery time estimates
- Recommendations for improvement

#### Use Case 3: Get Smart Recommendations

**What You Want**: Let the system suggest optimal network designs

**How to Do It**:
```python
response = requests.post(
    "http://localhost:8000/api/v1/learning/recommend-topology",
    json={
        "intent_name": "branch_network",
        "sites": 50,
        "redundancy_level": "high",
        "design_goal": "cost_optimized"
    }
)

recommendations = response.json()
for rec in recommendations['recommendations']:
    print(f"{rec['topology_type']}: Score {rec['confidence']}%")
```

**What You Get**:
- Top 5 recommended network designs
- Confidence scores (how sure the system is)
- Why each design is recommended
- Estimated costs and benefits

---

## API Endpoints Reference

### Overview

The system provides 18 REST API endpoints organized by function.

### 1. Topology Generation Endpoints

#### Generate a New Topology
```
POST /api/v1/topology/generate
```

**Parameters:**
- `intent_name` (string) - Name for this network
- `sites` (integer, 3-100) - Number of sites/locations
- `routers_per_site` (integer) - Routers at each site
- `switches_per_site` (integer) - Switches at each site
- `redundancy_level` (string) - "minimum", "standard", "high", or "critical"
- `design_goal` (string) - "cost_optimized", "redundancy_focused", "latency_optimized"

**Example:**
```json
{
  "intent_name": "datacenter_network",
  "sites": 3,
  "routers_per_site": 2,
  "switches_per_site": 4,
  "redundancy_level": "critical",
  "design_goal": "redundancy_focused"
}
```

**Response:**
```json
{
  "success": true,
  "id": "topo_123",
  "topology_type": "full_mesh",
  "num_devices": 18,
  "num_links": 24,
  "validation_score": 92,
  "estimated_cost": 150000
}
```

#### Get Topology Details
```
GET /api/v1/topology/{topology_id}
```

Returns complete topology information (devices, links, OSPF config).

#### Export for Deployment
```
GET /api/v1/topology/{topology_id}/export
```

Generates Containerlab YAML file ready for Docker deployment.

### 2. Analysis Endpoints

#### Analyze Network Health
```
POST /api/v1/analysis/health
```

**Parameters:**
- `topology_id` - Network to analyze

**Response:**
- Overall health score (0-100)
- SPOF (Single Points of Failure) detected
- Link coverage analysis
- Redundancy metrics

#### Check for SPOFs
```
POST /api/v1/analysis/spof
```

Identifies devices that, if they fail, break network connectivity.

#### Validate Design
```
POST /api/v1/analysis/validate
```

Checks if topology meets specified intent requirements.

### 3. Failure Simulation Endpoints

#### Simulate Node Failure
```
POST /api/v1/simulation/failure
```

**Parameters:**
```json
{
  "topology_id": "topo_123",
  "failure_scenario": "node_down",
  "devices_to_fail": ["router1"]
}
```

**Response:**
- Network connectivity impact
- Isolated devices
- Recovery time
- Alternative paths available

#### Simulate Link Failure
```
POST /api/v1/simulation/link-failure
```

Tests impact when network connections fail.

#### Run Cascade Failure Test
```
POST /api/v1/simulation/cascade
```

Simulates cascading failures (one failure triggers others).

### 4. Optimization Endpoints

#### Get Optimization Recommendations
```
POST /api/v1/optimization/recommendations
```

Suggests network improvements.

#### Optimize Design
```
POST /api/v1/optimization/improve
```

Automatically adjusts network design for better performance.

### 5. Learning & Recommendation Endpoints (NEW)

#### Get Smart Recommendations
```
POST /api/v1/learning/recommend-topology
```

**What It Does**: Analyzes historical data and recommends network designs.

**Parameters:**
```json
{
  "intent_name": "branch_office",
  "sites": 20,
  "redundancy_level": "high",
  "design_goal": "cost_optimized"
}
```

**Response:**
```json
{
  "success": true,
  "recommendations": [
    {
      "topology_type": "hub_spoke",
      "overall_score": 87,
      "confidence": 94,
      "pros": ["Cost-effective", "Easy to manage"],
      "cons": ["SPOF at hub"],
      "estimated_links": "~20",
      "recommendation_reason": "Strong historical performance"
    }
  ]
}
```

#### View Design History
```
GET /api/v1/learning/topology-history
```

**Parameters:**
- `topology_type` (optional) - Filter by network type
- `redundancy_level` (optional) - Filter by redundancy
- `days` (default: 30) - How far back to look
- `limit` (default: 100) - Max results to return

**Returns:** List of all previously generated networks and their performance.

#### Get Learning Analysis
```
POST /api/v1/learning/learning-report
```

**What It Does**: Comprehensive analysis of system learning and recommendations.

**Response:**
```json
{
  "learning_analysis": {
    "topologies_analyzed": 45,
    "insights": [
      {
        "type": "best_performer",
        "title": "Full Mesh Most Reliable",
        "description": "..."
      }
    ],
    "recommendations": [...]
  },
  "optimization_activity": {...},
  "key_findings": {...}
}
```

### 6. Intent & Configuration Endpoints

#### Parse Intent
```
POST /api/v1/intent/parse
```

Converts natural language into network requirements.

**Example:**
```json
{
  "intent": "I need a highly redundant network for 50 branch offices with emphasis on business continuity"
}
```

#### Get Configuration Template
```
GET /api/v1/configuration/template/{device_type}
```

Returns device configuration templates.

### 7. Deployment Endpoints

#### Export for Containerlab
```
GET /api/v1/deployment/containerlab/{topology_id}
```

Creates Docker Compose and Containerlab YAML files.

#### Generate Docker Compose
```
GET /api/v1/deployment/docker/{topology_id}
```

Creates ready-to-run Docker deployment files.

---

## Learning & Recommendation System

### How the Learning System Works

The Learning System makes the Networking Automation Engine intelligent by learning from experience.

#### The Learning Loop (4 Steps)

```
Step 1: RECORD
├─ Every topology generated is saved
├─ Validation results are stored
└─ Failure simulation outcomes recorded

Step 2: ANALYZE
├─ System identifies successful patterns
├─ Calculates performance metrics
└─ Groups similar designs by type

Step 3: LEARN
├─ Best performers are identified
├─ Confidence scores calculated
└─ Insights generated

Step 4: RECOMMEND
├─ New intent is matched to history
├─ Recommendations ranked by performance
└─ User selects and provides feedback
```

### Key Metrics Explained

#### Validation Score (0-100)
How well the network meets its requirements:
- **85-100**: Excellent - Meets all goals
- **70-84**: Good - Meets most goals
- **50-69**: Fair - Meets some goals
- **Below 50**: Poor - Needs improvement

#### Redundancy Score (0-100)
Network ability to survive component failures:
- **90-100**: Critical redundancy (every device has backup)
- **70-89**: High redundancy (most critical parts have backup)
- **50-69**: Standard redundancy (main links have backup)
- **Below 50**: Minimum redundancy (basic connectivity only)

#### Confidence Score (0-100)
How sure the system is about its recommendation:
- **80-100**: Very confident (many similar successful designs)
- **60-79**: Confident (several similar designs)
- **40-59**: Moderate confidence (some similar designs)
- **Below 40**: Low confidence (little data available)

### Using Recommendations Effectively

#### Step 1: Get Recommendations

```python
response = requests.post(
    "http://localhost:8000/api/v1/learning/recommend-topology",
    json={
        "intent_name": "expansion_network",
        "sites": 30,
        "redundancy_level": "high",
        "design_goal": "latency_optimized"
    }
)

recommendations = response.json()
```

#### Step 2: Review Top Recommendations

```python
for i, rec in enumerate(recommendations['recommendations'][:3], 1):
    print(f"\n{i}. {rec['topology_type'].upper()}")
    print(f"   Score: {rec['overall_score']}/100")
    print(f"   Confidence: {rec['confidence']}%")
    print(f"   Pros: {', '.join(rec['pros'])}")
    print(f"   Cons: {', '.join(rec['cons'])}")
    print(f"   Why: {rec['recommendation_reason']}")
```

#### Step 3: Generate Using Recommended Type

```python
# Use the recommended topology type
selected = recommendations['recommendations'][0]

response = requests.post(
    "http://localhost:8000/api/v1/topology/generate",
    json={
        "intent_name": "expansion_network",
        "sites": 30,
        "routers_per_site": 2,
        "switches_per_site": 3,
        "topology_type": selected['topology_type'],
        "redundancy_level": "high"
    }
)

new_topology = response.json()
print(f"Generated network ID: {new_topology['id']}")
```

#### Step 4: Get Feedback (Optional)

The system improves when you tell it how recommendations worked:

```python
# After testing the network...
requests.post(
    "http://localhost:8000/api/v1/learning/feedback",
    json={
        "recommendation_id": rec['id'],
        "feedback_score": 5,  # 1-5 stars
        "topology_id": new_topology['id']
    }
)
```

---

## Configuration Guide

### Environment Variables

Create a `.env` file in the project directory:

```env
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_ENV=development

# Database
DATABASE_URL=sqlite:///./networks.db
# For PostgreSQL: postgresql://user:password@localhost/networks

# Logging
LOG_LEVEL=INFO

# AI Features
USE_AI_ANALYSIS=true
AI_MODEL=gpt-3.5-turbo
```

### Database Configuration

#### Using SQLite (Default - No Setup Needed)

```python
# In app/config.py or .env
DATABASE_URL=sqlite:///./networks.db
```

The database file is created automatically.

#### Using PostgreSQL (Production)

```python
# In .env file
DATABASE_URL=postgresql://user:password@localhost:5432/networks

# Create database first:
# CREATE DATABASE networks;
# CREATE USER automation WITH PASSWORD 'secure_password';
# GRANT ALL PRIVILEGES ON DATABASE networks TO automation;
```

### Topology Generation Parameters

#### Redundancy Levels

- **minimum**: Single path between sites (cheapest, risky)
- **standard**: Primary + 1 backup path (balanced)
- **high**: Multiple paths with redundancy (safer)
- **critical**: Full mesh or near-full for maximum reliability

#### Design Goals

- **cost_optimized**: Minimize links and equipment
- **redundancy_focused**: Maximize fault tolerance
- **latency_optimized**: Minimize hop count
- **scalability**: Optimized for growth

#### Topology Types Explanation

| Type | Use Case | Cost | Complexity |
|------|----------|------|-----------|
| **Full Mesh** | Small networks (2-10 nodes) where every device connects to every other | High | Low |
| **Hub & Spoke** | Star topology with central hub; good for branch offices | Low | Low |
| **Ring** | Devices connected in circle; simple but limited | Medium | Low |
| **Tree** | Hierarchical structure; scales well | Medium | Medium |
| **Leaf-Spine** | Data centers; high performance, all paths equal cost | High | High |
| **Hybrid** | Combination of techniques; flexible but complex | Variable | High |

---

## Practical Examples

### Example 1: Design Network for Small Startup

**Scenario**: A startup with 3 offices needs a network. Budget is limited, but some redundancy is important.

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Get recommendations for our scenario
print("Getting recommendations...")
response = requests.post(
    f"{BASE_URL}/api/v1/learning/recommend-topology",
    json={
        "intent_name": "startup_network",
        "sites": 3,
        "redundancy_level": "standard",
        "design_goal": "cost_optimized"
    }
)

recommendations = response.json()
best = recommendations['recommendations'][0]
print(f"\nBest recommendation: {best['topology_type']}")
print(f"Confidence: {best['confidence']}%")

# Step 2: Generate the topology
print("\nGenerating network...")
response = requests.post(
    f"{BASE_URL}/api/v1/topology/generate",
    json={
        "intent_name": "startup_network",
        "sites": 3,
        "routers_per_site": 1,
        "switches_per_site": 2,
        "topology_type": best['topology_type'],
        "redundancy_level": "standard"
    }
)

topology = response.json()
topo_id = topology['id']
print(f"Network created: {topo_id}")
print(f"Quality score: {topology['validation_score']}/100")

# Step 3: Analyze for weaknesses
print("\nAnalyzing network health...")
response = requests.post(
    f"{BASE_URL}/api/v1/analysis/health",
    json={"topology_id": topo_id}
)

health = response.json()
if health['spofs_detected'] > 0:
    print(f"⚠️  Warning: {health['spofs_detected']} single points of failure found")
else:
    print("✅ No single points of failure")

# Step 4: Export for deployment
print("\nExporting for deployment...")
response = requests.get(
    f"{BASE_URL}/api/v1/topology/{topo_id}/export"
)

with open("network_config.yaml", "w") as f:
    f.write(response.text)
print("✅ Network configuration saved to network_config.yaml")
```

**Output:**
```
Getting recommendations...
Best recommendation: hub_spoke
Confidence: 89%

Generating network...
Network created: topo_abc123
Quality score: 84/100

Analyzing network health...
✅ No single points of failure

Exporting for deployment...
✅ Network configuration saved to network_config.yaml
```

### Example 2: Compare Network Designs

**Scenario**: You want to see how different designs perform and make an informed choice.

```python
import requests

BASE_URL = "http://localhost:8000"
SITES = 10

topology_types = ["hub_spoke", "ring", "tree"]

print("Comparing network designs for 10 sites...\n")

for topo_type in topology_types:
    # Generate topology
    response = requests.post(
        f"{BASE_URL}/api/v1/topology/generate",
        json={
            "intent_name": f"comparison_{topo_type}",
            "sites": SITES,
            "routers_per_site": 2,
            "switches_per_site": 3,
            "topology_type": topo_type,
            "redundancy_level": "high"
        }
    )
    
    topo = response.json()
    topo_id = topo['id']
    
    # Analyze
    response = requests.post(
        f"{BASE_URL}/api/v1/analysis/health",
        json={"topology_id": topo_id}
    )
    
    health = response.json()
    
    # Test failure
    response = requests.post(
        f"{BASE_URL}/api/v1/simulation/failure",
        json={
            "topology_id": topo_id,
            "failure_scenario": "node_down",
            "devices_to_fail": ["router1"]
        }
    )
    
    simulation = response.json()
    
    # Print comparison
    print(f"{topo_type.upper()}")
    print(f"  Devices: {topo['num_devices']}")
    print(f"  Links: {topo['num_links']}")
    print(f"  Health Score: {topo['validation_score']}/100")
    print(f"  Single Points of Failure: {health['spofs_detected']}")
    print(f"  Recovery Time if router fails: {simulation['recovery_time_ms']}ms")
    print()
```

**Output:**
```
HUB_SPOKE
  Devices: 23
  Links: 11
  Health Score: 78/100
  Single Points of Failure: 1
  Recovery Time if router fails: 450ms

RING
  Devices: 23
  Links: 20
  Health Score: 85/100
  Single Points of Failure: 0
  Recovery Time if router fails: 200ms

TREE
  Devices: 23
  Links: 19
  Health Score: 82/100
  Single Points of Failure: 2
  Recovery Time if router fails: 320ms
```

### Example 3: Stress Test with Multiple Failures

**Scenario**: You want to see how your network handles multiple simultaneous failures.

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a network
response = requests.post(
    f"{BASE_URL}/api/v1/topology/generate",
    json={
        "intent_name": "stress_test",
        "sites": 8,
        "routers_per_site": 3,
        "switches_per_site": 2,
        "redundancy_level": "critical"
    }
)

topo_id = response.json()['id']
print(f"Testing network: {topo_id}\n")

# Simulate different failure scenarios
scenarios = [
    {
        "name": "Single Router Failure",
        "failure_scenario": "node_down",
        "devices_to_fail": ["router1"]
    },
    {
        "name": "Multiple Router Failures",
        "failure_scenario": "node_down",
        "devices_to_fail": ["router1", "router2", "router3"]
    },
    {
        "name": "Cascading Failure",
        "failure_scenario": "cascade",
        "devices_to_fail": ["router1"]
    }
]

results = []

for scenario in scenarios:
    response = requests.post(
        f"{BASE_URL}/api/v1/simulation/failure",
        json={
            "topology_id": topo_id,
            "failure_scenario": scenario['failure_scenario'],
            "devices_to_fail": scenario['devices_to_fail']
        }
    )
    
    result = response.json()
    results.append({
        "scenario": scenario['name'],
        "impact": result['resilience_impact'],
        "recovery_time": result['recovery_time_ms'],
        "isolated": len(result['isolated_devices'])
    })

# Print results
print("Failure Scenario Results:")
print("-" * 60)
for r in results:
    status = "✅ PASS" if r['impact'] < 30 else "⚠️  FAIL"
    print(f"{r['scenario']:<30} {status}")
    print(f"  Impact: {r['impact']}%")
    print(f"  Isolated Devices: {r['isolated']}")
    print(f"  Recovery Time: {r['recovery_time']}ms")
    print()
```

---

## Understanding the Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI Application              │
├─────────────────────────────────────────────────────┤
│  API Layer (routes.py)                              │
│  ├─ Topology Endpoints                              │
│  ├─ Analysis Endpoints                              │
│  ├─ Simulation Endpoints                            │
│  ├─ Learning Endpoints                              │
│  └─ Deployment Endpoints                            │
├─────────────────────────────────────────────────────┤
│  Core Modules                                       │
│  ├─ Generator (topology.py)                         │
│  │  └─ Creates network designs                      │
│  ├─ Analysis (analysis/)                            │
│  │  └─ Evaluates network quality                    │
│  ├─ Simulation (simulation/)                        │
│  │  └─ Tests failure scenarios                      │
│  ├─ Learning (learning/)                            │
│  │  ├─ analyzer.py - Pattern analysis              │
│  │  └─ optimizer.py - Auto-optimization             │
│  ├─ Recommendation (recommendation/)                │
│  │  └─ recommender.py - Smart suggestions           │
│  ├─ History (history/)                              │
│  │  └─ manager.py - Data storage                    │
│  └─ Validation (validation/)                        │
│     └─ Checks requirements met                      │
├─────────────────────────────────────────────────────┤
│  Data Layer (Database)                              │
│  ├─ Topology Records                                │
│  ├─ Validation Scores                               │
│  ├─ Simulation Results                              │
│  ├─ Performance Metrics                             │
│  ├─ Recommendations History                         │
│  └─ Optimization Logs                               │
└─────────────────────────────────────────────────────┘
```

### Key Classes and Functions

#### Topology Generator

```python
from app.generator.topology import TopologyGenerator

generator = TopologyGenerator(
    sites=10,
    routers_per_site=2,
    switches_per_site=3
)

topology = generator.generate()
# Returns: NetworkX graph with all connections
```

#### Network Analyzer

```python
from app.analysis.analyzer import NetworkAnalyzer

analyzer = NetworkAnalyzer(topology)

# Check for weaknesses
spofs = analyzer.find_spofs()
score = analyzer.calculate_health_score()
redundancy = analyzer.calculate_redundancy()
```

#### Failure Simulator

```python
from app.simulation.failure import FailureSimulator

simulator = FailureSimulator(topology)

# Test what happens if a device fails
result = simulator.simulate_node_failure("router1")
print(f"Network impact: {result['resilience_impact']}%")
```

#### Learning System

```python
from app.learning.analyzer import LearningAnalyzer
from app.learning.optimizer import AutonomousOptimizer
from app.recommendation.recommender import RecommendationEngine

# Analyze historical data
analyzer = LearningAnalyzer(db_session)
analysis = analyzer.analyze_all()

# Get recommendations
engine = RecommendationEngine(db_session)
recommendations = engine.recommend_topologies(intent)

# Autonomous optimization
optimizer = AutonomousOptimizer(db_session)
improved_type = optimizer.optimize_generation(intent, original_type)
```

---

## Advanced Usage

### Custom Topology Types

Create your own topology pattern:

```python
from app.generator.topology import TopologyGenerator

class CustomRingMesh(TopologyGenerator):
    """Ring with mesh backbone"""
    
    def generate(self):
        # Get base ring
        graph = super().generate()
        
        # Add mesh connections between core routers
        core_routers = [d for d in graph.nodes() 
                       if 'core' in d.lower()]
        
        for i, r1 in enumerate(core_routers):
            for r2 in core_routers[i+1:]:
                graph.add_edge(r1, r2, weight=1)
        
        return graph
```

### Custom Scoring Rules

Define what makes a good network for your use case:

```python
from app.validation.validator import NetworkValidator

class CustomValidator(NetworkValidator):
    """Bank-specific network requirements"""
    
    def validate(self, topology):
        base_score = super().validate(topology)
        
        # Banks need high redundancy (worth 30% of score)
        redundancy = self._check_redundancy(topology)
        
        # Banks need low latency (worth 20% of score)  
        latency = self._check_latency(topology)
        
        # Banks need SPOF-free (worth 50% of score)
        spof_free = self._check_spof_free(topology)
        
        return {
            'base': base_score,
            'redundancy': redundancy * 0.3,
            'latency': latency * 0.2,
            'spof_free': spof_free * 0.5,
            'total': base_score + (redundancy * 0.3) + (latency * 0.2) + (spof_free * 0.5)
        }
```

### Batch Processing Networks

Generate and analyze multiple networks automatically:

```python
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

configs = [
    {"sites": 5, "redundancy": "minimum", "goal": "cost_optimized"},
    {"sites": 10, "redundancy": "standard", "goal": "balanced"},
    {"sites": 15, "redundancy": "high", "goal": "reliability"},
]

results = []

for config in configs:
    # Generate
    response = requests.post(
        f"{BASE_URL}/api/v1/topology/generate",
        json={
            "intent_name": f"batch_{config['sites']}",
            "sites": config['sites'],
            "routers_per_site": 2,
            "switches_per_site": 3,
            "redundancy_level": config['redundancy'],
            "design_goal": config['goal']
        }
    )
    
    topo = response.json()
    
    # Store result
    results.append({
        "config": config,
        "topology_id": topo['id'],
        "score": topo['validation_score'],
        "timestamp": datetime.now().isoformat()
    })

# Export results
with open("batch_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Generated {len(results)} topologies")
```

### Webhook Integration

Post results to your own system:

```python
import requests
import json

BASE_URL = "http://localhost:8000"
WEBHOOK_URL = "https://your-system.com/webhooks/network-generated"

# Generate topology
response = requests.post(
    f"{BASE_URL}/api/v1/topology/generate",
    json={...}
)

topology = response.json()

# Send to your system
requests.post(
    WEBHOOK_URL,
    json={
        "event": "topology_generated",
        "topology_id": topology['id'],
        "score": topology['validation_score'],
        "devices": topology['num_devices'],
        "links": topology['num_links']
    }
)
```

---

## Troubleshooting

### Problem: "Failed to connect to localhost:8000"

**Cause**: Server is not running

**Solution**:
```bash
# In project directory, activate virtual environment first:
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Then start server:
python -m uvicorn app.main:app --reload
```

### Problem: "ModuleNotFoundError: No module named 'fastapi'"

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

### Problem: "Database connection error"

**Cause**: Database file not accessible or corrupt

**Solution**:
```bash
# Delete old database
rm networks.db  # Linux/macOS
del networks.db # Windows

# Application will create new database automatically on next run
```

### Problem: "API returns status 422 with validation error"

**Cause**: Invalid parameters in request

**Solution**: Check your JSON:
```python
# WRONG:
{"sites": "10"}  # String instead of number

# CORRECT:
{"sites": 10}    # Number
```

### Problem: "Topology generation is too slow"

**Cause**: Large network size or slow computer

**Solution**:
```bash
# Use smaller networks first to test
{"sites": 3, "routers_per_site": 1, "switches_per_site": 1}

# Python is slower than compiled languages - this is expected
# For production, consider deploying in Docker
```

### Problem: "Recommendations are generic/not helpful"

**Cause**: Not enough historical data

**Solution**:
```python
# The system learns from history
# Generate 10-20 topologies with different parameters
# Then recommendations will be more specific

# You can also check confidence score:
# - Low confidence (< 40%) means little learning data
# - High confidence (> 80%) means many similar topologies tested
```

---

## FAQ

### Q: Can this replace my network engineer?

**A**: No. The system is a tool TO HELP engineers:
- **Before**: Network design took weeks of planning → Now takes minutes
- **Validation**: System finds issues engineers might miss
- **Testing**: Quickly test multiple design options
- **Documentation**: Automatic config generation saves time

Engineers still provide requirements, approval, and oversight.

### Q: How accurate are the failure simulations?

**A**: The simulations are simplified models:
- They show CONNECTIVITY impact (good for topology design)
- They don't include: performance degradation, software bugs, manual errors
- **Use for**: Testing network design, finding SPOFs
- **Don't use for**: Predicting exact outage duration, real-world performance

### Q: Can I use this for my current production network?

**A**: Not directly, but concepts apply:
- Export generated topologies as documentation
- Use recommendations as design guidelines
- Use failure simulations to test your design
- Not designed to directly replace your network

### Q: How many devices can it handle?

**A**: Tested up to 500 devices. Beyond that:
- Generation still works but gets slower
- Analysis may be slow
- For very large networks, use hierarchical approach (separate per-region networks)

### Q: Does it support BGP or other protocols?

**A**: Currently supports OSPF:
- Architecture allows adding protocols
- BGP support is planned for future versions
- Community contributions welcome

### Q: Can I export to actual network devices?

**A**: Partial support:
- Exports OSPF configurations in text format
- Containerlab export for Docker testing
- Not designed for direct device deployment
- Use professionally-built tools (Terraform, Ansible) for production

### Q: Is my data private?

**A**: Complete privacy by default:
- All data stored locally in SQLite
- No cloud upload (unless you configure PostgreSQL remote)
- No external API calls (unless you add AI features)
- Open source - audit the code yourself

### Q: What about Docker and Kubernetes?

**A**: Full support:
- Docker Compose export included
- Containerlab YAML generation
- Kubernetes manifests (in deployment/)
- Ready for docker-compose up

### Q: Can I integrate this with existing tools?

**A**: Yes, via REST API:
- Terraform: Generate topologies, output as JSON
- Ansible: Call API endpoints, parse JSON responses
- Custom scripts: Use Python requests or curl to API

---

## Getting Help

### Documentation Resources

| Resource | Location | Best For |
|----------|----------|----------|
| **START_HERE.md** | Project root | Quick overview |
| **README.md** | Project root | Features and setup |
| **This Guide** | COMPLETE_USER_GUIDE.md | Learning and how-to |
| **ARCHITECTURE.md** | Project root | Extending system |
| **API Examples** | Examples folder | Code examples |
| **Interactive API Docs** | http://localhost:8000/docs | Trying API endpoints |
| **Source Code Comments** | app/ directory | Understanding implementation |

### Step-by-Step Troubleshooting

If something isn't working:

1. **Check if server is running**
   ```bash
   # Open http://localhost:8000/docs in browser
   # You should see the API interface
   ```

2. **Verify dependencies**
   ```bash
   pip list | grep -E "fastapi|pydantic|networkx"
   ```

3. **Check application logs**
   ```bash
   # Server output in terminal shows errors
   # Look for red text or "ERROR" messages
   ```

4. **Review the interactive API docs**
   ```
   http://localhost:8000/docs
   Click on an endpoint → Click "Try it out" → Check response
   ```

5. **Test with minimal example**
   ```python
   import requests
   response = requests.get("http://localhost:8000/api/v1/health")
   print(response.json())  # Should show {"status": "healthy"}
   ```

### Getting Code Help

The code is well-documented:

```python
# Every class has a docstring explaining what it does
# Example from app/generator/topology.py:

class TopologyGenerator:
    """
    Generates network topologies based on intent.
    
    Attributes:
        sites: Number of network sites
        routers_per_site: Routers at each location
        switches_per_site: Switches at each location
    
    Example:
        generator = TopologyGenerator(sites=5)
        topology = generator.generate()
    """
```

### Community & Support

- **GitHub Issues**: Report bugs or request features
- **Code Comments**: Check existing code for how to extend
- **Examples Folder**: See working examples of common tasks
- **Test Files**: Look at tests/ folder for usage patterns

### Before Asking for Help

Try these steps:

1. ✅ Read the relevant documentation
2. ✅ Check if your code matches the examples
3. ✅ Verify dependencies are installed
4. ✅ Look at the interactive API docs
5. ✅ Review error messages carefully
6. ✅ Try the simplest possible example

---

## Next Steps

### Beginner Path

1. Run the application following "Installation & Setup"
2. Try generating a topology via the web interface
3. Read "How to Use the System" section
4. Try Example 1 from "Practical Examples"

### Intermediate Path

1. Complete Beginner path
2. Try all 3 practical examples
3. Understand Learning System (read that section)
4. Experiment with your own use cases
5. Review "Advanced Usage" section

### Advanced Path

1. Complete Intermediate path
2. Read ARCHITECTURE.md for technical details
3. Review source code in app/ directory
4. Extend with custom validators or generators
5. Consider contributing improvements back

### Production Path

1. Follow all previous paths
2. Set up PostgreSQL database (not SQLite)
3. Configure environment variables properly
4. Deploy using Docker-Compose or Kubernetes
5. Set up monitoring and logging
6. Review DEPLOYMENT.md for details

---

## Summary

The Networking Automation Engine is a comprehensive tool for:

✅ **Quick Design**: Generate network topologies in seconds  
✅ **Smart Analysis**: Identify weaknesses and single points of failure  
✅ **Failure Testing**: Understand how networks handle outages  
✅ **Learning System**: Improve recommendations over time  
✅ **Rapid Testing**: Validate designs before implementation  

It's designed to be **easy to use** but **powerful enough** for professional network engineering work.

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Compatible With**: Networking Automation Engine v2.0+

For the latest documentation, visit the project repository.
