#!/bin/bash

#
# Container Registry Management Script
# Handles authenticating with and managing Docker images in container registries
# Supports: GitHub Container Registry (GHCR), Docker Hub, AWS ECR
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY_TYPE="${REGISTRY_TYPE:-ghcr}"  # ghcr, dockerhub, ecr
IMAGE_NAME="${IMAGE_NAME:-networking-automation-engine}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-}"
DOCKERHUB_TOKEN="${DOCKERHUB_TOKEN:-}"
GHCR_TOKEN="${GHCR_TOKEN:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Functions
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

print_usage() {
    cat << EOF
Container Registry Management Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  login               Authenticate with container registry
  push                Push image to registry
  pull                Pull image from registry
  list                List images in registry
  cleanup             Remove old images from registry
  info                Display registry configuration
  help                Show this help message

Options:
  --registry-type     Registry type: ghcr, dockerhub, ecr (default: ghcr)
  --image-name        Image name (default: networking-automation-engine)
  --image-tag         Image tag (default: latest)
  --retention-days    Days to retain images (default: 30)
  --dockerhub-user    Docker Hub username
  --dockerhub-token   Docker Hub token
  --ghcr-token        GitHub Container Registry token
  --aws-region        AWS region (for ECR)
  --aws-account-id    AWS account ID (for ECR)

Examples:
  Login to GHCR:
    $0 login --registry-type ghcr --ghcr-token YOUR_TOKEN

  Push to GHCR:
    $0 push --registry-type ghcr --image-tag v1.0.0

  Cleanup old images:
    $0 cleanup --registry-type ghcr --retention-days 30

EOF
}

# Validate command
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        exit 1
    fi
}

# GHCR Functions
ghcr_login() {
    log_info "Authenticating with GitHub Container Registry..."
    
    if [ -z "$GHCR_TOKEN" ]; then
        log_error "GHCR_TOKEN is not set"
        exit 1
    fi
    
    echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin 2>/dev/null
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Successfully authenticated with GHCR"
    else
        log_error "Failed to authenticate with GHCR"
        exit 1
    fi
}

ghcr_push() {
    log_info "Pushing image to GHCR..."
    
    local full_image="ghcr.io/${GITHUB_REPOSITORY}:${IMAGE_TAG}"
    log_info "Target image: $full_image"
    
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$full_image"
    docker push "$full_image"
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        log_success "Successfully pushed image to GHCR"
        log_info "Image: $full_image"
    else
        log_error "Failed to push image to GHCR"
        exit 1
    fi
}

ghcr_pull() {
    log_info "Pulling image from GHCR..."
    
    local full_image="ghcr.io/${GITHUB_REPOSITORY}:${IMAGE_TAG}"
    docker pull "$full_image"
    docker tag "$full_image" "${IMAGE_NAME}:${IMAGE_TAG}"
    
    if [ $? -eq 0 ]; then
        log_success "Successfully pulled image from GHCR"
    else
        log_error "Failed to pull image from GHCR"
        exit 1
    fi
}

ghcr_list() {
    log_info "Listing images in GHCR..."
    
    curl -s -H "Authorization: token $GHCR_TOKEN" \
        "https://api.github.com/user/packages?package_type=container" | \
        grep -o '"name":"[^"]*"' | cut -d'"' -f4
}

ghcr_cleanup() {
    log_warning "Note: Cleanup via GHCR API requires different authentication"
    log_info "See: https://docs.github.com/en/packages/managing-github-packages-with-github-actions-workflows/publishing-and-installing-a-package-with-github-actions"
}

# Docker Hub Functions
dockerhub_login() {
    log_info "Authenticating with Docker Hub..."
    
    if [ -z "$DOCKERHUB_USERNAME" ] || [ -z "$DOCKERHUB_TOKEN" ]; then
        log_error "DOCKERHUB_USERNAME and DOCKERHUB_TOKEN are not set"
        exit 1
    fi
    
    echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
    
    if [ $? -eq 0 ]; then
        log_success "Successfully authenticated with Docker Hub"
    else
        log_error "Failed to authenticate with Docker Hub"
        exit 1
    fi
}

dockerhub_push() {
    log_info "Pushing image to Docker Hub..."
    
    local full_image="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "Target image: $full_image"
    
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$full_image"
    docker push "$full_image"
    
    if [ $? -eq 0 ]; then
        log_success "Successfully pushed image to Docker Hub"
        log_info "Image: $full_image"
    else
        log_error "Failed to push image to Docker Hub"
        exit 1
    fi
}

dockerhub_pull() {
    log_info "Pulling image from Docker Hub..."
    
    local full_image="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker pull "$full_image"
    docker tag "$full_image" "${IMAGE_NAME}:${IMAGE_TAG}"
    
    if [ $? -eq 0 ]; then
        log_success "Successfully pulled image from Docker Hub"
    else
        log_error "Failed to pull image from Docker Hub"
        exit 1
    fi
}

dockerhub_list() {
    log_info "Listing images in Docker Hub repository..."
    
    curl -s "https://hub.docker.com/v2/repositories/${DOCKERHUB_USERNAME}/${IMAGE_NAME}/tags/" | \
        grep -o '"name":"[^"]*"' | cut -d'"' -f4
}

# AWS ECR Functions
ecr_login() {
    log_info "Authenticating with AWS ECR..."
    
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        log_error "AWS_ACCOUNT_ID is not set"
        exit 1
    fi
    
    check_command "aws"
    
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin \
        "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    if [ $? -eq 0 ]; then
        log_success "Successfully authenticated with AWS ECR"
    else
        log_error "Failed to authenticate with AWS ECR"
        exit 1
    fi
}

