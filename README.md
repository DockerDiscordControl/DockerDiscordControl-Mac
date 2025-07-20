# DockerDiscordControl - macOS Edition

[![Docker Hub](https://img.shields.io/docker/v/dockerdiscordcontrol/dockerdiscordcontrol-mac?label=docker%20hub)](https://hub.docker.com/r/dockerdiscordcontrol/dockerdiscordcontrol-mac)
[![Docker Pulls](https://img.shields.io/docker/pulls/dockerdiscordcontrol/dockerdiscordcontrol-mac)](https://hub.docker.com/r/dockerdiscordcontrol/dockerdiscordcontrol-mac)
[![Image Size](https://img.shields.io/docker/image-size/dockerdiscordcontrol/dockerdiscordcontrol-mac/latest)](https://hub.docker.com/r/dockerdiscordcontrol/dockerdiscordcontrol-mac)

**Control your Docker containers directly from Discord on macOS!**

DockerDiscordControl-Mac is specifically optimized for macOS environments, providing seamless integration with Docker Desktop for Mac and enhanced Apple Silicon (M1/M2/M3) support for the best Discord bot experience on Mac.

**🌐 Homepage: [https://ddc.bot](https://ddc.bot)**

## 🚀 Quick Start

### Using Docker Hub

```bash
# Pull the latest macOS-optimized image
docker pull dockerdiscordcontrol/dockerdiscordcontrol-mac:latest

# Run with Docker Compose
docker-compose up -d
```

### Using Docker Run

```bash
docker run -d \
  --name dockerdiscordcontrol-mac \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ./config:/app/config \
  -e DISCORD_BOT_TOKEN=your_bot_token_here \
  -e ALLOWED_CHANNELS=channel_id_1,channel_id_2 \
  -e ALLOWED_ROLES=role_id_1,role_id_2 \
  -p 8080:8080 \
  dockerdiscordcontrol/dockerdiscordcontrol-mac:latest
```

## ✨ macOS-Specific Features

- **Apple Silicon Optimization**: Native support for M1/M2/M3 processors (ARM64)
- **Docker Desktop for Mac Integration**: Seamless integration with Docker Desktop
- **macOS Performance Tuning**: Optimized for macOS virtual machine constraints
- **Homebrew Compatibility**: Easy installation alongside Homebrew packages
- **macOS Notifications**: Native system notification support (planned)

## 🏗️ Architecture

This macOS-optimized version includes:

- **Alpine Linux Base**: Ultra-lightweight foundation perfect for macOS virtualization
- **Python 3.13**: Latest Python runtime with macOS optimizations
- **Supervisor**: Efficient process management for Mac environments
- **Multi-Architecture**: Native support for both Intel (AMD64) and Apple Silicon (ARM64)

## 📋 Requirements

### System Requirements
- **macOS**: macOS 10.15 Catalina or later (macOS 12+ recommended)
- **Architecture**: Intel x64 or Apple Silicon (M1/M2/M3)
- **Docker Desktop for Mac**: Version 4.0+ with latest updates
- **Memory**: Minimum 512MB RAM (1GB+ recommended)
- **Storage**: 500MB+ free disk space

### Discord Requirements
- Discord bot token with necessary permissions
- Guild/server with appropriate permissions
- Channel IDs for command execution

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DISCORD_BOT_TOKEN` | Your Discord bot token | ✅ Yes | - |
| `ALLOWED_CHANNELS` | Comma-separated channel IDs | ✅ Yes | - |
| `ALLOWED_ROLES` | Comma-separated role IDs | ✅ Yes | - |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | ❌ No | `INFO` |
| `WEB_UI_PORT` | Web interface port | ❌ No | `8080` |
| `MAX_CONTAINERS` | Maximum containers to manage | ❌ No | `25` |
| `MACOS_OPTIMIZED` | Enable macOS-specific optimizations | ❌ No | `true` |

### Docker Compose Example

```yaml
version: '3.8'
services:
  dockerdiscordcontrol:
    image: dockerdiscordcontrol/dockerdiscordcontrol-mac:latest
    container_name: dockerdiscordcontrol-mac
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - ALLOWED_CHANNELS=${ALLOWED_CHANNELS}
      - ALLOWED_ROLES=${ALLOWED_ROLES}
      - LOG_LEVEL=INFO
      - MACOS_OPTIMIZED=true
    ports:
      - "8080:8080"
    networks:
      - dockerdiscordcontrol
    labels:
      - "com.dockerdiscordcontrol.version=1.0.4"
      - "com.dockerdiscordcontrol.platform=macos"

networks:
  dockerdiscordcontrol:
    driver: bridge
```

## 🎮 Discord Commands

### Container Management
- `/docker ps` - List running containers
- `/docker start <container>` - Start a container
- `/docker stop <container>` - Stop a container
- `/docker restart <container>` - Restart a container
- `/docker logs <container>` - View container logs
- `/docker stats` - Show container statistics

### System Information
- `/system info` - Display system information
- `/system resources` - Show resource usage
- `/docker version` - Docker version information

### macOS-Specific Commands
- `/system cpu` - Show Apple Silicon CPU information
- `/system memory` - macOS memory usage statistics
- `/docker desktop` - Docker Desktop for Mac status

## 🌐 Web Interface

Access the web interface at `http://localhost:8080` for:

- **Real-time Container Monitoring**: Live status optimized for Mac
- **Configuration Management**: macOS-friendly setup interface
- **Log Viewer**: Centralized log management with macOS styling
- **Performance Dashboard**: Apple Silicon performance metrics
- **Resource Monitor**: macOS-specific resource tracking

## 🔒 Security Features

### Built-in Security
- **Role-based Access Control**: Discord role verification
- **Channel Restrictions**: Limit commands to specific channels
- **Command Auditing**: Full audit trail of all commands
- **Rate Limiting**: Prevention of command spam
- **Input Validation**: Sanitized command parameters

### macOS Security Integration
- **Keychain Integration**: Secure credential storage (planned)
- **Gatekeeper Compatibility**: Signed for macOS security
- **Sandbox Support**: Runs within macOS security sandbox
- **Privacy Permissions**: Respects macOS privacy settings

## 🔍 Monitoring & Logging

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning messages for attention
- **ERROR**: Error conditions

### Health Checks
The container includes macOS-optimized health checks:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' dockerdiscordcontrol-mac

# View health check logs
docker inspect dockerdiscordcontrol-mac | grep -A5 Health
```

### Performance Monitoring
```bash
# Monitor resource usage on Mac
docker stats dockerdiscordcontrol-mac

# Check Apple Silicon specific metrics
curl http://localhost:8080/metrics/macos
```

## 🛠️ Troubleshooting

### Common macOS Issues

#### Docker Desktop Connection
```bash
# Check Docker Desktop status
docker info

# Restart Docker Desktop if needed
open -a Docker
```

#### Permission Issues
```bash
# Check Docker socket permissions
ls -la /var/run/docker.sock

# Verify user is in docker group
groups $USER
```

#### Apple Silicon Specific
```bash
# Verify ARM64 image is being used
docker inspect dockerdiscordcontrol-mac | grep Architecture

# Check for Intel emulation
docker exec dockerdiscordcontrol-mac uname -m
```

#### Bot Not Responding
```bash
# Check bot logs
docker logs dockerdiscordcontrol-mac --tail 50

# Verify network connectivity
docker exec dockerdiscordcontrol-mac ping discord.com
```

### Performance Optimization
- Use Apple Silicon native images when available
- Adjust `MAX_CONTAINERS` based on Mac performance
- Monitor Docker Desktop resource allocation
- Use SSD storage for optimal performance

## 📦 Tags & Versions

| Tag | Description | Architecture |
|-----|-------------|--------------|
| `latest` | Latest stable release | `linux/amd64`, `linux/arm64` |
| `1.0.4` | Version 1.0.4 | `linux/amd64`, `linux/arm64` |
| `1.0.3` | Version 1.0.3 | `linux/amd64`, `linux/arm64` |
| `m1` | Apple Silicon optimized | `linux/arm64` |
| `intel` | Intel Mac optimized | `linux/amd64` |
| `alpine` | Alpine Linux base | `linux/amd64`, `linux/arm64` |

## 🍎 Installation on macOS

### Prerequisites
```bash
# Install Docker Desktop for Mac
brew install --cask docker

# Verify installation
docker --version
docker-compose --version
```

### Quick Setup
```bash
# Clone repository
git clone https://github.com/dockerdiscordcontrol/dockerdiscordcontrol-mac.git
cd dockerdiscordcontrol-mac

# Setup configuration
cp env.template .env
open -a TextEdit .env

# Start the service
docker-compose up -d

# Open web interface
open http://localhost:8080
```

## 🤝 Support

### Documentation
- **🌐 Official Homepage**: [https://ddc.bot](https://ddc.bot)
- **Main Repository (Unraid)**: [DockerDiscordControl](https://github.com/DockerDiscordControl/DockerDiscordControl)
- **Mac Repository**: [DockerDiscordControl-Mac](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac)
- **Installation Guide**: [macOS Setup Instructions](https://github.com/DockerDiscordControl/DockerDiscordControl/blob/main/INSTALL_MAC.md)
- **Wiki**: [Comprehensive Documentation](https://github.com/DockerDiscordControl/DockerDiscordControl/wiki)

### Community
- **Discord Server**: Join our community for support
- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Community Q&A and discussions

### macOS-Specific Support
- Apple Silicon optimization help
- Docker Desktop for Mac integration
- macOS security and permissions guidance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/DockerDiscordControl/DockerDiscordControl/blob/main/LICENSE) file for details.

## 🎉 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/DockerDiscordControl/DockerDiscordControl/blob/main/CONTRIBUTING.md) for details.

## 💝 Support DDC Development

Help keep DockerDiscordControl growing and improving for macOS Docker Desktop users:

- **[☕ Buy Me A Coffee](https://buymeacoffee.com/dockerdiscordcontrol)** - Quick one-time support for development
- **[💳 PayPal Donation](https://www.paypal.com/donate/?hosted_button_id=XKVC6SFXU2GW4)** - Direct contribution to the project

**Your support helps:**
- 🛠️ Maintain DDC for Mac with latest Docker Desktop compatibility
- ✨ Develop new macOS-specific features and Apple Silicon optimizations  
- 🔒 Keep DockerDiscordControl zero-vulnerability secure for Mac environments
- 📚 Create comprehensive macOS documentation and setup guides
- 🚀 Performance optimizations for Apple Silicon and Intel Mac users

**Thank you for supporting open source development!** 🙏

---

**Made with ❤️ for the macOS Docker community**

[![GitHub](https://img.shields.io/badge/GitHub-DockerDiscordControl-blue?logo=github)](https://github.com/DockerDiscordControl)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-dockerdiscordcontrol-blue?logo=docker)](https://hub.docker.com/u/dockerdiscordcontrol)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-Optimized-success?logo=apple)](https://github.com/DockerDiscordControl)
