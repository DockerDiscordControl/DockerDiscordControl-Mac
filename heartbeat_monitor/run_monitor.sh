#!/bin/bash

# DDC Heartbeat Monitor Launcher Script
# For macOS and Linux

set -e

echo "========================================"
echo "   DDC Heartbeat Monitor"
echo "========================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    echo "❌ ERROR: Python 3 is not installed"
    echo "📦 Please install Python 3:"
    echo "   - macOS: brew install python"
    echo "   - Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "   - CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.7"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
    echo "❌ ERROR: Python 3.7+ is required (found: $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Check if pip is available
if ! command_exists pip3; then
    echo "❌ ERROR: pip3 is not installed"
    echo "📦 Please install pip3 for your system"
    exit 1
fi

# Check if discord.py is installed
if ! python3 -c "import discord" >/dev/null 2>&1; then
    echo "📦 Installing discord.py..."
    pip3 install discord.py
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Failed to install discord.py"
        exit 1
    fi
    echo "✅ discord.py installed successfully"
else
    echo "✅ discord.py is already installed"
fi

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo "⚠️  WARNING: config.json not found!"
    echo "📝 Please copy config.json.example to config.json and edit it:"
    echo "   cp config.json.example config.json"
    echo "   nano config.json  # or your preferred editor"
    exit 1
fi

echo "✅ Configuration file found"
echo
echo "🚀 Starting DDC Heartbeat Monitor..."
echo "🛑 Press Ctrl+C to stop the monitor"
echo

# Run the monitor
python3 ddc_heartbeat_monitor.py

echo
echo "👋 Monitor stopped." 