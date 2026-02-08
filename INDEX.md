# Networking Automation Engine - Quick Index

Welcome to the **Networking Automation Engine**! This is a complete, production-ready network automation system. Use this index to navigate the project.

## 🚀 Start Here

**New to the project?**
1. Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 5 min overview
2. Read [README.md](README.md) - Features and getting started
3. Run the application (see "Running the Application" below)
4. Try [examples.py](examples.py) - Working code examples

## 📁 Documentation Files

| File | Purpose | Best For |
|------|---------|----------|
| [README.md](README.md) | Quick start, features, API reference | Getting started, API examples |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, patterns, extension | Understanding design, extending |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment options, production setup | DevOps, deployment |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete project overview | Project understanding |
| [API_EXAMPLES.py](API_EXAMPLES.py) | curl, Python, Postman examples | Testing API |

## 💻 Code Organization

```
app/
├── main.py                 # FastAPI application entry point
├── api/routes.py           # 6 REST API endpoints
├── generator/topology.py    # Topology generation (300 lines)
├── core/configuration.py    # OSPF configuration (130 lines)
├── deployment/exporter.py   # Export to Containerlab/YAML (220 lines)
├── models/                 # Pydantic data models
│   ├── topology.py
│   ├── configuration.py
│   └── deployment.py
├── utils/ipaddr.py         # IP address utilities
└── config/settings.py      # Configuration management

templates/
├── ospf_router.j2          # OSPF configuration template
├── cisco_config.j2         # Cisco IOS template
└── linux_network.j2        # Linux network template

tests/test_engine.py        # 25+ unit tests
examples.py                 # 7 working examples
```

## ▶️ Running the Application

### Option 1: PowerShell (Windows)
```bash
.\run.ps1
```

### Option 2: Bash (Linux/macOS)
```bash
chmod +x run.sh
./run.sh
```

### Option 3: Manual
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then visit: **http://localhost:8000/docs**

## 🔌 API Endpoints

All endpoints documented at http://localhost:8000/docs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/api/v1/info` | GET | API information |
| `/api/v1/topology/generate` | POST | **Generate topology** |
| `/api/v1/configuration/generate` | POST | **Generate OSPF config** |
| `/api/v1/topology/export/containerlab` | POST | **Export to Containerlab** |
| `/api/v1/topology/export/yaml` | POST | **Export to YAML** |
| `/api/v1/stats/topology` | GET | Topology statistics |

**See [README.md](README.md#-api-endpoints) for detailed endpoint documentation and examples.**

## 🎯 Common Tasks

### Generate a Topology
```bash
curl -X POST http://localhost:8000/api/v1/topology/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-lab",
    "num_routers": 5,
    "num_switches": 2,
    "seed": 42
  }'
```

### Generate Configuration
See [API_EXAMPLES.py](API_EXAMPLES.py) for complete request body

### Export to Containerlab
```bash
curl -X POST http://localhost:8000/api/v1/topology/export/containerlab \
  -H "Content-Type: application/json" \
  -d @topology.json
```

### Run Python Examples
```bash
python examples.py
```

### Run Tests
```bash
pip install pytest
pytest tests/test_engine.py -v
```

## 📖 Learning Paths

### Path 1: Quick Start (30 minutes)
1. Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
2. Run the application
3. Try [API_EXAMPLES.py](API_EXAMPLES.py)
4. Visit http://localhost:8000/docs

### Path 2: Understanding Design (1-2 hours)
1. Read [README.md](README.md) - Features
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) - Design patterns
3. Review `app/generator/topology.py` - Main logic
4. Review `tests/test_engine.py` - How it works

