#!/bin/bash
# Docker Compose deployment script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENV_FILE="${1:-.env}"
COMPOSE_FILE="${2:-docker-compose.yml}"
MODE="${3:-dev}"

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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

main() {
    print_header "Docker Compose Deployment - $MODE mode"

    # Check prerequisites
    print_info "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
    fi
    print_success "Docker found"

    # Create .env if not exists
    if [ ! -f "$ENV_FILE" ]; then
        print_info "Creating .env file from .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example "$ENV_FILE"
            print_warning "Please update $ENV_FILE with your configuration"
        fi
    fi

    # Select compose file based on mode
    if [ "$MODE" = "prod" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
        print_info "Using production configuration"
    fi

    # Pull latest images
    print_info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull

    # Start services
    print_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
    fi

    # Wait for services
    print_info "Waiting for services to be healthy..."
    sleep 5

    # Show status
    echo
    print_header "Service Status"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

    # Show endpoints
    echo
    print_header "Available Endpoints"
    echo "API:               http://localhost:8000"
    echo "API Docs:          http://localhost:8000/docs"
    echo "Prometheus:        http://localhost:9090"
    echo "Grafana:           http://localhost:3000"
    echo "Kibana:            http://localhost:5601"

    print_success "Deployment completed!"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

main "$@"
