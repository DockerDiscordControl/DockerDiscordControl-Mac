# DockerDiscordControl for Mac (DDC-Mac)

**The Mac-optimized Discord bot for Docker container management**

Control your Docker containers directly from Discord on your Mac! This Mac-native version provides a Discord bot and web interface specifically built for **macOS** with **Apple Silicon** performance optimizations and **Docker Desktop** integration.

[![Version](https://img.shields.io/badge/version-1.0.0--mac-blue.svg)](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/blob/main/LICENSE)
[![Mac Optimized](https://img.shields.io/badge/Mac-Apple_Silicon_Ready-orange.svg)](https://docs.docker.com/desktop/mac/)
[![Docker Desktop](https://img.shields.io/badge/Requires-Docker_Desktop-blue.svg)](https://docs.docker.com/desktop/install/mac-install/)
[![Memory Optimized](https://img.shields.io/badge/RAM-~100MB-green.svg)](#performance-metrics)

## 🍎 Mac-Native Features

### Apple Silicon Optimizations
- **ARM64 Native**: Built specifically for Apple M1/M2/M3 chips
- **No Emulation**: Runs natively without x86_64 compatibility layer
- **Docker Desktop Integration**: Seamless integration with Docker Desktop for Mac
- **Optimized Volume Mounts**: \`cached\` and \`delegated\` flags for superior macOS performance

### Mac Performance Enhancements
- **Faster File I/O**: Optimized volume caching for macOS filesystem
- **Memory Efficient**: ~100MB RAM usage optimized for Mac development workflows  
- **CPU Management**: Smart resource allocation working with macOS power management
- **Network Isolation**: Dedicated bridge network preventing port conflicts

## 🚀 Performance Highlights

- **Ultra-Fast Cache Updates**: 16x performance improvement
- **Quick Message Updates**: 7x faster Discord responses (350ms average)
- **No Docker Timeouts**: Eliminated critical 5-17 second delays
- **Apple Silicon Optimized**: Native ARM64 performance
- **Mac File System**: Optimized I/O with intelligent caching

## ✨ Core Features

- **Discord Bot**: Full slash command interface for container management
- **Web Interface**: Secure configuration panel with real-time monitoring
- **Container Control**: Start, stop, restart any Docker container from Discord
- **Real-time Status**: Live container statistics and health monitoring
- **Scheduled Tasks**: Automated container actions (daily, weekly, monthly)
- **Multi-Language**: English, German, French support
- **Security**: Channel-based permissions and rate limiting
- **Development Ready**: Perfect for Mac-based Docker development workflows

## 📋 Mac Requirements

### System Requirements
- **macOS**: Current version or two previous major releases
- **Hardware**: Mac with Apple Silicon (M1/M2/M3) or Intel chip
- **RAM**: 4GB minimum (8GB+ recommended for development)
- **Storage**: 2GB free space for Docker Desktop and containers

### Required Software
- **Docker Desktop for Mac**: [Download here](https://docs.docker.com/desktop/install/mac-install/)
- **Discord Bot**: [Create via Developer Portal](https://discord.com/developers/applications)

## 🚀 Quick Start

### 1. Install Docker Desktop

**For Apple Silicon (M1/M2/M3):**
\`\`\`bash
# Download and install Docker Desktop for Apple Silicon
curl -o Docker.dmg https://desktop.docker.com/mac/main/arm64/Docker.dmg
sudo hdiutil attach Docker.dmg
sudo /Volumes/Docker/Docker.app/Contents/MacOS/install --accept-license
sudo hdiutil detach /Volumes/Docker
\`\`\`

**For Intel Mac:**
\`\`\`bash
# Download and install Docker Desktop for Intel
curl -o Docker.dmg https://desktop.docker.com/mac/main/amd64/Docker.dmg
sudo hdiutil attach Docker.dmg
sudo /Volumes/Docker/Docker.app/Contents/MacOS/install --accept-license
sudo hdiutil detach /Volumes/Docker
\`\`\`

### 2. Setup DDC-Mac

\`\`\`bash
# Clone the Mac-optimized repository
git clone https://github.com/DockerDiscordControl/DockerDiscordControl-Mac.git
cd DockerDiscordControl-Mac

# Create directories and environment
mkdir -p config logs
echo "FLASK_SECRET_KEY=\$(openssl rand -hex 32)" > .env
echo "TZ=\$(date +%Z)" >> .env

# Validate your setup
./test-mac-setup.sh
\`\`\`

### 3. Start DDC-Mac

\`\`\`bash
# Build and start (Apple Silicon)
docker compose up --build -d

# For Intel Macs
docker compose build --platform linux/amd64
docker compose up -d

# Check status
docker compose logs -f ddc
\`\`\`

### 4. Configure via Web Interface

1. **Open**: http://localhost:8374
2. **Login**: Username \`admin\`, Password \`admin\`
3. **⚠️ CHANGE PASSWORD IMMEDIATELY!**
4. **Configure**: Discord bot token and Guild ID
5. **Set Permissions**: Choose which containers to control
6. **Restart**: \`docker compose restart ddc\`

## 🔧 Mac Configuration

### Docker Desktop Settings

**Resources → Advanced:**
- **CPUs**: 2-4 cores (adjust for your Mac)
- **Memory**: 4-8GB (minimum 4GB for DDC)
- **Swap**: 1GB

**File Sharing:**
- Ensure project directory is accessible
- Add \`/Users\` if not present

### Environment Variables

Create/edit \`.env\` file:
\`\`\`bash
# Required
FLASK_SECRET_KEY=your_generated_secret_key
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_discord_server_id

# Mac optimizations
TZ=America/New_York
DOCKER_SOCKET=/var/run/docker.sock
DOCKER_CONTEXT=desktop-linux
LOG_LEVEL=INFO
\`\`\`

## 🐛 Mac Troubleshooting

### Docker Issues
\`\`\`bash
# Check if Docker Desktop is running
docker info

# Restart Docker Desktop
osascript -e 'quit app "Docker Desktop"'
open /Applications/Docker.app
\`\`\`

### File Permissions
\`\`\`bash
# Fix file permissions
sudo chown -R \$(whoami):staff ./config ./logs
chmod -R 755 ./config ./logs
\`\`\`

### Port Conflicts
\`\`\`bash
# Find what's using port 8374
lsof -ti:8374

# Kill conflicting process (if safe)
kill -9 \$(lsof -ti:8374)
\`\`\`

### Apple Silicon Issues
\`\`\`bash
# Force ARM64 build
docker compose build --platform linux/arm64

# Verify native architecture
docker inspect ddc-mac | grep Architecture
\`\`\`

## 📊 Performance Metrics

### Resource Usage
- **Memory**: ~100MB typical usage
- **CPU**: <5% on M2 Mac during normal operation  
- **Startup**: ~20-30 seconds on Apple Silicon
- **Build Time**: ~2-3 minutes on M2 Mac

### Mac vs Other Platforms
| Metric | Mac Version | Benefits |
|--------|-------------|----------|
| Memory Limit | 100MB | Optimized for Mac multitasking |
| CPU Cores | 1.5 | Conservative for development |
| Platform | ARM64 Native | No emulation overhead |
| Volume Caching | cached/delegated | 3-5x faster file I/O |
| Network | Dedicated bridge | No port conflicts |
| Context | desktop-linux | Docker Desktop integration |

## 🛠️ Management Commands

\`\`\`bash
# Status and monitoring
docker ps | grep ddc-mac                 # Check container status
docker stats ddc-mac                    # Monitor resources
docker compose logs -f ddc              # View live logs

# Container management  
docker compose restart ddc              # Restart DDC
docker compose stop                     # Stop DDC
docker compose down                     # Stop and remove
docker compose up -d                    # Start in background

# Updates and maintenance
git pull                                # Get latest changes
docker compose down && docker compose up --build -d  # Update DDC
./test-mac-setup.sh                     # Validate setup
\`\`\`

## 🔐 Security Best Practices

1. **Change Default Password**: First priority after installation
2. **Secure Bot Token**: Keep Discord bot token private and secure
3. **Network Security**: Consider restricting port 8374 access
4. **Regular Updates**: Keep Docker Desktop and DDC-Mac updated
5. **Backup Configuration**: Regular backups of config directory

## 🆘 Getting Help

- **Mac Issues**: [GitHub Issues](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/issues)
- **Installation Guide**: [INSTALL_MAC.md](INSTALL_MAC.md)
- **Feature Overview**: [MAC_FEATURES.md](MAC_FEATURES.md)
- **Setup Validation**: Run \`./test-mac-setup.sh\`
- **Docker Desktop**: [Official Mac Documentation](https://docs.docker.com/desktop/mac/)

## 🤝 Contributing

Mac-specific improvements and optimizations are welcome! This is a specialized Mac port focused on:

- Apple Silicon performance optimizations
- Docker Desktop integration improvements  
- Mac-specific UX enhancements
- macOS filesystem optimizations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built for Mac Developers** | **Optimized for Apple Silicon** | **Docker Desktop Ready**

### ☕ Support Development

Help improve DDC-Mac for the Mac community:

- **[GitHub Sponsors](https://github.com/sponsors/DockerDiscordControl)** - Support ongoing development
- **[Report Issues](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/issues)** - Help improve stability  
- **[Submit PRs](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/pulls)** - Contribute Mac optimizations

**Made with ❤️ for Mac developers** 🍎🐳
