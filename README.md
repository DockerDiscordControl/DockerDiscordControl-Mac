# DockerDiscordControl (DDC)

**Homepage:** [https://ddc.bot](https://ddc.bot) | **📖 [Complete Documentation](../../wiki)**

Control your Docker containers directly from Discord! This application provides a Discord bot and a web interface to manage Docker containers (start, stop, restart, view status) with ultra-fast performance optimizations.

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/DockerDiscordControl/DockerDiscordControl)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/DockerDiscordControl/DockerDiscordControl/blob/main/LICENSE)
[![Wiki](https://img.shields.io/badge/documentation-wiki-blue.svg)](../../wiki)

## ✨ Features

- **🤖 Discord Bot**: Slash commands, status monitoring, container controls with 90% performance improvement
- **🌐 Web Interface**: Secure configuration, permissions, logs, and performance monitoring  
- **⚡ Ultra-Fast Performance**: Revolutionary optimizations with intelligent caching and batch processing
- **📅 Task System**: Schedule automated container actions (daily, weekly, monthly, one-time)
- **🛡️ Security**: Channel-based permissions, rate limiting, comprehensive security framework
- **🌍 Multi-Language**: English, German, French support

**New in v3.0:** Revolutionary performance optimizations, complete security vulnerability remediation, 36% code reduction, 100% English documentation.

## 🚀 Quick Start

### Prerequisites

1. **Create Discord Bot**: [📖 Bot Setup Guide](../../wiki/Discord‐Bot‐Setup)
2. **Docker**: [Install Docker](https://docs.docker.com/engine/install/) + [Docker Compose](https://docs.docker.com/compose/install/)

### Installation

**Method 1: Docker Compose (Recommended)**

```bash
# Clone repository
git clone https://github.com/DockerDiscordControl/DockerDiscordControl.git
cd DockerDiscordControl

# Create directories
mkdir config logs

# Create .env file with secure secret key
echo "FLASK_SECRET_KEY=$(openssl rand -hex 32)" > .env

# Start container
docker compose up --build -d
```

**Method 2: Unraid**
- Install via Community Applications
- Search for "DockerDiscordControl"
- [📖 Detailed Unraid Setup](../../wiki/Installation‐Guide#unraid)

### Configuration

1. **Access Web UI**: `http://<your-server-ip>:8374`
2. **Login**: Username `admin`, Password `admin` (change immediately!)
3. **Configure**: Bot token, Guild ID, container permissions
4. **Restart**: `docker compose restart` after initial setup

## 📚 Documentation

| Topic | Description |
|-------|-------------|
| [📖 Installation Guide](../../wiki/Installation‐Guide) | Detailed setup for all platforms |
| [⚙️ Configuration](../../wiki/Configuration) | Web UI, permissions, channels |
| [📅 Task System](../../wiki/Task‐System) | Automated scheduling system |
| [🚀 Performance](../../wiki/Performance‐and‐Architecture) | V3.0 optimizations & monitoring |
| [🔧 Troubleshooting](../../wiki/Troubleshooting) | Common issues & solutions |
| [👩‍💻 Development](../../wiki/Development) | Contributing & development setup |
| [🔒 Security](../../wiki/Security) | Best practices & considerations |

## ⚠️ Security Notice

**Docker Socket Access Required**: This application requires access to `/var/run/docker.sock` to control containers. Only run in trusted environments and ensure proper host security.

**Default Credentials**: Change the default admin password immediately after first login!

## 🆘 Quick Help

**Common Issues:**
- **Permission Errors**: Run `docker exec ddc /app/scripts/fix_permissions.sh`
- **Configuration Not Saving**: Check file permissions in logs
- **Bot Not Responding**: Verify token and Guild ID in Web UI

**Need Help?** Check our [📖 Troubleshooting Guide](../../wiki/Troubleshooting) or create an issue.

## 🤝 Contributing

We welcome contributions! See our [📖 Development Guide](../../wiki/Development) for setup instructions and coding standards.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**⭐ Like DDC? Star the repository!** | **🐛 Found a bug?** [Report it](../../issues) | **💡 Feature idea?** [Suggest it](../../discussions) 