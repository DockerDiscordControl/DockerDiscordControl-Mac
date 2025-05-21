import os

# --- Gevent Monkey Patching ---
# IMPORTANT: This must be done BEFORE any other modules that might use ssl,
# such as requests, urllib3, or even Flask itself indirectly.
if os.getenv("GUNICORN_WORKER_CLASS", "sync") == "gevent":
    try:
        import gevent.monkey
        gevent.monkey.patch_all()
        print("Gevent monkey patches applied.") # Use print for early feedback
    except ImportError:
        print("Gevent not installed, cannot apply monkey patches.")
    except Exception as e:
        print(f"Error applying Gevent monkey patches: {e}")
# -----------------------------

import multiprocessing
import logging
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# Assumption: web_ui.py is in the 'app' subdirectory
# Adjust the Python path so we can import modules from 'app'
import sys
sys.path.insert(0, '/app')

# Import necessary functions/objects from the web app
# It's important that these imports do not trigger Flask app initialization at the module level,
# which is handled by Gunicorn itself.
try:
    # Import directly from source modules, not via app.web_ui
    from utils.config_loader import load_config
    from app.utils.web_helpers import get_docker_containers_live 
    # Setup logger
    logging.basicConfig(level=logging.INFO) # Ensure basicConfig is called somewhere
    logger = logging.getLogger("gunicorn.config")
    logger.info("Gunicorn config logger initialized.")
except ImportError as e:
    # Fallback logger 
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"Error importing required components: {e}.") 
    sys.exit("Critical import error in gunicorn_config.py")


# --- Gunicorn Configuration ---
# Optimized worker calculation based on CPU cores
# Formula: (2 × CPU cores) + 1, with sensible limits
cpu_count = multiprocessing.cpu_count()
default_workers = max(2, min(cpu_count * 2 + 1, 8))  # Minimum 2, maximum 8 workers
workers = int(os.getenv('GUNICORN_WORKERS', default_workers))
logger.info(f"Gunicorn starting with {workers} workers based on {cpu_count} CPU cores")

# Address and port Gunicorn should listen on
bind = "0.0.0.0:9374"

# Worker class (gevent for asynchronous workers is often recommended)
worker_class = "gevent"

# Worker timeout increased for long-running Docker operations
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))

# Logging - Gunicorn logs go to stdout/stderr, which Supervisor catches
accesslog = "-"
errorlog = "-"
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# --- Scheduler and Hooks ---
# Scheduler might not be needed anymore if only for docker cache update
# scheduler = None

def when_ready(server):
    """Gunicorn Hook: Executed when the master process is ready (before forking workers)."""
    logger.info(f"[Gunicorn Master {os.getpid()}] Server ready. Performing initial cache population...")

    try:
        # Fill initial cache synchronously (keep this part)
        logger.info(f"[Gunicorn Master {os.getpid()}] Performing initial Docker cache update...")
        get_docker_containers_live(logger) # Pass the logger
        logger.info(f"[Gunicorn Master {os.getpid()}] Initial cache update complete.")

    except Exception as e:
        logger.error(f"[Gunicorn Master {os.getpid()}] Error during initial cache population: {e}", exc_info=True)
        # server.stop() # Consider stopping if initial cache fails?

# Optional: Hooks for workers (e.g., post_fork)
# def post_fork(server, worker):
#     logger.info(f"[Gunicorn Worker {worker.pid}] Worker started.")

# Optional: Hook on worker exit
# def worker_exit(server, worker):
#    logger.info(f"[Gunicorn Worker {worker.pid}] Worker exited.") 

# Gunicorn Server Configuration

# Path to WSGI application
wsgi_app = "app.web_ui:create_app()"

# Worker & Threading
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)  # Max. 8 workers
worker_class = "gevent"  # Use Gevent for asynchronous processing
worker_connections = 1000  # Number of simultaneous connections per worker
threads = 1  # For Gevent workers: Use 1 thread

# Timeouts
timeout = 60  # Timeout for workers in seconds
graceful_timeout = 10  # Time workers get to terminate
keepalive = 5  # How long connections remain open (seconds)

# Binding
bind = "0.0.0.0:9374"  # Host:Port for binding
backlog = 2048  # Number of pending connections

# HTTP Settings
max_requests = 1000  # Number of requests after which workers are restarted
max_requests_jitter = 100  # Jitter to avoid simultaneous restarts

# Logging
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
loglevel = os.environ.get('LOGGING_LEVEL', 'info').lower()  # Logging level from environment or default
capture_output = True  # Log stdout/stderr of the application
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process management
daemon = False  # Don't run as daemon
pidfile = None  # No PID file (managed by Supervisor)
user = None  # User for worker processes
group = None  # Group for worker processes
umask = 0  # File permissions mask

# Gevent-specific optimizations
gevent_monkey_patching = True  # Enables monkey patching
worker_greenlet_concurrency = 1000  # Max. number of concurrent greenlets per worker

# Gevent-specific optimizations for better thread compatibility
def post_fork(server, worker):
    # Remove compatibility checks for threads - manually patched in web_ui.py
    if worker_class == "gevent":
        # Reduce frequency of thread checks
        import gevent.hub
        gevent.hub.get_hub().threadpool_size = 20
        
        try:
            # Adjust the hub for better thread compatibility
            from gevent import monkey
            from gevent.threading import _ForkHooks
            
            # Safe hooks for better thread compatibility
            original_after_fork = _ForkHooks.after_fork_in_child
            
            def safer_after_fork_in_child(self, thread):
                # Override the assert check
                pass
                
            # Replace the hook method
            _ForkHooks.after_fork_in_child = safer_after_fork_in_child
            
            # Provide worker info
            worker.log.info("Gevent worker patched for better thread compatibility")
        except (ImportError, AttributeError) as e:
            worker.log.warning(f"Could not patch Gevent fork hooks: {e}")

# Pre-initialization before worker start
def pre_exec(server):
    server.log.info("Initializing server (pre-exec)")

# Dynamic settings based on environment variables
if os.environ.get('DDC_DISABLE_CACHE_LOCKS', '').lower() == 'true':
    os.environ['DDC_CACHE_LOCKS_DISABLED'] = 'true'
    server_socket = "/tmp/gunicorn.sock" 