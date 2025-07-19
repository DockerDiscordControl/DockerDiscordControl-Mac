#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    🏭 Unraid Production Build Script                         ║
# ║                                                                              ║
# ║  Simplified version for Unraid servers - single architecture                ║
# ║  Avoids multi-platform build issues                                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# 🎨 Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 📁 Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 🔢 Version
VERSION=${1:-"latest"}
DOCKER_REPO="dockerdiscordcontrol"
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo -e "${PURPLE}🏭 Unraid Production Build${NC}"
echo -e "${BLUE}📁 Project: ${WHITE}$(pwd)${NC}"
echo -e "${GREEN}📦 Version: ${WHITE}${VERSION}${NC}"
echo ""

# 🧪 Pre-build validation
echo -e "${BLUE}🧪 Pre-build validation...${NC}"

# Check Dockerfile
if [ -f "Dockerfile.optimized" ]; then
    echo -e "${GREEN}✅ Using optimized Dockerfile${NC}"
    DOCKERFILE="Dockerfile.optimized"
else
    echo -e "${YELLOW}⚠️  Using standard Dockerfile${NC}"
    DOCKERFILE="Dockerfile"
fi

# Check requirements
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# 🏗️ Build process
echo -e "${BLUE}🏗️  Building image for Unraid (linux/amd64)...${NC}"

# Build tags
TAGS=(
    "${DOCKER_REPO}:${VERSION}"
    "${DOCKER_REPO}:latest"
)

# Build command
BUILD_CMD="docker build"
BUILD_CMD+=" --file ${DOCKERFILE}"
BUILD_CMD+=" --build-arg BUILD_DATE=${BUILD_DATE}"
BUILD_CMD+=" --build-arg VERSION=${VERSION}"

# Add tags
for tag in "${TAGS[@]}"; do
    BUILD_CMD+=" --tag ${tag}"
done

BUILD_CMD+=" ."

# Execute build
echo -e "${BLUE}⚙️  Executing build...${NC}"
echo -e "${CYAN}Command: ${WHITE}${BUILD_CMD}${NC}"
echo ""

START_TIME=$(date +%s)

if eval "$BUILD_CMD"; then
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))
    
    echo ""
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
    echo -e "${BLUE}⏱️  Build time: ${WHITE}${BUILD_TIME}s${NC}"
    echo ""
    
    # Display built images
    echo -e "${PURPLE}🏷️  Built tags:${NC}"
    for tag in "${TAGS[@]}"; do
        echo -e "${WHITE}   📦 ${tag}${NC}"
    done
    echo ""
    
    # Size information
    echo -e "${BLUE}📏 Image size:${NC}"
    docker images "${DOCKER_REPO}" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | head -n 3
    echo ""
    
    # Next steps
    echo -e "${PURPLE}🚀 Next steps:${NC}"
    echo -e "${WHITE}   Test:     ${CYAN}docker run --rm ${DOCKER_REPO}:${VERSION}${NC}"
    echo -e "${WHITE}   Use:      ${CYAN}./scripts/rebuild.sh${NC} (to restart your container)"
    echo ""
    
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Unraid build completed successfully!${NC}" 