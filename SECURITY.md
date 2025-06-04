# Security Policy

## Supported Versions

The following versions of DockerDiscordControl (DDC) are currently supported with security updates:

| Version | Supported          | Notes                    |
| ------- | ------------------ | ------------------------ |
| 5.1.x   | :white_check_mark: | Latest stable release    |
| 5.0.x   | :white_check_mark: | LTS support until 2025  |
| 4.x.x   | :x:                | End of life             |
| < 4.0   | :x:                | No longer supported     |

**Note:** DDC is developed and maintained by a single person as a passion project. While we strive to provide timely security updates, please understand that response times may vary based on real-life commitments. We strongly recommend always using the latest stable version for the best security and feature support.

## Reporting a Vulnerability

We take security vulnerabilities seriously and appreciate responsible disclosure. If you discover a security vulnerability in DDC, please follow these steps:

### 🔒 **Private Disclosure (Recommended)**

1. **DO NOT** open a public GitHub issue for security vulnerabilities
2. Send an email to: **security@ddc.bot** (or use GitHub's private vulnerability reporting)
3. Include the following information:
   - Detailed description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Any suggested fixes (if available)

### 📋 **What to Expect**

**Please note:** DDC is maintained by a single developer alongside a full-time job, family, and other commitments. Response times reflect this reality:

- **Initial Response:** Within 1-2 weeks (depending on availability)
- **Regular Updates:** When significant progress is made
- **Fix Timeline:** 
  - **Critical vulnerabilities:** Best effort to address quickly, but may take several weeks
  - **Non-critical issues:** Will be addressed in regular development cycles

**Important:** If you discover a critical security vulnerability that poses immediate risk, please clearly mark it as "CRITICAL" in your report. While I cannot guarantee immediate patches, critical issues will be prioritized above feature development.

### ✅ **If Your Report is Accepted**

- We will work with you to understand and reproduce the issue
- A fix will be developed and tested
- Security advisory will be published after the fix is released
- You will be credited in our security acknowledgments (unless you prefer to remain anonymous)

### ❌ **If Your Report is Declined**

- We will provide a detailed explanation of why the issue is not considered a vulnerability
- We may suggest alternative reporting channels if appropriate
- We appreciate all reports, even if they don't qualify as security vulnerabilities

## Security Best Practices

When deploying DDC, please follow these security recommendations:

- **Docker Security:** Use non-root containers when possible
- **Network Security:** Limit network exposure using Docker networks
- **Access Control:** Use strong passwords for the web interface
- **Updates:** Keep DDC and its dependencies up to date
- **Monitoring:** Enable logging and monitor for suspicious activities

## Security Features

DDC includes several built-in security features:

- 🔐 **Authentication:** Web interface requires login
- 🛡️ **Input Validation:** All user inputs are sanitized
- 📊 **Audit Logging:** User actions are logged for security monitoring
- 🔒 **Permission System:** Granular access control for containers
- 🚫 **Rate Limiting:** Protection against abuse

## Hall of Fame

I appreciate security researchers who responsibly disclose vulnerabilities and help make DDC safer for everyone:

*No vulnerabilities have been responsibly disclosed yet.*

---

**Contact:** For general questions, visit [https://ddc.bot](https://ddc.bot) or [GitHub Issues](https://github.com/DockerDiscordControl/DockerDiscordControl/issues)

**Security Contact:** security@ddc.bot 