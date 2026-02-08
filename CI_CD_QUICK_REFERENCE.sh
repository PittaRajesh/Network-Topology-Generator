#!/bin/bash

#
# Quick Reference for CI/CD Operations
# Common commands and operations for managing the CI/CD pipeline
#

# =============================================================================
# GitHub Actions CLI Operations (requires 'gh' CLI)
# =============================================================================

# List all workflow runs
gh run list --limit 10

# View a specific workflow run (with verbose logs)
gh run view <RUN_ID> --log

# Re-run a failed workflow
gh run rerun <RUN_ID>

# Re-run only failed jobs
gh run rerun <RUN_ID> --failed

# Download workflow logs
gh run download <RUN_ID> --dir logs/

# Cancel a running workflow
gh run cancel <RUN_ID>

# View workflow file
gh workflow view ci-cd.yml

# List all workflows
gh workflow list

# =============================================================================
# Manual Workflow Dispatch (Run via GitHub CLI)
# =============================================================================

# Manually trigger CI/CD pipeline
gh workflow run ci-cd.yml -r main

# Manually trigger release workflow
gh workflow run release.yml -r main

# Trigger with input parameters
gh workflow run -F environment=production

# =============================================================================
# Local Testing with 'act'
# =============================================================================

# Install act (GitHub Actions local runner)
# macOS:
brew install act

# Linux:
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# List available workflows
act --list

# Run specific job
act -j lint

# Run with verbose output
act -j test --verbose

# Provide secrets
act -s GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Run with different runner
act --container-architecture linux/amd64

# =============================================================================
# Docker Operations
# =============================================================================

# Build Docker image locally
docker build -t networking-automation-engine:latest .

# Build with specific tag
docker build -t networking-automation-engine:v1.0.0 .

# Build without cache
docker build --no-cache -t networking-automation-engine:latest .

# List Docker images
docker images | grep networking

# Push to GHCR
docker tag networking-automation-engine:latest ghcr.io/owner/repo:latest
docker push ghcr.io/owner/repo:latest

# Push to Docker Hub
docker tag networking-automation-engine:latest username/repo:latest
docker push username/repo:latest

# Pull from registry
docker pull ghcr.io/owner/repo:latest

# Run image
docker run -p 8000:8000 networking-automation-engine:latest

# Inspect image
docker inspect networking-automation-engine:latest

# View image layers
docker history networking-automation-engine:latest

# =============================================================================
# Docker Compose Operations
# =============================================================================

# Validate docker-compose files
docker-compose config  # Development
docker-compose -f docker-compose.prod.yml config  # Production

# Build services
docker-compose build

# Build specific service
docker-compose build api

# Start services
docker-compose up -d

# Start with logs
docker-compose up

# Stop services
docker-compose down

# Remove everything including volumes
docker-compose down -v

# View logs
docker-compose logs -f api
docker-compose logs -f /5min  # Last 5 minutes

# Execute command in container
docker-compose exec api bash

# Restart service
docker-compose restart api

# Check service health
docker-compose ps

# =============================================================================
# CI/CD Utility Scripts
# =============================================================================

# Run all quality checks
./scripts/ci-cd-utils.sh all

# Run only tests
./scripts/ci-cd-utils.sh test

# Run quality checks
./scripts/ci-cd-utils.sh quality

# Build Docker image
./scripts/ci-cd-utils.sh build latest

# Run security scan
./scripts/ci-cd-utils.sh security

# Validate docker-compose
./scripts/ci-cd-utils.sh docker-check

# Check image size
./scripts/ci-cd-utils.sh image-size

# Generate documentation
./scripts/ci-cd-utils.sh docs

# =============================================================================
# Registry Manager Operations
# =============================================================================

# Login to GHCR
REGISTRY_TYPE=ghcr GHCR_TOKEN=$TOKEN ./scripts/registry-manager.sh login

# Login to Docker Hub
REGISTRY_TYPE=dockerhub DOCKERHUB_USERNAME=user DOCKERHUB_TOKEN=$TOKEN \
  ./scripts/registry-manager.sh login

# Login to AWS ECR
REGISTRY_TYPE=ecr AWS_ACCOUNT_ID=123456 AWS_REGION=us-east-1 \
  ./scripts/registry-manager.sh login

# Push image
REGISTRY_TYPE=ghcr ./scripts/registry-manager.sh push

# Pull image
REGISTRY_TYPE=ghcr IMAGE_TAG=v1.0.0 ./scripts/registry-manager.sh pull

# List images
REGISTRY_TYPE=dockerhub DOCKERHUB_USERNAME=user \
  ./scripts/registry-manager.sh list

# Cleanup old images (AWS ECR)
REGISTRY_TYPE=ecr AWS_ACCOUNT_ID=123456 RETENTION_DAYS=30 \
  ./scripts/registry-manager.sh cleanup

# Display registry info
./scripts/registry-manager.sh info

# =============================================================================
# Containerlab Operations
# =============================================================================

# Check if containerlab is installed
which containerlab

# Deploy topology
./scripts/deploy-containerlab.sh

# Deploy with CI mode
./scripts/deploy-containerlab.sh --ci

# Check status
containerlab inspect -t containerlab/networking-automation.yml

# View endpoints
containerlab inspect -t containerlab/networking-automation.yml --format table

