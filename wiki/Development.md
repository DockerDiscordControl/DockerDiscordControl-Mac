# Development Guide

This guide covers contributing to DockerDiscordControl, development setup, and coding standards.

## Getting Started

### Prerequisites

**Required Software:**
- **Python 3.9+**: Core runtime environment
- **Docker**: For containerization and testing
- **Git**: Version control
- **Code Editor**: VS Code, PyCharm, or similar

**Development Environment:**
- **Linux/macOS**: Recommended for development
- **Windows**: WSL2 recommended for best compatibility

### Repository Setup

**1. Fork and Clone**
```bash
# Fork the repository on GitHub first
git clone https://github.com/your-username/DockerDiscordControl.git
cd DockerDiscordControl

# Add upstream remote
git remote add upstream https://github.com/DockerDiscordControl/DockerDiscordControl.git
```

**2. Development Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # if exists
```

**3. Environment Configuration**
```bash
# Create development .env file
cp .env.example .env

# Edit .env with your settings
FLASK_SECRET_KEY=$(openssl rand -hex 32)
DDC_ADMIN_PASSWORD=dev_password
```

## Project Structure

```
DockerDiscordControl/
├── app/                          # Flask web application
│   ├── blueprints/              # Flask blueprints
│   │   ├── main_routes.py       # Main web routes
│   │   ├── log_routes.py        # Log viewing routes
│   │   └── tasks_bp.py          # Task management routes
│   ├── static/                  # Static web assets
│   │   ├── css/                 # Stylesheets
│   │   ├── js/                  # JavaScript files
│   │   └── vendor/              # Third-party assets
│   ├── templates/               # Jinja2 templates
│   │   ├── _base.html           # Base template
│   │   ├── config.html          # Main configuration page
│   │   └── tasks/               # Task-related templates
│   └── utils/                   # App utilities
├── cogs/                        # Discord bot cogs
│   ├── docker_control.py       # Main container control
│   ├── scheduler_commands.py   # Task scheduling
│   ├── command_handlers.py     # Command implementations
│   └── translation_manager.py  # Multi-language support
├── utils/                       # Core utilities
│   ├── config_loader.py        # Configuration management
│   ├── config_manager.py       # Advanced config handling
│   ├── docker_utils.py         # Docker operations
│   ├── logging_utils.py        # Centralized logging
│   └── scheduler.py            # Task scheduling system
├── config/                      # Configuration files
├── logs/                        # Application logs
├── scripts/                     # Utility scripts
└── wiki/                        # Documentation content
```

## Development Workflow

### Branch Strategy

**Main Branches:**
- `main`: Stable release code
- `develop`: Development integration branch (if used)

**Feature Branches:**
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Work on your feature
git add .
git commit -m "feat: add new feature"

# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

### Commit Standards

**Use Conventional Commits:**
```bash
# Format: type(scope): description
feat(bot): add new Discord command
fix(web): resolve configuration saving issue
docs(wiki): update installation guide
style(app): format code according to standards
refactor(utils): improve logging utilities
test(scheduler): add task validation tests
```

**Commit Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

### Pull Request Process

**Before Submitting:**
1. Ensure code follows style guidelines
2. Add/update tests if applicable
3. Update documentation
4. Test your changes thoroughly
5. Rebase on latest main branch

**Pull Request Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Documentation update
- [ ] Code refactoring

## Testing
- [ ] Tested locally
- [ ] Added/updated tests
- [ ] Tested in Docker environment

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Coding Standards

### Python Style Guide

**Follow PEP 8 with modifications:**

**Imports:**
```python
# Standard library imports
import os
import logging
from typing import Dict, List, Optional

# Third-party imports
import discord
from flask import Flask, request

# Local imports
from utils.logging_utils import setup_logger
from cogs.translation_manager import _
```

**Function Documentation:**
```python
def process_container_action(container_name: str, action: str) -> bool:
    """
    Process a container action with proper error handling.
    
    Args:
        container_name: Name of the Docker container
        action: Action to perform (start, stop, restart)
        
    Returns:
        bool: True if action succeeded, False otherwise
        
    Raises:
        ValueError: If action is invalid
        DockerException: If Docker operation fails
    """
    pass
```

**Error Handling:**
```python
# Use specific exception types
try:
    result = docker_operation()
except DockerException as e:
    logger.error(f"Docker operation failed: {e}")
    return False
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

### Code Organization

**Logging Standards:**
```python
# Use centralized logging
from utils.logging_utils import setup_logger

logger = setup_logger('ddc.module_name', level=logging.DEBUG)

# Consistent log levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning conditions")
logger.error("Error conditions")
logger.critical("Critical errors")
```

**Configuration Handling:**
```python
# Use config cache for performance
from utils.config_cache import get_cached_config

def my_function():
    config = get_cached_config()  # Don't call load_config() repeatedly
    return config.get('setting', default_value)
```

**Translation Support:**
```python
# Use translation system for user-facing messages
from cogs.translation_manager import _

# In Discord commands
await ctx.respond(_("Container '{name}' started successfully").format(name=container_name))

# In web UI (templates)
{{ _("Save Configuration") }}
```

## Testing

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_config_loader.py
│   ├── test_docker_utils.py
│   └── test_scheduler.py
├── integration/             # Integration tests  
│   ├── test_discord_bot.py
│   └── test_web_ui.py
└── fixtures/               # Test data
    ├── config_samples.json
    └── docker_responses.json
```

### Writing Tests

**Unit Test Example:**
```python
import unittest
from unittest.mock import patch, MagicMock
from utils.docker_utils import get_container_status

