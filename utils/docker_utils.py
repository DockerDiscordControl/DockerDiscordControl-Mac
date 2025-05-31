# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any, List
import docker
import docker.client
from utils.logging_utils import setup_logger
import time
import os

# Logger for Docker utils
logger = setup_logger('ddc.docker_utils', level=logging.INFO)

# Docker client pool for improved performance
_docker_client = None
_client_last_used = 0
_CLIENT_TIMEOUT = 300  # Erhöht von 60 auf 300 Sekunden (5 Minuten)
_client_ping_cache = 0  # Cache für Ping-Ergebnisse
_PING_CACHE_TTL = 120   # Ping-Cache für 2 Minuten

async def get_docker_client():
    """
    Returns a Docker client from the pool or creates a new one.
    Optimized with reduced ping frequency and longer client lifetime.
    """
    global _docker_client, _client_last_used, _client_ping_cache
    
    current_time = time.time()
    
    # Check if we have a client and if it's still valid
    if _docker_client is not None:
        # If client was used recently, return it without ping
        if current_time - _client_last_used < _CLIENT_TIMEOUT:
            _client_last_used = current_time
            
            # Only ping if cache is expired
            if current_time - _client_ping_cache > _PING_CACHE_TTL:
                try:
                    await asyncio.to_thread(_docker_client.ping)
                    _client_ping_cache = current_time
                    logger.debug("Docker client ping successful (cached)")
                except Exception as e:
                    logger.warning(f"Docker client ping failed, recreating client: {e}")
                    _docker_client = None
                    _client_ping_cache = 0
            
            if _docker_client is not None:
                return _docker_client
    
    # Create new client if needed
    if _docker_client is None:
        logger.info(f"Creating new DockerClient with base_url='unix:///var/run/docker.sock'. Current DOCKER_HOST env: {os.environ.get('DOCKER_HOST')}")
        try:
            client_instance = await asyncio.to_thread(docker.DockerClient, base_url='unix:///var/run/docker.sock', timeout=15) # Erhöht von 10 auf 15
            logger.info("Successfully created DockerClient instance.")
            
            # Initial ping for new client
            logger.debug("Performing initial ping for new Docker client...")
            await asyncio.to_thread(client_instance.ping)
            logger.info("Successfully pinged Docker daemon.")
            
            _docker_client = client_instance
            _client_last_used = current_time
            _client_ping_cache = current_time
            return _docker_client
        except Exception as e:
            logger.error(f"Error creating (or pinging) DockerClient with base_url='unix:///var/run/docker.sock': {e}", exc_info=True)
            return None
    
    return _docker_client

async def release_docker_client():
    """Closes the current Docker client if idle for too long."""
    global _docker_client, _client_last_used
    
    if _docker_client is not None and (time.time() - _client_last_used > _CLIENT_TIMEOUT):
        try:
            await asyncio.to_thread(_docker_client.close)
            logger.info("Released Docker client due to inactivity.")
            _docker_client = None
        except Exception as e:
            logger.debug(f"Error during client release: {e}")

class DockerError(Exception):
    """Custom exception class for Docker-related errors."""
    pass

