# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC) - Config Cache                                   #
# https://ddc.bot                                                              #
# Copyright (c) 2023-2025 MAX                                                  #
# Licensed under the MIT License                                               #
# ============================================================================ #

import threading
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger('ddc.config_cache')

class ConfigCache:
    """
    Thread-safe configuration cache for performance optimization.
    Reduces filesystem I/O by caching frequently accessed config data.
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._last_update: Optional[datetime] = None
        
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Sets the cached configuration.
        
        Args:
            config: The configuration dictionary to cache
        """
        with self._lock:
            self._cache = config.copy() if config else {}
            self._last_update = datetime.now(timezone.utc)
            logger.debug(f"Config cache updated at {self._last_update}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Gets the cached configuration.
        
        Returns:
            The cached configuration dictionary
        """
        with self._lock:
            return self._cache.copy()
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """
        Gets the servers list from cached configuration.
        Optimized for autocomplete functions.
        
        Returns:
            List of server configurations
        """
        with self._lock:
            return self._cache.get('servers', [])
    
    def get_guild_id(self) -> Optional[int]:
        """
        Gets the guild ID from cached configuration.
        Optimized for autocomplete functions.
        
        Returns:
            Guild ID as integer or None if not configured
        """
        with self._lock:
            guild_id_str = self._cache.get('guild_id')
            if guild_id_str and isinstance(guild_id_str, str) and guild_id_str.isdigit():
                return int(guild_id_str)
            return None
    
    def get_language(self) -> str:
        """
        Gets the language from cached configuration.
        
        Returns:
            Language code (defaults to 'en')
        """
        with self._lock:
            return self._cache.get('language', 'en')
    
    def get_timezone(self) -> str:
        """
        Gets the timezone from cached configuration.
        
        Returns:
            Timezone string (defaults to 'Europe/Berlin')
        """
        with self._lock:
            return self._cache.get('timezone', 'Europe/Berlin')
    
    def get_channel_permissions(self) -> Dict[str, Any]:
        """
        Gets channel permissions from cached configuration.
        
        Returns:
            Channel permissions dictionary
        """
        with self._lock:
            return self._cache.get('channel_permissions', {})
    
    def get_default_channel_permissions(self) -> Dict[str, Any]:
        """
        Gets default channel permissions from cached configuration.
        
        Returns:
            Default channel permissions dictionary
        """
        with self._lock:
            return self._cache.get('default_channel_permissions', {})
    
    def is_valid(self) -> bool:
        """
        Checks if the cache contains valid data.
        
        Returns:
            True if cache is valid, False otherwise
        """
        with self._lock:
            return bool(self._cache and self._last_update)
    
    def get_last_update(self) -> Optional[datetime]:
        """
        Gets the timestamp of the last cache update.
        
        Returns:
            Last update timestamp or None if never updated
        """
        with self._lock:
            return self._last_update
    
    def clear(self) -> None:
        """Clears the cache."""
        with self._lock:
            self._cache.clear()
            self._last_update = None
            logger.debug("Config cache cleared")

# Global instance
_config_cache = ConfigCache()

def get_config_cache() -> ConfigCache:
    """
    Gets the global config cache instance.
    
    Returns:
        The global ConfigCache instance
    """
    return _config_cache

def init_config_cache(config: Dict[str, Any]) -> None:
    """
    Initializes the global config cache with the provided configuration.
    
    Args:
        config: The configuration dictionary to cache
    """
    _config_cache.set_config(config)
    logger.info("Global config cache initialized")

def get_cached_config() -> Dict[str, Any]:
    """
    Gets the cached configuration. Falls back to load_config() if cache is empty.
    
    Returns:
        The configuration dictionary
    """
    if _config_cache.is_valid():
        return _config_cache.get_config()
    else:
        # Fallback to loading from file
        logger.warning("Config cache is empty, falling back to load_config()")
        from utils.config_loader import load_config
        config = load_config()
        _config_cache.set_config(config)
        return config

def get_cached_servers() -> List[Dict[str, Any]]:
    """
    Gets the servers list from cache. Optimized for autocomplete.
    
    Returns:
        List of server configurations
    """
    if _config_cache.is_valid():
        return _config_cache.get_servers()
    else:
        return get_cached_config().get('servers', [])

def get_cached_guild_id() -> Optional[int]:
    """
    Gets the guild ID from cache. Optimized for autocomplete.
    
    Returns:
        Guild ID as integer or None
    """
    if _config_cache.is_valid():
        return _config_cache.get_guild_id()
    else:
        config = get_cached_config()
        guild_id_str = config.get('guild_id')
        if guild_id_str and isinstance(guild_id_str, str) and guild_id_str.isdigit():
            return int(guild_id_str)
        return None 