ecr_push() {
    log_info "Pushing image to AWS ECR..."
    
    local registry="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    local full_image="${registry}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    log_info "Target image: $full_image"
    
    # Create repository if it doesn't exist
    aws ecr create-repository \
        --repository-name "$IMAGE_NAME" \
        --region "$AWS_REGION" 2>/dev/null || true
    
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$full_image"
    docker push "$full_image"
    
    if [ $? -eq 0 ]; then
        log_success "Successfully pushed image to AWS ECR"
        log_info "Image: $full_image"
    else
        log_error "Failed to push image to AWS ECR"
        exit 1
    fi
}

ecr_pull() {
    log_info "Pulling image from AWS ECR..."
    
    local registry="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    local full_image="${registry}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    docker pull "$full_image"
    docker tag "$full_image" "${IMAGE_NAME}:${IMAGE_TAG}"
    
    if [ $? -eq 0 ]; then
        log_success "Successfully pulled image from AWS ECR"
    else
        log_error "Failed to pull image from AWS ECR"
        exit 1
    fi
}

ecr_list() {
    log_info "Listing images in AWS ECR repository..."
    
    check_command "aws"
    
    aws ecr describe-images \
        --repository-name "$IMAGE_NAME" \
        --region "$AWS_REGION" \
        --query 'imageDetails[*].imageTags[]' \
        --output text
}

ecr_cleanup() {
    log_info "Cleaning up old images in AWS ECR (older than $RETENTION_DAYS days)..."
    
    check_command "aws"
    
    local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%s)
    
    aws ecr describe-images \
        --repository-name "$IMAGE_NAME" \
        --region "$AWS_REGION" \
        --query "imageDetails[?imagePushedAt <= \`$(date -d "$RETENTION_DAYS days ago" -u +%Y-%m-%dT%H:%M:%S)\`].[imageDigest,imageTags[0]]" \
        --output json | \
    jq -r '.[] | @tsv' | \
    while IFS=$'\t' read -r digest tag; do
        log_warning "Deleting image: $tag (pushed more than $RETENTION_DAYS days ago)"
        aws ecr batch-delete-image \
            --repository-name "$IMAGE_NAME" \
            --region "$AWS_REGION" \
            --image-ids "imageDigest=$digest"
    done
    
    log_success "Cleanup completed"
}

# Display information
show_info() {
    log_info "Container Registry Configuration"
    echo ""
    echo "  Registry Type:   $REGISTRY_TYPE"
    echo "  Image Name:      $IMAGE_NAME"
    echo "  Image Tag:       $IMAGE_TAG"
    
    case "$REGISTRY_TYPE" in
        ghcr)
            echo "  GHCR Token:      $([ -n "$GHCR_TOKEN" ] && echo 'Set' || echo 'Not set')"
            ;;
        dockerhub)
            echo "  DH Username:     $DOCKERHUB_USERNAME"
            echo "  DH Token:        $([ -n "$DOCKERHUB_TOKEN" ] && echo 'Set' || echo 'Not set')"
            ;;
        ecr)
            echo "  AWS Region:      $AWS_REGION"
            echo "  AWS Account:     $AWS_ACCOUNT_ID"
            ;;
    esac
    
    echo ""
}

# Main command handler
main() {
    local command="${1:-help}"
    
    case "$command" in
        login)
            case "$REGISTRY_TYPE" in
                ghcr) ghcr_login ;;
                dockerhub) dockerhub_login ;;
                ecr) ecr_login ;;
                *) log_error "Unknown registry type: $REGISTRY_TYPE"; exit 1 ;;
            esac
            ;;
        push)
            case "$REGISTRY_TYPE" in
                ghcr) ghcr_push ;;
                dockerhub) dockerhub_push ;;
                ecr) ecr_push ;;
                *) log_error "Unknown registry type: $REGISTRY_TYPE"; exit 1 ;;
            esac
            ;;
        pull)
            case "$REGISTRY_TYPE" in
                ghcr) ghcr_pull ;;
                dockerhub) dockerhub_pull ;;
                ecr) ecr_pull ;;
                *) log_error "Unknown registry type: $REGISTRY_TYPE"; exit 1 ;;
            esac
            ;;
        list)
            case "$REGISTRY_TYPE" in
                ghcr) ghcr_list ;;
                dockerhub) dockerhub_list ;;
                ecr) ecr_list ;;
                *) log_error "Unknown registry type: $REGISTRY_TYPE"; exit 1 ;;
            esac
            ;;
        cleanup)
            case "$REGISTRY_TYPE" in
                ghcr) ghcr_cleanup ;;
                dockerhub) log_warning "Manual cleanup required for Docker Hub"; exit 0 ;;
                ecr) ecr_cleanup ;;
                *) log_error "Unknown registry type: $REGISTRY_TYPE"; exit 1 ;;
            esac
            ;;
        info)
            show_info
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

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --registry-type)
            REGISTRY_TYPE="$2"
            shift 2
            ;;
        --image-name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --dockerhub-user)
            DOCKERHUB_USERNAME="$2"
            shift 2
            ;;
        --dockerhub-token)
            DOCKERHUB_TOKEN="$2"
            shift 2
            ;;
        --ghcr-token)
            GHCR_TOKEN="$2"
            shift 2
            ;;
        --aws-region)
            AWS_REGION="$2"
            shift 2
            ;;
        --aws-account-id)
            AWS_ACCOUNT_ID="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

main "$@"
