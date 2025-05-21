# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC)                                                  #
# https://ddc.bot                                                              #
# Copyright (c) 2023-2025 MAX                                                  #
# Licensed under the MIT License                                               #
# ============================================================================ #

import discord
from discord.ext import commands, tasks
import asyncio
import re
from datetime import datetime, timedelta, timezone
import traceback
import os
import logging
import sys
import time
import json
import random
import pytz
from typing import Dict, Any, List, Optional, Tuple, Union, Literal
import hashlib
import typing
from functools import partial

# Create a preliminary logger for the import phase
_import_logger = logging.getLogger("discord.app_commands_import")

# Conditional import of app_commands and Option
DiscordOption = None  # Ensure DiscordOption is always defined
app_commands_available = False

try:
    from discord import app_commands, Option as DiscordOptionImported
    DiscordOption = DiscordOptionImported
    app_commands_available = True
    _import_logger.debug("Imported app_commands and Option directly from discord module (PyCord style)")
except ImportError:
    _import_logger.debug("Could not import app_commands and Option from discord directly. Trying discord.ext.commands.")
    try:
        from discord.ext.commands import app_commands
        app_commands_available = True 
        # Try to get Option from discord.commands if discord.ext.commands.app_commands exists
        try:
            from discord.commands import Option as DiscordOptionImported
            DiscordOption = DiscordOptionImported
            _import_logger.debug("Imported app_commands from discord.ext.commands and Option from discord.commands")
        except ImportError:
            # DiscordOption remains None if not found here
            _import_logger.warning("Imported app_commands from discord.ext.commands, but discord.commands.Option not found.")
    except ImportError:
        _import_logger.warning("Could not import app_commands from discord.ext.commands either.")