# Connect to node
docker exec -it clab-networking-automation-api bash

# View node logs
docker logs clab-networking-automation-api

# Destroy topology
containerlab destroy -t containerlab/networking-automation.yml

# =============================================================================
# Git Operations
# =============================================================================

# Create feature branch
git checkout -b feature/my-feature

# Create release tag
git tag v1.0.0
git push origin v1.0.0

# Create annotated tag (recommended)
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# View tags
git tag -l
git tag -l v1.*

# Delete tag locally
git tag -d v1.0.0

# Delete tag from remote
git push origin --delete v1.0.0

# Push with skip CI
git push --force-with-lease

# Commit with skip-ci message
git commit -m "Update docs [skip ci]"

# =============================================================================
# Secrets Management
# =============================================================================

# Create GitHub secret (requires gh CLI)
gh secret set DOCKER_TOKEN --body "$(cat token.txt)"

# List all secrets
gh secret list

# Remove secret
gh secret remove DOCKER_TOKEN

# Create local .env file
cat > .env << EOF
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
EOF

# Load .env file
export $(cat .env | xargs)

# =============================================================================
# Testing & Quality Commands
# =============================================================================

# Run pytest
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test function
pytest tests/test_api.py::test_health_check -v

# Run with markers
pytest tests/ -m "not slow" -v

# Run linting
black --check app/ tests/
isort --check-only app/ tests/
flake8 app/ tests/

# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/ --ignore-missing-imports

# Security scanning
bandit -r app/

# =============================================================================
# Monitoring & Logs
# =============================================================================

# View GitHub Actions usage
gh api repos/:owner/:repo/actions/billing/summary

# View workflow runs
gh run list --workflow=ci-cd.yml

# Check notifications
gh notification list

# Save workflow logs
gh run download <RUN_ID> --dir workflow-logs/

# Stream container logs
docker logs -f container_name

# View system logs (macOS)
log stream --predicate 'process == "Docker"'

# =============================================================================
# Troubleshooting Commands
# =============================================================================

# Check Docker daemon
docker system info

# Prune Docker system
docker system prune -a --volumes

# Check Docker buildx
docker buildx ls

# Set default buildx builder
docker buildx create --use

# Validate YAML files
python -m yaml < docker-compose.yml > /dev/null && echo "Valid YAML"

# Check Python environment
python -m venv --help
pip --version
pip list

# View pip freeze
pip freeze > current-requirements.txt

# =============================================================================
# Useful Combinations
# =============================================================================

# Development workflow
git checkout -b feature/my-feature && \
  ./scripts/ci-cd-utils.sh all && \
  git add . && \
  git commit -m "feat: implement feature" && \
  git push origin feature/my-feature

# Pre-commit check
./scripts/ci-cd-utils.sh quality && \
  ./scripts/ci-cd-utils.sh test && \
  git push

# Full pipeline locally
docker-compose down -v && \
  docker-compose build && \
  docker-compose up -d &&\
  sleep 10 && \
  curl http://localhost:8000/api/v1/info

# Release new version
git tag -a v1.0.0 -m "Release v1.0.0" && \
  git push origin v1.0.0

# =============================================================================
# Useful Aliases (Add to ~/.bashrc or ~/.zshrc)
# =============================================================================

# Add these to your shell profile:

alias ghrun='gh run list --limit 10'
alias ghlog='gh run view --log'
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dclogs='docker-compose logs -f'
alias test='./scripts/ci-cd-utils.sh test'
alias quality='./scripts/ci-cd-utils.sh quality'
alias build='./scripts/ci-cd-utils.sh build'
alias devchat='python run all'
alias lab='./scripts/deploy-containerlab.sh'

# =============================================================================
# Debugging Tips
# =============================================================================

# Enable debug logging in GitHub Actions:
# 1. Set ACTIONS_STEP_DEBUG=true in workflow
# 2. Re-run workflow
# 3. Check logs for detailed output

# For container issues:
# - Use 'docker logs' to see container output
# - Use 'docker exec' to run commands in container
# - Use 'docker inspect' to see container configuration

# For workflow issues:
# - Use 'act' to test locally
# - Check logs in GitHub Actions UI
# - Use 'gh run download' to save full logs

# For Python issues:
# - Add print statements or use pdb
# - Check environment variables
# - Verify dependencies installed

# =============================================================================
# Quick Reference Links
# =============================================================================

# Documentation:
# - README.md - Quick start
# - CICD.md - CI/CD pipeline details
# - GITHUB_ACTIONS_SETUP.md - GitHub Actions setup
# - DOCKER.md - Docker guide
# - DEPLOYMENT.md - Deployment procedures
# - ARCHITECTURE.md - Architecture overview

# External Tools:
# - GitHub CLI: https://cli.github.com
# - act: https://github.com/nektos/act
# - GitHub Actions: https://github.com/features/actions
# - Docker: https://www.docker.com
# - Containerlab: https://containerlab.dev

# =============================================================================
# Support
# =============================================================================

# For issues or questions:
# 1. Check the documentation (CICD.md, etc.)
# 2. Review workflow logs in GitHub Actions
# 3. Test locally with 'act'
# 4. Check Docker container logs
# 5. Open issue with error details and logs

echo "CI/CD Quick Reference loaded!"
echo "Run this file as source: source CI_CD_QUICK_REFERENCE.sh"
