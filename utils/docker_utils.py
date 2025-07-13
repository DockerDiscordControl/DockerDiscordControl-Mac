# -*- coding: utf-8 -*-
"""
Docker utilities for container management and status retrieval
Optimized for performance with timeout handling and background processing
"""

import asyncio
import json
import subprocess
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any

# Import logging utilities
from utils.logging_utils import get_module_logger

# Configure logger for this module
logger = get_module_logger('docker_utils')

# =============================================================================
# PERFORMANCE MONITORING & DEGRADATION DETECTION
# =============================================================================

class PerformanceMonitor:
    """Monitors performance degradation and suggests preventive actions."""
    
    def __init__(self):
        self.container_performance_history = {}
        self.memory_usage_history = {}
        self.last_cleanup_time = datetime.now(timezone.utc)
        self.degradation_threshold = 2.0  # 2x slower than baseline
        
    def record_container_timing(self, container_name: str, duration_ms: float):
        """Record timing for container operations to detect degradation."""
        if container_name not in self.container_performance_history:
            self.container_performance_history[container_name] = []
        
        # Keep only last 50 measurements
        history = self.container_performance_history[container_name]
        history.append({
            'timestamp': datetime.now(timezone.utc),
            'duration_ms': duration_ms
        })
        
        if len(history) > 50:
            history.pop(0)
        
        # Check for degradation
        self._check_performance_degradation(container_name, history)
    
    def record_memory_usage(self, container_name: str, memory_mb: float):
        """Record memory usage to detect memory leaks."""
        if container_name not in self.memory_usage_history:
            self.memory_usage_history[container_name] = []
        
        history = self.memory_usage_history[container_name]
        history.append({
            'timestamp': datetime.now(timezone.utc),
            'memory_mb': memory_mb
        })
        
        # Keep only last 100 measurements (about 50 minutes at 30s intervals)
        if len(history) > 100:
            history.pop(0)
        
        # Check for memory leaks
        self._check_memory_leak(container_name, history)
    
    def _check_performance_degradation(self, container_name: str, history: list):
        """Check if container performance is degrading."""
        if len(history) < 10:
            return
        
        # Compare recent performance vs baseline
        recent_avg = sum(h['duration_ms'] for h in history[-5:]) / 5
        baseline_avg = sum(h['duration_ms'] for h in history[:10]) / 10
        
        if recent_avg > baseline_avg * self.degradation_threshold:
            logger.warning(f"PERFORMANCE DEGRADATION detected for {container_name}: "
                         f"Recent avg: {recent_avg:.1f}ms vs Baseline: {baseline_avg:.1f}ms "
                         f"({recent_avg/baseline_avg:.1f}x slower)")
            
            # Suggest preventive action
            self._suggest_preventive_action(container_name, recent_avg, baseline_avg)
    
    def _check_memory_leak(self, container_name: str, history: list):
        """Check for potential memory leaks."""
        if len(history) < 20:
            return
        
        # Check if memory usage is consistently increasing
        recent_memory = [h['memory_mb'] for h in history[-10:]]
        old_memory = [h['memory_mb'] for h in history[:10]]
        
        recent_avg = sum(recent_memory) / len(recent_memory)
        old_avg = sum(old_memory) / len(old_memory)
        
        if recent_avg > old_avg * 1.5 and recent_avg > 1000:  # 50% increase and >1GB
            logger.warning(f"MEMORY LEAK suspected for {container_name}: "
                         f"Memory increased from {old_avg:.1f}MB to {recent_avg:.1f}MB")
            
            # Suggest container restart
            self._suggest_container_restart(container_name, recent_avg)
    
    def _suggest_preventive_action(self, container_name: str, recent_avg: float, baseline_avg: float):
        """Suggest specific preventive actions based on degradation."""
        degradation_factor = recent_avg / baseline_avg
        
        if degradation_factor > 3.0:
            logger.error(f"CRITICAL degradation for {container_name}: Consider immediate restart")
        elif degradation_factor > 2.0:
            logger.warning(f"Significant degradation for {container_name}: Consider restart within 1 hour")
        
        # Container-specific recommendations
        if container_name.lower() in ['satisfactory', 'vrising', 'valheim']:
            logger.info(f"Game server {container_name} showing typical memory growth - restart recommended after 24h uptime")
    
    def _suggest_container_restart(self, container_name: str, memory_mb: float):
        """Suggest container restart for memory issues."""
        logger.warning(f"Container {container_name} using {memory_mb:.1f}MB - restart recommended")
    
    def should_trigger_cleanup(self) -> bool:
        """Check if system-wide cleanup should be triggered."""
        now = datetime.now(timezone.utc)
        hours_since_cleanup = (now - self.last_cleanup_time).total_seconds() / 3600
        
        # Trigger cleanup every 12 hours
        if hours_since_cleanup > 12:
            self.last_cleanup_time = now
            return True
        
        return False
    
    def get_performance_summary(self) -> dict:
        """Get summary of current performance status."""
        summary = {
            'containers_monitored': len(self.container_performance_history),
            'degraded_containers': [],
            'memory_issues': [],
            'recommendations': []
        }
        
        for container_name, history in self.container_performance_history.items():
            if len(history) >= 10:
                recent_avg = sum(h['duration_ms'] for h in history[-5:]) / 5
                baseline_avg = sum(h['duration_ms'] for h in history[:10]) / 10
                
                if recent_avg > baseline_avg * 1.5:
                    summary['degraded_containers'].append({
                        'name': container_name,
                        'degradation_factor': recent_avg / baseline_avg,
                        'recent_avg_ms': recent_avg,
                        'baseline_avg_ms': baseline_avg
                    })
        
        return summary

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# =============================================================================
# CONTAINER TIMEOUT CONFIGURATION
# =============================================================================

