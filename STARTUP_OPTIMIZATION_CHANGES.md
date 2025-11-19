# Startup Optimization Changes for Main Repository

## Overview
This document describes the startup optimization changes made to the Mac repository that should be applied to the main DockerDiscordControl repository. These changes eliminate bot crashes when the Discord bot token is not configured.

## Problem Statement
**Before:**
- Bot crashes immediately when Discord token is missing
- Container exits with error status
- No way to configure token via Web-UI because container is dead
- Poor user experience

**After:**
- Bot implements intelligent retry loop with countdown (configurable interval, default 60s)
- Container stays running, Web-UI remains accessible
- User can configure token via Web-UI while bot waits
- Clean, informative logs with countdown messages

## Changes Required

### Change 1: bot.py - Add Intelligent Retry Loop

**Location:** `bot.py` around line 95-130 (in the `main()` function, after `bot = create_bot(runtime)`)

**Add import at top of file:**
```python
import time
```

**Replace the token retrieval section with:**
```python
def main() -> None:
    """Main entry point for the Discord bot."""

    configure_environment()
    config = load_main_configuration()
    runtime = build_runtime(config)

    _ensure_timezone(runtime.logger)

    bot = create_bot(runtime)
    register_event_handlers(bot, runtime)

    # Retry loop for missing token with countdown
    retry_interval = int(os.getenv("DDC_TOKEN_RETRY_INTERVAL", "60"))
    max_retries = int(os.getenv("DDC_TOKEN_MAX_RETRIES", "0"))  # 0 = infinite
    retry_count = 0

    while True:
        token = get_decrypted_bot_token(runtime)
        if token:
            break

        retry_count += 1
        runtime.logger.error("FATAL: Bot token not found or could not be decrypted.")
        runtime.logger.error(
            "Please configure the bot token in the Web UI or check the configuration files."
        )

        if max_retries > 0 and retry_count >= max_retries:
            runtime.logger.error(f"Maximum retries ({max_retries}) reached. Exiting.")
            sys.exit(1)

        runtime.logger.warning(f"Retry {retry_count}: Waiting {retry_interval} seconds before next attempt...")

        # Countdown timer
        for remaining in range(retry_interval, 0, -1):
            if remaining % 10 == 0 or remaining <= 5:
                runtime.logger.info(f"⏳ Retrying in {remaining} seconds...")
            time.sleep(1)

        runtime.logger.info("Attempting to reload configuration and retry...")
        # Reload config in case it was updated
        config = load_main_configuration()
        runtime = build_runtime(config)

    runtime.logger.info("Starting bot with token ending in: ...%s", token[-4:])
    bot.run(token)
    runtime.logger.info("Bot has stopped gracefully.")
```

### Change 2: gunicorn_config.py - Fix Missing Import and Exception Handling

**Location:** `gunicorn_config.py`

**Problem:** Web-UI crashes on startup when Docker is unavailable due to:
1. Missing `import docker` - causes NameError
2. Missing exception handler for `DockerConnectionError` - causes uncaught exception crash

**Add import at line ~28 (after other imports):**
```python
import docker
```

**Add custom exception import at line ~43 (in the try block with other imports):**
```python
try:
    # Import directly from source modules, not via app.web_ui
    from services.config.config_service import load_config
    from app.utils.web_helpers import get_docker_containers_live
    from services.exceptions import DockerConnectionError  # ADD THIS LINE
    # Setup logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("gunicorn.config")
    logger.info("Gunicorn config logger initialized.")
except ImportError as e:
    # Fallback logger
    ...
```

**Update exception handling at line ~96 (in when_ready function):**
```python
def when_ready(server):
    """Gunicorn Hook: Executed when the master process is ready (before forking workers)."""
    logger.info(f"[Gunicorn Master {os.getpid()}] Server ready. Performing initial cache population...")

    try:
        # Fill initial cache synchronously (keep this part)
        logger.info(f"[Gunicorn Master {os.getpid()}] Performing initial Docker cache update...")
        get_docker_containers_live(logger) # Pass the logger
        logger.info(f"[Gunicorn Master {os.getpid()}] Initial cache update complete.")

    # ADD DockerConnectionError to the exception tuple:
    except (RuntimeError, docker.errors.APIError, docker.errors.DockerException, DockerConnectionError) as e:
        logger.error(f"[Gunicorn Master {os.getpid()}] Error during initial cache population: {e}", exc_info=True)
```

**Why These Changes Are Critical:**
- Without `import docker`: NameError crashes gunicorn immediately
- Without `DockerConnectionError` handling: Web-UI crashes when Docker socket unavailable (common during first setup)
- With these fixes: Web-UI starts gracefully and logs the error, remaining accessible for configuration

