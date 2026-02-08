#!/bin/bash
# Containerlab deployment automation script for Networking Automation Engine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TOPOLOGY_FILE="${1:-containerlab/networking-automation.yml}"
TOPOLOGY_NAME="networking-automation-engine"
DOCKER_IMAGE="networking-automation-engine:latest"
LOG_DIR="logs"

# Functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check for containerlab
    if ! command -v clab &> /dev/null; then
        print_error "Containerlab is not installed. Please install it first:"
        echo "  https://containerlab.dev/install/"
    fi
    print_success "Containerlab found"

    # Check for Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
    fi
    print_success "Docker found"

    # Check topology file
    if [ ! -f "$TOPOLOGY_FILE" ]; then
        print_error "Topology file not found: $TOPOLOGY_FILE"
    fi
    print_success "Topology file found"

    echo
}

# Build Docker image
build_image() {
    print_header "Building Docker Image"

    if docker image inspect "$DOCKER_IMAGE" &> /dev/null; then
        print_warning "Image $DOCKER_IMAGE already exists. Skipping build."
    else
        print_info "Building image: $DOCKER_IMAGE"
        docker build -t "$DOCKER_IMAGE" -f Dockerfile .
        if [ $? -eq 0 ]; then
            print_success "Docker image built successfully"
        else
            print_error "Failed to build Docker image"
        fi
    fi

    echo
}

# Deploy topology
deploy_topology() {
    print_header "Deploying Topology"

    print_info "Creating topology from: $TOPOLOGY_FILE"
    clab deploy -t "$TOPOLOGY_FILE" --recycle

    if [ $? -eq 0 ]; then
        print_success "Topology deployed successfully"
    else
        print_error "Failed to deploy topology"
    fi

    echo
}

# Wait for services to be healthy
wait_for_services() {
    print_header "Waiting for Services to be Healthy"

    # Wait for API
    print_info "Waiting for API service..."
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
            print_success "API service is healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        print_warning "API service did not respond in time"
    fi

    # Wait for database
    print_info "Waiting for database service..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        docker exec ${TOPOLOGY_NAME}-database \
            pg_isready -U automation > /dev/null 2>&1 && break
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -lt $max_attempts ]; then
        print_success "Database service is healthy"
    else
        print_warning "Database service did not respond in time"
    fi

    # Wait for cache
    print_info "Waiting for cache service..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        docker exec ${TOPOLOGY_NAME}-cache \
            redis-cli ping > /dev/null 2>&1 && break
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -lt $max_attempts ]; then
        print_success "Cache service is healthy"
    fi

    echo
}

# Display topology information
show_endpoints() {
    print_header "Service Endpoints"

    echo -e "${GREEN}API and Services:${NC}"
    echo "  API Documentation:   http://localhost:8000/docs"
    echo "  API Health:          http://localhost:8000/"
    echo "  Prometheus:          http://localhost:9090"
    echo "  Grafana:             http://localhost:3000"
    echo "  PostgreSQL:          localhost:5432"
    echo "  Redis:               localhost:6379"

    echo -e "\n${GREEN}Container Access:${NC}"
    clab inspect -t "$TOPOLOGY_FILE"

    echo -e "\n${GREEN}Useful Commands:${NC}"
    echo "  View logs:           docker logs networking-automation-engine-api"
    echo "  Access container:    docker exec -it networking-automation-engine-api bash"
    echo "  Destroy topology:    clab destroy -t $TOPOLOGY_FILE"
    echo "  List containers:     clab ins -t $TOPOLOGY_FILE"

    echo
}

# Test API
test_api() {
    print_header "Testing API"

    print_info "Testing health endpoint..."
    if curl -s http://localhost:8000/ | grep -q "healthy"; then
        print_success "Health check passed"
    else
        print_warning "Health check returned unexpected response"
    fi

    print_info "Testing API info endpoint..."
    if curl -s http://localhost:8000/api/v1/info | grep -q "Networking Automation Engine"; then
        print_success "API info endpoint working"
    else
        print_warning "API info endpoint returned unexpected response"
    fi

    echo
}

# Show summary
show_summary() {
    print_header "Deployment Summary"

    echo -e "${GREEN}Status:${NC}"
    echo "  Topology:     $TOPOLOGY_NAME"
    echo "  Status:       Deployed and Running"
    echo "  Docker Image: $DOCKER_IMAGE"

    echo -e "\n${GREEN}Next Steps:${NC}"
    echo "  1. Visit http://localhost:8000/docs to access the API"
    echo "  2. Generate a topology: POST /api/v1/topology/generate"
    echo "  3. Visit http://localhost:3000 to view Grafana dashboards"
    echo "  4. Check logs: docker logs networking-automation-engine-api"

    echo -e "\n${GREEN}Useful Documentation:${NC}"
    echo "  README.md          - Quick start guide"
    echo "  DOCKER.md          - Docker documentation"
    echo "  CONTAINERLAB.md    - Containerlab guide"
    echo "  CI_CD.md           - CI/CD pipeline documentation"

    echo
}

# Cleanup on error
cleanup_on_error() {
    print_error "Deployment failed. Run: clab destroy -t $TOPOLOGY_FILE"
}

trap cleanup_on_error ERR

# Main execution
main() {
    print_header "Networking Automation Engine - Containerlab Deployment"

    check_prerequisites
    build_image
    deploy_topology
    wait_for_services
    show_endpoints
    test_api
    show_summary

    print_success "Deployment completed successfully!"
}

# Run main function
main "$@"
