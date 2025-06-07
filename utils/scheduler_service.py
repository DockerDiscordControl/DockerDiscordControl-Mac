# -*- coding: utf-8 -*-
import asyncio
import logging
import time
from datetime import datetime, timedelta
import threading
from typing import Dict, List, Optional, Any
import traceback

from utils.scheduler import (
    load_tasks, 
    update_task, 
    execute_task, 
    ScheduledTask,
    find_task_by_id
)
from utils.logging_utils import setup_logger

# Logger for Scheduler Service
logger = setup_logger('ddc.scheduler_service', level=logging.DEBUG)

# Check interval in seconds
CHECK_INTERVAL = 60  # Checks every 60 seconds (much more reasonable for task scheduling)

class SchedulerService:
    """Service for managing and executing scheduled tasks."""
    
    def __init__(self):
        """Initializes the Scheduler Service."""
        self.running = False
        self.thread = None
        self.event_loop = None
        self.last_check_time = None

    def start(self):
        """Starts the Scheduler Service as a background process."""
        if self.running:
            logger.warning("Scheduler Service is already running.")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run_service)
        self.thread.daemon = True  # Daemon thread terminates when the main program ends
        self.thread.start()
        logger.info("Scheduler Service started.")
        return True
    
    def stop(self):
        """Stops the Scheduler Service."""
        if not self.running:
            logger.warning("Scheduler Service is not running.")
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)  # Wait maximum 2 seconds for thread termination
            self.thread = None
        logger.info("Scheduler Service stopped.")
        return True
    
    def _run_service(self):
        """Runs the service loop in the background."""
        # Create a new event loop for this thread
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        try:
            # Start the loop
            self.event_loop.run_until_complete(self._service_loop())
        except Exception as e:
            logger.error(f"Error in Scheduler Service loop: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.event_loop.close()
            self.event_loop = None
            self.running = False
            logger.info("Scheduler Service loop ended.")
    
    async def _service_loop(self):
        """Main loop of the service, which regularly checks and executes tasks."""
        logger.info("Scheduler Service loop started.")
        
        while self.running:
            try:
                await self._check_and_execute_tasks()
                self.last_check_time = time.time()
                
                # Wait until the next check interval
                await asyncio.sleep(CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error checking or executing tasks: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(CHECK_INTERVAL)  # Wait anyway before the next attempt
    
    async def _check_and_execute_tasks(self):
        """Checks all tasks and executes those that are due."""
        try:
            tasks = load_tasks()
            if not tasks:
                return
            
            logger.debug(f"Checking {len(tasks)} scheduled tasks")
            current_time = time.time()
            
            # Track executed tasks in this cycle to prevent re-execution
            executed_task_ids = set()
            
            # First collect all tasks to be executed
            pending_tasks = []
            for task in tasks:
                # Skip inactive tasks
                if not task.is_active:
                    continue
                    
                if not task.next_run_ts:
                    # Task has no next execution time (e.g., expired)
                    continue
                
                # Check if we already executed this task in this cycle
                if task.task_id in executed_task_ids:
                    logger.debug(f"Skipping task {task.task_id} - already executed in this cycle")
                    continue
                
                if current_time >= task.next_run_ts:
                    # Task is due and should be executed
                    logger.info(f"Task {task.task_id} ({task.container_name} {task.action}) marked for execution")
                    pending_tasks.append(task)
                    executed_task_ids.add(task.task_id)
            
            # Sort tasks by container and action for more efficient grouping
            if pending_tasks:
                # Group by container
                container_groups = {}
                for task in pending_tasks:
                    if task.container_name not in container_groups:
                        container_groups[task.container_name] = []
                    container_groups[task.container_name].append(task)
                
                # Execute tasks grouped by container
                for container_name, container_tasks in container_groups.items():
                    logger.info(f"Processing {len(container_tasks)} tasks for container '{container_name}'")
                    
                    # Sort by action - starts first, then restarts, then stops
                    action_priority = {"start": 0, "restart": 1, "stop": 2}
                    container_tasks.sort(key=lambda t: action_priority.get(t.action, 99))
                    
                    # Execute all tasks for this container sequentially
                    for task in container_tasks:
                        logger.info(f"Executing task {task.task_id} ({task.container_name} {task.action})")
                        
                        # Execute the task
                        success = await execute_task(task)
                        
                        if success:
                            logger.info(f"Task {task.task_id} executed successfully")
                            # CRITICAL: Reload the task to get the updated next_run_ts
                            updated_task = find_task_by_id(task.task_id)
                            if updated_task:
                                logger.debug(f"Task {task.task_id} next run updated from {task.next_run_ts} to {updated_task.next_run_ts}")
                        else:
                            logger.error(f"Task {task.task_id} could not be executed")
                        
                        # Short pause between tasks for the same container
                        await asyncio.sleep(1.0)
        
        except Exception as e:
            logger.error(f"Unexpected error checking tasks: {e}")
            logger.error(traceback.format_exc())

# Singleton instance of the Scheduler Service
_scheduler_service_instance = None

def get_scheduler_service() -> SchedulerService:
    """Returns the singleton instance of the Scheduler Service."""
    global _scheduler_service_instance
    if _scheduler_service_instance is None:
        _scheduler_service_instance = SchedulerService()
    return _scheduler_service_instance

def start_scheduler_service() -> bool:
    """Starts the Scheduler Service if it's not already running."""
    service = get_scheduler_service()
    return service.start()

def stop_scheduler_service() -> bool:
    """Stops the Scheduler Service if it's running."""
    service = get_scheduler_service()
    return service.stop() 