### Change 3: container_status_service.py - Auto-Cleanup for Missing Containers

**Location:** `services/infrastructure/container_status_service.py`

**Problem:** When containers are deleted outside the application, the service logs ERROR messages with full tracebacks, causing log pollution.

**Add imports at top of file (if not already present):**
```python
import json  # Around line 17
from pathlib import Path  # Around line 22
```

**Add the `_deactivate_container()` method after `_record_performance()` method (around line 536):**
```python
def _deactivate_container(self, container_name: str) -> bool:
    """
    Set container to active=false in JSON config when container is not found.
    Does NOT delete the file, just marks it as inactive for auto-cleanup.

    Args:
        container_name: Name of the container to deactivate

    Returns:
        True if successfully deactivated, False otherwise
    """
    try:
        # Construct path to container config file
        config_dir = Path('/app/config/containers')
        container_file = config_dir / f'{container_name}.json'

        if not container_file.exists():
            self.logger.debug(f"Container config file not found: {container_file}")
            return False

        # Read existing config
        with open(container_file, 'r', encoding='utf-8') as f:
            container_config = json.load(f)

        # Set active to false
        container_config['active'] = False

        # Write back to file
        with open(container_file, 'w', encoding='utf-8') as f:
            json.dump(container_config, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Auto-cleanup: Container '{container_name}' marked as inactive (active=false)")
        return True

    except (OSError, IOError) as e:
        self.logger.warning(f"Failed to deactivate container '{container_name}': {e}")
        return False
    except (ValueError, KeyError) as e:
        self.logger.warning(f"Invalid JSON in container config '{container_name}': {e}")
        return False
```

**Update the `docker.errors.NotFound` exception handler (around line 472):**
```python
# BEFORE:
except docker.errors.NotFound as e:
    # Container not found error
    duration_ms = (time.time() - start_time) * 1000
    self.logger.error(f"Container not found: {request.container_name}: {e}", exc_info=True)

    return ContainerStatusResult(
        success=False,
        container_name=request.container_name,
        error_message=f"Container not found: {str(e)}",
        error_type="container_not_found",
        query_duration_ms=duration_ms
    )

# AFTER:
except docker.errors.NotFound as e:
    # Container not found - auto-cleanup
    duration_ms = (time.time() - start_time) * 1000
    self.logger.warning(f"Container '{request.container_name}' not found in Docker, marking as inactive...")

    # Auto-cleanup: Mark container as inactive in JSON
    self._deactivate_container(request.container_name)

    return ContainerStatusResult(
        success=False,
        container_name=request.container_name,
        error_message=f"Container not found: {str(e)}",
        error_type="container_not_found",
        query_duration_ms=duration_ms
    )
```

**Why This Change Is Important:**
- **Before:** Full ERROR traceback logged every time a deleted container is queried
- **After:** Clean WARNING message + automatic cleanup by setting `active=false` in JSON
- **Benefits:**
  - Cleaner logs (WARNING instead of ERROR with traceback)
  - Auto-deactivates missing containers (sets `active=false` in config)
  - Prevents log pollution from normal container lifecycle events
  - Container config preserved (not deleted), just marked inactive

## New Environment Variables

Add these to your documentation:

```bash
# Bot Token Retry Configuration (New in v2.0)
DDC_TOKEN_RETRY_INTERVAL=60    # Seconds between retry attempts (default: 60)
DDC_TOKEN_MAX_RETRIES=0        # Maximum retry attempts, 0 = infinite (default: 0)
```

## Why NOT to modify Web-UI startup

**IMPORTANT:** Do NOT add startup delays or token checks to the Web-UI!

**Reasons:**
1. **Web-UI is the configuration interface** - Users NEED access to configure the token
2. **Web-UI doesn't require Discord token** - Runs independently with only Flask secret key
3. **Creates Catch-22** - Can't access Web-UI to set token if Web-UI waits for token
4. **Unnecessary complexity** - Web-UI should always be accessible

**Keep supervisord.conf as-is:**
```ini
[program:web-ui]
command=/usr/bin/python3 -m gunicorn -c gunicorn_config.py app.web_ui:app
directory=/app
autostart=true
autorestart=true
stdout_logfile=/app/logs/webui.log
stderr_logfile=/app/logs/webui.log
environment=DDC_WEB_PORT="9374"
user=ddc
```

## Benefits

1. **No Bot Crashes:** Container runs stably even without token configured
2. **Web-UI Always Accessible:** Users can configure token at any time
3. **Better User Experience:** Clear countdown messages inform users what's happening
4. **Configurable:** Users can adjust retry timing via environment variables
5. **Production Ready:** Handles edge cases like token being added while running

## Testing

Test with these scenarios:

```bash
# Test 1: No token configured (should retry every 60s, Web-UI accessible)
docker run --rm -e FLASK_SECRET_KEY="test" yourimage:latest

# Test 2: Custom retry interval (should retry every 20s)
docker run --rm -e DDC_TOKEN_RETRY_INTERVAL=20 -e FLASK_SECRET_KEY="test" yourimage:latest

# Test 3: Max retries limit (should exit after 3 attempts)
docker run --rm -e DDC_TOKEN_RETRY_INTERVAL=10 -e DDC_TOKEN_MAX_RETRIES=3 -e FLASK_SECRET_KEY="test" yourimage:latest
```

## macOS-Specific: Docker Socket Permissions

**Problem:** On macOS with Docker Desktop, the Docker socket (`/var/run/docker.sock`) has GID 0 (root/wheel), not the docker group. This prevents the container from accessing the Docker API for container management.

**Solution:** Add `--group-add 0` when running the container on macOS:

```bash
# macOS: Add --group-add 0 for Docker socket access
docker run --rm \
  --group-add 0 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -p 9374:9374 \
  -e FLASK_SECRET_KEY="your-secret-key" \
  yourimage:latest
```

**Why This Works:**
- On macOS Docker Desktop, the socket is owned by `root:wheel` (GID 0)
- The `ddc` user (UID 1000) inside the container needs to be in GID 0 to access the socket
- `--group-add 0` adds the container user to the root/wheel group without changing the primary UID
- This is **safe** because the container user is still non-root (UID 1000), just with socket access

**Verification:**
```bash
# Test Docker API access on macOS
docker run --rm --group-add 0 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --entrypoint=python3 yourimage:latest -c "
import docker
client = docker.from_env()
containers = client.containers.list()
print(f'✅ Docker API works! Found {len(containers)} containers')
"
```

**Linux vs macOS:**
- **Linux:** Socket typically has docker group (GID 999 or similar) - no `--group-add` needed
- **macOS:** Socket has root group (GID 0) - requires `--group-add 0`
- **Container auto-detection:** The entrypoint script will warn if socket is inaccessible

## Expected Log Output

**Bot (without token):**
```
2025-11-19 19:31:51 CET - ddc.bot - ERROR - FATAL: Bot token not found or could not be decrypted.
2025-11-19 19:31:51 CET - ddc.bot - ERROR - Please configure the bot token in the Web UI or check the configuration files.
2025-11-19 19:31:51 CET - ddc.bot - WARNING - Retry 1: Waiting 60 seconds before next attempt...
2025-11-19 19:31:51 CET - ddc.bot - INFO - ⏳ Retrying in 60 seconds...
2025-11-19 19:32:01 CET - ddc.bot - INFO - ⏳ Retrying in 50 seconds...
2025-11-19 19:32:11 CET - ddc.bot - INFO - ⏳ Retrying in 40 seconds...
...
```

**Web-UI (should start normally):**
```
2025-11-19 19:31:50,689 INFO success: web-ui entered RUNNING state
[2025-11-19 19:31:52 +0100] [15] [INFO] Starting gunicorn 23.0.0
[2025-11-19 19:31:52 +0100] [15] [INFO] Listening at: http://0.0.0.0:9374
```

## Rollback Instructions

If these changes cause issues, rollback by:

1. Revert `bot.py` changes (remove retry loop, restore original token check that exits on failure)
2. That's it - only one file changed!

## Common Mistakes to Avoid

❌ **WRONG:** Adding startup delays to Web-UI
✅ **CORRECT:** Only modify bot.py retry logic

❌ **WRONG:** Making Web-UI wait for Discord token
✅ **CORRECT:** Web-UI starts immediately and always

❌ **WRONG:** Complex startup scripts
✅ **CORRECT:** Simple retry loop in bot.py only

## Implementation Notes

- **Three-file changes:** `bot.py`, `gunicorn_config.py`, and `container_status_service.py` need modification
- **bot.py:** Add intelligent retry loop for missing Discord token
- **gunicorn_config.py:** Fix missing import and exception handling for Docker connectivity
- **container_status_service.py:** Add auto-cleanup for missing containers
- **No Docker rebuild required:** Code changes only (unless using cached image layers)
- **Backward compatible:** Works with existing configurations
- **No breaking changes:** All existing functionality preserved
- **Critical for production:**
  - Without gunicorn_config.py fixes, Web-UI crashes on startup
  - Without container_status_service.py fixes, logs are polluted with ERROR tracebacks

## Author

These changes were developed for the DockerDiscordControl Mac repository and tested thoroughly with:
- Alpine Linux 3.22.2
- Python 3.12.12
- Supervisord 4.2.5
- Gunicorn 23.0.0

## License

MIT License - Same as main DockerDiscordControl project