class TestDockerUtils(unittest.TestCase):
    
    @patch('utils.docker_utils.docker.from_env')
    def test_get_container_status(self, mock_docker):
        # Setup mock
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_container = MagicMock()
        mock_container.status = 'running'
        mock_client.containers.get.return_value = mock_container
        
        # Test
        status = get_container_status('test_container')
        
        # Assert
        self.assertEqual(status, 'running')
        mock_client.containers.get.assert_called_once_with('test_container')
```

**Running Tests:**
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/test_config_loader.py

# Run with coverage
python -m pytest --cov=utils --cov-report=html
```

## Debugging

### Local Development

**Run Components Separately:**
```bash
# Run web UI only
python app.py

# Run Discord bot only
python bot.py

# Run with debug mode
FLASK_DEBUG=1 python app.py
```

**Debug Configuration:**
```python
# In development settings
DEBUG = True
SCHEDULER_DEBUG_MODE = True
LOGGING_LEVEL = 'DEBUG'
```

### Docker Development

**Development Docker Setup:**
```yaml
# docker-compose.dev.yml
services:
  ddc-dev:
    build: .
    volumes:
      - .:/app  # Mount source code for live editing
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - FLASK_DEBUG=1
      - FLASK_ENV=development
    ports:
      - "8374:8374"
```

**Debug Commands:**
```bash
# Build development image
docker-compose -f docker-compose.dev.yml build

# Run with live code mounting
docker-compose -f docker-compose.dev.yml up

# Execute commands in development container
docker-compose -f docker-compose.dev.yml exec ddc-dev bash
```

## Performance Guidelines

### Optimization Principles

**Cache Efficiently:**
```python
# Good: Use cached configuration
from utils.config_cache import get_cached_config

def frequent_operation():
    config = get_cached_config()  # Fast cached access
    return config.get('setting')

# Bad: Repeated file I/O
def frequent_operation():
    config = load_config()  # Slow file system access
    return config.get('setting')
```

**Batch Operations:**
```python
# Good: Batch Docker operations
containers_to_process = ['container1', 'container2', 'container3']
for batch in chunked(containers_to_process, batch_size=3):
    process_container_batch(batch)
    await asyncio.sleep(0.1)  # Rate limiting

# Bad: Individual operations without batching
for container in containers:
    process_container(container)  # No rate limiting
```

**Async Best Practices:**
```python
# Use async for I/O-bound operations
async def update_discord_messages(messages: List[discord.Message]):
    tasks = []
    for message in messages:
        tasks.append(update_message(message))
    
    # Process in batches to avoid rate limits
    for batch in chunked(tasks, 5):
        await asyncio.gather(*batch)
        await asyncio.sleep(1)  # Discord rate limiting
```

## Contributing Guidelines

### Issue Types

**Bug Reports:**
- Use bug report template
- Include reproduction steps
- Provide system information
- Include relevant logs

**Feature Requests:**
- Describe the problem/need
- Propose solution approach
- Consider backward compatibility
- Discuss implementation complexity

**Documentation:**
- Identify gaps or inaccuracies
- Propose improvements
- Consider user experience
- Update related sections

### Code Review Process

**As a Contributor:**
- Request review from maintainers
- Respond to feedback promptly
- Make requested changes
- Keep discussions constructive

**Review Checklist:**
- [ ] Code follows style guidelines
- [ ] Functionality works as intended
- [ ] Edge cases are handled
- [ ] Performance impact considered
- [ ] Security implications reviewed
- [ ] Documentation updated
- [ ] Tests included/updated

### Release Process

**Version Management:**
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Document breaking changes
- Update changelog
- Tag releases properly

**Pre-release Testing:**
- Test all major workflows
- Verify Docker builds
- Check documentation accuracy
- Validate upgrade path

## Development Tools

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-azuretools.vscode-docker"
  ]
}
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.9
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88]
```

### Development Scripts

```bash
# scripts/dev-setup.sh
#!/bin/bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo "Development environment ready!"
```

## Architecture Overview

### Component Interaction

```
┌─────────────────┐    ┌─────────────────┐
│   Discord Bot   │    │    Web UI       │
│     (bot.py)    │    │   (Flask App)   │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌─────────────────┐
          │  Core Utils     │
          │ (config, logs,  │
          │  docker, etc.)  │
          └─────────┬───────┘
                    │
          ┌─────────────────┐
          │  Docker Engine  │
          │ (Container Mgmt)│
          └─────────────────┘
```

### Data Flow

1. **Configuration**: Web UI → Config Files → Bot
2. **Commands**: Discord → Bot → Docker Engine
3. **Status**: Docker Engine → Cache → Bot/Web UI
4. **Logs**: All Components → Centralized Logging

## Troubleshooting Development Issues

### Common Problems

**Import Errors:**
```bash
# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Permission Issues:**
```bash
# Fix config file permissions
chmod 644 config/*.json
```

**Docker Connection:**
```bash
# Test Docker access
docker ps
# Ensure socket is accessible
ls -la /var/run/docker.sock
```

### Getting Help

**Development Support:**
- GitHub Discussions for questions
- Code review feedback
- Architecture discussions
- Performance optimization help

**Documentation:**
- API documentation (if available)
- Architecture decision records
- Development blog posts
- Community knowledge base

## Future Development

### Roadmap Considerations

**Potential Features:**
- Plugin system for extensibility
- REST API for external integrations
- Advanced container orchestration
- Multi-server support
- Enhanced security features

**Architecture Evolution:**
- Microservices architecture
- Event-driven design
- Enhanced caching layers
- Improved testing coverage
- Documentation automation

Contributing to DDC is a great way to learn about Discord bots, Docker, and Python web development. We welcome contributions of all sizes and experience levels! 