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
