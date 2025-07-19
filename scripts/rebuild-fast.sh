#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    ⚡ Fast Rebuild Script for DDC Development                ║
# ║                                                                              ║
# ║  Features:                                                                   ║
# ║  - Uses Docker layer caching                                                 ║
# ║  - Parallel builds when possible                                             ║
# ║  - Skips unnecessary steps                                                   ║
# ║  - Optimized for development workflow                                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# 🎨 Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 📁 Change to parent directory if script is run from scripts/ folder
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ "$SCRIPT_DIR" == *"/scripts" ]]; then
    cd "$PROJECT_ROOT"
    echo -e "${BLUE}📁 Working in: ${WHITE}$(pwd)${NC}"
fi

# Set Docker buildkit for faster builds
export DOCKER_BUILDKIT=1

# Function to check if container is running
is_container_running() {
    docker ps --format "table {{.Names}}" | grep -q "^ddc$"
}

# Function to stop container gracefully
stop_container() {
    if is_container_running; then
        echo -e "${YELLOW}⏸️  Stopping container...${NC}"
        docker stop ddc >/dev/null 2>&1
        echo -e "${GREEN}✅ Container stopped${NC}"
    else
        echo -e "${CYAN}ℹ️  Container not running${NC}"
    fi
}

# Function to remove container
remove_container() {
    if docker ps -a --format "table {{.Names}}" | grep -q "^ddc$"; then
        echo -e "${YELLOW}🗑️  Removing container...${NC}"
        docker rm ddc >/dev/null 2>&1
        echo -e "${GREEN}✅ Container removed${NC}"
    else
        echo -e "${CYAN}ℹ️  Container doesn't exist${NC}"
    fi
}

# Start timer
START_TIME=$(date +%s)

echo -e "${PURPLE}⚡ Starting fast rebuild...${NC}"

# Stop and remove container
stop_container
remove_container

# Clean cache (optional - comment out for even faster builds)
echo -e "${PURPLE}🧹 Quick cleanup...${NC}"
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Build with cache (much faster)
echo -e "${BLUE}🚀 Building with cache optimization...${NC}"
echo -e "${CYAN}💡 Using Docker BuildKit for parallel builds${NC}"

# Use optimized Dockerfile if available, otherwise use standard
if [ -f "Dockerfile.optimized" ]; then
    DOCKERFILE="Dockerfile.optimized"
    echo -e "${GREEN}📄 Using optimized Dockerfile${NC}"
else
    DOCKERFILE="Dockerfile"
    echo -e "${YELLOW}📄 Using standard Dockerfile${NC}"
fi

# Build with cache
if docker build --progress=plain -t dockerdiscordcontrol -f "$DOCKERFILE" . 2>/dev/null; then
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

# Check for configuration
echo -e "${PURPLE}🔑 Configuration check...${NC}"
if [ -f "./config/bot_config.json" ]; then
    TOKEN_EXISTS=$(grep -c "bot_token" ./config/bot_config.json 2>/dev/null || echo "0")
    if [ "$TOKEN_EXISTS" -gt "0" ]; then
        echo -e "${GREEN}✅ Bot token configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Bot token needs configuration${NC}"
    fi
else
    echo -e "${CYAN}ℹ️  No config file yet${NC}"
fi

# Environment setup
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Environment file found${NC}"
    source .env
else
    echo -e "${CYAN}ℹ️  No .env file${NC}"
fi

if [ -z "$FLASK_SECRET_KEY" ]; then
    FLASK_SECRET_KEY="dev-key-$(date +%s)"
fi

# Start container
echo -e "${GREEN}🚀 Starting container...${NC}"
CONTAINER_ID=$(docker run -d \
    --name ddc \
    -p 8374:9374 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ./config:/app/config \
    -v ./logs:/app/logs \
    -e FLASK_SECRET_KEY="${FLASK_SECRET_KEY}" \
    -e ENV_FLASK_SECRET_KEY="${FLASK_SECRET_KEY}" \
    -e PYTHONWARNINGS="ignore" \
    -e LOGGING_LEVEL="INFO" \
    -e DDC_CACHE_TTL="60" \
    -e DDC_DOCKER_CACHE_DURATION="120" \
    -e DDC_DISCORD_SKIP_TOKEN_LOCK="true" \
    --restart unless-stopped \
    --log-driver json-file \
    --log-opt max-size=10m \
    --log-opt max-file=3 \
    --cpus 2.0 \
    --memory 512M \
    --memory-reservation 128M \
    dockerdiscordcontrol 2>/dev/null)

if [ $? -eq 0 ]; then
    # Calculate build time
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))
    
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo -e "${BLUE}⏱️  Total build time: ${WHITE}${BUILD_TIME}s${NC}"
    echo ""
    echo -e "${PURPLE}🌐 Web UI available at:${NC}"
    
    # Get local IP
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || ip route get 1 | awk '{print $7}' 2>/dev/null || echo "localhost")
    
    echo -e "${WHITE}   📍 Local:    ${CYAN}http://localhost:8374${NC}"
    if [ "$LOCAL_IP" != "localhost" ] && [ -n "$LOCAL_IP" ]; then
        echo -e "${WHITE}   🌍 Network:  ${CYAN}http://${LOCAL_IP}:8374${NC}"
    fi
    echo ""
    echo -e "${BLUE}📋 Quick commands:${NC}"
    echo -e "${WHITE}   Logs:     ${CYAN}docker logs ddc -f${NC}"
    echo -e "${WHITE}   Restart:  ${CYAN}docker restart ddc${NC}"
    echo -e "${WHITE}   Stop:     ${CYAN}docker stop ddc${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi 