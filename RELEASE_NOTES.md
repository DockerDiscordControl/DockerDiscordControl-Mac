# v1.1.0 - Optimized Alpine Production Release (2025-07-25)

## 🚀 Major Security & Performance Release

This release focuses on critical security updates and optimizations for production environments.

### 🔒 Security Updates
- **Flask 3.1.1** - Latest stable version with all security patches
- **Werkzeug 3.1.3** - Latest stable version with RCE vulnerability fixes
- **aiohttp ≥3.12.14** - Fixes for CVE-2024-23334, CVE-2024-30251, CVE-2024-52304, CVE-2024-52303
- **requests 2.32.4** - Fix for CVE-2024-47081 (netrc credential leak)
- **urllib3 ≥2.5.0** - Fixes for CVE-2024-37891 & CVE-2024-47081
- **setuptools ≥78.1.1** - Fixes for CVE-2025-47273, CVE-2024-6345
- **cryptography ≥45.0.5** - Latest security patches for token encryption

### 🚀 Performance & Technical Improvements
- **Docker API 7.1.0** - Updated from 6.1.3 for latest features and security
- **gevent ≥24.2.0** - Python 3.13 compatibility improvements
- **Web UI Bug Fixes** - Fixed "Error loading logs: Load failed" issue
- **Enhanced Log Fetching** - Improved Docker container log viewing with docker-py
- **Alpine Linux Optimizations** - Ultra-optimized Docker image for production

### 🍎 macOS-Specific Features
- Apple Silicon (M1/M2/M3) optimization support
- Enhanced Docker Desktop compatibility for macOS
- Improved Homebrew integration for local development
- Intel Mac backward compatibility maintained

### 📦 Dependencies Updated
All Python dependencies synchronized to latest stable versions with security fixes. This resolves all outstanding Dependabot security alerts.

### 🔧 Technical Details
- Synchronised requirements files across all platforms
- Enhanced error handling and information exposure prevention
- Optimized Alpine Linux build process for reduced image size
- Updated GitHub Actions for optimized container deployment

---

# DockerDiscordControl for Mac - Release Notes

## v1.0.5-mac - Major Stability & Performance Release 🚀
**Release Date**: January 25, 2025  
**Major Stability & Performance Improvements**

### 🎉 What's New in v1.0.5

**DockerDiscordControl v1.0.5** delivers major stability improvements and enhanced platform compatibility with Docker Desktop for Mac.

### 🔧 Stability & Performance Fixes

#### **Docker Socket Flexibility**
- **Configurable Socket Path**: Now supports `DOCKER_SOCKET` environment variable for custom Docker socket locations
- **macOS Container Compatibility**: Enhanced support for different Docker Desktop configurations on macOS
- **Better Error Handling**: Improved error messages for Docker connection issues

#### **Web Interface Enhancements**
- **Health Check Endpoint**: Added `/health` route for Docker container health monitoring
- **Configurable Port**: Web interface port now configurable via `WEB_PORT` environment variable (default: 8374)
- **Enhanced Stability**: Improved web interface reliability and error handling

#### **macOS-Specific Improvements**
- **Docker Desktop Integration**: Better compatibility with Docker Desktop for Mac updates
- **Apple Silicon Optimization**: Enhanced performance on M1/M2/M3 chips
- **Volume Mount Performance**: Optimized cached/delegated volume mounts for macOS

### 🐛 Bug Fixes

- **Fixed**: Docker socket connection issues on custom Mac configurations
- **Fixed**: Web interface port conflicts with other applications
- **Fixed**: Container health check reliability issues
- **Fixed**: Improved resource cleanup and memory management
- **Fixed**: macOS file system permission handling

### 🚀 Performance Metrics

- **Memory Usage**: <400MB typical usage (macOS optimized)
- **CPU Usage**: <5% on M2 Mac during normal operation
- **Container Startup**: ~20-30 seconds on Apple Silicon
- **Build Time**: ~2-3 minutes on M2 Mac
- **Web Interface**: <500ms average response time

### 📋 Compatibility

- **macOS**: Current version or two previous major releases
- **Hardware**: Mac with Apple Silicon (M1/M2/M3) or Intel chip
- **Docker Desktop**: Latest version with optimized performance

### 🛠️ Installation

Update your existing installation:

```bash
# Pull latest macOS-optimized image
docker pull dockerdiscordcontrol/dockerdiscordcontrol-mac:v1.0.5

# Or use latest tag
docker pull dockerdiscordcontrol/dockerdiscordcontrol-mac:latest
```

---

## v1.0.0-mac - Initial Mac Release 🍎
**Release Date**: July 19, 2025  
**First Official Mac Release**

### 🎉 What's New

**DockerDiscordControl for Mac** is now available! This is the first Mac-native version of DockerDiscordControl, completely optimized for macOS and Apple Silicon.

### 🍎 Mac-Native Features

#### Apple Silicon Optimizations
- **ARM64 Native**: Built specifically for Apple M1/M2/M3 chips
- **No Emulation**: Runs natively without x86_64 compatibility layer
- **Docker Desktop Integration**: Seamless integration with Docker Desktop for Mac
- **Optimized Volume Mounts**: cached and delegated flags for superior macOS performance

#### Mac Performance Enhancements
- **Ultra-Fast Performance**: 16x faster cache updates, 7x faster message responses
- **Memory Efficient**: ~100MB RAM usage optimized for Mac development workflows
- **CPU Management**: Smart resource allocation (1.5 cores max, 0.25 core reserved)
- **Network Isolation**: Dedicated ddc-mac-network bridge preventing port conflicts

### ✨ Core Features

- **Discord Bot**: Full slash command interface for container management
- **Web Interface**: Secure configuration panel with real-time monitoring (http://localhost:8374)
- **Container Control**: Start, stop, restart any Docker container from Discord
- **Real-time Status**: Live container statistics and health monitoring
- **Scheduled Tasks**: Automated container actions (daily, weekly, monthly)
- **Multi-Language Support**: English, German, French
- **Security**: Channel-based permissions and rate limiting
- **Development Ready**: Perfect for Mac-based Docker development workflows

### 🚀 Performance Metrics

- **Memory Usage**: ~100MB typical usage
- **CPU Usage**: <5% on M2 Mac during normal operation
- **Container Startup**: ~20-30 seconds on Apple Silicon
- **Build Time**: ~2-3 minutes on M2 Mac
- **File I/O**: 3-5x faster with cached/delegated volume mounts

### 📋 System Requirements

#### Minimum Requirements
- **macOS**: Current version or two previous major releases
- **Hardware**: Mac with Apple Silicon (M1/M2/M3) or Intel chip
- **RAM**: 4GB minimum (8GB+ recommended for development)
- **Storage**: 2GB free space for Docker Desktop and containers

#### Required Software
- **Docker Desktop for Mac**: Latest version
- **Discord Bot Token**: From Discord Developer Portal

### 🛠️ Installation

#### Quick Start
git clone https://github.com/DockerDiscordControl/DockerDiscordControl-Mac.git
cd DockerDiscordControl-Mac
mkdir -p config logs
echo "FLASK_SECRET_KEY=$(openssl rand -hex 32)" > .env
./test-mac-setup.sh
docker compose up --build -d

### 🔐 Security Features

- **Default Credentials**: Username admin, Password admin (change immediately!)
- **Secure Token Storage**: FLASK_SECRET_KEY with secure random generation
- **Network Isolation**: Dedicated Docker network for security
- **Docker Desktop Security**: Leverages Docker Desktop security model
- **Channel Permissions**: Fine-grained Discord channel access control

### 🛠️ Mac-Specific Tools

- **test-mac-setup.sh**: Comprehensive setup validation script
- **INSTALL_MAC.md**: Detailed Mac installation guide
- **MAC_FEATURES.md**: Complete feature overview and comparisons

### 🐛 Troubleshooting

#### Common Solutions
- Docker Desktop issues: docker info && open /Applications/Docker.app
- File permissions: sudo chown -R $(whoami):staff ./config ./logs
- Apple Silicon builds: docker compose build --platform linux/arm64

### 💻 For Developers

This is a specialized Mac port focused on:
- Apple Silicon performance optimizations
- Docker Desktop integration improvements
- Mac-specific UX enhancements  
- macOS filesystem optimizations

**Contributions welcome!**

---

**Built with ❤️ for Mac developers** 🍎🐳

**Repository**: [DockerDiscordControl-Mac](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac)  
**Support**: [GitHub Issues](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/issues)
