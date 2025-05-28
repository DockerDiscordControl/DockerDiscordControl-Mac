# DDC Heartbeat Monitor

A standalone application to monitor DockerDiscordControl (DDC) bot heartbeats and send alerts when the bot becomes unresponsive.

## 🌟 Features

- **Cross-platform**: Works on Windows, macOS, and Linux
- **JSON Configuration**: Easy-to-edit configuration file
- **Automatic Recovery Detection**: Notifies when heartbeat is restored
- **Comprehensive Logging**: File and console logging with configurable levels
- **Graceful Shutdown**: Proper cleanup on exit
- **Role Mentions**: Optional role pinging for critical alerts
- **Multiple Alert Channels**: Send alerts to multiple Discord channels

## 📋 Requirements

- Python 3.7 or higher
- discord.py library
- A separate Discord bot token (different from your DDC bot)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the heartbeat monitor files
# Navigate to the heartbeat_monitor directory

# Install required dependencies
pip install discord.py
```

### 2. Configuration

1. Copy `config.json.example` to `config.json`
2. Edit `config.json` with your settings:

```json
{
  "monitor": {
    "bot_token": "YOUR_MONITOR_BOT_TOKEN_HERE",
    "ddc_bot_user_id": 123456789012345678,
    "heartbeat_channel_id": 123456789012345678,
    "alert_channel_ids": [123456789012345678],
    "heartbeat_timeout_seconds": 300,
    "check_interval_seconds": 30
  }
}
```

### 3. Setup Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application for the monitor bot
3. Create a bot user and copy the token
4. Invite the bot to your server with permissions:
   - Send Messages
   - Use External Emojis
   - Read Message History

### 4. Run the Monitor

```bash
python ddc_heartbeat_monitor.py
```

## ⚙️ Configuration Reference

### Monitor Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `bot_token` | string | Discord bot token for the monitor bot | Required |
| `ddc_bot_user_id` | integer | User ID of your DDC bot | Required |
| `heartbeat_channel_id` | integer | Channel ID where DDC sends heartbeats | Required |
| `alert_channel_ids` | array | Channel IDs where alerts will be sent | Required |
| `heartbeat_timeout_seconds` | integer | Seconds before considering heartbeat missing | 300 |
| `check_interval_seconds` | integer | How often to check for heartbeats | 30 |

### Logging Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `level` | string | Log level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `file_enabled` | boolean | Enable logging to file | true |
| `file_name` | string | Log file name | ddc_heartbeat_monitor.log |
| `console_enabled` | boolean | Enable console logging | true |

### Alert Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `startup_notification` | boolean | Send notification when monitor starts | true |
| `recovery_notification` | boolean | Send notification when heartbeat recovers | true |
| `include_timestamp` | boolean | Include timestamp in alert embeds | true |
| `mention_roles` | array | Role IDs to mention in alerts | [] |

## 🔧 Platform-Specific Setup

### Windows

1. Install Python from [python.org](https://python.org)
2. Open Command Prompt or PowerShell
3. Run the installation and setup commands above

**Running as a Service:**
```batch
# Create a batch file (run_monitor.bat)
@echo off
cd /d "C:\path\to\heartbeat_monitor"
python ddc_heartbeat_monitor.py
pause
```

### macOS

1. Python is usually pre-installed, or install via Homebrew:
   ```bash
   brew install python
   ```
2. Follow the standard setup instructions

**Running as a Service:**
```bash
# Create a launch agent (optional)
# See: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
```

### Linux

1. Install Python via package manager:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install python3 python3-pip
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip
   
   # Arch Linux
   sudo pacman -S python python-pip
   ```

2. Follow the standard setup instructions

**Running as a Service (systemd):**

Create `/etc/systemd/system/ddc-heartbeat-monitor.service`:

```ini
[Unit]
Description=DDC Heartbeat Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/heartbeat_monitor
ExecStart=/usr/bin/python3 ddc_heartbeat_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ddc-heartbeat-monitor
sudo systemctl start ddc-heartbeat-monitor
sudo systemctl status ddc-heartbeat-monitor
```

## 📊 Monitoring and Logs

### Log Files

The monitor creates detailed logs in `ddc_heartbeat_monitor.log` (configurable):

```
2024-01-15 10:30:00,123 - ddc_monitor - INFO - 🤖 DDC Heartbeat Monitor v1.0.0 started
2024-01-15 10:30:01,456 - ddc_monitor - INFO - 👤 Logged in as MonitorBot#1234 (ID: 123456789)
2024-01-15 10:30:01,789 - ddc_monitor - INFO - 🎯 Monitoring DDC bot ID: 987654321
2024-01-15 10:35:00,123 - ddc_monitor - DEBUG - 💓 Heartbeat detected at 2024-01-15T10:35:00+00:00
```

### Alert Types

1. **Startup Notification** (Blue): Monitor has started
2. **Missing Heartbeat** (Red): DDC bot heartbeat is missing
3. **Heartbeat Recovered** (Green): DDC bot heartbeat restored
4. **Shutdown Notification** (Orange): Monitor is stopping

## 🔍 Troubleshooting

### Common Issues

**"Bot token is invalid"**
- Verify the bot token in `config.json`
- Ensure the bot is properly created in Discord Developer Portal

**"Channel not found"**
- Check channel IDs are correct (right-click channel → Copy ID)
- Ensure the monitor bot has access to the channels

**"No heartbeat detected"**
- Verify DDC bot is sending heartbeats to the correct channel
- Check DDC heartbeat configuration
- Ensure heartbeat feature is enabled in DDC

**"Permission denied"**
- Monitor bot needs "Send Messages" permission in alert channels
- Monitor bot needs "Read Message History" in heartbeat channel

### Debug Mode

Enable debug logging by changing the log level:

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

This will show detailed information about heartbeat detection and processing.

## 🔄 Integration with DDC

### DDC Configuration

In your DDC web interface, configure the heartbeat settings:

1. **Heartbeat Channel ID**: Channel where DDC sends heartbeats
2. **Monitor Bot Token**: Token for this monitor application
3. **DDC Bot User ID**: Your DDC bot's user ID
4. **Alert Channels**: Where you want to receive alerts

### Heartbeat Message Format

The monitor detects heartbeat messages containing:
- ❤️ (heart emoji)
- 💓 (beating heart emoji)
- "heartbeat" (text)
- "alive" (text)
- "ping" (text)

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Support

For support and questions:
- DDC Documentation: https://ddc.bot
- GitHub Issues: [Create an issue](https://github.com/DockerDiscordControl/DockerDiscordControl/issues)
- Discord Community: [Join our Discord](https://discord.gg/your-invite)

## 🔄 Updates

To update the monitor:
1. Download the latest version
2. Stop the current monitor
3. Replace the files (keep your `config.json`)
4. Restart the monitor

---

**Made with ❤️ by MAX for the DDC community** 