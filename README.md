# DockerDiscordControl for macOS 🍎

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

[![Version](https://img.shields.io/badge/version-v1.1.2-blue.svg)](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/DockerDiscordControl/DockerDiscordControl-Mac/blob/main/LICENSE)
[![macOS Optimized](https://img.shields.io/badge/macOS-Docker_Desktop-blue.svg)](#performance-metrics)
[![Apple Silicon](https://img.shields.io/badge/Apple_Silicon-M1_M2_M3-orange.svg)](#installation)
[![Memory Optimized](https://img.shields.io/badge/RAM-~98MB-green.svg)](#performance-metrics)

## 🚀 Revolutionary macOS Performance

**Major Mac-Specific Optimizations Delivered:**

- **Docker Desktop Integration**: Native macOS Docker Desktop support with 98MB typical RAM usage
- **Universal Binary Support**: Optimized for both Apple Silicon (M1/M2/M3) and Intel Macs
- **macOS Native Features**: Homebrew integration and native macOS management
- **Resource Efficiency**: Tuned specifically for macOS resource management patterns
- **Alpine Optimization**: Ultra-lightweight Alpine Linux base for maximum efficiency

## 🐳 Docker Hub Repository

**Mac-Optimized Image:** \`dockerdiscordcontrol/dockerdiscordcontrol-mac\`

This repository publishes **only** the Mac-optimized Alpine-based image, specifically tuned for:
- Apple Silicon (M1/M2/M3) and Intel Mac compatibility
- macOS Docker Desktop integration
- Optimal resource usage on macOS systems
- Native macOS Docker socket handling

**Other Platform Images:**
- **Universal/Unraid**: \`dockerdiscordcontrol/dockerdiscordcontrol\`
- **Windows**: \`dockerdiscordcontrol/dockerdiscordcontrol-windows\`  
- **Linux**: \`dockerdiscordcontrol/dockerdiscordcontrol-linux\`

## 🛠️ Quick Installation

### **Docker Hub Installation (Recommended)**
\`\`\`bash
# Pull the Mac-optimized image
docker pull dockerdiscordcontrol/dockerdiscordcontrol-mac:latest

# Run with docker compose
docker compose up -d

# Or run directly
docker run -d --name ddc \\
  -p 8374:8374 \\
  -v /var/run/docker.sock:/var/run/docker.sock \\
  -v ./config:/app/config \\
  -v ./logs:/app/logs \\
  dockerdiscordcontrol/dockerdiscordcontrol-mac:latest
\`\`\`

## 🔧 Configuration

1. **Access the Web Interface**: \`http://localhost:8374\`
2. **Default Login**: \`admin\` / \`admin\` (change immediately!)
3. **Configure Discord Bot**: Add your bot token and guild ID
4. **Set Docker Settings**: Configure container refresh intervals
5. **Channel Permissions**: Set up Discord channel access controls

## 🆕 Latest Updates (v1.1.2)

### **✅ Critical ConfigManager Stability Fixes**
- **Fixed ConfigManager**: Resolved missing attributes and cache invalidation issues
- **Eliminated CPU spikes**: Fixed restart loops that caused high CPU usage
- **Enhanced error handling**: Improved subscriber notification system
- **System stability**: Eliminated config cache reload loops

### **✅ macOS Docker Desktop Optimizations**
- **Native Apple Silicon support**: Full M1/M2/M3 chip optimization
- **Resource optimization**: ~98MB RAM usage with minimal CPU impact
- **Health monitoring**: Added \`/health\` endpoint for proper Docker health checks  
- **Alpine efficiency**: Ultra-lightweight Alpine Linux base for maximum performance

**🎉 Ready for production deployment on any macOS Docker Desktop environment!**

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