### Path 3: Extending System (2-3 hours)
1. Read [ARCHITECTURE.md](ARCHITECTURE.md#extending-the-system)
2. Study `app/core/configuration.py`
3. Follow BGP addition example in ARCHITECTURE.md
4. Create new protocol generator
5. Add API endpoint

### Path 4: Deploying to Production (1-2 hours)
1. Read [DEPLOYMENT.md](DEPLOYMENT.md)
2. Choose deployment option (Docker, K8s, Cloud)
3. Follow deployment steps
4. Configure for your environment

## 🔧 Key Features

✅ **Topology Generation**
- Generate random but valid L2/L3 topologies
- 2-20 routers, 0-10 switches
- Reproducible with seed
- Automatic IP allocation

✅ **Configuration Generation**
- OSPF routing configurations
- Interface configurations
- Network statements
- Extensible for BGP, ISIS

✅ **Export Formats**
- Containerlab YAML (production-ready)
- Universal YAML format
- Device configuration text
- Multiple vendor templates

✅ **REST API**
- 6 endpoints
- Full input validation
- Comprehensive error handling
- OpenAPI documentation

✅ **Clean Code**
- Type hints throughout
- Pydantic models for validation
- Clean architecture
- 25+ unit tests
- Well documented

## 🚨 Troubleshooting

### Port already in use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :8000
kill -9 <PID>
```

### Module not found
```bash
pip install -r requirements.txt --force-reinstall
```

### Template not found
```bash
# Verify templates exist
ls templates/
# Check template_dir in app/config/settings.py
```

### API not responding
```bash
# Check application is running
curl http://localhost:8000/
# Check logs for errors
# Verify port 8000 is not blocked
```

### Tests failing
```bash
pip install pytest
pytest tests/ -v --tb=short
```

## 📚 Documentation Map

```
Getting Started
├── PROJECT_SUMMARY.md ← Start here
├── README.md ← Features & examples
└── Quick Index ← You are here

Understanding System
├── README.md (Architecture section)
├── ARCHITECTURE.md ← Deep dive
└── app/ (source code)

Using API
├── README.md (API Endpoints)
├── API_EXAMPLES.py
├── examples.py
└── http://localhost:8000/docs (live)

Deploying
└── DEPLOYMENT.md ← All options

Extending
├── ARCHITECTURE.md (Extending section)
└── examples in code comments
```

## 🔗 External References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Containerlab Documentation](https://containerlab.dev/)
- [OSPF RFC 2328](https://tools.ietf.org/html/rfc2328)
- [Design Patterns](https://refactoring.guru/design-patterns)

## ❓ FAQ

**Q: Do I need to install Python?**
A: Yes, Python 3.10+ is required. Verify with `python --version`

**Q: How do I use this in production?**
A: See [DEPLOYMENT.md](DEPLOYMENT.md) for all deployment options

**Q: How do I add support for BGP?**
A: Follow the example in [ARCHITECTURE.md](ARCHITECTURE.md#adding-new-routing-protocol)

**Q: Can I use this offline?**
A: Yes! No external API calls are made. All processing is local.

**Q: How do I contribute?**
A: The code is yours! Feel free to extend and modify. Follow patterns in ARCHITECTURE.md

**Q: What's the performance?**
A: See performance section in [ARCHITECTURE.md](ARCHITECTURE.md#performance-considerations)

**Q: Is this suitable for production?**
A: Yes! It includes logging, error handling, validation, and deployment guides.

**Q: Can I use this in a Docker container?**
A: Yes! See [DEPLOYMENT.md](DEPLOYMENT.md#docker-deployment)

**Q: How do I run tests?**
A: Run `pytest tests/test_engine.py -v` (requires pytest)

## 📊 Project Statistics

- **2,500+ lines** of Python code
- **2,000+ lines** of documentation
- **25+ unit tests**
- **6 REST API endpoints**
- **7 working examples**
- **Production-ready deployment guides**

## ✨ Key Files to Review

For understanding how it works, read these in order:

1. **app/models/topology.py** (70 lines) - Data structures
2. **app/generator/topology.py** (150 lines) - Main algorithm
3. **app/core/configuration.py** (130 lines) - Config generation
4. **app/deployment/exporter.py** (220 lines) - Export logic
5. **app/api/routes.py** (250 lines) - API endpoints

Each file has comprehensive docstrings explaining the logic.

---

**Version**: 1.0.0  
**Python**: 3.10+  
**Status**: ✅ Production Ready  
**License**: Provided as-is for use

**Get Started**: 
1. Run the application (`./run.ps1` or `./run.sh`)
2. Visit http://localhost:8000/docs
3. Try generating a topology!

Happy automating! 🚀