# Container-specific timeouts based on observed performance patterns
CONTAINER_TIMEOUTS = {
    'satisfactory': 15.0,  # Heavy game server
    'vrising': 15.0,       # Heavy game server  
    'v-rising': 15.0,      # Alternative naming
    'valheim': 15.0,       # Heavy game server
    'plex': 8.0,           # Media server
    'icarus': 5.0,         # Lighter game server
    'icarus2': 5.0,        # Lighter game server
    'default': 6.0         # Default for unknown containers
}

def get_container_timeout(container_name: str) -> float:
    """Get appropriate timeout for specific container."""
    container_key = container_name.lower().replace('-', '').replace('_', '')
    
    for key, timeout in CONTAINER_TIMEOUTS.items():
        if key != 'default' and key in container_key:
            return timeout
    
    return CONTAINER_TIMEOUTS['default']

# =============================================================================
# DOCKER UTILITIES WITH PERFORMANCE MONITORING  
# =============================================================================

async def get_docker_info(container_name: str) -> Optional[Dict[str, Any]]:
    """
    Gets detailed information about a Docker container.
    Optimized with container-specific timeouts.
    
    Args:
        container_name: Name of the Docker container
        
    Returns:
        Dictionary with container information or None if not found
    """
    try:
        timeout = get_container_timeout(container_name)
        
        # Run docker inspect command
        result = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                'docker', 'inspect', container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            ),
            timeout=timeout
        )
        
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            info_list = json.loads(stdout.decode())
            if info_list:
                return info_list[0]  # Return first (and only) container info
        else:
            logger.debug(f"Container '{container_name}' not found: {stderr.decode()}")
            
    except asyncio.TimeoutError:
        logger.warning(f"Timeout getting info for container '{container_name}' after {timeout}s")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON for container '{container_name}': {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting info for container '{container_name}': {e}")
    
    return None

async def get_docker_stats(container_name: str) -> Optional[Tuple[str, str]]:
    """
    Gets CPU and RAM usage statistics for a Docker container.
    Optimized with container-specific timeouts and performance monitoring.
    
    Args:
        container_name: Name of the Docker container
        
    Returns:
        Tuple of (cpu_percentage, memory_usage) as strings or None if error
    """
    start_time = time.time()
    
    try:
        timeout = get_container_timeout(container_name)
        
        # Run docker stats command with no-stream flag for single measurement
        result = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                'docker', 'stats', '--no-stream', '--format',
                'table {{.CPUPerc}}\t{{.MemUsage}}', container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            ),
            timeout=timeout
        )
        
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            lines = stdout.decode().strip().split('\n')
            if len(lines) >= 2:  # Header + data line
                data_line = lines[1].strip()
                parts = data_line.split('\t')
                
                if len(parts) >= 2:
                    cpu_perc = parts[0].strip()
                    mem_usage = parts[1].strip()
                    
                    # Record performance timing
                    elapsed_ms = (time.time() - start_time) * 1000
                    performance_monitor.record_container_timing(f"docker_stats_{container_name}", elapsed_ms)
                    
                    # Extract memory in MB for monitoring
                    try:
                        # Parse memory like "1.2GiB / 8GiB" -> extract first number and convert to MB
                        mem_parts = mem_usage.split('/')
                        if mem_parts:
                            mem_str = mem_parts[0].strip()
                            if 'GiB' in mem_str:
                                mem_gb = float(mem_str.replace('GiB', '').strip())
                                mem_mb = mem_gb * 1024
                            elif 'MiB' in mem_str:
                                mem_mb = float(mem_str.replace('MiB', '').strip())
                            else:
                                mem_mb = 0
                            
                            performance_monitor.record_memory_usage(container_name, mem_mb)
                    except:
                        pass  # Memory parsing is optional
                    
                    return (cpu_perc, mem_usage)
        else:
            logger.debug(f"Failed to get stats for container '{container_name}': {stderr.decode()}")
            
    except asyncio.TimeoutError:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning(f"Timeout getting stats for container '{container_name}' after {timeout}s ({elapsed_ms:.1f}ms)")
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"Error getting stats for container '{container_name}' after {elapsed_ms:.1f}ms: {e}")
    
    return None

