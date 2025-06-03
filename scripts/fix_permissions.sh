#!/bin/bash
# DDC Permission Fix Script
# This script fixes common permission issues with configuration files

echo "Docker Discord Control - Permission Fix Script"
echo "============================================="

# Detect if we're running inside Docker
if [ -f /.dockerenv ]; then
    echo "Running inside Docker container..."
    CONFIG_DIR="/app/config"
else
    echo "Running on host system..."
    # Try to find the config directory
    if [ -d "/mnt/user/appdata/dockerdiscordcontrol/config" ]; then
        CONFIG_DIR="/mnt/user/appdata/dockerdiscordcontrol/config"
    elif [ -d "/volume1/docker/dockerdiscordcontrol/config" ]; then
        CONFIG_DIR="/volume1/docker/dockerdiscordcontrol/config"
    elif [ -d "./config" ]; then
        CONFIG_DIR="./config"
    else
        echo "ERROR: Could not find config directory!"
        echo "Please run this script from the DDC directory or specify the path."
        exit 1
    fi
fi

echo "Config directory: $CONFIG_DIR"
echo ""

# Check current permissions
echo "Current permissions:"
ls -la "$CONFIG_DIR"/*.json 2>/dev/null || echo "No JSON files found in $CONFIG_DIR"
echo ""

# Fix permissions
echo "Fixing permissions..."
if [ -f /.dockerenv ]; then
    # Inside Docker - simple chmod
    chmod 644 "$CONFIG_DIR"/*.json 2>/dev/null
    echo "✓ Set permissions to 644 for all JSON files"
else
    # On host - need to determine correct user
    if [ -f /etc/unraid-version ]; then
        # Unraid system
        echo "Detected Unraid system"
        chmod 644 "$CONFIG_DIR"/*.json
        chown nobody:users "$CONFIG_DIR"/*.json
        echo "✓ Set ownership to nobody:users"
    elif command -v synopkg >/dev/null 2>&1; then
        # Synology system
        echo "Detected Synology system"
        chmod 644 "$CONFIG_DIR"/*.json
        # Synology typically uses specific UIDs
        echo "✓ Set permissions to 644"
        echo "Note: You may need to adjust ownership manually for your Synology setup"
    else
        # Generic Linux
        echo "Generic Linux system"
        chmod 644 "$CONFIG_DIR"/*.json
        
        # Try to detect Docker user
        if [ -n "$PUID" ] && [ -n "$PGID" ]; then
            chown "$PUID:$PGID" "$CONFIG_DIR"/*.json
            echo "✓ Set ownership to $PUID:$PGID (from environment)"
        else
            echo "✓ Set permissions to 644"
            echo "Note: You may need to adjust ownership manually (e.g., chown 1000:1000)"
        fi
    fi
fi

echo ""
echo "Updated permissions:"
ls -la "$CONFIG_DIR"/*.json 2>/dev/null
echo ""
echo "Permission fix complete!"
echo ""
echo "If you still have issues, please ensure:"
echo "1. The Docker container has the correct user mapping"
echo "2. The config directory is properly mounted"
echo "3. SELinux/AppArmor are not blocking access" 