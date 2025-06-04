# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with DockerDiscordControl.

## Common Issues and Solutions

### 1. Configuration Changes Not Saving

**Symptoms:**
- Changes made in the Web UI are not saved
- Container permissions always show as empty `[]`
- Error messages about file permissions
- Configuration reverts after browser refresh

**Cause:** 
File permission issues preventing the application from writing to configuration files.

**Solutions:**

**Method 1: Automatic Fix (Recommended)**
```bash
docker exec ddc /app/scripts/fix_permissions.sh
```

**Method 2: Manual Fix on Host**
```bash
# Navigate to your DDC config directory
cd /mnt/user/appdata/dockerdiscordcontrol/config  # Unraid
cd /path/to/dockerdiscordcontrol/config          # Other systems

# Fix permissions
chmod 644 *.json
chown nobody:users *.json  # Unraid specific
```

**Method 3: Fix from Container**
```bash
docker exec ddc chmod 644 /app/config/*.json
```

**Verification:**
```bash
# Check if permissions are correct
ls -la /path/to/config/*.json

# Should show something like:
# -rw-r--r-- 1 nobody users  324 Jun  4 19:46 bot_config.json
```

### 2. Discord Bot Not Responding

**Symptoms:**
- Bot appears online but doesn't respond to commands
- Slash commands don't appear in Discord
- Bot doesn't post status messages

**Diagnostic Steps:**

**Check Basic Configuration:**
1. **Verify Bot Token**
   - Check if token is correct in Web UI
   - Ensure token wasn't regenerated in Discord Developer Portal
   - Look for authentication errors in logs

2. **Verify Guild ID**
   - Confirm server ID matches your Discord server
   - Enable Developer Mode in Discord to copy correct ID

3. **Check Bot Permissions**
   - Ensure bot has required Discord permissions
   - Verify bot role position in server hierarchy
   - Check channel-specific permission overrides

**Check DDC Configuration:**
```bash
# Check logs for errors
docker logs ddc | grep -i "error\|guild\|token"

# Check if bot is connecting
docker logs ddc | grep -i "ready\|logged in"
```

**Common Error Messages:**
- `Incorrect token`: Bot token is invalid or regenerated
- `Guild not found`: Guild ID is incorrect
- `Missing permissions`: Bot lacks Discord permissions
- `Rate limited`: Too many API requests (temporary)

### 3. Container Actions Not Working

**Symptoms:**
- Start/Stop/Restart buttons don't work
- Commands execute but containers don't change state
- "Permission denied" errors

**Solutions:**

**Check Docker Socket Access:**
```bash
# Verify socket is mounted correctly
docker exec ddc ls -la /var/run/docker.sock

# Should show socket file with proper permissions
```

**Verify Container Configuration:**
1. **Check Allowed Actions**
   - In Web UI, verify container has required permissions
   - Ensure `allowed_actions` includes the action you're trying

2. **Check Container Selection**
   - Verify container is marked as "Active" in Web UI
   - Ensure container name matches exactly

**Test Docker Access:**
```bash
# Test if DDC can see containers
docker exec ddc docker ps

# Should list all containers
```

### 4. Permission Errors on Different Systems

**Unraid Systems:**
```bash
# Correct ownership for Unraid
chown nobody:users /mnt/user/appdata/dockerdiscordcontrol/config/*.json
chmod 644 /mnt/user/appdata/dockerdiscordcontrol/config/*.json
```

**Synology Systems:**
```bash
# Check current ownership
ls -la /volume1/docker/dockerdiscordcontrol/config/

# Adjust ownership (user/group may vary)
chown admin:users /volume1/docker/dockerdiscordcontrol/config/*.json
chmod 644 /volume1/docker/dockerdiscordcontrol/config/*.json
```

**Standard Linux:**
```bash
# Common ownership patterns
chown 1000:1000 /path/to/dockerdiscordcontrol/config/*.json  # User ID 1000
chown root:root /path/to/dockerdiscordcontrol/config/*.json   # Root
```

### 5. Slash Commands Not Appearing

**Symptoms:**
- `/serverstatus`, `/command`, etc. don't show in Discord
- Commands were working before but disappeared

**Solutions:**

**Wait for Discord Registration:**
- Slash commands can take up to 1 hour to register globally
- Server-specific commands update faster (usually minutes)

**Check Bot Permissions:**
- Verify bot has "Use Slash Commands" permission
- Ensure bot wasn't removed and re-added (resets permissions)

**Force Command Refresh:**
```bash
# Restart container to re-register commands
docker restart ddc

# Check logs for command registration
docker logs ddc | grep -i "command\|slash"
```

### 6. Web UI Authentication Issues

**Symptoms:**
- Cannot log into Web UI
- "Invalid credentials" errors
- Password not working

**Solutions:**

**Reset to Default Password:**
1. Stop container: `docker stop ddc`
2. Edit `config/web_config.json`
3. Reset password hash to default or delete the file
4. Start container: `docker start ddc`
5. Login with `admin`/`admin`

**Check Password Hash:**
```bash
# View current web config
cat config/web_config.json

# Should contain valid password hash
```

### 7. Performance Issues

**Symptoms:**
- Slow response times
- High CPU/memory usage
- Timeouts in Discord

**Optimization Steps:**

**Adjust Cache Settings:**
```bash
# In .env file or environment variables
DDC_DOCKER_CACHE_DURATION=150     # Increase cache time
DDC_BACKGROUND_REFRESH_INTERVAL=60 # Reduce refresh frequency
```

