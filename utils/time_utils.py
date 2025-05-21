# -*- coding: utf-8 -*-
import time
import pytz
import logging
from datetime import datetime, timedelta, timezone
from typing import Union, Tuple, List, Dict, Any, Optional
from utils.logging_utils import setup_logger

logger = setup_logger('ddc.time_utils')

def format_datetime_with_timezone(dt: datetime, 
                                  timezone_name: Optional[str] = None,
                                  fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Formats a datetime object with the specified timezone.
    
    Args:
        dt: Datetime object to format
        timezone_name: Name of the timezone to use (e.g., 'Europe/Berlin')
        fmt: Format string for the output
        
    Returns:
        Formatted datetime string with timezone information
    """
    if not dt:
        return "N/A"
    
    # Ensure dt is timezone-aware - if naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    try:
        # Attempt to get target timezone
        if timezone_name:
            target_tz = pytz.timezone(timezone_name)
        else:
            target_tz = timezone.utc # Fall back to UTC if no timezone specified
        
        # Convert to target timezone
        dt_in_target_tz = dt.astimezone(target_tz)
        
        # Format according to provided pattern
        return dt_in_target_tz.strftime(fmt)
    except Exception as e:
        logger.error(f"Error formatting datetime with timezone: {e}")
        target_tz = timezone.utc # Ensure fallback on generic error too
        try:
            # Fallback to UTC formatting if localization fails
            dt_in_utc = dt.astimezone(timezone.utc)
            return dt_in_utc.strftime(fmt) + " UTC"
        except Exception as inner_e:
            logger.error(f"Failed even with UTC fallback: {inner_e}")
            return str(dt)
            
def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse a timestamp string into a datetime object.
    Supports multiple common formats.
    
    Args:
        timestamp_str: String containing a timestamp
        
    Returns:
        Datetime object or None if parsing fails
    """
    # List of formats to try, most specific first
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with microseconds and Z
        "%Y-%m-%dT%H:%M:%SZ",     # ISO 8601 with Z
        "%Y-%m-%d %H:%M:%S.%f",   # Python datetime default with microseconds
        "%Y-%m-%d %H:%M:%S",      # Python datetime default
        "%Y-%m-%d %H:%M",         # Date with hours and minutes
        "%Y-%m-%d",               # Just date
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            # For formats without timezone, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
            
    # If no format matched
    logger.warning(f"Could not parse timestamp string: {timestamp_str}")
    return None 