# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC) - Performance Monitor                            #
# https://ddc.bot                                                              #
# Copyright (c) 2023-2025 MAX                                                  #
# Licensed under the MIT License                                               #
# ============================================================================ #

"""
Performance monitoring system for DockerDiscordControl.
Monitors optimizations, collects statistics and identifies bottlenecks.
"""

import os
from typing import Dict, Any, List, Optional
from utils.logging_utils import get_module_logger
from utils.time_utils import get_datetime_imports, format_duration, get_utc_timestamp
from utils.import_utils import get_performance_imports, safe_import

# Central datetime imports
datetime, timedelta, timezone, time = get_datetime_imports()

logger = get_module_logger('performance_monitor')

# Optional psutil import
psutil, _psutil_available = safe_import('psutil')
if not _psutil_available:
    logger.info("psutil not available - system metrics will be disabled")

class PerformanceMonitor:
    """Central class for performance monitoring"""
    
    def __init__(self):
        self.start_time = get_utc_timestamp()
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'docker_api_calls': 0,
            'toggle_operations': 0,
            'fast_toggles': 0,
            'slow_operations': [],
            'memory_usage': [],
            'cpu_usage': []
        }
        self.performance_imports = get_performance_imports()
        
    def record_cache_hit(self, cache_type: str = 'general'):
        """Records a cache hit"""
        self.metrics['cache_hits'] += 1
        logger.debug(f"Cache hit recorded for {cache_type}")
        
    def record_cache_miss(self, cache_type: str = 'general'):
        """Records a cache miss"""
        self.metrics['cache_misses'] += 1
        logger.debug(f"Cache miss recorded for {cache_type}")
        
    def record_docker_api_call(self, operation: str, duration: float):
        """Records a Docker API call"""
        self.metrics['docker_api_calls'] += 1
        if duration > 2.0:  # Slow operations (>2s)
            self.metrics['slow_operations'].append({
                'operation': f"docker_{operation}",
                'duration': duration,
                'timestamp': get_utc_timestamp()
            })
        logger.debug(f"Docker API call: {operation} took {duration:.2f}s")
        
    def record_toggle_operation(self, duration: float, was_fast: bool = True):
        """Records a toggle operation"""
        self.metrics['toggle_operations'] += 1
        if was_fast:
            self.metrics['fast_toggles'] += 1
        
        if duration > 0.5:  # Slow toggle operations (>500ms)
            self.metrics['slow_operations'].append({
                'operation': 'toggle',
                'duration': duration,
                'timestamp': get_utc_timestamp(),
                'was_fast': was_fast
            })
        logger.debug(f"Toggle operation took {duration:.3f}s (fast: {was_fast})")
        
    def record_system_metrics(self):
        """Records system metrics"""
        if not _psutil_available:
            logger.debug("psutil not available - skipping system metrics")
            return
            
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].append({
                'timestamp': get_utc_timestamp(),
                'percent': memory.percent,
                'available_mb': memory.available // (1024 * 1024)
            })
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].append({
                'timestamp': get_utc_timestamp(),
                'percent': cpu_percent
            })
            
            # Keep only the last 100 entries
            if len(self.metrics['memory_usage']) > 100:
                self.metrics['memory_usage'] = self.metrics['memory_usage'][-100:]
            if len(self.metrics['cpu_usage']) > 100:
                self.metrics['cpu_usage'] = self.metrics['cpu_usage'][-100:]
                
        except Exception as e:
            logger.warning(f"Failed to record system metrics: {e}")
            
    def get_cache_efficiency(self) -> float:
        """Calculates cache efficiency"""
        total_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total_requests == 0:
            return 0.0
        return (self.metrics['cache_hits'] / total_requests) * 100
        
    def get_toggle_efficiency(self) -> float:
        """Calculates toggle efficiency"""
        total_toggles = self.metrics['toggle_operations']
        if total_toggles == 0:
            return 0.0
        return (self.metrics['fast_toggles'] / total_toggles) * 100
        
    def get_uptime(self) -> str:
        """Returns formatted uptime"""
        uptime_seconds = get_utc_timestamp() - self.start_time
        return format_duration(uptime_seconds)
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        # Monitor system performance metrics for optimization
        uptime = get_utc_timestamp() - self.start_time
        
        # Analyze cache efficiency and hit ratios
        cache_hits = sum(self.metrics['cache_hits'])
        cache_misses = sum(self.metrics['cache_misses'])
        total_requests = cache_hits + cache_misses
        cache_efficiency = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # eXamine Docker API call performance
        api_calls = self.metrics['docker_api_calls']
        avg_api_duration = sum(call['duration'] for call in api_calls) / len(api_calls) if api_calls else 0
        
        # Determine toggle operation performance
        toggle_ops = self.metrics['toggle_operations']
        avg_toggle_duration = sum(op['duration'] for op in toggle_ops) / len(toggle_ops) if toggle_ops else 0
        
        # Detect performance library availability
        performance_imports = get_performance_imports()
        
        # Collect system resource information
        system_info = self._get_system_info()
        
        return {
            'uptime': format_duration(uptime),
            'cache_efficiency': f"{cache_efficiency:.1f}%",
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'avg_api_duration': f"{avg_api_duration:.3f}s",
            'avg_toggle_duration': f"{avg_toggle_duration:.3f}s",
            'performance_imports': {name: info['available'] for name, info in performance_imports.items()},
            'system_info': system_info,
            'optimization_recommendations': self._get_optimization_recommendations()
        }
        
    def log_performance_report(self):
        """Logs a detailed performance report"""
        summary = self.get_performance_summary()
        
        logger.info("=== PERFORMANCE REPORT ===")
        logger.info(f"Uptime: {summary['uptime']}")
        logger.info(f"Cache Efficiency: {summary['cache_efficiency']}")
        logger.info(f"Toggle Efficiency: {summary['toggle_efficiency']}")
        logger.info(f"Total Cache Requests: {summary['total_cache_requests']}")
        logger.info(f"Total Docker API Calls: {summary['total_docker_calls']}")
        logger.info(f"Total Toggle Operations: {summary['total_toggles']}")
        logger.info(f"Slow Operations: {summary['slow_operations_count']}")
        
        logger.info("Performance Optimizations:")
        for name, available in summary['performance_imports'].items():
            status = "ENABLED" if available else "DISABLED"
            logger.info(f"  {name}: {status}")
            
        # Log recent slow operations
        recent_slow = [op for op in self.metrics['slow_operations'] 
                      if get_utc_timestamp() - op['timestamp'] < 3600]  # Last hour
        if recent_slow:
            logger.warning(f"Recent slow operations ({len(recent_slow)}):")
            for op in recent_slow[-5:]:  # Last 5
                logger.warning(f"  {op['operation']}: {op['duration']:.2f}s")
                
    def get_optimization_recommendations(self) -> List[str]:
        """Returns optimization recommendations"""
        recommendations = []
        
        # Check cache efficiency
        cache_eff = self.get_cache_efficiency()
        if cache_eff < 80:
            recommendations.append(f"Cache efficiency is low ({cache_eff:.1f}%). Consider longer cache TTLs.")
            
        # Check toggle efficiency
        toggle_eff = self.get_toggle_efficiency()
        if toggle_eff < 90:
            recommendations.append(f"Toggle efficiency is low ({toggle_eff:.1f}%). Check Docker API performance.")
            
        # Check performance imports
        for name, info in self.performance_imports.items():
            if not info['available']:
                recommendations.append(f"Install {name} for better performance: {info['description']}")
                
        # Check slow operations
        recent_slow = len([op for op in self.metrics['slow_operations'] 
                          if get_utc_timestamp() - op['timestamp'] < 3600])
        if recent_slow > 10:
            recommendations.append(f"Many slow operations ({recent_slow}) in the last hour. Check system performance.")
            
        return recommendations

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Returns the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        logger.info("Performance monitor initialized")
    return _performance_monitor

# Convenience functions for easy usage
def record_cache_hit(cache_type: str = 'general'):
    """Records a cache hit"""
    get_performance_monitor().record_cache_hit(cache_type)

def record_cache_miss(cache_type: str = 'general'):
    """Records a cache miss"""
    get_performance_monitor().record_cache_miss(cache_type)

def record_docker_api_call(operation: str, duration: float):
    """Records a Docker API call"""
    get_performance_monitor().record_docker_api_call(operation, duration)

def record_toggle_operation(duration: float, was_fast: bool = True):
    """Records a toggle operation"""
    get_performance_monitor().record_toggle_operation(duration, was_fast)

def log_performance_report():
    """Logs a performance report"""
    get_performance_monitor().log_performance_report()

def get_optimization_recommendations() -> List[str]:
    """Returns optimization recommendations"""
    return get_performance_monitor().get_optimization_recommendations() 