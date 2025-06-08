#!/bin/bash

# Change to parent directory if script is run from scripts/ folder
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# If we're in the scripts directory, move up to the project root
if [[ "$SCRIPT_DIR" == *"/scripts" ]]; then
    cd "$PROJECT_ROOT"
    echo ">>> Changed working directory to project root: $(pwd)"
fi

# Exits the script immediately if a command fails (except those with || true)
set -e

echo ">>> Stopping container ddc-alpine-test..."
docker stop ddc-alpine-test || true # || true prevents errors if the container is not running
sleep 1

echo ">>> Removing container ddc-alpine-test..."
docker rm ddc-alpine-test || true # || true prevents errors if the container does not exist
sleep 1

# <<< NEW: Delete pycache >>>
echo ">>> Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +
sleep 1
# <<< End of pycache deletion >>>

echo ">>> Rebuilding Alpine image dockerdiscordcontrol:alpine (without cache)..."
docker build --no-cache -f Dockerfile.alpine -t dockerdiscordcontrol:alpine .
# If the build fails, the script stops here thanks to 'set -e'

sleep 1

# Fix an existing token if present
echo ">>> Checking for existing bot token..."
if [ -f "./config/bot_config.json" ]; then
    # Try to extract the token (without decrypting it)
    TOKEN_EXISTS=$(grep -c "bot_token" ./config/bot_config.json || echo "0")
    
    if [ "$TOKEN_EXISTS" -gt "0" ]; then
        echo ">>> Bot token found, ensuring it's properly configured..."
    else
        echo ">>> No bot token found in configuration. Please set it in the web UI."
    fi
fi

# Set environment variable for restricted logging
export PYTHONWARNINGS="ignore"
export LOGGING_LEVEL="WARNING"

# Ask for Flask secret key if not provided in .env
if [ -f ".env" ]; then
    echo ">>> Using .env file for environment variables"
    source .env
fi

if [ -z "$FLASK_SECRET_KEY" ]; then
    echo ">>> WARNING: FLASK_SECRET_KEY not set. Using a temporary key for development purposes only."
    echo ">>> For production, create a .env file with a secure FLASK_SECRET_KEY value."
    FLASK_SECRET_KEY="temporary-dev-key-$(date +%s)"
fi

# Start Alpine test container with optimized environment
echo ">>> Starting new Alpine test container ddc-alpine-test..."
docker run -d \
  --name ddc-alpine-test \
  -p 9375:9374 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ./config:/app/config \
  -v ./logs:/app/logs \
  -e FLASK_SECRET_KEY="${FLASK_SECRET_KEY}" \
  -e ENV_FLASK_SECRET_KEY="${FLASK_SECRET_KEY}" \
  -e ENV_DOCKER_SOCKET='/var/run/docker.sock' \
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
  dockerdiscordcontrol:alpine

sleep 1
echo ">>> Script finished. Check the logs with 'docker logs ddc-alpine-test -f'"
echo ">>> Alpine test container running on port 9375"
echo ">>> Web UI: http://[YOUR-IP]:9375"