**Monitor Resources:**
```bash
# Check container resource usage
docker stats ddc

# Check system resources
htop  # or top
```

**Enable Performance Monitoring:**
1. Access Web UI
2. Enable "Scheduler Debug Mode"
3. Monitor logs for performance metrics

### 8. Container Status Not Updating

**Symptoms:**
- Status shows old information
- CPU/RAM/Uptime not updating
- "Pending" status stuck

**Solutions:**

**Check Cache Settings:**
- Verify cache duration isn't too high
- Check if background refresh is working

**Manual Refresh:**
```bash
# Restart container to clear cache
docker restart ddc

# Check refresh logs
docker logs ddc | grep -i "refresh\|cache"
```

**Verify Container Access:**
```bash
# Test if DDC can access container stats
docker exec ddc docker stats --no-stream
```

### 9. Task Scheduler Issues

**Symptoms:**
- Scheduled tasks not executing
- Tasks show as "inactive"
- Timing issues with schedules

**Solutions:**

**Check Container Permissions:**
- Verify target container has required action permissions
- Ensure container is marked as "Active"

**Check Channel Permissions:**
- Verify channel has "task" permissions enabled
- Tasks respect channel permission restrictions

**Debug Task Execution:**
1. Enable "Scheduler Debug Mode" in Web UI
2. Monitor logs during task execution time
3. Check for error messages in logs

**Verify System Time:**
```bash
# Check system timezone
docker exec ddc date
docker exec ddc cat /etc/timezone

# Should match your configured timezone
```

## Diagnostic Commands

### Log Analysis

**View Recent Logs:**
```bash
# Last 100 lines
docker logs ddc --tail 100

# Follow logs in real-time
docker logs ddc -f

# Filter for errors
docker logs ddc | grep -i "error\|exception\|failed"
```

**Check Specific Components:**
```bash
# Bot connection issues
docker logs ddc | grep -i "discord\|bot\|guild"

# Configuration issues  
docker logs ddc | grep -i "config\|permission\|save"

# Task scheduler issues
docker logs ddc | grep -i "task\|schedule\|cron"
```

### System Information

**Container Health:**
```bash
# Check if container is running
docker ps | grep ddc

# Check container resources
docker stats ddc --no-stream

# Check container inspect
docker inspect ddc
```

**File System Check:**
```bash
# Check config file permissions
docker exec ddc ls -la /app/config/

# Check if files are readable
docker exec ddc cat /app/config/bot_config.json

# Check available disk space
docker exec ddc df -h
```

### Network Connectivity

**Test Discord API Access:**
```bash
# Test from container
docker exec ddc ping discord.com

# Test HTTPS connectivity
docker exec ddc wget -q --spider https://discord.com/api/v10/gateway
echo $?  # Should return 0 for success
```

**Test Local Network:**
```bash
# Test if web UI port is accessible
curl -I http://localhost:8374

# Check if port is listening
netstat -tlnp | grep 8374
```

## Debug Mode

Enable debug logging for detailed troubleshooting:

### Temporary Debug Mode

1. **Access Web UI**: `http://your-server:8374`
2. **Enable Temporary Debug**: Select duration (5-60 minutes)
3. **Monitor Logs**: Watch detailed debug output
4. **Auto-Disable**: Debug mode automatically turns off after timeout

### Permanent Debug Mode

1. **Access Web UI**: Navigate to configuration
2. **Enable Scheduler Debug Mode**: Check the box
3. **Save Configuration**: Changes persist until manually disabled

### Debug Information

**Debug logs include:**
- Detailed Discord API interactions
- Container operation step-by-step
- Configuration loading and validation
- Task scheduling and execution details
- Performance metrics and bottlenecks

## Getting Help

### Before Asking for Help

1. **Check Logs**: Review recent error messages
2. **Try Basic Solutions**: Restart container, check permissions
3. **Search Documentation**: Review relevant wiki pages
4. **Test Isolation**: Try with minimal configuration

### Information to Include

When reporting issues, include:

1. **System Information:**
   - Platform (Unraid, Synology, Linux distro)
   - Docker version
   - DDC version/commit hash

2. **Configuration:**
   - Number of containers managed
   - Channel setup (without sensitive tokens)
   - Environment variables used

3. **Error Details:**
   - Exact error messages
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant log excerpts (remove tokens!)

4. **Diagnostic Output:**
   ```bash
   # Include output of these commands
   docker logs ddc --tail 50
   docker exec ddc ls -la /app/config/
   docker ps | grep ddc
   ```

### Support Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Wiki**: Comprehensive documentation and guides

## Emergency Recovery

### Complete Reset

If DDC is completely broken:

1. **Stop Container:**
   ```bash
   docker stop ddc
   ```

2. **Backup Configuration:**
   ```bash
   cp -r config config.backup
   ```

3. **Reset Configuration:**
   ```bash
   rm config/*.json  # Remove all config files
   ```

4. **Start Fresh:**
   ```bash
   docker start ddc
   # Reconfigure through Web UI
   ```

### Rollback Container

If update caused issues:

```bash
# Stop current container
docker stop ddc && docker rm ddc

# Pull previous version (if available)
docker pull ghcr.io/dockerdiscordcontrol/dockerdiscordcontrol:previous-tag

# Start with previous version
docker run ... # Use your original run command
```

This troubleshooting guide covers the most common issues. For additional help, check the other wiki pages or create an issue on GitHub. 