async def get_docker_stats(docker_container_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Gets CPU and memory usage for a Docker container using the SDK.

    Args:
        docker_container_name: Name of the Docker container

    Returns:
        Tuple of (CPU percentage, memory usage) or (None, None) on error
    """
    if not docker_container_name:
        return None, None

    try:
        client = await get_docker_client()
        if not client:
            logger.warning(f"get_docker_stats: Could not get Docker client for {docker_container_name}.")
            return None, None
            
        container = await asyncio.to_thread(client.containers.get, docker_container_name)
        stats = await asyncio.to_thread(container.stats, stream=False)

        cpu_usage = stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
        system_cpu_usage = stats.get('cpu_stats', {}).get('system_cpu_usage', 0)
        previous_cpu = stats.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
        previous_system = stats.get('precpu_stats', {}).get('system_cpu_usage', 0)
        
        cpu_delta = cpu_usage - previous_cpu
        system_delta = system_cpu_usage - previous_system
        
        cpu_percent = 'N/A'
        if cpu_delta > 0 and system_delta > 0:
            online_cpus = stats.get('cpu_stats', {}).get('online_cpus')
            if online_cpus is None: # Fallback for older Docker API versions or if online_cpus is not present
                percpu_usage = stats.get('cpu_stats', {}).get('cpu_usage', {}).get('percpu_usage', [1])
                online_cpus = len(percpu_usage) if percpu_usage else 1
            cpu_percent_raw = (cpu_delta / system_delta) * online_cpus * 100.0
            cpu_percent = f"{cpu_percent_raw:.2f}"
        elif stats.get('State', {}).get('Running', False):
            logger.debug(f"Could not calculate CPU percentage for {docker_container_name}. Stats: {stats}")

        memory_usage = stats.get('memory_stats', {}).get('usage', 0)
        mem_usage_str = 'N/A'
        if memory_usage > 0:
             if memory_usage < 1024 * 1024:
                 mem_usage_str = f"{memory_usage / 1024:.1f} KiB"
             elif memory_usage < 1024 * 1024 * 1024:
                 mem_usage_str = f"{memory_usage / (1024 * 1024):.1f} MiB"
             else:
                 mem_usage_str = f"{memory_usage / (1024 * 1024 * 1024):.1f} GiB"
        return cpu_percent, mem_usage_str
    except docker.errors.NotFound:
        logger.warning(f"Container '{docker_container_name}' not found during stats retrieval.")
        return None, None
    except Exception as e:
        logger.error(f"Error getting Docker stats for {docker_container_name}: {e}", exc_info=True)
        return None, None

async def get_docker_info(docker_container_name: str) -> Optional[Dict[str, Any]]:
    if not docker_container_name:
        logger.warning("get_docker_info called without container name.")
        return None
    try:
        client = await get_docker_client()
        if not client:
            logger.warning(f"get_docker_info: Could not get Docker client for {docker_container_name}.")
            return None
        container = await asyncio.to_thread(client.containers.get, docker_container_name)
        return container.attrs
    except docker.errors.NotFound:
        logger.warning(f"Container '{docker_container_name}' not found.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_docker_info for '{docker_container_name}': {e}", exc_info=True)
        return None

async def docker_action(docker_container_name: str, action: str) -> bool:
    valid_actions = {
        'start': lambda c: c.start(),
        'stop': lambda c: c.stop(),
        'restart': lambda c: c.restart(),
    }
    if action not in valid_actions:
        raise DockerError(f"Invalid Docker action: {action}")
    if not docker_container_name:
        logger.error("Docker action failed: No container name provided")
        return False
    try:
        client = await get_docker_client()
        if not client:
            logger.warning(f"docker_action: Could not get Docker client for {docker_container_name}.")
            return False
        container = await asyncio.to_thread(client.containers.get, docker_container_name)
        action_func = valid_actions[action]
        await asyncio.to_thread(action_func, container)
        logger.info(f"Docker action '{action}' on container '{docker_container_name}' successful via SDK")
        return True
    except docker.errors.NotFound:
        logger.warning(f"Container '{docker_container_name}' not found for action '{action}'.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during docker action '{action}' on '{docker_container_name}': {e}", exc_info=True)
        return False

_containers_cache = None
_cache_timestamp = 0
_CACHE_TTL = 10  # seconds

async def list_docker_containers() -> List[Dict[str, Any]]:
    try:
        client = await get_docker_client()
        if not client:
            logger.warning("list_docker_containers: Could not get Docker client.")
            return []
        raw_containers = await asyncio.to_thread(client.containers.list, all=True)
        containers = []
        for container in raw_containers:
            try:
                 image_tags = container.image.tags
                 image_name = image_tags[0] if image_tags else container.image.id[:12]
                 containers.append({
                     "id": container.short_id,
                     "name": container.name,
                     "status": container.status,
                     "image": image_name
                 })
            except docker.errors.NotFound:
                 logger.warning(f"Could not get full details for a listed container (possibly removed during listing): {container.id}")
                 continue
            except Exception as e_inner:
                 logger.warning(f"Error processing container {container.id} in list: {e_inner}")
                 continue
        return sorted(containers, key=lambda x: x.get('name', '').lower())
    except Exception as e:
        logger.error(f"Unexpected error listing Docker containers: {e}", exc_info=True)
        return []

async def is_container_exists(docker_container_name: str) -> bool:
    if not docker_container_name:
        return False
    try:
        client = await get_docker_client()
        if not client:
            logger.warning(f"is_container_exists: Could not get Docker client for {docker_container_name}.")
            return False
        await asyncio.to_thread(client.containers.get, docker_container_name)
        return True
    except docker.errors.NotFound:
        return False
    except Exception as e:
        logger.error(f"Docker error checking existence of '{docker_container_name}': {e}", exc_info=True)
        return False

async def get_containers_data() -> List[Dict[str, Any]]:
    global _containers_cache, _cache_timestamp
    current_time = time.time()
    if _containers_cache is not None and (current_time - _cache_timestamp < _CACHE_TTL):
        logger.debug("Using cached container data")
        return _containers_cache
    try:
        client = await get_docker_client()
        if not client:
            logger.warning("get_containers_data: Could not get Docker client.")
            return []
        containers_api_list = await asyncio.to_thread(client.api.containers, all=True, Lstat=True) # Use low-level API for more resilience
        result = []
        for c_data in containers_api_list:
            try:
                name = (c_data.get('Names') or ['N/A'])[0].lstrip('/') # Names can be a list
                status = c_data.get('State', 'unknown').lower()
                is_running = status == "running"
                image_name = c_data.get('Image', 'N/A')
                if '@sha256:' in image_name: # often image name is with digest
                    image_name = image_name.split('@sha256:')[0]
                
                container_info = {
                    "id": c_data.get('Id', 'N/A')[:12],
                    "name": name,
                    "status": status,
                    "running": is_running,
                    "image": image_name,
                    "created": datetime.fromtimestamp(c_data.get('Created', 0), timezone.utc).isoformat() if c_data.get('Created') else "N/A",
                }
                if is_running:
                    ports_info = c_data.get("Ports", {})
                    container_info["ports"] = ports_info
                    state_detail = c_data.get("State", {})
                    if state_detail:
                        container_info["started_at"] = state_detail.get("StartedAt", "")
                        # Health status is not directly in low-level API list, would need inspect
                        # container_info["health"] = "unknown" 
                result.append(container_info)
            except Exception as e_inner:
                logger.warning(f"Error processing individual container data for {c_data.get('Id', 'unknown_id')}: {e_inner}")
                result.append({
                    "id": c_data.get('Id', 'unknown_id')[:12],
                    "name": (c_data.get('Names') or ['error'])[0].lstrip('/'),
                    "status": "error_processing",
                    "running": False,
                    "error": str(e_inner)
                })
        sorted_result = sorted(result, key=lambda x: x.get("name", "").lower())
        _containers_cache = sorted_result
        _cache_timestamp = current_time
        return sorted_result
    except Exception as e:
        logger.error(f"Error in get_containers_data: {e}", exc_info=True)
        return []
