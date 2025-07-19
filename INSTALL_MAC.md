# DockerDiscordControl Mac Installation Guide

This guide provides detailed steps for installing and running DockerDiscordControl on macOS with Docker Desktop.

## 🍎 Prerequisites

### 1. System Requirements
- **macOS**: Current or two previous major releases
- **Hardware**: Mac with Apple Silicon (M1/M2/M3) or Intel
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 2GB free space

### 2. Install Docker Desktop

**Download and Install:**
1. Visit [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Download the version for your chip:
   - **Apple Silicon**: Docker Desktop for Mac with Apple silicon
   - **Intel**: Docker Desktop for Mac with Intel chip
3. Install by dragging to Applications folder
4. Launch Docker Desktop and complete setup

**Verify Installation:**
```bash
docker --version
docker compose version
```

## 🚀 Installation Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/DockerDiscordControl/DockerDiscordControl-Mac.git
cd DockerDiscordControl-Mac
```

### Step 2: Create Directories
```bash
mkdir -p config logs
```

### Step 3: Configure Environment
```bash
# Create secure environment file
echo "FLASK_SECRET_KEY=$(openssl rand -hex 32)" > .env

# Add timezone (optional)
echo "TZ=$(ls -la /etc/localtime | cut -d/ -f8-9 2>/dev/null || echo 'America/New_York')" >> .env

# Show generated .env content
cat .env
```

### Step 4: Build and Start
```bash
# Build and start the container (Apple Silicon)
docker compose up --build -d

# For Intel Macs, force platform
docker compose build --platform linux/amd64
docker compose up -d

# View logs
docker compose logs -f ddc
```

### Step 5: Configure DDC
1. Open browser to `http://localhost:8374`
2. Login with username: `admin`, password: `admin`
3. **IMMEDIATELY change the admin password!**
4. Configure Discord bot token and Guild ID
5. Set container permissions
6. Restart: `docker compose restart ddc`

## 🔧 Configuration

### Docker Desktop Settings
Optimize Docker Desktop for DDC:

**Resources → Advanced:**
- **CPUs**: 2-4 cores
- **Memory**: 4-8GB (minimum 4GB)
- **Swap**: 1GB
- **Disk image size**: 64GB+

**File Sharing:**
- Ensure `/Users` is in shared folders
- Add your project directory if needed

### Environment Variables
Create `.env` file with:
```bash
# Required
FLASK_SECRET_KEY=your_generated_secret_key
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_GUILD_ID=your_server_id

# Optional Mac optimizations
TZ=America/New_York
DOCKER_SOCKET=/var/run/docker.sock
DOCKER_CONTEXT=desktop-linux
LOG_LEVEL=INFO
```

## 🐛 Troubleshooting

### Docker Desktop Issues
```bash
# Check if Docker is running
docker info

# Restart Docker Desktop
osascript -e 'quit app "Docker Desktop"'
open /Applications/Docker.app
```

### Permission Problems
```bash
# Fix file permissions
sudo chown -R $(whoami):staff ./config ./logs
chmod -R 755 ./config ./logs
```

### Port Conflicts
```bash
# Check what's using port 8374
lsof -ti:8374

# Kill process if safe
kill -9 $(lsof -ti:8374)

# Or change port in docker-compose.yml
# ports: ["8375:9374"]
```

### Platform Issues (Apple Silicon)
```bash
# Force correct platform
docker compose build --platform linux/arm64
docker compose up -d

# Check container architecture
docker inspect ddc-mac | grep Architecture
```

### Container Won't Start
```bash
# Check logs
docker compose logs ddc

# Rebuild from scratch
docker compose down
docker system prune -f
docker compose up --build -d
```

## 🔄 Updates

### Update DDC-Mac
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose up --build -d
```

### Update Docker Desktop
1. Docker Desktop will notify you of updates
2. Follow the update process
3. Restart DDC after Docker Desktop update

## 📊 Performance Monitoring

### Check Resource Usage
```bash
# Container stats
docker stats ddc-mac

# Mac system monitoring
top -pid $(docker inspect -f '{{.State.Pid}}' ddc-mac)
```

### Optimize Performance
```bash
# Clear Docker cache periodically
docker system prune -f

# Restart container to clear memory
docker compose restart ddc
```

## 🛡️ Security Best Practices

1. **Change Default Password**: First priority after installation
2. **Secure Bot Token**: Keep Discord bot token private
3. **Firewall**: Consider restricting port 8374 access
4. **Updates**: Keep Docker Desktop and DDC updated
5. **Backups**: Backup config directory regularly

## 📞 Get Help

- **Mac-specific issues**: [GitHub Issues](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/issues)
- **Docker Desktop help**: [Docker Documentation](https://docs.docker.com/desktop/mac/)
- **Discord**: Join our support server (link in README)

---

**Happy containerizing on Mac!** 🍎🐳 