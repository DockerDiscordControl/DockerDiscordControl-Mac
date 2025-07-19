#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    🏭 Production Build Script for DDC                       ║
# ║                                                                              ║
# ║  Features:                                                                   ║
# ║  - Multi-architecture builds (amd64, arm64)                                  ║
# ║  - Docker Hub publishing                                                     ║
# ║  - Semantic versioning                                                       ║
# ║  - Optimized for Unraid Community Apps                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# 🎨 Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# 📋 Configuration
DOCKER_REPO="dockerdiscordcontrol/ddc"
PLATFORMS="linux/amd64,linux/arm64"
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# 📁 Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${PURPLE}🏭 Production Build Pipeline${NC}"
echo -e "${BLUE}📁 Project: ${WHITE}$(pwd)${NC}"
echo -e "${BLUE}🌿 Branch: ${WHITE}${GIT_BRANCH}${NC}"
echo -e "${BLUE}📝 Commit: ${WHITE}${GIT_COMMIT}${NC}"
echo ""

# 🔢 Version detection
if [ -n "$1" ]; then
    VERSION="$1"
    echo -e "${GREEN}📦 Version: ${WHITE}${VERSION}${NC} (manual)"
elif [ -f "VERSION" ]; then
    VERSION=$(cat VERSION)
    echo -e "${GREEN}📦 Version: ${WHITE}${VERSION}${NC} (from file)"
else
    VERSION="latest"
    echo -e "${YELLOW}📦 Version: ${WHITE}${VERSION}${NC} (default)"
fi

# 🐳 Docker setup
echo -e "${BLUE}🐳 Setting up Docker Buildx...${NC}"
docker buildx create --name ddc-builder --use 2>/dev/null || true
docker buildx inspect --bootstrap >/dev/null 2>&1

# 🧪 Pre-build checks
echo -e "${PURPLE}🧪 Pre-build validation...${NC}"

# Check Dockerfile
if [ ! -f "Dockerfile.optimized" ]; then
    echo -e "${YELLOW}⚠️  Dockerfile.optimized not found, using standard Dockerfile${NC}"
    DOCKERFILE="Dockerfile"
else
    echo -e "${GREEN}✅ Using optimized Dockerfile${NC}"
    DOCKERFILE="Dockerfile.optimized"
fi

# Check requirements
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Validate Python syntax (optional)
echo -e "${BLUE}🐍 Validating Python syntax...${NC}"
if command -v python3 &> /dev/null; then
    if python3 -m py_compile bot.py 2>/dev/null; then
        echo -e "${GREEN}✅ Python syntax validation passed${NC}"
    else
        echo -e "${RED}❌ Python syntax errors found${NC}"
        exit 1
    fi
elif command -v python &> /dev/null; then
    if python -m py_compile bot.py 2>/dev/null; then
        echo -e "${GREEN}✅ Python syntax validation passed${NC}"
    else
        echo -e "${RED}❌ Python syntax errors found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Python not found, skipping syntax validation (will be validated during Docker build)${NC}"
fi

# 🏗️ Build process
echo -e "${BLUE}🏗️  Building multi-architecture image...${NC}"
echo -e "${CYAN}🏗️  Platforms: ${WHITE}${PLATFORMS}${NC}"

# Build tags
TAGS=(
    "${DOCKER_REPO}:${VERSION}"
    "${DOCKER_REPO}:${GIT_COMMIT}"
)

if [ "$VERSION" != "latest" ]; then
    TAGS+=("${DOCKER_REPO}:latest")
fi

# Build command
BUILD_CMD="docker buildx build"
BUILD_CMD+=" --platform ${PLATFORMS}"
BUILD_CMD+=" --file ${DOCKERFILE}"
BUILD_CMD+=" --build-arg BUILD_DATE=${BUILD_DATE}"
BUILD_CMD+=" --build-arg GIT_COMMIT=${GIT_COMMIT}"
BUILD_CMD+=" --build-arg VERSION=${VERSION}"

# Add tags
for tag in "${TAGS[@]}"; do
    BUILD_CMD+=" --tag ${tag}"
done

# Production optimizations
BUILD_CMD+=" --build-arg PYTHON_VERSION=3.12"
BUILD_CMD+=" --build-arg ALPINE_VERSION=3.18"

# Push to registry (optional)
if [ "$PUSH" = "true" ] || [ "$2" = "push" ]; then
    BUILD_CMD+=" --push"
    echo -e "${GREEN}🚀 Will push to Docker Hub${NC}"
else
    # For local builds, use single platform to avoid --load issues
    if [[ "$PLATFORMS" == *","* ]]; then
        echo -e "${YELLOW}📦 Building locally - using single platform (linux/amd64)${NC}"
        BUILD_CMD="${BUILD_CMD/--platform ${PLATFORMS}/--platform linux/amd64}"
    fi
    BUILD_CMD+=" --load"
    echo -e "${YELLOW}📦 Building locally only${NC}"
fi

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
    if [ "$PUSH" != "true" ] && [ "$2" != "push" ]; then
        echo -e "${BLUE}📏 Image size:${NC}"
        docker images "${DOCKER_REPO}" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | head -n 5
        echo ""
    fi
    
    # Next steps
    echo -e "${PURPLE}🚀 Next steps:${NC}"
    echo -e "${WHITE}   Test:     ${CYAN}docker run --rm ${DOCKER_REPO}:${VERSION}${NC}"
    echo -e "${WHITE}   Push:     ${CYAN}$0 ${VERSION} push${NC}"
    echo -e "${WHITE}   Deploy:   ${CYAN}./scripts/deploy-unraid.sh${NC}"
    echo ""
    
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

# 🧹 Cleanup
echo -e "${BLUE}🧹 Cleaning up...${NC}"
docker buildx rm ddc-builder 2>/dev/null || true
echo -e "${GREEN}✅ Cleanup completed${NC}" 