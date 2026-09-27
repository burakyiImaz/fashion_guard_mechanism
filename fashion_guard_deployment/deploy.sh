#!/bin/bash

# Fashion Guard - RunPod Deployment Script
# This script builds and pushes the Docker image to Docker Hub

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-}"
IMAGE_NAME="fashion-guard"
VERSION="${VERSION:-v1}"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Fashion Guard - RunPod Deployment Script                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED} Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED} Docker daemon is not running. Please start Docker.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is available${NC}"
echo ""

# Get Docker username if not provided
if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${YELLOW}📝 Docker Configuration${NC}"
    read -p "Enter your Docker Hub username: " DOCKER_USERNAME
    
    if [ -z "$DOCKER_USERNAME" ]; then
        echo -e "${RED}❌ Docker username is required.${NC}"
        exit 1
    fi
fi

read -p "Enter image version (default: v1): " INPUT_VERSION
VERSION="${INPUT_VERSION:-v1}"

FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"

echo ""
echo -e "${BLUE} Build Configuration:${NC}"
echo "  Docker Username: $DOCKER_USERNAME"
echo "  Image Name: $IMAGE_NAME"
echo "  Version: $VERSION"
echo "  Full Image: $FULL_IMAGE_NAME"
echo ""

# Check if Docker Hub login is needed
echo -e "${YELLOW} Checking Docker Hub authentication...${NC}"
if ! docker info 2>&1 | grep -q "Username"; then
    echo -e "${YELLOW}  You need to login to Docker Hub to push images.${NC}"
    echo ""
    read -p "Do you want to login now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login
    else
        echo -e "${YELLOW}⚠️  Note: You can manually login later with: docker login${NC}"
    fi
fi

echo ""
echo -e "${BLUE}🔨 Building Docker image...${NC}"
echo "   Command: docker build -f runpod_Dockerfile -t ${FULL_IMAGE_NAME} ."
echo ""

# Build the image
if docker build -f runpod_Dockerfile -t "$FULL_IMAGE_NAME" .; then
    echo ""
    echo -e "${GREEN}✓ Docker image built successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Docker build failed.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📤 Pushing image to Docker Hub...${NC}"
echo "   Target: $FULL_IMAGE_NAME"
echo ""

# Push the image
if docker push "$FULL_IMAGE_NAME"; then
    echo ""
    echo -e "${GREEN}✓ Image pushed successfully!${NC}"
else
    echo ""
    echo -e "${RED} Docker push failed.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    Deployment Preparation Complete!                    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "1. Go to RunPod Console:"
echo "   https://www.runpod.io/console/serverless"
echo ""
echo "2. Click 'Create an endpoint' or '+ New Endpoint'"
echo ""
echo "3. Select 'Deploy from a Docker image'"
echo ""
echo "4. Fill in the configuration:"
echo "   • Container Image: ${FULL_IMAGE_NAME}"
echo "   • GPU: Select 16GB (A4000) or 24GB (RTX 4090)"
echo "   • Min Workers: 0"
echo "   • Max Workers: 1 or 2"
echo "   • Execution Timeout: 60 seconds"
echo ""
echo "5. Click 'Deploy Endpoint'"
echo ""
echo "6. Copy your ENDPOINT_ID and test with:"
echo ""
echo "   curl -X POST 'https://api.runpod.io/v2/{ENDPOINT_ID}/runsync' \\"
echo "     -H 'Authorization: Bearer {API_KEY}' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"input\": {\"query\": \"Siyah bot arıyorum\"}}'"
echo ""

echo -e "${YELLOW} Documentation:${NC}"
echo "   • Detailed Guide: RUNPOD_DEPLOYMENT_GUIDE.md"
echo "   • API Reference: API_REFERENCE.md"
echo ""

# Save configuration for future use
CONFIG_FILE="${HOME}/.fashion_guard_deployment"
cat > "$CONFIG_FILE" <<EOF
DOCKER_USERNAME=$DOCKER_USERNAME
LAST_VERSION=$VERSION
LAST_IMAGE=$FULL_IMAGE_NAME
EOF

echo -e "${GREEN}✓ Configuration saved to: ${CONFIG_FILE}${NC}"
echo ""
