# Changelog - DockerDiscordControl for macOS

All notable changes to the macOS version of DockerDiscordControl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-11-19

### 🎉 MAJOR UPDATE - Complete Rewrite

This is a complete synchronization with the main DockerDiscordControl v2.0 release, bringing all new features and improvements to macOS.

### ✨ Added

#### Discord-First Control
- **Live Logs Viewer** - Monitor container output in real-time directly in Discord
- **Task System** - Create, view, delete tasks (Once, Daily, Weekly, Monthly, Yearly) entirely in Discord
- **Container Info System** - Attach custom info and password-protected info to containers
- **Public IP Display** - Automatic WAN IP detection with custom port support
- **Full Container Management** - Start, stop, restart, bulk operations without leaving Discord

#### Multi-Language Support
- **Full Discord UI Translation** in German, French, and English
- **Dynamic Language Switching** via Web UI settings
- **100% Translation Coverage** across entire bot interface

#### Mech Evolution System
- **11-Stage Mech Evolution** with animated WebP graphics
- **Continuous Power Decay System** for fair donation tracking
- **Premium Key System** for power users
- **Visual Feedback** with stage-specific animations and particle effects

#### New Architecture Components
- **New Cogs**: `admin_overview.py`, `enhanced_info_modal_simple.py`, `status_info_integration.py`
- **Services Directory**: Modular service-oriented architecture
- **Encrypted Assets**: Secure storage for sensitive data
- **Cached Animations**: Pre-rendered mech evolution animations
- **Cached Displays**: Pre-rendered status displays
- **Tools Directory**: Development and maintenance utilities

### ⚡ Performance Improvements
- **16x Faster Docker Status Cache** - Optimized from 500ms to 31ms
- **7x Faster Container Processing** - Through async optimization
- **Smart Queue System** with fair request processing
- **Intelligent Caching** with background refresh

### 🔒 Security Enhancements
- **Alpine Linux 3.22.2** - 94% fewer vulnerabilities
- **Multi-Stage Docker Build** - Ultra-compact image (<200MB RAM)
- **Production-Ready Security Hardening**
- **Enhanced Token Encryption and Validation**

### 🍎 macOS-Specific Optimizations
- **Native Docker Desktop Integration** - Optimized socket handling
- **Universal Binary Support** - Full M1/M2/M3/M4 and Intel compatibility
- **Resource Efficiency** - <200MB RAM usage
- **Multi-Stage Dockerfile** - 78% size reduction

### 🎨 UI/UX Improvements
- **Beautiful Discord Embeds** with consistent styling
- **Advanced Spam Protection** with configurable cooldowns
- **Enhanced Container Information System**
- **Real-Time Monitoring** and status updates

### 🔧 Configuration Changes
- **New Environment Variables** for performance optimization
- **First-Time Setup** with temporary 'setup' password
- **Multiple Setup Methods** - Web setup, credentials, or env variable

### 🐛 Bug Fixes
- **Port Mapping Consistency** - Standardized on port 9374
- **Interaction Timeout Issues** - Fixed with defer() pattern
- **Container Control Reliability** - Improved through async optimization

### 🔄 Changed
- **Bot Entry Point** - Refactored to 157 lines (was 608)
- **Dockerfile** - Complete rewrite with multi-stage build
- **Requirements** - Added `Pillow>=10.2.0` for mech animations
- **User** - Changed from `ddcuser` to `ddc`

### 🗑️ Removed
- **Heartbeat Monitor** - Replaced with integrated health checks
- **Old Dockerfiles** - Consolidated into single optimized Dockerfile
- **Legacy Code** - Removed in favor of modular architecture

---

## v1.1.2-alpine (2025-01-26)

### 🐛 Bug Fixes
- **ConfigManager Critical Fixes**: Fixed missing attributes `_last_cache_invalidation` and `_min_invalidation_interval` in ConfigManager initialization
- **Configuration Save Errors**: Fixed `'ConfigManager' object has no attribute '_notify_subscribers'` error that prevented configuration saves
- **Cache Invalidation**: Resolved cache invalidation failures that caused repeated config reloads and system instability
- **Observer Pattern**: Added proper subscriber management with `add_subscriber()` and `remove_subscriber()` methods

### 🔧 Technical Improvements
- **Anti-Thrashing**: Implemented minimum 1-second interval between cache invalidations to prevent thrashing
- **Error Handling**: Enhanced error handling in subscriber notifications with individual exception catching
- **System Stability**: Eliminated config cache reload loops that caused excessive log spam
- **Code Quality**: Added comprehensive method documentation and proper initialization of all ConfigManager attributes

### 📋 Notes
- This release focuses on critical stability fixes for the configuration management system
- No breaking changes - fully backward compatible
- Resolves runtime errors that were affecting system reliability

---

## v1.1.1-alpine (2025-01-25)

### 🚀 **Major Performance & Security Update**

**Ultra-Optimized Alpine Linux Image:**
- ✅ **84% size reduction:** From 924MB to 150MB
- ✅ **Alpine Linux 3.22.1:** Latest secure base image
- ✅ **Security fixes:** Flask 3.1.1 & Werkzeug 3.1.3 (all CVEs resolved)
- ✅ **Improved startup time:** Faster container initialization
- ✅ **Reduced memory footprint:** Optimized for resource-constrained environments

**Technical Improvements:**
- ✅ **Docker Socket permissions:** Fixed for proper container management
- ✅ **Configuration persistence:** Resolved volume mount issues
- ✅ **Logging enhancement:** Full application logs visible in `docker logs`
- ✅ **Non-root execution:** Enhanced security with proper user permissions

**Compatibility:**
- ✅ **Full backward compatibility:** All existing features preserved
- ✅ **Unraid optimized:** Perfect integration with Unraid systems
- ✅ **Multi-architecture:** Supports AMD64 and ARM64

--- 