async def docker_action(container_name: str, action: str) -> Tuple[bool, str]:
    """
    Performs a Docker action on a container (start, stop, restart).
    Optimized with container-specific timeouts and performance monitoring.
    
    Args:
        container_name: Name of the Docker container
        action: Action to perform ('start', 'stop', 'restart')
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    start_time = time.time()
    
    # Validate action
    valid_actions = ['start', 'stop', 'restart']
    if action not in valid_actions:
        return False, f"Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}"
    
    try:
        # Use longer timeout for actions (especially restart)
        action_timeout = get_container_timeout(container_name) * 2  # Double timeout for actions
        
        logger.info(f"Performing Docker action '{action}' on container '{container_name}'")
        
        # Run docker command
        result = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                'docker', action, container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            ),
            timeout=action_timeout
        )
        
        stdout, stderr = await result.communicate()
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        if result.returncode == 0:
            success_msg = f"Successfully {action}ed container '{container_name}'"
            logger.info(f"{success_msg} in {elapsed_ms:.1f}ms")
            
            # Record performance timing
            performance_monitor.record_container_timing(f"docker_action_{action}_{container_name}", elapsed_ms)
            
            return True, success_msg
        else:
            error_msg = f"Failed to {action} container '{container_name}': {stderr.decode().strip()}"
            logger.error(f"{error_msg} (took {elapsed_ms:.1f}ms)")
            return False, error_msg
            
    except asyncio.TimeoutError:
        elapsed_ms = (time.time() - start_time) * 1000
        timeout_msg = f"Timeout performing '{action}' on container '{container_name}' after {action_timeout}s ({elapsed_ms:.1f}ms)"
        logger.error(timeout_msg)
        return False, timeout_msg
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        error_msg = f"Unexpected error performing '{action}' on container '{container_name}' after {elapsed_ms:.1f}ms: {e}"
        logger.error(error_msg)
        return False, error_msg

# =============================================================================
# CONTAINER INSPECTION AND VALIDATION
# =============================================================================

async def container_exists(container_name: str) -> bool:
    """Check if a Docker container exists."""
    info = await get_docker_info(container_name)
    return info is not None

async def is_container_running(container_name: str) -> bool:
    """Check if a Docker container is currently running."""
    info = await get_docker_info(container_name)
    if info:
        return info.get('State', {}).get('Running', False)
    return False

# =============================================================================
# BULK OPERATIONS FOR PERFORMANCE
# =============================================================================

async def bulk_container_info(container_names: list) -> Dict[str, Optional[Dict]]:
    """Get info for multiple containers in parallel."""
    if not container_names:
        return {}
    
    # Create tasks for parallel execution
    tasks = [get_docker_info(name) for name in container_names]
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results into dictionary
    bulk_info = {}
    for container_name, result in zip(container_names, results):
        if isinstance(result, Exception):
            logger.error(f"Error getting info for {container_name}: {result}")
            bulk_info[container_name] = None
        else:
            bulk_info[container_name] = result
    
    return bulk_info

async def bulk_container_stats(container_names: list) -> Dict[str, Optional[Tuple[str, str]]]:
    """Get stats for multiple containers in parallel."""
    if not container_names:
        return {}
    
    # Create tasks for parallel execution
    tasks = [get_docker_stats(name) for name in container_names]
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results into dictionary
    bulk_stats = {}
    for container_name, result in zip(container_names, results):
        if isinstance(result, Exception):
            logger.error(f"Error getting stats for {container_name}: {result}")
            bulk_stats[container_name] = None
        else:
            bulk_stats[container_name] = result
    
    return bulk_stats
