# Networking Automation Engine - Deployment Guide

## Production Deployment

### Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Build and Run

```bash
# Build image
docker build -t networking-automation-engine:latest .

# Run container
docker run -p 8000:8000 networking-automation-engine:latest

# Run with volume mount for persistent data
docker run -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  networking-automation-engine:latest
```

### Docker Compose Deployment

#### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - DEBUG=False
    volumes:
      - ./templates:/app/templates
      - ./configs:/app/configs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  # Optional: Add database for configuration storage
  database:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: networking_automation
      POSTGRES_USER: automation
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Deploy with Docker Compose

```bash
docker-compose up -d
```

### Kubernetes Deployment

#### 1. Create Namespace

```bash
kubectl create namespace networking-automation
```

#### 2. Create ConfigMap for templates

```bash
kubectl create configmap net-templates \
  --from-file=templates/ \
  -n networking-automation
```

#### 3. Create Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: networking-engine
  namespace: networking-automation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: networking-engine
  template:
    metadata:
      labels:
        app: networking-engine
    spec:
      containers:
      - name: api
        image: networking-automation-engine:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/info
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        volumeMounts:
        - name: templates
          mountPath: /app/templates
      volumes:
      - name: templates
        configMap:
          name: net-templates
```

#### 4. Create Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: networking-engine-service
  namespace: networking-automation
spec:
  selector:
    app: networking-engine
  type: LoadBalancer
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
```

#### 5. Deploy to Kubernetes

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods -n networking-automation
kubectl get svc -n networking-automation
```

### Cloud Platform Deployment

#### AWS ECS

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name networking-automation

# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster networking-automation \
  --service-name networking-engine \
  --task-definition networking-engine:1 \
  --desired-count 3
```

#### Google Cloud Run

```bash
# Build image
gcloud builds submit --tag gcr.io/PROJECT_ID/networking-engine

# Deploy
gcloud run deploy networking-engine \
  --image gcr.io/PROJECT_ID/networking-engine \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated
```

## Monitoring and Observability

### Prometheus Metrics

Add to `app/main.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
topology_generations = Counter(
    'topology_generations_total',
    'Total topologies generated'
)
generation_duration = Histogram(
    'topology_generation_seconds',
    'Time spent generating topology'
)

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

### Structured Logging

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
)
```

### ELK Stack Integration

```yaml
# docker-compose-elk.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    depends_on:
      - logstash

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
```

## Performance Optimization

### 1. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_topology_template(template_name: str):
    # Load template
    pass
```

### 2. Async Processing

```python
from background jobs import BackgroundTasks

@app.post("/topology/generate")
async def generate_topology(request: TopologyRequest, background_tasks: BackgroundTasks):
    topology = generate_sync(request)
    background_tasks.add_task(export_topology, topology)
    return topology
```

### 3. Database Optimization

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

## Security Hardening

### 1. HTTPS/TLS

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with HTTPS
uvicorn app.main:app \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

### 2. Authentication

```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@app.post("/api/v1/topology/generate")
async def generate_topology(
    request: TopologyRequest,
    credentials: HTTPAuthCredentials = Depends(security)
):
    # Validate token
    pass
```

### 3. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/topology/generate")
@limiter.limit("10/minute")
async def generate_topology(request: TopologyRequest):
    pass
```

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump networking_automation > backup.sql

# Restore
psql networking_automation < backup.sql
```

### Configuration Backup

```bash
# Automated backup
aws s3 sync ./configs s3://backup-bucket/configs/

# Or with rsync
rsync -avz ./configs backup-server:/backups/
```

## Health Checks

```bash
# Simple health check
curl http://localhost:8000/

# Detailed health check
curl http://localhost:8000/api/v1/info

# Kubernetes liveness probe
curl -f http://localhost:8000/ || exit 1

# Readiness probe
curl -f http://localhost:8000/api/v1/info || exit 1
```

## Load Testing

Using Apache Bench:

```bash
ab -n 1000 -c 10 http://localhost:8000/

# With POST data
ab -n 1000 -c 10 -p payload.json -T application/json http://localhost:8000/api/v1/topology/generate
```

Using wrk:

```bash
wrk -t12 -c400 -d30s http://localhost:8000/
```

Using locust:

```python
# locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def generate_topology(self):
        self.client.post("/api/v1/topology/generate", json={
            "name": "test",
            "num_routers": 5,
            "num_switches": 2
        })
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill process using port 8000
   lsof -i :8000
   kill -9 <PID>
   ```

2. **Module import errors**
   ```bash
   # Reinstall requirements
   pip install --force-reinstall -r requirements.txt
   ```

3. **Template loading errors**
   ```bash
   # Check template directory
   ls -la templates/
   # Verify path in settings
   ```

4. **High memory usage**
   ```bash
   # Check for memory leaks
   python -m memory_profiler app/main.py
   ```

## Maintenance

### Regular Tasks

- **Weekly**: Check logs for errors
- **Monthly**: Update dependencies
- **Quarterly**: Security audit
- **Annually**: Capacity planning

### Dependency Updates

```bash
# Check for updates
pip list --outdated

# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade fastapi
```

---

**For support files, see:**
- `README.md` - Quick start and features
- `API_EXAMPLES.py` - API usage examples
- `examples.py` - Python SDK examples
