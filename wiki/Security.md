# Security Guide

This guide covers security best practices and considerations for DockerDiscordControl.

## ⚠️ Important Security Notice

**Docker Socket Access**: DDC requires access to `/var/run/docker.sock` to control containers. This grants the application extensive control over your Docker environment and represents a significant security risk if the application or container is compromised.

**Only run DDC in trusted environments** and ensure your host system is properly secured.

## Core Security Principles

### 1. Principle of Least Privilege

**Container Permissions:**
- Only grant necessary permissions to each container
- Use granular permissions (status, start, stop, restart) based on need
- Regularly audit and remove unused permissions

**Channel Permissions:**
- Restrict bot commands to appropriate channels
- Use read-only status channels for public monitoring
- Limit administrative commands to private channels

**Discord Permissions:**
- Grant minimal required Discord permissions to the bot
- Avoid "Administrator" permission unless absolutely necessary
- Use role-based access control in Discord

### 2. Defense in Depth

**Multiple Security Layers:**
- Web UI authentication (strong passwords)
- Discord channel permissions
- Container-specific permissions
- Network-level restrictions
- Host system security

### 3. Regular Security Maintenance

**Keep Systems Updated:**
- Update DDC regularly for security patches
- Keep Docker and host OS updated
- Monitor security advisories

**Audit and Monitor:**
- Review action logs regularly
- Monitor for unusual activity
- Audit user permissions periodically

## Authentication and Access Control

### Web UI Security

**Strong Authentication:**
```bash
# Use strong, unique passwords
DDC_ADMIN_PASSWORD=ComplexPassword123!@#

# Change default password immediately after installation
```

**Password Best Practices:**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Unique password not used elsewhere
- Change passwords regularly
- Consider using a password manager

**Access Restrictions:**
- Limit web UI access to trusted networks
- Consider using VPN for remote access
- Implement firewall rules for port 8374

### Discord Bot Security

**Token Security:**
```bash
# Store bot token securely
FLASK_SECRET_KEY=secure_32_byte_hex_key
# Never share or commit tokens to version control
```

**Bot Token Management:**
- Regenerate tokens if potentially compromised
- Use environment variables for token storage
- Never log or display tokens in plaintext
- Restrict access to configuration files

**Permission Management:**
- Use Discord roles for access control
- Implement channel-specific permissions
- Regular permission audits
- Monitor bot activity logs

## Network Security

### Port Management

**Web UI Port (8374):**
```yaml
# Option 1: Change default port
ports:
  - "9000:8374"

# Option 2: Bind to localhost only
ports:
  - "127.0.0.1:8374:8374"
```

**Firewall Configuration:**
```bash
# Allow only specific IPs (example)
iptables -A INPUT -p tcp --dport 8374 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8374 -j DROP
```

### Reverse Proxy Security

**Use HTTPS with reverse proxy:**
```nginx
# Nginx example
server {
    listen 443 ssl;
    server_name ddc.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8374;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Additional Security Headers:**
```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000";
```

## Container and Docker Security

### Docker Socket Security

**Minimize Socket Exposure:**
```yaml
# If possible, use Docker API over TCP with TLS
environment:
  - DOCKER_HOST=tcp://docker-host:2376
  - DOCKER_TLS_VERIFY=1
```

**Socket Permission Management:**
```bash
# Ensure proper socket permissions
chmod 660 /var/run/docker.sock
chown root:docker /var/run/docker.sock
```

### Container Isolation

**Resource Limits:**
```yaml
services:
  ddc:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 512M
        reservations:
          memory: 128M
```

**Security Options:**
```yaml
services:
  ddc:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
