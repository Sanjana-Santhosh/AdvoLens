#!/bin/bash

# ============================================
# AdvoLens Backend - Local Build Script
# Build for local testing (native architecture)
# ============================================

set -e  # Exit on error

# Configuration
DOCKER_IMAGE="${DOCKER_IMAGE:-advolens-backend}"
DOCKER_TAG="${DOCKER_TAG:-local}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AdvoLens Backend - Local Build${NC}"
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

# Build for local architecture
echo -e "\n${YELLOW}🏗️  Building image for local architecture...${NC}"
echo -e "${YELLOW}📦 Image: ${DOCKER_IMAGE}:${DOCKER_TAG}${NC}\n"

docker build -t "$DOCKER_IMAGE:$DOCKER_TAG" .

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Local build complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${BLUE}Image: ${DOCKER_IMAGE}:${DOCKER_TAG}${NC}"
echo -e "\n${YELLOW}Run locally with:${NC}"
echo -e "${YELLOW}  docker run -p 8000:8000 --env-file .env ${DOCKER_IMAGE}:${DOCKER_TAG}${NC}\n"
