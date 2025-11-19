# DockerDiscordControl for macOS v2.0 🍎

Control your Docker containers directly from Discord on macOS! This Mac-native version provides a Discord bot and web interface specifically optimized for **macOS systems** with **Docker Desktop integration** and **Apple Silicon + Intel compatibility**.

---

## 💖 **Support DDC Development**

**Help keep DockerDiscordControl growing and improving across all platforms!**

<div align="center">

[![Buy Me A Coffee](https://img.shields.io/badge/☕_Buy_Me_A_Coffee-Support_DDC-orange?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/dockerdiscordcontrol)
&nbsp;&nbsp;&nbsp;
[![PayPal Donation](https://img.shields.io/badge/💝_PayPal_Donation-Support_DDC-blue?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/dockerdiscordcontrol)

**Your support helps maintain DDC across Windows, Linux, macOS, and Universal versions!**

</div>

---

**Homepage:** [DDC for Mac](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac) | **Main Project:** [DockerDiscordControl](https://github.com/DockerDiscordControl/DockerDiscordControl)

[![Version](https://img.shields.io/badge/version-v2.0.0-brightgreen.svg?style=for-the-badge)](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/blob/main/LICENSE)
[![macOS Optimized](https://img.shields.io/badge/macOS-Docker_Desktop-blue.svg?style=for-the-badge)](#performance-metrics)
[![Apple Silicon](https://img.shields.io/badge/Apple_Silicon-M1_M2_M3_M4-orange.svg?style=for-the-badge)](#installation)
[![Memory Optimized](https://img.shields.io/badge/RAM-<200MB-green.svg?style=for-the-badge)](#performance-metrics)
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge)](https://python.org)
[![Alpine](https://img.shields.io/badge/Base-Alpine%203.22.2-blueviolet?style=for-the-badge)](#docker-hub-repository)

## 🆕 Latest Updates - v2.0.0 (2025-11-19)

### ✅ **MAJOR UPDATE - Complete Rewrite for macOS**

🎮 **EVERYTHING via Discord - Complete Control:**
- **NEW:** Live Logs Viewer - Monitor container output in real-time directly in Discord
- **NEW:** Task System - Create, view, delete tasks (Once, Daily, Weekly, Monthly, Yearly) entirely in Discord
- **NEW:** Container Info System - Attach custom info and password-protected info to containers
- **NEW:** Public IP Display - Automatic WAN IP detection with custom port support
- Full container management without leaving Discord (start, stop, restart, bulk operations)

🌍 **Multi-Language Support:**
- **NEW:** Full Discord UI translation in German, French, and English
- Complete language coverage for all buttons, messages, and interactions
- Dynamic language switching via Web UI settings
- 100% translation coverage across entire bot interface

🤖 **Mech Evolution System:**
- **NEW:** 11-stage Mech Evolution with animated WebP graphics
- Continuous power decay system for fair donation tracking
- Premium key system for power users
- Visual feedback with stage-specific animations and particle effects

⚡ **Performance Improvements:**
- **IMPROVED:** 16x faster Docker status cache (500ms → 31ms)
- 7x faster container processing through async optimization
- Smart queue system with fair request processing
- Operation-specific timeout optimization

🍎 **macOS-Specific Optimizations:**
- **Native Docker Desktop Integration:** Optimized socket handling for macOS
- **Universal Binary Support:** Full M1/M2/M3/M4 and Intel Mac compatibility
- **Resource Efficiency:** <200MB RAM usage, tuned for macOS resource patterns
- **Alpine Linux 3.22.2:** Ultra-lightweight base with 94% fewer vulnerabilities

🎨 **Modern UI/UX Overhaul:**
- **IMPROVED:** Beautiful Discord embeds with consistent styling
- Advanced spam protection with configurable cooldowns
- Enhanced container information system
- Real-time monitoring and status updates

🔒 **Security & Optimization:**
- **IMPROVED:** Alpine Linux 3.22.2 base (94% fewer vulnerabilities)
- Ultra-compact multi-stage Docker build (<200MB RAM usage)
- Production-ready security hardening
- Enhanced token encryption and validation

**🚀 Ready for production on any macOS system with Docker Desktop!**

---

## 🐳 Docker Hub Repository

**Mac-Optimized Image:** `dockerdiscordcontrol/dockerdiscordcontrol-mac`

This repository publishes **only** the Mac-optimized Alpine-based image, specifically tuned for:
- Apple Silicon (M1/M2/M3/M4) and Intel Mac compatibility
- macOS Docker Desktop integration
- Optimal resource usage on macOS systems
- Native macOS Docker socket handling

**Other Platform Images:**
- **Universal/Unraid**: `dockerdiscordcontrol/dockerdiscordcontrol`
- **Windows**: `dockerdiscordcontrol/dockerdiscordcontrol-windows`
- **Linux**: `dockerdiscordcontrol/dockerdiscordcontrol-linux`

---

## 🚀 Revolutionary macOS Performance

**Major Mac-Specific Optimizations Delivered:**

- **Docker Desktop Integration**: Native macOS Docker Desktop support with <200MB typical RAM usage
- **Universal Binary Support**: Optimized for both Apple Silicon (M1/M2/M3/M4) and Intel Macs
- **macOS Native Features**: Homebrew integration and native macOS management
- **Resource Efficiency**: Tuned specifically for macOS resource management patterns
- **Alpine Optimization**: Ultra-lightweight Alpine Linux 3.22.2 base for maximum efficiency
- **Multi-Stage Build**: Optimized Docker build process reducing image size by 78%

---

## Features - EVERYTHING via Discord! 🚀

### 🎮 Discord Container Control
- **Start, Stop, Restart** individual containers or **ALL containers at once**
- **Live Logs Viewer** - Monitor container output in real-time directly in Discord
- **Attach Custom Info** to containers (e.g., current WAN IP address, connection details)
- **Password-Protected Info** for secure data sharing within your Discord community
- **Container Status** monitoring with real-time updates

### 📅 Discord Task Scheduler
- **Create, view, and delete** automated tasks directly in Discord channels
- **Flexible Scheduling**: Once, Daily, Weekly, Monthly, Yearly
- **Full Task Management** - Complete control without leaving Discord
- **Timezone Configuration** for accurate scheduling across regions

### 🔒 Flexible Permissions System
- **Status Channels**: All members see container status and public info
- **Status Channels**: Admin users get admin panel access for full control
- **Control Channels**: Everyone gets full admin access to all features
- **Granular Container Permissions**: Fine-grained control per container (Status, Start, Stop, Restart, Active visibility)
- **Hide Containers** from Discord or configure custom visibility per container
- **Password-Protected Info**: Viewable by anyone who knows the password
- **Spam Protection**: All Discord commands and button clicks protected by configurable cooldowns

### 🌐 Web Interface
- **Secure Configuration Panel** with real-time monitoring
- **Container Management**: Configure permissions, custom info, and visibility
- **Task Management**: Create and manage scheduled tasks
- **Admin User Management**: Define who gets admin panel access in status channels
- **Security Audit**: Built-in security scoring and recommendations

### 🎨 Customization & Localization
- **Multi-Language Support**: Full Discord UI in English, German, and French
- **Customizable Container Order**: Organize containers in your preferred display order
- **Mech Evolution System**: 11-stage evolution with animated graphics and premium keys
- **Custom Branding**: Configure container display names and information

### ⚡ Performance & Optimization
- **16x Faster Docker Cache**: Optimized from 500ms to 31ms response time
- **7x Faster Processing**: Through async optimization and smart queue system
- **Alpine Linux 3.22.2**: 94% fewer vulnerabilities, less than 200MB RAM usage
- **Production Ready**: Supports 50 containers across 15 Discord channels
- **Intelligent Caching**: Background refresh for real-time data

---

## 🛠️ Quick Installation

### **Prerequisites**

1. **macOS System**: macOS 10.15+ (Catalina or later)
2. **Docker Desktop**: [Install Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
3. **Discord Bot**: [Create a Discord Bot](https://github.com/DockerDiscordControl/DockerDiscordControl/wiki/Discord‐Bot‐Setup)

### **Method 1: Docker Hub Installation (Recommended)**

```bash
# Pull the Mac-optimized image
docker pull dockerdiscordcontrol/dockerdiscordcontrol-mac:latest

# Create directories
mkdir -p config logs

# Create .env file with secure secret key
echo "FLASK_SECRET_KEY=$(openssl rand -hex 32)" > .env

# Run with docker compose
docker compose up -d
```

### **Method 2: Docker Run (Direct)**

```bash
# Run directly with Docker
docker run -d --name ddc \
  -p 9374:9374 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ./config:/app/config \
  -v ./logs:/app/logs \
  -e FLASK_SECRET_KEY="$(openssl rand -hex 32)" \
  --restart unless-stopped \
  dockerdiscordcontrol/dockerdiscordcontrol-mac:latest
```

### **Method 3: Build from Source**

```bash
# Clone the repository
git clone https://github.com/DockerDiscordControl/DockerDiscordControl-Mac.git
cd DockerDiscordControl-Mac

# Create directories
mkdir -p config logs

# Create .env file
echo "FLASK_SECRET_KEY=$(openssl rand -hex 32)" > .env

# Build and start
docker compose up --build -d
```

---

## 🔧 Configuration

### **First-Time Setup**

**🚀 Easy Web Setup (Recommended)**

1. **Access Web UI**: `http://localhost:9374`
2. **Setup Options**:
   - **Method 1**: Visit `/setup` for guided web setup
   - **Method 2**: Use temporary credentials: `admin` / `setup`
   - **Method 3**: Set `DDC_ADMIN_PASSWORD=your_password` before starting

3. **Complete Setup**: Configure bot token, Guild ID, container permissions
4. **Restart**: `docker compose restart` after initial configuration

**Security Note**: Default password is 'setup' for initial access. MUST be changed immediately after first login for security!

### **Environment Variables**

#### Security & Authentication

```bash
# Option 1: Set admin password before first start (Recommended)
DDC_ADMIN_PASSWORD=your_secure_password_here

# Option 2: Use temporary credentials for web setup
# Visit http://localhost:9374 and login with: admin / setup

# Flask security (auto-generated if not provided)
FLASK_SECRET_KEY=your-64-character-random-secret-key
```

#### Performance Optimization (New in v2.0)

```bash
# Docker Cache Settings
DDC_MAX_CACHED_CONTAINERS=100          # Maximum containers in cache
DDC_DOCKER_CACHE_DURATION=45           # Cache duration in seconds
DDC_ENABLE_BACKGROUND_REFRESH=true     # Enable background refresh

# Web Server Settings
GUNICORN_WORKERS=2                     # Number of worker processes
GUNICORN_TIMEOUT=45                    # Request timeout
```

See the [Main Documentation](https://github.com/DockerDiscordControl/DockerDiscordControl#environment-variables) for complete environment variable reference.

---

## 🍎 macOS-Specific Features

### **Apple Silicon Optimization**
- Full native support for M1, M2, M3, and M4 chips
- Optimized ARM64 binary compilation
- No Rosetta 2 translation required

### **Intel Mac Compatibility**
- Full x86_64 support for Intel-based Macs
- Same feature set as Apple Silicon

### **Docker Desktop Integration**
- Native macOS Docker socket handling at `/var/run/docker.sock`
- Optimized for Docker Desktop's macOS-specific architecture
- Seamless integration with Docker Desktop GUI

### **Resource Management**
- Tuned for macOS memory management patterns
- Minimal CPU usage optimized for battery life
- <200MB RAM footprint for efficient operation

---

## 📊 Performance Metrics

**macOS Docker Desktop Performance (v2.0):**

| Metric | Value | Notes |
|--------|-------|-------|
| **RAM Usage** | <200MB | Typical production usage |
| **Startup Time** | <5s | Cold start to ready |
| **Docker Cache** | 31ms | 16x faster than v1.x |
| **Container Processing** | 7x faster | Async optimization |
| **Image Size** | 176MB | Multi-stage Alpine build |
| **Vulnerabilities** | 0 Critical/High | Alpine 3.22.2 + latest deps |

---

## 🔒 Security Notice

**Docker Socket Access Required**: This application requires access to `/var/run/docker.sock` to control containers. Only run in trusted environments and ensure proper host security.

**First-Time Setup Required**: DDC v2.0+ uses temporary default password 'setup' for initial access. Use one of these secure setup methods:
- **Web Setup**: Visit `/setup` and create your password
- **Temporary Access**: Login with `admin` / `setup`, then set real password
- **Environment Variable**: Set `DDC_ADMIN_PASSWORD` before starting container

**Password Security**: All passwords are hashed with PBKDF2-SHA256 (600,000 iterations) for maximum security.

---

## 🆘 Quick Help

**First-Time Setup Issues:**
- **Can't Login**: Visit `/setup` or use `admin` / `setup` credentials
- **"Authentication Required"**: Use default credentials `admin` / `setup` or configure DDC_ADMIN_PASSWORD
- **Password Reset**: Run `docker exec -it ddc python3 scripts/reset_password.py`

**Common Issues:**
- **Permission Errors**: Run `docker exec ddc /app/scripts/fix_permissions.sh`
- **Configuration Not Saving**: Check file permissions in logs
- **Bot Not Responding**: Verify token and Guild ID in Web UI

**macOS-Specific Issues:**
- **Docker Socket Not Found**: Ensure Docker Desktop is running
- **Permission Denied on Socket**: Check Docker Desktop settings → Advanced → Allow default Docker socket
- **Port Already in Use**: Change host port in docker-compose.yml (first 9374 in `9374:9374`)

**Need Help?** Check our [Troubleshooting Guide](../../wiki/Troubleshooting) or [Mac-Specific Docs](TROUBLESHOOTING.md).

---

## 📚 Documentation

| Topic | Description |
|-------|-------------|
| [Installation Guide](INSTALL_MAC.md) | Detailed macOS setup |
| [Mac Features](MAC_FEATURES.md) | macOS-specific features |
| [Configuration](../../wiki/Configuration) | Web UI, permissions, channels |
| [Task System](../../wiki/Task‐System) | Automated scheduling |
| [Performance](../../wiki/Performance‐and‐Architecture) | Optimizations & monitoring |
| [Troubleshooting](TROUBLESHOOTING.md) | Mac-specific issues |
| [Main Documentation](../../wiki) | Complete wiki |

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guidelines](CONTRIBUTING.md) for setup instructions and coding standards.

**Contributing to Platform-Specific Versions:**
- **Windows**: [Contribute to Windows version](https://github.com/DockerDiscordControl/DockerDiscordControl-Windows)
- **Linux**: [Contribute to Linux version](https://github.com/DockerDiscordControl/DockerDiscordControl-Linux)
- **macOS**: This repository!

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 **Show Your Support**

If DockerDiscordControl helps you manage your Mac containers, please consider supporting the project:

<div align="center">

### **💖 Support DDC Development**

[![⭐ Star on GitHub](https://img.shields.io/badge/⭐_Star_on_GitHub-Show_Support-brightgreen?style=for-the-badge&logo=github)](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac)

[![☕ Buy Me A Coffee](https://img.shields.io/badge/☕_Buy_Me_A_Coffee-orange?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/dockerdiscordcontrol)
&nbsp;&nbsp;
[![💝 PayPal Donation](https://img.shields.io/badge/💝_PayPal_Donation-blue?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/dockerdiscordcontrol)

**Your support helps maintain DDC across all platforms and develop new features!**

</div>

---

**🍎 Built with ❤️ for macOS Docker Desktop users**

**🚀 Perfect for Mac desktops, home labs, and development environments!**

**⭐ Star this repo if DockerDiscordControl helps you manage your Mac containers!**

**Like DDC? Star the repository!** | **Found a bug?** [Report it](../../issues) | **Feature idea?** [Suggest it](../../discussions)

**Don't forget to star the other platform repos too!**
- **[Windows](https://github.com/DockerDiscordControl/DockerDiscordControl-Windows)**
- **[Linux](https://github.com/DockerDiscordControl/DockerDiscordControl-Linux)**
- **[Universal/Unraid](https://github.com/DockerDiscordControl/DockerDiscordControl)**

---

## Credits & Contributors

**DockerDiscordControl** is developed and maintained by:
- **Lead Developer**: MAX
- **Contributors**: Community contributions welcome via [Pull Requests](../../pulls)
- **Special Thanks**: All users who report bugs, suggest features, and support the project

**Built for macOS - optimized for your Mac environment!**