# If app_commands could not be imported from either location, create mock versions
if not app_commands_available:
    _import_logger.warning("Could not import app_commands module from any known location, creating mock version")
    class AppCommandsMock:
        def __init__(self):
            pass
        def command(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def describe(self, **kwargs):
            def decorator(func):
                return func
            return decorator
        def autocomplete(self, **kwargs):
            def decorator(func):
                return func
            return decorator
        class Choice:
            def __init__(self, name, value):
                self.name = name
                self.value = value
    app_commands = AppCommandsMock() # Assign the mock to app_commands
    _import_logger.debug("Created mock app_commands module as fallback")

# If DiscordOption is still None (meaning it wasn't imported successfully), create a mock Option
if DiscordOption is None:
    _import_logger.warning("DiscordOption was not successfully imported, creating ActualMockOption as fallback.")
    class ActualMockOption:
        def __init__(self, actual_input_type: type, description: str = "", name: Optional[str] = None, autocomplete: Optional[Any] = None, **kwargs):
            self._actual_input_type = actual_input_type # Store the original type like <class 'str'>
            self.description = description
            # self.name is used by PyCord's Option constructor when it processes this instance
            self.name = name 
            self.autocomplete = autocomplete
            self.kwargs = kwargs

            # Set the __name__ attribute on the instance to the name of the actual input type.
            # This is for when the instance itself is passed to something expecting a __name__ (like the error showed).
            if hasattr(actual_input_type, '__name__'):
                self.__name__ = actual_input_type.__name__
            else:
                self.__name__ = str(actual_input_type) # Fallback

            logger.debug(f"ActualMockOption INSTANCE created: holds _actual_input_type={self._actual_input_type}, instance __name__='{self.__name__}', desc='{self.description}'")

        # This property is crucial. When PyCord's Option constructor (discord.commands.options.Option)
        # receives an instance of our ActualMockOption (because it was used as a type hint),
        # it will access `instance_of_our_mock.input_type`.
        # This must return the *actual class* (e.g., <class 'str'>) for SlashCommandOptionType.from_datatype.
        @property
        def input_type(self) -> type:
            return self._actual_input_type

    DiscordOption = ActualMockOption
    _import_logger.debug("Replaced DiscordOption with ActualMockOption (has .input_type property and instance.__name__) as fallback.")

# Import our utility functions
from utils.config_loader import load_config, DEFAULT_CONFIG
from utils.docker_utils import get_docker_info, get_docker_stats, docker_action
from utils.time_utils import format_datetime_with_timezone
from utils.logging_utils import setup_logger
from utils.server_order import load_server_order, save_server_order

# Import scheduler module
from utils.scheduler import (
    ScheduledTask, add_task, delete_task, update_task, load_tasks,
    get_tasks_for_container, get_next_week_tasks, get_tasks_in_timeframe,
    VALID_CYCLES, VALID_ACTIONS, DAYS_OF_WEEK,
    parse_time_string, parse_month_string, parse_weekday_string,
    CYCLE_ONCE, CYCLE_DAILY, CYCLE_WEEKLY, CYCLE_MONTHLY,
    CYCLE_NEXT_WEEK, CYCLE_NEXT_MONTH, CYCLE_CUSTOM,
    check_task_time_collision
)

# Import outsourced parts
from .translation_manager import _, get_translations
from .control_helpers import get_guild_id, container_select, _channel_has_permission, _get_pending_embed
from .control_ui import ActionButton, ToggleButton, ControlView

# Import the autocomplete handlers that have been moved to their own module
from .autocomplete_handlers import (
    schedule_container_select, schedule_action_select, schedule_cycle_select,
    schedule_time_select, schedule_month_select, schedule_weekday_select,
    schedule_day_select, schedule_info_period_select, schedule_year_select
)

# Import the schedule commands mixin that contains schedule command handlers
from .scheduler_commands import ScheduleCommandsMixin

# Import the status handlers mixin that contains status-related functionality
from .status_handlers import StatusHandlersMixin

# Import the command handlers mixin that contains Docker action command functionality 
from .command_handlers import CommandHandlersMixin

# Import central logging function
from utils.action_logger import log_user_action

# Configure logger for the cog using utility
logger = setup_logger('ddc.docker_control', level=logging.DEBUG)

# Global variable for Docker status cache to allow access from other modules
docker_status_cache = {}

class DockerControlCog(commands.Cog, ScheduleCommandsMixin, StatusHandlersMixin, CommandHandlersMixin):
    """Cog for DockerDiscordControl container management via Discord."""

    def __init__(self, bot: commands.Bot, config: dict):
        """Initializes the DockerDiscordControl Cog."""
        logger.info("Initializing DockerControlCog... [DDC-SETUP]")
        self.bot = bot
        self.config = config
        self.expanded_states = {} 
        self.channel_server_message_ids: Dict[int, Dict[str, int]] = {}
        self.last_message_update_time: Dict[int, Dict[str, datetime]] = {}
        self.initial_messages_sent = False
        self.last_channel_activity: Dict[int, datetime] = {}
        self.status_cache = {}
        self.cache_ttl_seconds = 75
        self.pending_actions: Dict[str, datetime] = {}
        self.ordered_server_names = load_server_order()
        logger.info(f"[Cog Init] Loaded server order from persistent file: {self.ordered_server_names}")
        if not self.ordered_server_names:
            if 'server_order' in config:
                logger.info("[Cog Init] Using server_order from config")
                self.ordered_server_names = config.get('server_order', [])
            else:
                logger.info("[Cog Init] No server_order found, using all server names from config")
                self.ordered_server_names = [s.get('docker_name') for s in config.get('servers', []) if s.get('docker_name')]
            save_server_order(self.ordered_server_names)
            logger.info(f"[Cog Init] Saved default server order: {self.ordered_server_names}")
        self.translations = get_translations()

        logger.info("Ensuring other potential loops (if any residues from old structure) are cancelled.")
        if hasattr(self, 'heartbeat_send_loop') and self.heartbeat_send_loop.is_running(): self.heartbeat_send_loop.cancel()
        if hasattr(self, 'status_update_loop') and self.status_update_loop.is_running(): self.status_update_loop.cancel()
        if hasattr(self, 'inactivity_check_loop') and self.inactivity_check_loop.is_running(): self.inactivity_check_loop.cancel()

        # Set up the various background loops
        logger.info("Setting up and starting background loops...")
        
        # Start status update loop (30 seconds interval)
        self.bot.loop.create_task(self._start_loop_safely(self.status_update_loop, "Status Update Loop"))
        
        # Start periodic message edit loop (1 minute interval)
        logger.info("Scheduling controlled start of DIRECTLY DEFINED periodic_message_edit_loop...")
        self.bot.loop.create_task(self._start_periodic_message_edit_loop_safely())
        
        # Start inactivity check loop (1 minute interval)
        self.bot.loop.create_task(self._start_loop_safely(self.inactivity_check_loop, "Inactivity Check Loop"))
        
        # Start heartbeat loop if enabled (1 minute interval, configurable)
        heartbeat_config = self.config.get('heartbeat', {})
        if heartbeat_config.get('enabled', False):
            self.bot.loop.create_task(self._start_loop_safely(self.heartbeat_send_loop, "Heartbeat Loop"))
        
        # Schedule initial status send with a delay
        logger.info("Re-activating AUTOMATIC INITIAL STATUS SEND.")
        self.bot.loop.create_task(self.send_initial_status_after_delay_and_ready(10))

        # Initialize global status cache
        self.update_global_status_cache()
        
        logger.info("DockerControlCog __init__ complete. Background loops and initial status send scheduled.")

    # --- PERIODIC MESSAGE EDIT LOOP (FULL LOGIC, MOVED DIRECTLY INTO COG) ---
    @tasks.loop(minutes=1, reconnect=True)
    async def periodic_message_edit_loop(self):
        logger.info("--- DIRECT COG periodic_message_edit_loop cycle --- Starting Check --- ")
        if not self.initial_messages_sent:
             logger.debug("Direct Cog Periodic edit loop: Initial messages not sent yet, skipping.")
             return

        logger.info(f"Direct Cog Periodic Edit Loop: Checking {len(self.channel_server_message_ids)} channels with tracked messages.")
        tasks_to_run = []
        now_utc = datetime.now(timezone.utc)
        
        channel_permissions_config = self.config.get('channel_permissions', {})
        # Ensure DEFAULT_CONFIG is accessible here if not already a class/instance variable
        # It was imported at the top of the file: from utils.config_loader import DEFAULT_CONFIG
        default_perms = DEFAULT_CONFIG.get('default_channel_permissions', {})

        for channel_id in list(self.channel_server_message_ids.keys()):
            if channel_id not in self.channel_server_message_ids or not self.channel_server_message_ids[channel_id]:
                logger.debug(f"Direct Cog Periodic Edit Loop: Skipping channel {channel_id}, no server messages tracked or channel entry removed.")
                continue

            channel_config = channel_permissions_config.get(str(channel_id), default_perms) 
            enable_refresh = channel_config.get('enable_auto_refresh', default_perms.get('enable_auto_refresh', True))
            update_interval_minutes = channel_config.get('update_interval_minutes', default_perms.get('update_interval_minutes', 5))
            update_interval_delta = timedelta(minutes=update_interval_minutes)

            if not enable_refresh:
                logger.debug(f"Direct Cog Periodic Edit Loop: Auto-refresh disabled for channel {channel_id}. Skipping.")
                continue

            server_messages_in_channel = self.channel_server_message_ids[channel_id]
            logger.info(f"Direct Cog Periodic Edit Loop: Processing channel {channel_id} (Refresh: {enable_refresh}, Interval: {update_interval_minutes}m). It has {len(server_messages_in_channel)} tracked messages.")

            if channel_id not in self.last_message_update_time:
                self.last_message_update_time[channel_id] = {}
                logger.info(f"Direct Cog Periodic Edit Loop: Initialized last_message_update_time for channel {channel_id}.")

            for display_name in list(server_messages_in_channel.keys()):
                if display_name not in server_messages_in_channel:
                    logger.debug(f"Direct Cog Periodic Edit Loop: Server '{display_name}' no longer tracked in channel {channel_id}. Skipping.")
                    continue
                
                message_id = server_messages_in_channel[display_name]
                last_update_time = self.last_message_update_time[channel_id].get(display_name)

                should_update = False
                if last_update_time is None:
                    should_update = True
                    logger.info(f"Direct Cog Periodic Edit Loop: Scheduling edit for '{display_name}' in channel {channel_id} (Message ID: {message_id}). Reason: No previous update time recorded.")
                elif (now_utc - last_update_time) >= update_interval_delta:
                    should_update = True
                    logger.info(f"Direct Cog Periodic Edit Loop: Scheduling edit for '{display_name}' in channel {channel_id} (Message ID: {message_id}). Reason: Interval passed (Last: {last_update_time}, Now: {now_utc}, Interval: {update_interval_delta}).")
                else:
                    time_since_last_update = now_utc - last_update_time
                    time_to_next_update = update_interval_delta - time_since_last_update
                    logger.debug(f"Direct Cog Periodic Edit Loop: Skipping edit for '{display_name}' in channel {channel_id} (Message ID: {message_id}). Interval not passed. Time since last: {time_since_last_update}. Next update in: {time_to_next_update}.")

                if should_update:
                    allow_toggle_for_channel = _channel_has_permission(channel_id, 'control', self.config)
                    # Special case for overview message
                    if display_name == "overview":
                        tasks_to_run.append(self._update_overview_message(channel_id, message_id))
                    else:
                        # Regular server message
                        tasks_to_run.append(self._edit_single_message_wrapper(channel_id, display_name, message_id, self.config, allow_toggle_for_channel))
            
        if tasks_to_run:
            logger.info(f"Direct Cog Periodic Edit Loop: Attempting to run {len(tasks_to_run)} message edit tasks.")
            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            not_found_count = sum(1 for r in results if r is False) 
            error_count = sum(1 for r in results if isinstance(r, Exception))
            none_results_count = sum(1 for r in results if r is None) 

            logger.info(f"Direct Cog Periodic message update finished. Total tasks: {len(tasks_to_run)}. Success: {success_count}, NotFound: {not_found_count}, Errors: {error_count}, NoEmbed: {none_results_count}")
            if error_count > 0:
                for i, res in enumerate(results):
                    if isinstance(res, Exception):
                        logger.error(f"Direct Cog Periodic Edit Loop: Error during message update task (Index {i}): {type(res).__name__} - {res}")
            await asyncio.sleep(0.5) 
        else:
            logger.info("Direct Cog Periodic message update check: No messages were due for update in any channel.")

    # Wrapper for editing, needs to be part of this Cog now if periodic_message_edit_loop uses it.
    async def _edit_single_message_wrapper(self, channel_id: int, display_name: str, message_id: int, current_config: dict, allow_toggle: bool):
        # This is a method of DockerControlCog that handles message editing
        result = await self._edit_single_message(channel_id, display_name, message_id, current_config) 
        
        if result is True:
            now_utc = datetime.now(timezone.utc)
            if channel_id not in self.last_message_update_time:
                self.last_message_update_time[channel_id] = {}
            self.last_message_update_time[channel_id][display_name] = now_utc
            logger.debug(f"Updated last_message_update_time for '{display_name}' in {channel_id} to {now_utc}")
            
            # Also update channel activity if configured
            channel_permissions = current_config.get('channel_permissions', {})
            channel_config_specific = channel_permissions.get(str(channel_id))
            default_recreate_enabled = DEFAULT_CONFIG.get('default_channel_permissions', {}).get('recreate_messages_on_inactivity', True)
            default_timeout_minutes = DEFAULT_CONFIG.get('default_channel_permissions', {}).get('inactivity_timeout_minutes', 10)
            recreate_enabled = default_recreate_enabled
            timeout_minutes = default_timeout_minutes
            if channel_config_specific:
                recreate_enabled = channel_config_specific.get('recreate_messages_on_inactivity', default_recreate_enabled)
                timeout_minutes = channel_config_specific.get('inactivity_timeout_minutes', default_timeout_minutes)
            if recreate_enabled and timeout_minutes > 0:
                 self.last_channel_activity[channel_id] = now_utc
                 logger.debug(f"[_EDIT_WRAPPER in COG] Updated last_channel_activity for channel {channel_id} to {now_utc} due to successful bot edit.")
        return result

    # Helper function for editing a single message, needs to be part of this Cog or accessible (e.g. from StatusHandlersMixin)
    # Assuming _edit_single_message is available via StatusHandlersMixin or also moved.
    # For clarity, if _edit_single_message was also in TaskLoopsMixin, it needs to be moved here too.
    # If it's in StatusHandlersMixin, self._edit_single_message will work if StatusHandlersMixin is inherited.
    # Based on current inheritance, StatusHandlersMixin IS inherited, so self._edit_single_message should be fine.

    async def _start_loop_safely(self, loop_task, loop_name: str):
        """Generic helper to start a task loop safely."""
        try:
            await self.bot.wait_until_ready()
            if not loop_task.is_running():
                loop_task.start()
                logger.info(f"{loop_name} started successfully via _start_loop_safely.")
            else:
                logger.info(f"{loop_name} was already running when _start_loop_safely was called (or restarted). Attempting to ensure it is running.")
                if not loop_task.is_running():
                    loop_task.start()
                    logger.info(f"{loop_name} re-started successfully via _start_loop_safely after check.")
        except Exception as e:
            logger.error(f"Error starting {loop_name} via _start_loop_safely: {e}", exc_info=True)

    async def _start_periodic_message_edit_loop_safely(self):
        await self._start_loop_safely(self.periodic_message_edit_loop, "Periodic Message Edit Loop (Direct Cog)")

    async def send_initial_status_after_delay_and_ready(self, delay_seconds: int):
        """Waits for bot readiness, then delays, then sends initial status."""
        try:
            await self.bot.wait_until_ready()
            logger.info(f"Bot is ready. Waiting {delay_seconds}s before send_initial_status.")
            await asyncio.sleep(delay_seconds)
            logger.info(f"Executing send_initial_status from __init__ after delay.")
            await self.send_initial_status()
        except Exception as e:
            logger.error(f"Error in send_initial_status_after_delay_and_ready: {e}", exc_info=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listens to messages to update channel activity for inactivity tracking."""
        if message.author.bot:  # Ignore bot messages for triggering activity
            return
        if not message.guild:  # Ignore DMs
            return

        channel_id = message.channel.id
        channel_permissions = self.config.get('channel_permissions', {})
        # Need to access DEFAULT_CONFIG correctly, it might not be directly available as self.DEFAULT_CONFIG
        # It's imported in this module
        default_perms_inactivity = DEFAULT_CONFIG.get('default_channel_permissions', {}).get('recreate_messages_on_inactivity', True)
        default_perms_timeout = DEFAULT_CONFIG.get('default_channel_permissions', {}).get('inactivity_timeout_minutes', 10)

        channel_config = channel_permissions.get(str(channel_id))

        if channel_config:  # Only if this channel has specific permissions defined
            recreate_enabled = channel_config.get('recreate_messages_on_inactivity', default_perms_inactivity)
            timeout_minutes = channel_config.get('inactivity_timeout_minutes', default_perms_timeout)

            if recreate_enabled and timeout_minutes > 0:
                now_utc = datetime.now(timezone.utc)
                logger.debug(f"[on_message] Updating last_channel_activity for channel {channel_id} to {now_utc} due to user message.")
                self.last_channel_activity[channel_id] = now_utc

    # --- STATUS HANDLERS MOVED TO status_handlers.py ---
    # All status-related functionality has been moved to the StatusHandlersMixin class in status_handlers.py
    # This includes the following methods:
    # - get_status
    # - _generate_status_embed_and_view
    # - send_server_status

    # Send helpers (remain here as they interact closely with Cog state)
    async def _send_control_panel_and_statuses(self, channel: discord.TextChannel):
        """Sends the main control panel and all server statuses to a channel."""
        config = self.config
        servers = config.get('servers', [])
        lang = config.get('language', 'de')
        logger.info(f"Sending control panel and statuses to channel {channel.name} ({channel.id})")
        # Optional: Send an initial "Control Panel" message if desired
        # await channel.send(_("**Docker Control Panel**"))

        # Get ordered server names directly from the class attribute (loaded from persistent file)
        ordered_docker_names = self.ordered_server_names
        logger.debug(f"Using ordered_server_names from class attribute: {ordered_docker_names}")
        
        # Create a dictionary for quick server lookup by docker_name
        servers_by_name = {s.get('docker_name'): s for s in servers if s.get('docker_name')}
        
        # Create an ordered list of server configurations
        ordered_servers = []
        seen_docker_names = set()
        
        # First add servers in the defined order
        for docker_name in ordered_docker_names:
            if docker_name in servers_by_name:
                ordered_servers.append(servers_by_name[docker_name])
                seen_docker_names.add(docker_name)
        
        # Add any servers that weren't in the ordered list
        for server in servers:
            docker_name = server.get('docker_name')
            if docker_name and docker_name not in seen_docker_names:
                ordered_servers.append(server)
                seen_docker_names.add(docker_name)
        
        # Fallback: If ordered_servers is empty, use all servers
        if not ordered_servers:
            ordered_servers = servers
            logger.debug("No server order found, using default order from servers list")
        
        logger.debug(f"Final ordered server list: {[s.get('name', s.get('docker_name')) for s in ordered_servers]}")

        results = []
        for server_conf in ordered_servers:
            try:
                result = await self.send_server_status(channel, server_conf, config, allow_toggle=True, force_collapse=False)
                results.append(result)
            except Exception as e:
                results.append(e)
                logger.error(f"Exception while sending status for {server_conf.get('name', server_conf.get('docker_name'))} to {channel.id}: {e}", exc_info=True)

        # Logging results (optional)
        success_count = 0
        fail_count = 0
        for i, result_item in enumerate(results):
            server_conf_log = ordered_servers[i] # Get corresponding server_conf for logging
            name = server_conf_log.get('name', server_conf_log.get('docker_name', 'Unknown'))
            if isinstance(result_item, Exception):
                fail_count += 1
                # Error already logged above if it was caught directly
            elif isinstance(result_item, discord.Message):
                success_count += 1
            else: # None or other unexpected type
                fail_count += 1
                logger.warning(f"No message object or exception returned for {name} in {channel.id}, result type: {type(result_item)}")

        logger.info(f"Finished sending initial statuses to {channel.name}: {success_count} success, {fail_count} failure.")

    async def _send_all_server_statuses(self, channel: discord.TextChannel, allow_toggle: bool = True, force_collapse: bool = False):
        """Sends or updates status messages for ALL configured servers in a channel.
        Uses send_server_status, which only reads from the cache.
        Accepts allow_toggle to control the display of the toggle button.
        """
        config = self.config
        servers = config.get('servers', [])
        lang = config.get('language', 'de')
        logger.info(f"Sending all server statuses to channel {channel.name} ({channel.id}), allow_toggle={allow_toggle}, force_collapse={force_collapse}")

        # Get ordered server names directly from the class attribute (loaded from persistent file)
        ordered_docker_names = self.ordered_server_names
        logger.debug(f"Using ordered_server_names from class attribute: {ordered_docker_names}")
        
        # Create a dictionary for quick server lookup by docker_name
        servers_by_name = {s.get('docker_name'): s for s in servers if s.get('docker_name')}
        
        # Create an ordered list of server configurations
        ordered_servers = []
        seen_docker_names = set()
        
        # First add servers in the defined order
        for docker_name in ordered_docker_names:
            if docker_name in servers_by_name:
                ordered_servers.append(servers_by_name[docker_name])
                seen_docker_names.add(docker_name)
        
        # Add any servers that weren't in the ordered list
        for server in servers:
            docker_name = server.get('docker_name')
            if docker_name and docker_name not in seen_docker_names:
                ordered_servers.append(server)
                seen_docker_names.add(docker_name)
        
        # Fallback: If ordered_servers is empty, use all servers
        if not ordered_servers:
            ordered_servers = servers
            logger.debug("No server order found, using default order from servers list")
        
        logger.debug(f"Final ordered server list: {[s.get('name', s.get('docker_name')) for s in ordered_servers]}")

        results = []
        for server_conf in ordered_servers:
            try:
                result = await self.send_server_status(channel, server_conf, config, allow_toggle, force_collapse)
                results.append(result)
            except Exception as e:
                results.append(e)
                logger.error(f"Exception while sending/updating status for {server_conf.get('name', server_conf.get('docker_name'))} to {channel.id}: {e}", exc_info=True)

        # Logging results (optional)
        success_count = 0
        fail_count = 0
        for i, result_item in enumerate(results):
            server_conf_log = ordered_servers[i] # Get corresponding server_conf for logging
            name = server_conf_log.get('name', server_conf_log.get('docker_name', 'Unknown'))
            if isinstance(result_item, Exception):
                fail_count += 1
                # Error already logged above
            elif isinstance(result_item, discord.Message):
                success_count += 1
            elif result_item is None:
                 logger.debug(f"Status for {name} likely unchanged or failed fetch, no message sent/edited.") # Adjusted log
            else:
                fail_count += 1
                logger.warning(f"Received unexpected result type {type(result_item)} for {name} in {channel.id}") # Adjusted log

        logger.info(f"Finished sending/updating statuses to {channel.name}: {success_count} success, {fail_count} failure.")

    async def _regenerate_channel(self, channel: discord.TextChannel, mode: str):
        """Deletes old bot messages and resends according to the mode."""
        try:
            logger.info(f"Regenerating channel {channel.name} ({channel.id}) in mode '{mode}'")
            if channel.id in self.channel_server_message_ids:
                del self.channel_server_message_ids[channel.id]
                logger.info(f"Cleared message ID cache for channel {channel.id}")
            await self.delete_bot_messages(channel, limit=300)
            await asyncio.sleep(1.0)
            if mode == 'control':
                await self._send_control_panel_and_statuses(channel)
            elif mode == 'status':
                # Use serverstatus format (overview message) instead of individual messages
                config = self.config
                servers = config.get('servers', [])
                
                # Sort servers using ordered_server_names
                ordered_docker_names = self.ordered_server_names
                servers_by_name = {s.get('docker_name'): s for s in servers if s.get('docker_name')}
                
                # Create ordered list of servers
                ordered_servers = []
                seen_docker_names = set()
                
                # First add servers in defined order
                for docker_name in ordered_docker_names:
                    if docker_name in servers_by_name:
                        ordered_servers.append(servers_by_name[docker_name])
                        seen_docker_names.add(docker_name)
                
                # Add any remaining servers
                for server in servers:
                    docker_name = server.get('docker_name')
                    if docker_name and docker_name not in seen_docker_names:
                        ordered_servers.append(server)
                        seen_docker_names.add(docker_name)
                
                # Create the overview embed
                embed = await self._create_overview_embed(ordered_servers, config)
                
                # Send the embed
                overview_message = await channel.send(embed=embed)
                
                # Store message ID for later updates
                if channel.id not in self.channel_server_message_ids:
                    self.channel_server_message_ids[channel.id] = {}
                self.channel_server_message_ids[channel.id]["overview"] = overview_message.id
                
                # Set last update time
                if channel.id not in self.last_message_update_time:
                    self.last_message_update_time[channel.id] = {}
                self.last_message_update_time[channel.id]["overview"] = datetime.now(timezone.utc)
                
                logger.info(f"Created overview message for channel {channel.id} during regeneration")
            logger.info(f"Regeneration for channel {channel.name} completed.")
        except Exception as e:
            logger.error(f"Error regenerating channel {channel.name}: {e}", exc_info=True)

    async def send_initial_status(self):
        """Sends the initial status messages after a short delay."""
        logger.info("[INITIAL STATUS] Starting send_initial_status... [DDC-INIT]")
        initial_send_successful = False
        try:
            await self.bot.wait_until_ready() # Ensure bot is ready before fetching channels
            
            # Directly update the cache before waiting for loops
            logger.info("[INITIAL STATUS] Running status update once to populate the cache... [DDC-INIT]")
            await self.status_update_loop()
            logger.info("[INITIAL STATUS] Initial cache update completed. [DDC-INIT]")

            # --- Added: 5-second delay ---
            wait_seconds = 5
            logger.info(f"[INITIAL STATUS] Waiting {wait_seconds} seconds for cache loop to potentially run... [DDC-INIT]")
            await asyncio.sleep(wait_seconds)
            logger.info("[INITIAL STATUS] Wait finished. Proceeding with initial status send. [DDC-INIT]")
            # --- End delay ---

            current_config = self.config
            initial_post_channels = []
            channel_permissions = current_config.get('channel_permissions', {})
            logger.debug("[INITIAL STATUS] Searching for channels with initial posting enabled... [DDC-INIT]")

            tasks = []
            for channel_id_str, data in channel_permissions.items():
                if channel_id_str.isdigit():
                    channel_id = int(channel_id_str)
                    # Check if initial posting is enabled for this channel (default to False if key missing)
                    if data.get('post_initial', False):
                        # Check permissions and determine mode
                        has_control_perm = _channel_has_permission(channel_id, 'control', current_config)
                        has_status_perm = _channel_has_permission(channel_id, 'serverstatus', current_config)
                        mode_to_regenerate = None
                        
                        if has_control_perm:
                            mode_to_regenerate = 'control'
                            logger.debug(f"Channel {channel_id} has 'control' and 'post_initial'. Mode: control.")
                        elif has_status_perm:
                            mode_to_regenerate = 'status'
                            logger.debug(f"Channel {channel_id} has 'serverstatus' and 'post_initial'. Mode: status.")
                        
                        # If a mode was determined, fetch channel and add task
                        if mode_to_regenerate:
                            try:
                                channel = await self.bot.fetch_channel(channel_id)
                                if isinstance(channel, discord.TextChannel):
                                    logger.info(f"[INITIAL STATUS] Found channel '{channel.name}' ({channel_id}) for initial post in '{mode_to_regenerate}' mode. [DDC-INIT]")
                                    tasks.append(self._regenerate_channel(channel, mode_to_regenerate))
                                else:
                                    logger.warning(f"[INITIAL STATUS] Channel ID {channel_id} is not a text channel. [DDC-INIT]")
                            except discord.NotFound:
                                logger.warning(f"[INITIAL STATUS] Channel ID {channel_id} not found. [DDC-INIT]")
                            except discord.Forbidden:
                                logger.warning(f"[INITIAL STATUS] Missing permissions to fetch channel {channel_id}. [DDC-INIT]")
                            except Exception as e:
                                logger.error(f"[INITIAL STATUS] Error processing channel {channel_id}: {e} [DDC-INIT]")
                # else: post_initial is False or missing

            if tasks:
                logger.info(f"[INITIAL STATUS] Regenerating {len(tasks)} channels... [DDC-INIT]")
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Check results for errors
                error_count = 0
                for result in results:
                    if isinstance(result, Exception):
                        error_count += 1
                        logger.error(f"[INITIAL STATUS] Error during channel regeneration: {result} [DDC-INIT]")
                if error_count == 0:
                    initial_send_successful = True
                    logger.info("[INITIAL STATUS] All initial channel regenerations completed successfully. [DDC-INIT]")
                else:
                    logger.warning(f"[INITIAL STATUS] Completed initial channel regenerations with {error_count} errors. [DDC-INIT]")
                await asyncio.sleep(0.2) # Sleep if regenerations happened
            else:
                logger.info("[INITIAL STATUS] No channels configured for initial posting. [DDC-INIT]")

        except Exception as e:
            logger.error(f"[INITIAL STATUS] Critical error during send_initial_status: {e} [DDC-INIT]", exc_info=True)
        finally:
            self.initial_messages_sent = True
            logger.info(f"[INITIAL STATUS] send_initial_status finished. Initial messages sent flag set to True. Success: {initial_send_successful} [DDC-INIT]")
            # ... (Logging at the end remains the same)

    # _update_single_message WAS REMOVED
    # _update_single_server_message_by_name WAS REMOVED

    async def delete_bot_messages(self, channel: discord.TextChannel, limit: int = 200):
        """Deletes all bot messages in a channel up to the specified limit."""
        if not isinstance(channel, discord.TextChannel):
            logger.error(f"Attempted to delete messages in non-text channel: {channel}")
            return
        logger.info(f"Deleting up to {limit} bot messages in channel {channel.name} ({channel.id})")
        try:
            # Define a check function
            def is_me(m):
                return m.author == self.bot.user

            deleted_count = 0
            async for message in channel.history(limit=limit):
                 if is_me(message):
                     try:
                         await message.delete()
                         deleted_count += 1
                         await asyncio.sleep(0.1) # Small delay for rate limiting
                     except discord.Forbidden:
                         logger.error(f"Missing permissions to delete message {message.id} in {channel.name}.")
                         break # No permission, further attempts are pointless
                     except discord.NotFound:
                         logger.warning(f"Message {message.id} already deleted in {channel.name}.")
                     except Exception as e:
                         logger.error(f"Error deleting message {message.id} in {channel.name}: {e}")

            # Alternative: channel.purge (can be faster, but less control/logging)
            # try:
            #     deleted = await channel.purge(limit=limit, check=is_me)
            #     logger.info(f"Deleted {len(deleted)} bot messages in {channel.name} ({channel.id}) using purge.")
            # except discord.Forbidden:
            #     logger.error(f"Missing permissions to purge messages in {channel.name}.")
            # except discord.HTTPException as e:
            #     logger.error(f"HTTP error during purge in {channel.name}: {e}")

            logger.info(f"Finished deleting bot messages in {channel.name}. Deleted {deleted_count} messages.")
        except Exception as e:
            logger.error(f"An error occurred during message deletion in {channel.name}: {e}", exc_info=True)

    # --- Slash Commands ---
    @commands.slash_command(name="serverstatus", description=_("Shows the status of all containers"), guild_ids=get_guild_id())
    async def serverstatus(self, ctx: discord.ApplicationContext):
        """Shows an overview of all server statuses in a single message."""
        # Import translation function locally to ensure it's accessible
        from .translation_manager import _ as translate
        
        # Check if the channel has serverstatus permission
        channel_has_status_perm = _channel_has_permission(ctx.channel.id, 'serverstatus', self.config)
        if not channel_has_status_perm:
            embed = discord.Embed(
                title=translate("⚠️ Permission Denied"),
                description=translate("You cannot use this command in this channel."),
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Respond directly without deferring first
        await ctx.respond(translate("Generating overview..."), ephemeral=True)

        config = self.config
        servers = config.get('servers', [])
        if not servers:
            embed = discord.Embed(
                title=translate("⚠️ No Servers"),
                description=translate("No servers are configured for monitoring."),
                color=discord.Color.orange()
            )
            await ctx.channel.send(embed=embed)
            return

        # --- Delete old messages --- #
        try:
            logger.info(f"[/serverstatus] Deleting old bot messages in {ctx.channel.name}...")
            await self.delete_bot_messages(ctx.channel, limit=300) # Limit adjustable
            await asyncio.sleep(1.0) # Short pause after deleting
            logger.info(f"[/serverstatus] Finished deleting messages in {ctx.channel.name}.")
        except Exception as e_delete:
            logger.error(f"[/serverstatus] Error deleting messages in {ctx.channel.name}: {e_delete}")
            # Continue even if deletion fails
        # --- End message deletion --- #

        # Sort servers using ordered_server_names
        ordered_docker_names = self.ordered_server_names
        servers_by_name = {s.get('docker_name'): s for s in servers if s.get('docker_name')}
        
        # Create an ordered list of server configurations
        ordered_servers = []
        seen_docker_names = set()
        
        # First add servers in the defined order
        for docker_name in ordered_docker_names:
            if docker_name in servers_by_name:
                ordered_servers.append(servers_by_name[docker_name])
                seen_docker_names.add(docker_name)
        
        # Add any servers that weren't in the ordered list
        for server in servers:
            docker_name = server.get('docker_name')
            if docker_name and docker_name not in seen_docker_names:
                ordered_servers.append(server)
                seen_docker_names.add(docker_name)
        
        # Fallback: If ordered_servers is empty, use all servers
        if not ordered_servers:
            ordered_servers = servers

        # Create the overview embed
        embed = await self._create_overview_embed(ordered_servers, config)
        
        # Send the embed directly to the channel instead of using followup
        overview_message = await ctx.channel.send(embed=embed)
        
        # Store the message ID for later updates
        if ctx.channel.id not in self.channel_server_message_ids:
            self.channel_server_message_ids[ctx.channel.id] = {}
        self.channel_server_message_ids[ctx.channel.id]["overview"] = overview_message.id
        
        # Set last update time for channel activity tracking
        if ctx.channel.id not in self.last_message_update_time:
            self.last_message_update_time[ctx.channel.id] = {}
        self.last_message_update_time[ctx.channel.id]["overview"] = datetime.now(timezone.utc)
        
        # Also update channel activity for inactivity checks
        self.last_channel_activity[ctx.channel.id] = datetime.now(timezone.utc)
        
        logger.info(f"[/serverstatus] Sent overview message {overview_message.id} in channel {ctx.channel.id}")

    @commands.slash_command(name="ss", description=_("Shortcut: Shows the status of all containers"), guild_ids=get_guild_id())
    async def ss(self, ctx):
        """Shortcut for the serverstatus command."""
        await self.serverstatus(ctx)

    async def command(self, ctx: discord.ApplicationContext, 
                     container_name: str, 
                     action: str):
        """
        Slash command to control a Docker container.
        
        The implementation logic has been moved to the CommandHandlersMixin class 
        in command_handlers.py. This command delegates to the _impl_command method there.
        """
        # Simply delegate to the implementation in CommandHandlersMixin
        await self._impl_command(ctx, container_name, action)

    # Decorator adjusted
    @commands.slash_command(name="help", description=_("Displays help for available commands"), guild_ids=get_guild_id())
    async def help_command(self, ctx: discord.ApplicationContext):
        """Displays help information about available commands."""
        embed = discord.Embed(
            title=_("DockerDiscordControl - Help"),
            description=_("Here are the available commands:"),
            color=discord.Color.blue()
        )
        embed.add_field(name="`/serverstatus` or `/ss`", value=_("Displays the status of all configured Docker containers."), inline=False)
        embed.add_field(name="`/command <container> <action>`", value=_("Controls a specific Docker container. Actions: `start`, `stop`, `restart`. Requires permissions."), inline=False)
        embed.add_field(name="`/control`", value=_("(Re)generates the main control panel message in channels configured for it."), inline=False)
        embed.add_field(name="`/help`", value=_("Shows this help message."), inline=False)
        embed.add_field(name="`/ping`", value=_("Checks the bot's latency."), inline=False)
        embed.set_footer(text="https://ddc.bot")

        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="ping", description=_("Shows the bot's latency"), guild_ids=get_guild_id())
    async def ping_command(self, ctx: discord.ApplicationContext):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="🏓 Pong!", description=f"{latency}ms", color=discord.Color.blurple())
        await ctx.respond(embed=embed)

    async def _create_overview_embed(self, ordered_servers, config):
        """Creates the server overview embed with the status of all servers."""
        # Import translation function locally to ensure it's accessible
        from .translation_manager import _ as translate
        
        # Create the overview embed
        embed = discord.Embed(
            title=translate("Server Overview"),
            color=discord.Color.blue()
        )

        # Build server status lines
        now_utc = datetime.now(timezone.utc)
        timezone_str = config.get('timezone')
        current_time = format_datetime_with_timezone(now_utc, timezone_str, fmt="%H:%M:%S")
        
        # Add timestamp at the top
        last_update_text = translate("Last update")
        
        # Start building the content
        content_lines = [
            f"{last_update_text}: {current_time}",
            "┌── Status ─────────────────"
        ]

        # Collect all server statuses
        for server_conf in ordered_servers:
            display_name = server_conf.get('name', server_conf.get('docker_name'))
            docker_name = server_conf.get('docker_name')
            if not display_name or not docker_name:
                continue
                
            # Get status from cache or fetch if necessary
            cached_entry = self.status_cache.get(display_name)
            status_result = None
            
            if cached_entry:
                cache_age = (now_utc - cached_entry['timestamp']).total_seconds()
                if cache_age < self.cache_ttl_seconds:
                    status_result = cached_entry['data']
                else:
                    # Stale cache, fetch new data
                    try:
                        status_result = await self.get_status(server_conf)
                        if not isinstance(status_result, Exception):
                            self.status_cache[display_name] = {'data': status_result, 'timestamp': now_utc}
                    except Exception as e:
                        logger.error(f"Error getting status for {display_name}: {e}")
            else:
                # No cache, fetch new data
                try:
                    status_result = await self.get_status(server_conf)
                    if not isinstance(status_result, Exception):
                        self.status_cache[display_name] = {'data': status_result, 'timestamp': now_utc}
                except Exception as e:
                    logger.error(f"Error getting status for {display_name}: {e}")
            
            # Process status result
            if status_result and isinstance(status_result, tuple) and len(status_result) == 6:
                _, is_running, _, _, _, _ = status_result
                
                # Determine status icon
                if display_name in self.pending_actions:
                    pending_timestamp = self.pending_actions[display_name]
                    is_pending = (now_utc - pending_timestamp).total_seconds() < 15
                    if is_pending:
                        status_emoji = "🟡"  # Yellow for pending
                        # Use "Pending" status text instead of Online/Offline
                        status_text = translate("Pending")
                    else:
                        # Clear stale pending state
                        del self.pending_actions[display_name]
                        status_emoji = "🟢" if is_running else "🔴"
                        # Normal status text based on is_running
                        status_text = translate("Online") if is_running else translate("Offline")
                else:
                    status_emoji = "🟢" if is_running else "🔴"
                    # Normal status text based on is_running
                    status_text = translate("Online") if is_running else translate("Offline")
                
                # Add status line with proper spacing
                line = f"│ {status_emoji} {status_text:8} {display_name}"
                content_lines.append(line)
            else:
                # Error or no data
                line = f"│ ⚠️ {'Error':8} {display_name}"
                content_lines.append(line)

        # Add footer line
        content_lines.append("└───────────────────────────")
        
        # Combine all lines into the description
        embed.description = "```\n" + "\n".join(content_lines) + "\n```"
        
        # Add the footer with the website URL
        embed.set_footer(text="https://ddc.bot")
        
        return embed

    # --- Heartbeat Loop ---
    @tasks.loop(minutes=1)
    async def heartbeat_send_loop(self):
        """[BETA] Sends a heartbeat signal if enabled in config.
        
        This feature is in BETA and allows the bot to send periodic heartbeat messages
        to a specified Discord channel. These messages can be monitored by an external
        script to check if the bot is still operational.
        
        The heartbeat configuration is loaded from the bot's config and can be configured
        through the web UI.
        """
        try:
            # Load the heartbeat configuration
            # First check legacy format with 'heartbeat_channel_id' at root level
            heartbeat_channel_id = self.config.get('heartbeat_channel_id')
            
            # Initialize heartbeat config with defaults
            heartbeat_config = {
                'enabled': bool(heartbeat_channel_id),  # Enabled if channel ID exists
                'method': 'channel',                    # Only channel method is implemented
                'interval': 60,                         # Default: 60 minutes 
                'channel_id': heartbeat_channel_id      # Channel ID from root config
            }
            
            # Override with nested config if it exists (new format)
            if 'heartbeat' in self.config:
                nested_config = self.config.get('heartbeat', {})
                if isinstance(nested_config, dict):
                    heartbeat_config.update(nested_config)
            
            # Check if heartbeat is enabled
            if not heartbeat_config.get('enabled', False):
                logger.debug("Heartbeat monitoring disabled in config.")
                return
    
            # Get the heartbeat method and interval
            method = heartbeat_config.get('method', 'channel')
            interval_minutes = int(heartbeat_config.get('interval', 60))
    
            # Dynamically change interval if needed
            if self.heartbeat_send_loop.minutes != interval_minutes:
                try:
                    self.heartbeat_send_loop.change_interval(minutes=interval_minutes)
                    logger.info(f"[BETA] Heartbeat interval updated to {interval_minutes} minutes.")
                except Exception as e:
                    logger.error(f"[BETA] Failed to update heartbeat interval: {e}")
    
            logger.debug("[BETA] Heartbeat loop running.")
            
            # Handle different heartbeat methods
            if method == 'channel':
                # Get the channel ID from either nested config or root config
                channel_id_str = heartbeat_config.get('channel_id') or heartbeat_channel_id
                
                if not channel_id_str:
                    logger.error("[BETA] Heartbeat method is 'channel' but no channel_id is configured.")
                    return
                    
                if not str(channel_id_str).isdigit():
                    logger.error(f"[BETA] Heartbeat channel ID '{channel_id_str}' is not a valid numeric ID.")
                    return
                
                channel_id = int(channel_id_str)
                try:
                    # Fetch the channel
                    channel = await self.bot.fetch_channel(channel_id)
                    
                    if not isinstance(channel, discord.TextChannel):
                        logger.warning(f"[BETA] Heartbeat channel ID {channel_id} is not a text channel.")
                        return
                        
                    # Send the heartbeat message with timestamp
                    timestamp = datetime.now(timezone.utc).isoformat()
                    await channel.send(_("❤️ Heartbeat signal at {timestamp}").format(timestamp=timestamp))
                    logger.info(f"[BETA] Heartbeat sent to channel {channel_id}.")
                    
                except discord.NotFound:
                    logger.error(f"[BETA] Heartbeat channel ID {channel_id} not found. Please check your configuration.")
                except discord.Forbidden:
                    logger.error(f"[BETA] Missing permissions to send heartbeat message to channel {channel_id}.")
                except discord.HTTPException as http_err:
                    logger.error(f"[BETA] HTTP error sending heartbeat to channel {channel_id}: {http_err}")
                except Exception as e:
                    logger.error(f"[BETA] Error sending heartbeat to channel {channel_id}: {e}")
            elif method == 'api':
                # API method is not implemented yet
                logger.warning("[BETA] API heartbeat method is not yet implemented.")
            else:
                logger.warning(f"[BETA] Unknown heartbeat method specified in config: '{method}'. Supported methods: 'channel'")
        except Exception as e:
            logger.error(f"[BETA] Error in heartbeat_send_loop: {e}", exc_info=True)

    @heartbeat_send_loop.before_loop
    async def before_heartbeat_loop(self):
       """Wait until the bot is ready before starting the heartbeat loop."""
       await self.bot.wait_until_ready()
       logger.info("[BETA] Heartbeat monitoring loop is ready to start.")

    # --- Status Cache Update Loop ---
    @tasks.loop(seconds=30)
    async def status_update_loop(self):
        """Periodically updates the internal status cache for all servers."""
        try:
            if not self.bot.is_ready():
                logger.warning("Bot is not ready yet, skipping status update loop iteration")
                return
                
            logger.debug("Running status_update_loop to refresh Docker container status cache")
            
            # Get server configurations
            servers = self.config.get('servers', [])
            if not servers:
                logger.debug("No servers configured, status cache update skipped")
                return
                
            # Process each server
            update_count = 0
            error_count = 0
            now = datetime.now(timezone.utc)
            
            for server_conf in servers:
                try:
                    # Get status information
                    status_data = await self.get_status(server_conf)
                    
                    # If status check was successful and not an exception
                    if not isinstance(status_data, Exception):
                        # Extract display name from the returned status data
                        display_name = status_data[0] if isinstance(status_data, tuple) and len(status_data) > 0 else server_conf.get('name', server_conf.get('docker_name'))
                        
                        # Update cache with timestamp
                        self.status_cache[display_name] = {
                            'data': status_data,
                            'timestamp': now
                        }
                        update_count += 1
                    else:
                        # Log error but don't remove from cache (keep stale data)
                        logger.error(f"Error getting status for {server_conf.get('name', server_conf.get('docker_name'))}: {status_data}")
                        error_count += 1
                except Exception as e:
                    logger.exception(f"Exception during status update for {server_conf.get('name', server_conf.get('docker_name'))}: {e}")
                    error_count += 1
            
            # Set last cache update timestamp
            self.last_cache_update = time.time()
            
            # IMPORTANT: Update the global cache after all servers are processed
            self.update_global_status_cache()
            
            logger.debug(f"Status cache updated with {update_count} success, {error_count} errors.")
        except Exception as e:
            logger.error(f"Error in status_update_loop: {e}", exc_info=True)

    @status_update_loop.before_loop
    async def before_status_update_loop(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

    # --- Inactivity Check Loop ---
    @tasks.loop(minutes=1)
    async def inactivity_check_loop(self):
        """Checks for channel inactivity and regenerates messages if configured."""
        try:
            if not self.initial_messages_sent:
                logger.debug("Inactivity check loop: Initial messages not sent yet, skipping.")
                return

            logger.debug("Inactivity check loop running")
            
            # Get channel permissions from config
            channel_permissions = self.config.get('channel_permissions', {})
            default_recreate_enabled = DEFAULT_CONFIG.get('default_channel_permissions', {}).get('recreate_messages_on_inactivity', True)
            default_timeout_minutes = DEFAULT_CONFIG.get('default_channel_permissions', {}).get('inactivity_timeout_minutes', 10)
            now_utc = datetime.now(timezone.utc)
            
            # Check each channel we've previously registered activity for
            for channel_id, last_activity_time in list(self.last_channel_activity.items()):
                channel_config = channel_permissions.get(str(channel_id))
                
                # Skip channels with no config or recreate disabled
                if not channel_config:
                    continue
                    
                recreate_enabled = channel_config.get('recreate_messages_on_inactivity', default_recreate_enabled)
                timeout_minutes = channel_config.get('inactivity_timeout_minutes', default_timeout_minutes)
                
                if not recreate_enabled or timeout_minutes <= 0:
                    logger.debug(f"Inactivity check for channel {channel_id}: recreate_enabled={recreate_enabled}, timeout_minutes={timeout_minutes}. Skipping.")
                    continue
                    
                # Calculate time since last activity
                time_since_last_activity = now_utc - last_activity_time
                inactivity_threshold = timedelta(minutes=timeout_minutes)
                
                # Check if we've passed the inactivity threshold
                if time_since_last_activity >= inactivity_threshold:
                    logger.info(f"Channel {channel_id} has been inactive for {time_since_last_activity}, threshold is {inactivity_threshold}. Attempting regeneration.")
                    
                    try:
                        # Fetch the Discord channel
                        channel = await self.bot.fetch_channel(channel_id)
                        
                        if not isinstance(channel, discord.TextChannel):
                            logger.warning(f"Channel {channel_id} is not a text channel, removing from activity tracking.")
                            del self.last_channel_activity[channel_id]
                            continue
                            
                        # Check the last message to confirm inactivity
                        history = await channel.history(limit=1).flatten()
                        if history and history[0].author.id == self.bot.user.id:
                            # If the last message is from our bot, we should not regenerate
                            # Reset the timer instead, since the bot was the last to post
                            self.last_channel_activity[channel_id] = now_utc
                            logger.debug(f"Last message in channel {channel.name} ({channel_id}) is from the bot, resetting inactivity timer.")
                            continue
                            
                        # Determine the mode: control or status
                        has_control_permission = _channel_has_permission(channel_id, 'control', self.config)
                        regeneration_mode = 'control' if has_control_permission else 'status'
                        
                        # Attempt channel regeneration
                        await self._regenerate_channel(channel, regeneration_mode)
                        
                        # Reset activity timer
                        self.last_channel_activity[channel_id] = now_utc
                        logger.info(f"Channel {channel.name} ({channel_id}) regenerated due to inactivity. Mode: {regeneration_mode}")
                        
                    except discord.NotFound:
                        logger.warning(f"Channel {channel_id} not found. Removing from activity tracking.")
                        del self.last_channel_activity[channel_id]
                    except discord.Forbidden:
                        logger.error(f"Cannot access channel {channel_id} (forbidden). Continuing tracking but regeneration not possible.")
                    except Exception as e:
                        logger.error(f"Error during inactivity check for channel {channel_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error in inactivity_check_loop: {e}", exc_info=True)

    @inactivity_check_loop.before_loop
    async def before_inactivity_check_loop(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

    # --- Final Control Command ---
    @commands.slash_command(name="control", description=_("Displays the control panel in the control channel"), guild_ids=get_guild_id())
    async def control_command(self, ctx: discord.ApplicationContext):
        """(Re)generates the control panel message in the current channel if permitted."""
        if not ctx.channel or not isinstance(ctx.channel, discord.TextChannel):
            await ctx.respond(_("This command can only be used in server channels."), ephemeral=True)
            return

        if not _channel_has_permission(ctx.channel.id, 'control', self.config):
            await ctx.respond(_("You do not have permission to use this command in this channel, or control panels are disabled here."), ephemeral=True)
            return

        await ctx.defer(ephemeral=False)
        logger.info(f"Control panel regeneration requested by {ctx.author} in {ctx.channel.name}")

        try:
            await ctx.followup.send(_("Regenerating control panel... Please wait."), ephemeral=True)
        except Exception as e_followup:
            logger.error(f"Error sending initial followup for /control command: {e_followup}")

        channel_to_regenerate = ctx.channel
        async def run_regeneration():
            try:
                await self._regenerate_channel(channel_to_regenerate, 'control')
                logger.info(f"Background regeneration for channel {channel_to_regenerate.name} completed.")
            except Exception as e_regen:
                logger.error(f"Error during background regeneration for channel {channel_to_regenerate.name}: {e_regen}")

        self.bot.loop.create_task(run_regeneration())
        
    # --- SCHEDULE COMMANDS ---
    @commands.slash_command(name="schedule_once", description=_("Schedule a one-time task"), guild_ids=get_guild_id())
    async def schedule_once_command(self, ctx: discord.ApplicationContext, 
                              container_name: str = discord.Option(description=_("The Docker container to schedule"), autocomplete=container_select),
                              action: str = discord.Option(description=_("Action to perform"), autocomplete=schedule_action_select),
                              time: str = discord.Option(description=_("Time in HH:MM format (e.g., 14:30)"), autocomplete=schedule_time_select),
                              day: str = discord.Option(description=_("Day of month (e.g., 15)"), autocomplete=schedule_day_select),
                              month: str = discord.Option(description=_("Month (e.g., 07 or July)"), autocomplete=schedule_month_select),
                              year: str = discord.Option(description=_("Year (e.g., 2024)"), autocomplete=schedule_year_select)):
        """Schedules a one-time task for a Docker container."""
        await self._impl_schedule_once_command(ctx, container_name, action, time, day, month, year)
    
    @commands.slash_command(name="schedule_daily", description=_("Schedule a daily task"), guild_ids=get_guild_id())
    async def schedule_daily_command(self, ctx: discord.ApplicationContext, 
                              container_name: str = discord.Option(description=_("The Docker container to schedule"), autocomplete=container_select),
                              action: str = discord.Option(description=_("Action to perform"), autocomplete=schedule_action_select),
                              time: str = discord.Option(description=_("Time in HH:MM format (e.g., 08:00)"), autocomplete=schedule_time_select)):
        """Schedules a daily task for a Docker container."""
        await self._impl_schedule_daily_command(ctx, container_name, action, time)
    
    @commands.slash_command(name="schedule_weekly", description=_("Schedule a weekly task"), guild_ids=get_guild_id())
    async def schedule_weekly_command(self, ctx: discord.ApplicationContext, 
                              container_name: str = discord.Option(description=_("The Docker container to schedule"), autocomplete=container_select),
                              action: str = discord.Option(description=_("Action to perform"), autocomplete=schedule_action_select),
                              time: str = discord.Option(description=_("Time in HH:MM format"), autocomplete=schedule_time_select),
                              weekday: str = discord.Option(description=_("Day of the week (e.g., Monday or 1)"), autocomplete=schedule_weekday_select)):
        """Schedules a weekly task for a Docker container."""
        await self._impl_schedule_weekly_command(ctx, container_name, action, time, weekday)
    
    @commands.slash_command(name="schedule_monthly", description=_("Schedule a monthly task"), guild_ids=get_guild_id())
    async def schedule_monthly_command(self, ctx: discord.ApplicationContext, 
                              container_name: str = discord.Option(description=_("The Docker container to schedule"), autocomplete=container_select),
                              action: str = discord.Option(description=_("Action to perform"), autocomplete=schedule_action_select),
                              time: str = discord.Option(description=_("Time in HH:MM format"), autocomplete=schedule_time_select),
                              day: str = discord.Option(description=_("Day of the month (1-31)"), autocomplete=schedule_day_select)):
        """Schedules a monthly task for a Docker container."""
        await self._impl_schedule_monthly_command(ctx, container_name, action, time, day)
    
    @commands.slash_command(name="schedule_yearly", description=_("Schedule a yearly task"), guild_ids=get_guild_id())
    async def schedule_yearly_command(self, ctx: discord.ApplicationContext, 
                              container_name: str = discord.Option(description=_("The Docker container to schedule"), autocomplete=container_select),
                              action: str = discord.Option(description=_("Action to perform"), autocomplete=schedule_action_select),
                              time: str = discord.Option(description=_("Time in HH:MM format"), autocomplete=schedule_time_select),
                              month: str = discord.Option(description=_("Month (e.g., 07 or July)"), autocomplete=schedule_month_select),
                              day: str = discord.Option(description=_("Day of month (e.g., 15)"), autocomplete=schedule_day_select)):
        """Schedules a yearly task for a Docker container."""
        await self._impl_schedule_yearly_command(ctx, container_name, action, time, month, day)
    
    @commands.slash_command(name="schedule", description=_("Shows schedule command help"), guild_ids=get_guild_id())
    async def schedule_command(self, ctx: discord.ApplicationContext):
        """Shows help for the various scheduling commands."""
        await self._impl_schedule_command(ctx)
    
    @commands.slash_command(name="schedule_info", description=_("Shows information about scheduled tasks"), guild_ids=get_guild_id())
    async def schedule_info_command(self, ctx: discord.ApplicationContext,
                                  container_name: str = discord.Option(description=_("Container name (or 'all')"), default="all", autocomplete=container_select),
                                  period: str = discord.Option(description=_("Time period (e.g., next_week)"), default="all", autocomplete=schedule_info_period_select)):
        """Shows information about scheduled tasks."""
        await self._impl_schedule_info_command(ctx, container_name, period)

    # --- SCHEDULE COMMANDS MOVED TO scheduler_commands.py ---
    # All schedule related implementation logic has been moved to 
    # the ScheduleCommandsMixin class in scheduler_commands.py.
    # The command definitions remain here in DockerControlCog for proper registration,
    # but they delegate their actual implementation to methods in the mixin.
    # This includes the following implementation methods:
    # - _format_schedule_embed
    # - _create_scheduled_task
    # - _impl_schedule_once_command
    # - _impl_schedule_daily_command
    # - _impl_schedule_weekly_command
    # - _impl_schedule_monthly_command
    # - _impl_schedule_yearly_command
    # - _impl_schedule_command
    # - _impl_schedule_info_command

    # --- Cog Teardown ---
    def cog_unload(self):
        """Cancel all running background tasks when the cog is unloaded."""
        logger.info("Unloading DockerControlCog, cancelling tasks...")
        if hasattr(self, 'heartbeat_send_loop') and self.heartbeat_send_loop.is_running(): self.heartbeat_send_loop.cancel()
        if hasattr(self, 'status_update_loop') and self.status_update_loop.is_running(): self.status_update_loop.cancel()
        if hasattr(self, 'periodic_message_edit_loop') and self.periodic_message_edit_loop.is_running(): self.periodic_message_edit_loop.cancel()
        if hasattr(self, 'inactivity_check_loop') and self.inactivity_check_loop.is_running(): self.inactivity_check_loop.cancel()
        logger.info("All direct Cog loops cancellation attempted.")

    # Method to update global docker status cache from instance cache
    def update_global_status_cache(self):
        """Updates the global docker_status_cache from the instance's status_cache."""
        global docker_status_cache
        try:
            # Copy the instance cache to the global variable
            docker_status_cache = self.status_cache.copy()
            logger.debug(f"Updated global docker_status_cache with {len(docker_status_cache)} entries")
        except Exception as e:
            logger.error(f"Error updating global docker_status_cache: {e}")

    # Accessor method to get the current status cache
    def get_status_cache(self) -> Dict[str, Any]:
        """Returns the current status cache."""
        return self.status_cache.copy()

    async def _update_overview_message(self, channel_id: int, message_id: int) -> bool:
        """Updates the overview message with current server statuses."""
        logger.debug(f"Updating overview message {message_id} in channel {channel_id}")
        try:
            # Get channel
            channel = await self.bot.fetch_channel(channel_id)
            if not isinstance(channel, discord.TextChannel):
                logger.warning(f"Channel {channel_id} is not a text channel, cannot update overview.")
                return False
                
            # Get message
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                logger.warning(f"Overview message {message_id} in channel {channel_id} not found. Removing from tracking.")
                if channel_id in self.channel_server_message_ids and "overview" in self.channel_server_message_ids[channel_id]:
                    del self.channel_server_message_ids[channel_id]["overview"]
                return False
                
            # Get all servers
            config = self.config
            servers = config.get('servers', [])
            
            # Sort servers
            ordered_docker_names = self.ordered_server_names
            servers_by_name = {s.get('docker_name'): s for s in servers if s.get('docker_name')}
            
            ordered_servers = []
            seen_docker_names = set()
            
            # First add servers in the defined order
            for docker_name in ordered_docker_names:
                if docker_name in servers_by_name:
                    ordered_servers.append(servers_by_name[docker_name])
                    seen_docker_names.add(docker_name)
            
            # Add any servers that weren't in the ordered list
            for server in servers:
                docker_name = server.get('docker_name')
                if docker_name and docker_name not in seen_docker_names:
                    ordered_servers.append(server)
                    seen_docker_names.add(docker_name)
            
            # Create the updated embed
            embed = await self._create_overview_embed(ordered_servers, config)
            
            # Update the message
            await message.edit(embed=embed)
            
            # Update timestamp
            now_utc = datetime.now(timezone.utc)
            if channel_id not in self.last_message_update_time:
                self.last_message_update_time[channel_id] = {}
            self.last_message_update_time[channel_id]["overview"] = now_utc
            
            # Also update channel activity
            self.last_channel_activity[channel_id] = now_utc
            
            logger.debug(f"Successfully updated overview message {message_id} in channel {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating overview message in channel {channel_id}: {e}", exc_info=True)
            return False