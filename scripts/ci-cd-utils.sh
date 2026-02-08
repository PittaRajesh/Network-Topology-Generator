#!/bin/bash

#
# CI/CD Utilities Script
# Helper functions for CI/CD pipeline operations
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Run tests with coverage
run_tests() {
    log_info "Running unit tests with coverage..."
    
    python -m pip install --quiet pytest pytest-cov pytest-asyncio
    
    python -m pytest tests/ \
        -v \
        --cov=app \
        --cov-report=xml \
        --cov-report=html \
        --cov-report=term \
        --tb=short
    
    if [ $? -eq 0 ]; then
        log_success "Tests passed"
    else
        log_error "Tests failed"
        exit 1
    fi
}

# Run code quality checks
run_quality_checks() {
    log_info "Running code quality checks..."
    
    python -m pip install --quiet black flake8 isort mypy
    
    # Black formatting check
    log_info "Checking code formatting..."
    black --check app/ tests/ || return 1
    log_success "Code formatting OK"
    
    # Import sorting check
    log_info "Checking import sorting..."
    isort --check-only app/ tests/ || return 1
    log_success "Import sorting OK"
    
    # Linting
    log_info "Running linting..."
    flake8 app/ tests/ --max-line-length=100 --statistics || return 1
    log_success "Linting OK"
    
    # Type checking
    log_info "Running type checks..."
    mypy app/ --ignore-missing-imports --no-error-summary 2>/dev/null || true
    log_success "Type checking completed"
}

# Build Docker image
build_image() {
    local tag="${1:-latest}"
    log_info "Building Docker image with tag: $tag"
    
    docker build -t "networking-automation-engine:$tag" .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Run security scan with Trivy
security_scan() {
    log_info "Running security scan..."
    
    if ! command -v trivy &> /dev/null; then
        log_warning "Trivy not installed. Installing..."
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    fi
    
    trivy image \
        --severity HIGH,CRITICAL \
        "networking-automation-engine:latest"
    
    if [ $? -eq 0 ]; then
        log_success "Security scan completed"
    else
        log_warning "Security vulnerabilities found"
        return 1
    fi
}

# Validate Docker compose files
validate_docker_compose() {
    log_info "Validating docker-compose files..."
    
    docker-compose config > /dev/null
    if [ $? -eq 0 ]; then
        log_success "docker-compose.yml is valid"
    else
        log_error "Invalid docker-compose.yml"
        exit 1
    fi
    
    docker-compose -f docker-compose.prod.yml config > /dev/null
    if [ $? -eq 0 ]; then
        log_success "docker-compose.prod.yml is valid"
    else
        log_error "Invalid docker-compose.prod.yml"
        exit 1
    fi
}

# Check image size
check_image_size() {
    log_info "Checking image size..."
    
    local size=$(docker images networking-automation-engine:latest --format "{{.Size}}")
    log_info "Image size: $size"
    
    # Warn if image is larger than expected (e.g., 500MB)
    local size_mb=$(docker images networking-automation-engine:latest --format "{{.Size}}" | sed 's/MB//' | sed 's/GB/000/')
    if (( $(echo "$size_mb > 500" | bc -l) )); then
        log_warning "Image is quite large. Consider optimizing"
    else
        log_success "Image size is acceptable"
    fi
}

# Generate documentation
generate_docs() {
    log_info "Generating documentation..."
    
    # Check if documentation needs updating
    if [ -f "CICD.md" ]; then
        log_success "CI/CD documentation found"
    else
        log_warning "CICD.md not found. Creating template..."
        cat > CICD.md << 'EOF'
# CI/CD Pipeline Documentation

## Overview

This document describes the CI/CD pipeline for the Networking Automation Engine.

## Workflows

### 1. CI/CD Pipeline (ci-cd.yml)
- **Trigger**: Push to main/develop, PRs, nightly schedule
- **Stages**:
  - Lint & Code Quality
  - Unit Tests
  - Security Scanning
  - Docker Build & Push
  - Integration Tests
  - Deployment

### 2. Code Quality (code-quality.yml)
- **Trigger**: Commits to main/develop
- **Tools**: CodeQL, SonarCloud
- **Output**: SAST reports, quality metrics

### 3. Container Build (container-build.yml)
- **Trigger**: Push and tags
- **Tasks**: Build, Push, Scan, SBOM generation

### 4. Release (release.yml)
- **Trigger**: Git tags (v*)
- **Tasks**: Create release, publish images, documentation

## Secrets Configuration

Required secrets in GitHub:
- `GITHUB_TOKEN` (auto)
- `SLACK_WEBHOOK_URL` (optional)
- `SONAR_TOKEN` (optional)
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

EOF
    fi
}

print_usage() {
    cat << EOF
CI/CD Utilities

Usage: $0 [COMMAND]

Commands:
  test              Run unit tests with coverage
  quality           Run code quality checks
  build             Build Docker image
  security          Run security vulnerabilities scan
  docker-check      Validate Docker compose files
  image-size        Check Docker image size
  docs              Generate documentation
  all               Run all checks
  help              Show this help message

Examples:
  Run all checks:
    $0 all

  Run tests only:
    $0 test

  Build and scan:
    $0 build && $0 security

EOF
}

# Main handler
main() {
    local command="${1:-help}"
    
    case "$command" in
        test)
            run_tests
            ;;
        quality)
            run_quality_checks
            ;;
        build)
            build_image "${2:-latest}"
            ;;
        security)
            security_scan
            ;;
        docker-check)
            validate_docker_compose
            ;;
        image-size)
            check_image_size
            ;;
        docs)
            generate_docs
            ;;
        all)
            run_quality_checks && \
            run_tests && \
            build_image "latest" && \
            validate_docker_compose && \
            check_image_size && \
            log_success "All checks passed!"
            ;;
        help|--help|-h)
            print_usage
            ;;
        *)
            log_error "Unknown command: $command"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
