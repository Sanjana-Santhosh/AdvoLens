#!/bin/bash

# ============================================
# AdvoLens Backend - Build and Push Script
# For macOS (Intel & Apple Silicon)
# ============================================

set -e  # Exit on error

# Configuration
DOCKER_IMAGE="${DOCKER_IMAGE:-sanjanamsanthoshsct/advolens-backend}"
DOCKER_TAG="${DOCKER_TAG:-latest}"
PLATFORM="${PLATFORM:-linux/amd64}"  # Target platform for VPS

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AdvoLens Backend - Docker Build${NC}"
echo -e "${BLUE}========================================${NC}"

# Change to server directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../server"

echo -e "\n${YELLOW}📁 Working directory: $(pwd)${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if logged into Docker Hub
echo -e "\n${YELLOW}🔐 Checking Docker Hub login...${NC}"
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo -e "${YELLOW}Please login to Docker Hub:${NC}"
    docker login
fi

# Create buildx builder if needed (for multi-platform builds)
echo -e "\n${YELLOW}🔧 Setting up buildx builder...${NC}"
if ! docker buildx inspect advolens-builder > /dev/null 2>&1; then
    docker buildx create --name advolens-builder --use
    docker buildx inspect --bootstrap
else
    docker buildx use advolens-builder
fi

echo -e "${GREEN}✅ Buildx builder ready${NC}"

# Build and push
echo -e "\n${YELLOW}🏗️  Building image for platform: ${PLATFORM}${NC}"
echo -e "${YELLOW}📦 Image: ${DOCKER_IMAGE}:${DOCKER_TAG}${NC}\n"

docker buildx build \
    --platform "$PLATFORM" \
    -t "$DOCKER_IMAGE:$DOCKER_TAG" \
    --push \
    .

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Build and push complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${BLUE}Image: ${DOCKER_IMAGE}:${DOCKER_TAG}${NC}"
echo -e "${BLUE}Platform: ${PLATFORM}${NC}"
echo -e "\n${YELLOW}🔄 Watchtower will auto-deploy on VPS within 5 minutes${NC}"
echo -e "${YELLOW}   Or manually pull with: docker pull ${DOCKER_IMAGE}:${DOCKER_TAG}${NC}\n"
