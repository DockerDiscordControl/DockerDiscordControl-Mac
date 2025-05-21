# -*- coding: utf-8 -*-
import logging
import sys
import os
import time
from typing import Optional
from datetime import datetime

# Constants for logging
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEBUG_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]'

# Global variable for debug status
_debug_mode_enabled = None

def is_debug_mode_enabled() -> bool:
    """
    Checks if debug mode is enabled.
    This is loaded from the configuration, with the local copy being cached.
    
    Returns:
        bool: True if debug mode is enabled, otherwise False
    """
    global _debug_mode_enabled
    
    # Only reload if status hasn't been checked yet
    if _debug_mode_enabled is None:
        try:
            from utils.config_loader import load_config
            config = load_config()
            _debug_mode_enabled = config.get('scheduler_debug_mode', False)
            # Only output debug message when loaded for the first time
            print(f"Debug status loaded from configuration: {_debug_mode_enabled}")
        except Exception as e:
            # Fallback on errors
            print(f"Error loading debug status: {e}")
            _debug_mode_enabled = False
    
    return _debug_mode_enabled

# A filter that only allows DEBUG logs when debug mode is enabled
class DebugModeFilter(logging.Filter):
    """
    Filter that only allows DEBUG messages when debug mode is enabled.
    INFO and higher levels are always allowed.
    """
    def filter(self, record):
        # Check if log level is lower than INFO (i.e., DEBUG)
        if record.levelno < logging.INFO:
            return is_debug_mode_enabled()
        # Always allow all other levels (INFO and higher)
        return True

# A custom formatter class that uses the configured timezone
class TimezoneFormatter(logging.Formatter):
    """
    A custom formatter that uses the local timezone for timestamps in logs.
    """
    def __init__(self, fmt=None, datefmt=None, tz=None):
        super().__init__(fmt, datefmt)
        self.tz = tz

    def formatTime(self, record, datefmt=None):
        """
        Overrides the formatTime method to use the configured timezone.
        """
        if datefmt is None:
            datefmt = self.datefmt or '%Y-%m-%d %H:%M:%S'
        
        # We use record creation time as UTC timestamp
        ct = self.converter(record.created)
        
        try:
            from utils.config_loader import load_config
            import pytz
            
            # Try to load the timezone from the configuration
            config = load_config()
            timezone_str = config.get('timezone', 'Europe/Berlin')
            
            # Convert the timestamp to the configured timezone
            tz = pytz.timezone(timezone_str)
            dt = datetime.fromtimestamp(record.created, tz)
            
            # Format with the correct timezone
            formatted_time = dt.strftime(datefmt) + f" {dt.tzname()}"
            return formatted_time
        except Exception as e:
            # Fall back to standard formatting on errors
            return super().formatTime(record, datefmt)

def setup_logger(name: str, level=logging.INFO, log_to_console=True, log_to_file=False, custom_formatter=None) -> logging.Logger:
    """
    Creates a logger with the specified name and logging level.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_to_console: Whether to output logs to console
        log_to_file: Whether to output logs to a file
        custom_formatter: Optional custom formatter for the logs
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers in case of re-initialization
    if logger.handlers:
        return logger
    
    # Determine formatter to use
    if custom_formatter is None:
        if level <= logging.DEBUG:
            formatter = TimezoneFormatter(DEBUG_LOG_FORMAT)
        else:
            formatter = TimezoneFormatter(DEFAULT_LOG_FORMAT)
    else:
        formatter = custom_formatter
    
    # Console handler (stdout)
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        # Add the debug filter to the handler
        console_handler.addFilter(DebugModeFilter())
        
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        try:
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Create log file path
            log_file_path = os.path.join(logs_dir, f"{name.replace('.', '_')}.log")
            
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            
            # Add the filter to the file handler as well
            # This is optional - remove this line if you want debug messages
            # to always be written to the log file
            file_handler.addFilter(DebugModeFilter())
            
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to set up file logging for {name}: {e}")
    
    return logger

def refresh_debug_status():
    """
    Refreshes the cached debug status.
    Should be called when the configuration changes.
    """
    global _debug_mode_enabled
    _debug_mode_enabled = None
    # Reload status
    is_debug_mode_enabled()

def setup_all_loggers(level: int = logging.INFO) -> None:
    """
    Configures all project loggers with consistent settings.

    Args:
        level: Log level for all loggers
    """
    # Setup root logger
    root_logger = setup_logger('ddc', level)

    # Setup module loggers
    setup_logger('ddc.bot', level)
    setup_logger('ddc.docker_utils', level)
    setup_logger('ddc.config_loader', level)
    setup_logger('ddc.web_ui', level)
    
    # Check debug status and display in log
    debug_enabled = is_debug_mode_enabled()
    if debug_enabled:
        root_logger.info("Debug mode is enabled - DEBUG messages will be displayed")
    else:
        root_logger.info("Debug mode is disabled - DEBUG messages will be suppressed")

    root_logger.info("All loggers have been configured")

class LoggerMixin:
    """
    Mixin class for classes that require a logger.
    Adds a self.logger attribute.
    """

    def __init__(self, logger_name: Optional[str] = None, *args, **kwargs):
        # Derive name from class name if not provided
        if logger_name is None:
            logger_name = f"ddc.{self.__class__.__name__}"

        self.logger = logging.getLogger(logger_name)
        super().__init__(*args, **kwargs) 