```

### Host Security Considerations

**File System Security:**
```bash
# Secure config directory
chmod 750 /path/to/dockerdiscordcontrol
chmod 640 /path/to/dockerdiscordcontrol/config/*.json
```

**User Management:**
```bash
# Create dedicated user for DDC
useradd -r -s /bin/false ddc-user
chown ddc-user:ddc-group /path/to/dockerdiscordcontrol
```

## Configuration Security

### Secure Configuration Storage

**Environment Variables:**
```bash
# Use .env file with restricted permissions
chmod 600 .env
chown root:root .env

# Example .env content
FLASK_SECRET_KEY=your_secure_32_byte_hex_key
DDC_ADMIN_PASSWORD=your_secure_password
```

**Configuration File Security:**
```bash
# Secure configuration files
chmod 640 config/*.json
chown root:ddc-group config/*.json

# Prevent world-readable configuration
umask 027
```

### Secrets Management

**Avoid Hardcoded Secrets:**
```yaml
# BAD: Hardcoded in docker-compose.yml
environment:
  - FLASK_SECRET_KEY=hardcoded_key

# GOOD: From environment file
environment:
  - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
```

**External Secrets Management:**
- Consider Docker Secrets for production
- Use HashiCorp Vault for enterprise environments
- Implement secret rotation policies

## Monitoring and Auditing

### Activity Monitoring

**Action Log Monitoring:**
- Review user action logs regularly
- Monitor for unauthorized container operations
- Set up alerts for suspicious activity

**System Monitoring:**
```bash
# Monitor DDC processes
ps aux | grep ddc

# Monitor network connections
netstat -tulpn | grep 8374

# Monitor file access
auditctl -w /path/to/config -p wa -k ddc-config
```

### Log Analysis

**Security-Relevant Events:**
- Failed login attempts
- Unauthorized Discord commands
- Configuration changes
- Container operations
- Network access attempts

**Log Retention:**
- Implement log rotation policies
- Secure log storage
- Regular log analysis
- Backup important logs

### Incident Response

**Security Incident Checklist:**

1. **Immediate Response:**
   - Stop DDC container if compromised
   - Isolate affected systems
   - Preserve evidence

2. **Assessment:**
   - Determine scope of compromise
   - Identify affected containers
   - Review access logs

3. **Containment:**
   - Change all passwords
   - Regenerate Discord bot tokens
   - Update firewall rules

4. **Recovery:**
   - Restore from clean backups
   - Update DDC to latest version
   - Implement additional security measures

5. **Post-Incident:**
   - Document lessons learned
   - Update security procedures
   - Monitor for recurring issues

## Security Hardening Checklist

### Initial Setup

- [ ] Change default web UI password
- [ ] Use strong, unique passwords
- [ ] Secure Discord bot token
- [ ] Configure firewall rules
- [ ] Set proper file permissions
- [ ] Enable HTTPS (if using reverse proxy)

### Configuration Security

- [ ] Implement least privilege access
- [ ] Configure channel permissions appropriately
- [ ] Set container permissions minimally
- [ ] Secure configuration files
- [ ] Use environment variables for secrets

### Ongoing Maintenance

- [ ] Regularly update DDC
- [ ] Monitor action logs
- [ ] Audit user permissions
- [ ] Review security configurations
- [ ] Backup configurations securely
- [ ] Test incident response procedures

### Network Security

- [ ] Restrict web UI access
- [ ] Use reverse proxy with HTTPS
- [ ] Implement network segmentation
- [ ] Monitor network traffic
- [ ] Regular security scans

## Common Security Pitfalls

### Avoid These Mistakes

**1. Default Credentials:**
- Never leave default `admin`/`admin` credentials
- Change passwords during initial setup

**2. Overprivileged Access:**
- Don't give all containers all permissions
- Avoid Discord "Administrator" permission

**3. Insecure Storage:**
- Don't commit secrets to version control
- Avoid world-readable configuration files

**4. Inadequate Monitoring:**
- Don't ignore action logs
- Monitor for suspicious activity

**5. Poor Network Security:**
- Don't expose web UI to internet without protection
- Use HTTPS for remote access

## Compliance Considerations

### Data Protection

**Personal Data Handling:**
- Discord user IDs may be logged
- Minimize data collection and retention
- Implement data protection measures

**Configuration Backups:**
- Encrypt configuration backups
- Secure backup storage
- Regular backup testing

### Regulatory Compliance

**Consider relevant regulations:**
- GDPR (if handling EU data)
- SOX (for financial organizations)
- HIPAA (for healthcare)
- Industry-specific requirements

## Security Resources

### Tools and Technologies

**Security Scanning:**
- Docker Bench Security
- Container vulnerability scanners
- Network security tools

**Monitoring Solutions:**
- ELK Stack for log analysis
- Prometheus for metrics
- Security information and event management (SIEM)

### Further Reading

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Discord Developer Security](https://discord.com/developers/docs/topics/security)
- [OWASP Container Security](https://owasp.org/www-project-container-security/)

## Emergency Contacts

**In case of security incident:**
- Document the incident thoroughly
- Contact system administrators
- Consider professional security assistance
- Report to relevant authorities if required

Remember: Security is an ongoing process, not a one-time setup. Regular review and updates of security measures are essential for maintaining a secure DDC installation. 