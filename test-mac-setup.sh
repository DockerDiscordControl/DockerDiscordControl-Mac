#!/bin/bash
# DockerDiscordControl Mac Setup Test Script
# This script validates that the Mac version is properly configured

echo "🍎 DockerDiscordControl Mac Setup Test"
echo "======================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ "$1" == "OK" ]; then
        echo -e "${GREEN}✅ $2${NC}"
    elif [ "$1" == "WARN" ]; then
        echo -e "${YELLOW}⚠️  $2${NC}"
    elif [ "$1" == "ERROR" ]; then
        echo -e "${RED}❌ $2${NC}"
    else
        echo -e "${BLUE}ℹ️  $2${NC}"
    fi
}

# Check 1: macOS version
echo -e "\n${BLUE}1. System Requirements${NC}"
echo -e "   macOS Version: $(sw_vers -productVersion)"
echo -e "   Architecture: $(uname -m)"

if [[ $(uname -m) == "arm64" ]]; then
    print_status "OK" "Apple Silicon detected - using ARM64 optimizations"
elif [[ $(uname -m) == "x86_64" ]]; then
    print_status "WARN" "Intel Mac detected - consider updating docker-compose.yml platform"
fi

# Check 2: Docker Desktop
echo -e "\n${BLUE}2. Docker Desktop${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_status "OK" "Docker installed: $DOCKER_VERSION"
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        print_status "OK" "Docker Desktop is running"
        
        # Check Docker context
        DOCKER_CONTEXT=$(docker context show)
        if [[ "$DOCKER_CONTEXT" == "desktop-linux" ]]; then
            print_status "OK" "Using Docker Desktop context: $DOCKER_CONTEXT"
        else
            print_status "WARN" "Current context: $DOCKER_CONTEXT (should be desktop-linux)"
        fi
        
        # Check platform support
        if [[ $(uname -m) == "arm64" ]]; then
            if docker buildx ls | grep -q "linux/arm64"; then
                print_status "OK" "ARM64 platform support available"
            else
                print_status "WARN" "ARM64 platform might not be configured"
            fi
        fi
    else
        print_status "ERROR" "Docker Desktop is not running. Please start Docker Desktop."
        exit 1
    fi
else
    print_status "ERROR" "Docker not found. Please install Docker Desktop for Mac."
    exit 1
fi

# Check 3: Project structure
echo -e "\n${BLUE}3. Project Structure${NC}"
if [[ -f "docker-compose.yml" ]]; then
    print_status "OK" "docker-compose.yml found"
else
    print_status "ERROR" "docker-compose.yml not found"
fi

if [[ -f "Dockerfile" ]]; then
    print_status "OK" "Dockerfile found"
else
    print_status "ERROR" "Dockerfile not found"
fi

if [[ -f "requirements.txt" ]]; then
    print_status "OK" "requirements.txt found"
else
    print_status "ERROR" "requirements.txt not found"
fi

if [[ -d "config" ]]; then
    print_status "OK" "config directory exists"
else
    print_status "WARN" "config directory missing - creating it"
    mkdir -p config
fi

if [[ -d "logs" ]]; then
    print_status "OK" "logs directory exists"
else
    print_status "WARN" "logs directory missing - creating it"
    mkdir -p logs
fi

# Check 4: Environment configuration
echo -e "\n${BLUE}4. Environment Configuration${NC}"
if [[ -f ".env" ]]; then
    print_status "OK" ".env file exists"
    
    if grep -q "FLASK_SECRET_KEY" .env; then
        print_status "OK" "FLASK_SECRET_KEY configured"
    else
        print_status "ERROR" "FLASK_SECRET_KEY missing in .env"
    fi
    
    if grep -q "TZ" .env; then
        TZ_VALUE=$(grep "TZ=" .env | cut -d'=' -f2)
        print_status "OK" "Timezone set to: $TZ_VALUE"
    else
        print_status "WARN" "Timezone not set in .env"
    fi
else
    print_status "ERROR" ".env file not found. Please create one with FLASK_SECRET_KEY."
fi

# Check 5: Port availability
echo -e "\n${BLUE}5. Network Configuration${NC}"
if lsof -i :8374 &> /dev/null; then
    PROCESS=$(lsof -t -i :8374)
    print_status "WARN" "Port 8374 is in use by process $PROCESS"
    echo "       You may need to change the port in docker-compose.yml"
else
    print_status "OK" "Port 8374 is available"
fi

# Check 6: File permissions
echo -e "\n${BLUE}6. File Permissions${NC}"
if [[ -w "config" && -w "logs" ]]; then
    print_status "OK" "Directories are writable"
else
    print_status "WARN" "Permission issues detected. Run: sudo chown -R \$(whoami):staff ./config ./logs"
fi

# Test build (dry run)
echo -e "\n${BLUE}7. Docker Build Test${NC}"
echo "Testing Docker build configuration..."

if [[ $(uname -m) == "arm64" ]]; then
    PLATFORM_FLAG="--platform linux/arm64"
else
    PLATFORM_FLAG="--platform linux/amd64"
fi

if docker compose config &> /dev/null; then
    print_status "OK" "docker-compose.yml syntax is valid"
else
    print_status "ERROR" "docker-compose.yml syntax error"
    docker compose config
fi

# Summary and next steps
echo -e "\n${BLUE}🎯 Summary${NC}"
echo "======================================="

if docker info &> /dev/null && [[ -f ".env" ]]; then
    print_status "OK" "Ready to start DDC-Mac!"
    echo -e "\n${GREEN}Next steps:${NC}"
    echo "1. Configure Discord bot token in .env file:"
    echo "   echo 'DISCORD_BOT_TOKEN=your_token_here' >> .env"
    echo "   echo 'DISCORD_GUILD_ID=your_server_id_here' >> .env"
    echo ""
    echo "2. Build and start DDC-Mac:"
    echo "   docker compose up --build -d"
    echo ""
    echo "3. Access web interface:"
    echo "   open http://localhost:8374"
    echo ""
    echo "4. Check logs:"
    echo "   docker compose logs -f ddc"
else
    print_status "ERROR" "Setup incomplete. Please resolve the issues above."
fi

echo -e "\n${BLUE}🍎 Mac-specific tips:${NC}"
echo "- Use 'docker compose' (not 'docker-compose')"
echo "- For Apple Silicon: builds automatically use ARM64"
echo "- For Intel Macs: specify --platform linux/amd64 if needed"
echo "- Monitor resources in Docker Desktop settings"
echo "- Use ./INSTALL_MAC.md for detailed instructions"

echo -e "\n${BLUE}Happy containerizing! 🐳${NC}" 