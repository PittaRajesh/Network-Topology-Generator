"""
API Request Examples and Test Collection

This file contains example requests that can be used with curl, Postman,
or any other HTTP client. Copy and paste the examples to test the API.
"""

# ============================================================================
# CURL EXAMPLES
# ============================================================================

"""
1. Health Check
"""
curl -X GET "http://localhost:8000/" \
  -H "accept: application/json"

"""
2. Get API Information
"""
curl -X GET "http://localhost:8000/api/v1/info" \
  -H "accept: application/json"

"""
3. Generate Basic Topology (3 routers, 2 switches)
"""
curl -X POST "http://localhost:8000/api/v1/topology/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "basic-topology",
    "num_routers": 3,
    "num_switches": 2,
    "seed": null
  }'

"""
4. Generate Reproducible Topology (with seed)
"""
curl -X POST "http://localhost:8000/api/v1/topology/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "reproducible-lab",
    "num_routers": 5,
    "num_switches": 2,
    "seed": 42
  }'

"""
5. Generate Large Topology
"""
curl -X POST "http://localhost:8000/api/v1/topology/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "large-datacenter",
    "num_routers": 15,
    "num_switches": 8,
    "seed": null
  }'

"""
6. Export Topology to Containerlab Format
   
   Note: You'll need to first generate a topology and use its output
"""
curl -X POST "http://localhost:8000/api/v1/topology/export/containerlab?image=frrouting%2Ffrr%3Alatest" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "export-test",
    "num_routers": 3,
    "num_switches": 1,
    "devices": [],
    "links": [],
    "routing_protocol": "ospf"
  }'

"""
7. Export Topology to YAML
"""
curl -X POST "http://localhost:8000/api/v1/topology/export/yaml" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "yaml-export",
    "num_routers": 4,
    "num_switches": 2,
    "devices": [],
    "links": [],
    "routing_protocol": "ospf"
  }'

"""
8. Generate OSPF Configuration
   
   Note: You need to pass a full topology object from generate endpoint
"""
curl -X POST "http://localhost:8000/api/v1/configuration/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "config-test",
    "num_routers": 3,
    "num_switches": 1,
    "devices": [],
    "links": [],
    "routing_protocol": "ospf"
  }'

"""
9. Get Topology Statistics
"""
curl -X GET "http://localhost:8000/api/v1/stats/topology" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "stats-test",
    "num_routers": 5,
    "num_switches": 2,
    "devices": [],
    "links": [],
    "routing_protocol": "ospf"
  }'


# ============================================================================
# PYTHON REQUESTS EXAMPLES
# ============================================================================

"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Health check
response = requests.get(f"{BASE_URL}/")
print(response.json())

# 2. Generate topology
topo_request = {
    "name": "python-test",
    "num_routers": 4,
    "num_switches": 2,
    "seed": 123
}
response = requests.post(
    f"{BASE_URL}/api/v1/topology/generate",
    json=topo_request
)
topology = response.json()
print(f"Generated topology: {topology['name']}")
print(f"Devices: {len(topology['devices'])}")

# 3. Export to Containerlab
response = requests.post(
    f"{BASE_URL}/api/v1/topology/export/containerlab?image=frrouting/frr:latest",
    json=topology
)
containerlab = response.json()
print(json.dumps(containerlab, indent=2))

# 4. Export to YAML
response = requests.post(
    f"{BASE_URL}/api/v1/topology/export/yaml",
    json=topology
)
yaml_export = response.json()
print(yaml_export['yaml_content'])

# 5. Generate configuration
response = requests.post(
    f"{BASE_URL}/api/v1/configuration/generate",
    json=topology
)
config = response.json()
print(f"Generated configs for {len(config['device_configurations'])} devices")

# 6. Get statistics
response = requests.post(
    f"{BASE_URL}/api/v1/stats/topology",
    json=topology
)
stats = response.json()
print(json.dumps(stats, indent=2))
"""


# ============================================================================
# POSTMAN COLLECTION (JSON)
# ============================================================================

"""
Import this into Postman as a new collection.

{
  "info": {
    "name": "Networking Automation Engine API",
    "description": "API for generating network topologies and configurations",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000"
        }
      }
    },
    {
      "name": "API Information",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/api/v1/info",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "info"]
        }
      }
    },
    {
      "name": "Generate Topology",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\\n  \\\"name\\\": \\\"test-topology\\\",\\n  \\\"num_routers\\\": 5,\\n  \\\"num_switches\\\": 3,\\n  \\\"seed\\\": null\\n}"
        },
        "url": {
          "raw": "http://localhost:8000/api/v1/topology/generate",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "topology", "generate"]
        }
      }
    },
    {
      "name": "Generate Configuration",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{ }"
        },
        "description": "Paste the topology response from 'Generate Topology' here",
        "url": {
          "raw": "http://localhost:8000/api/v1/configuration/generate",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "configuration", "generate"]
        }
      }
    },
    {
      "name": "Export to Containerlab",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{ }"
        },
        "description": "Paste the topology response here",
        "url": {
          "raw": "http://localhost:8000/api/v1/topology/export/containerlab?image=frrouting/frr:latest",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "topology", "export", "containerlab"],
          "query": [
            {
              "key": "image",
              "value": "frrouting/frr:latest"
            }
          ]
        }
      }
    },
    {
      "name": "Export to YAML",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{ }"
        },
        "description": "Paste the topology response here",
        "url": {
          "raw": "http://localhost:8000/api/v1/topology/export/yaml",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "topology", "export", "yaml"]
        }
      }
    }
  ]
}
"""
