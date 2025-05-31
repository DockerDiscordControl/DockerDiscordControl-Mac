# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC)                                                  #
# https://ddc.bot                                                              #
# Copyright (c) 2023-2025 MAX                                                  #
# Licensed under the MIT License                                               #
# ============================================================================ #

"""
Module containing status handler functions for Docker containers.
These are implemented as a mixin class to be used with the main DockerControlCog.
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
import discord

# Import necessary utilities
from utils.logging_utils import setup_logger
from utils.docker_utils import get_docker_info, get_docker_stats
from utils.time_utils import format_datetime_with_timezone

# Import helper functions
from .control_helpers import _channel_has_permission, _get_pending_embed
from .control_ui import ControlView

# Import translation function
from .translation_manager import _

# Configure logger for this module
logger = setup_logger('ddc.status_handlers', level=logging.DEBUG)

class StatusHandlersMixin:
    """
    Mixin class containing status handler functionality for DockerControlCog.
    Handles retrieving, processing, and displaying Docker container statuses.
    """
    
    def _get_cached_translations(self, lang: str) -> dict:
        """Cached translations für bessere Performance."""
        cache_key = f"translations_{lang}"
        now = datetime.now(timezone.utc)
        
        # Cache-Invalidierung alle 5 Minuten
        if (now - self._embed_cache['last_cache_clear']).total_seconds() > self._EMBED_CACHE_TTL:
            self._embed_cache['translated_terms'].clear()
            self._embed_cache['box_elements'].clear()
            self._embed_cache['last_cache_clear'] = now
            logger.debug("Cleared embed element cache due to TTL expiration")
        
        if cache_key not in self._embed_cache['translated_terms']:
            self._embed_cache['translated_terms'][cache_key] = {
                'online_text': _("**Online**"),
                'offline_text': _("**Offline**"),
                'cpu_text': _("CPU"),
                'ram_text': _("RAM"),
                'uptime_text': _("Uptime"),
                'detail_denied_text': _("Detailed status not allowed."),
                'last_update_text': _("Last update")
            }
            logger.debug(f"Cached translations for language: {lang}")
        
        return self._embed_cache['translated_terms'][cache_key]
    
    def _get_cached_box_elements(self, display_name: str, BOX_WIDTH: int = 28) -> dict:
        """Cached box elements für bessere Performance."""
        cache_key = f"box_{display_name}_{BOX_WIDTH}"
        
        if cache_key not in self._embed_cache['box_elements']:
            header_text = f"── {display_name} "
            max_name_len = BOX_WIDTH - 4
            if len(header_text) > max_name_len:
                header_text = header_text[:max_name_len-1] + "… "
            padding_width = max(1, BOX_WIDTH - 1 - len(header_text))
            
            self._embed_cache['box_elements'][cache_key] = {
                'header_line': f"┌{header_text}{'─' * padding_width}",
                'footer_line': f"└{'─' * (BOX_WIDTH - 1)}"
            }
            logger.debug(f"Cached box elements for: {display_name}")
        
        return self._embed_cache['box_elements'][cache_key]
    
    async def get_status(self, server_config: Dict[str, Any]) -> Union[Tuple[str, bool, str, str, str, bool], Exception]:
        """
        Gets the status of a server.
        Returns: (display_name, is_running, cpu, ram, uptime, details_allowed) or Exception
        """
        docker_name = server_config.get('docker_name')
        display_name = server_config.get('name', docker_name)
        details_allowed = server_config.get('allow_detailed_status', True) # Default to True if not set

        if not docker_name:
            return ValueError(_("Missing docker_name in server configuration"))

        try:
            info = await get_docker_info(docker_name)

            if not info:
                # Container does not exist or Docker daemon is unreachable
                logger.warning(f"Container info not found for {docker_name}. Assuming offline.")
                return (display_name, False, 'N/A', 'N/A', 'N/A', details_allowed)

            is_running = info.get('State', {}).get('Running', False)
            uptime = "N/A"
            cpu = "N/A"
            ram = "N/A"

            if is_running:
                # Calculate uptime (requires the start date)
                started_at_str = info.get('State', {}).get('StartedAt')
                if started_at_str:
                    try:
                        # Adjust Docker time format (ISO 8601 with nanoseconds and Z)
                        started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        delta = now - started_at

                        days = delta.days
                        hours, remainder = divmod(delta.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        uptime_parts = []
                        if days > 0:
                            uptime_parts.append(f"{days}d")
                        if hours > 0:
                            uptime_parts.append(f"{hours}h")
                        if minutes > 0 or (days == 0 and hours == 0):
                             uptime_parts.append(f"{minutes}m")
                        uptime = " ".join(uptime_parts) if uptime_parts else "< 1m"

                    except ValueError as e:
                        logger.error(f"Could not parse StartedAt timestamp '{started_at_str}' for {docker_name}: {e}")
                        uptime = "Error"

                # Fetch CPU and RAM only if allowed
                if details_allowed:
                    stats_tuple = await get_docker_stats(docker_name)
                    if stats_tuple and isinstance(stats_tuple, tuple) and len(stats_tuple) == 2:
                         cpu_stat, ram_stat = stats_tuple
                         cpu = cpu_stat if cpu_stat is not None else 'N/A'
                         ram = ram_stat if ram_stat is not None else 'N/A'
                    else:
                         logger.warning(f"Could not retrieve valid stats tuple for running container {docker_name}")
                         cpu = "N/A"
                         ram = "N/A"
                else:
                    cpu = _("Hidden")
                    ram = _("Hidden")

            return (display_name, is_running, cpu, ram, uptime, details_allowed)

        except Exception as e:
            logger.error(f"Error getting status for {docker_name}: {e}", exc_info=True)
            return e # Return the exception itself
    
    async def _generate_status_embed_and_view(self, channel_id: int, display_name: str, server_conf: dict, current_config: dict, allow_toggle: bool, force_collapse: bool) -> tuple[Optional[discord.Embed], Optional[discord.ui.View], bool]:
        """
        Generates the status embed and view based on cache and settings.
        Returns: (embed, view, running_status)
        
        Parameters:
        - channel_id: The ID of the channel where the embed will be displayed
        - display_name: The display name of the server to show
        - server_conf: The configuration of the specific server
        - current_config: The full bot configuration
        - allow_toggle: Whether to allow the toggle button in the view
        - force_collapse: Whether to force the status to be collapsed
        """
        lang = current_config.get('language', 'de')
        timezone_str = current_config.get('timezone')
        all_servers_config = current_config.get('servers', [])

        logger.debug(f"[_GEN_EMBED] Generating embed for '{display_name}' in channel {channel_id}, lang={lang}, allow_toggle={allow_toggle}, force_collapse={force_collapse}")
        if not allow_toggle or force_collapse:
             logger.debug(f"[_GEN_EMBED_FLAGS] '{display_name}': allow_toggle={allow_toggle}, force_collapse={force_collapse}. ToggleButton/Expanded view should be suppressed.")
            
        embed = None
        view = None
        running = False # Default running state
        status_result = None
        cached_entry = self.status_cache.get(display_name)
        now = datetime.now(timezone.utc)

        # --- Check for pending action first --- (Moved before status_result processing)
        if display_name in self.pending_actions:
            pending_data = self.pending_actions[display_name]
            pending_timestamp = pending_data['timestamp']
            pending_action = pending_data['action']
            pending_duration = (now - pending_timestamp).total_seconds()
            
            # IMPROVED: Longer timeout and smarter pending logic
            PENDING_TIMEOUT_SECONDS = 120  # 2 minutes timeout instead of 15 seconds
            
            if pending_duration < PENDING_TIMEOUT_SECONDS:
                logger.debug(f"[_GEN_EMBED] '{display_name}' is in pending state (action: {pending_action} at {pending_timestamp}, duration: {pending_duration:.1f}s)")
                embed = _get_pending_embed(display_name) # Uses a standardized pending embed
                return embed, None, False # No view, running status is effectively false for pending display
            else:
                # IMPROVED: Smart timeout - check if container status actually changed based on action
                logger.info(f"[_GEN_EMBED] '{display_name}' pending timeout reached ({pending_duration:.1f}s). Checking if {pending_action} action succeeded...")
                
                # Try to get current container status to see if it changed
                current_server_conf_for_check = next((s for s in all_servers_config if s.get('name', s.get('docker_name')) == display_name), None)
                if current_server_conf_for_check:
                    fresh_status = await self.get_status(current_server_conf_for_check)
                    if not isinstance(fresh_status, Exception) and isinstance(fresh_status, tuple) and len(fresh_status) >= 2:
                        current_running_state = fresh_status[1]  # is_running is second element
                        
                        # ACTION-AWARE SUCCESS DETECTION
                        action_succeeded = False
                        if pending_action == 'start':
                            # Start succeeds when container is running
                            action_succeeded = current_running_state
                        elif pending_action == 'stop':
                            # Stop succeeds when container is NOT running
                            action_succeeded = not current_running_state
                        elif pending_action == 'restart':
                            # Restart succeeds when container is running (after stop+start cycle)
                            action_succeeded = current_running_state
                        
                        if action_succeeded:
                            logger.info(f"[_GEN_EMBED] '{display_name}' {pending_action} action succeeded - clearing pending state")
                            del self.pending_actions[display_name]
                            # Update cache with fresh status
                            self.status_cache[display_name] = {'data': fresh_status, 'timestamp': now}
                        else:
                            # Action might have failed or container takes very long
                            logger.warning(f"[_GEN_EMBED] '{display_name}' {pending_action} action did not succeed after {pending_duration:.1f}s timeout - clearing pending state")
                            del self.pending_actions[display_name]
                    else:
                        logger.warning(f"[_GEN_EMBED] '{display_name}' pending timeout - could not get fresh status, clearing pending state")
                        del self.pending_actions[display_name]
                else:
                    logger.warning(f"[_GEN_EMBED] '{display_name}' pending timeout - no server config found, clearing pending state")
                    del self.pending_actions[display_name]

        # --- Determine status_result (from cache or live) ---
        if cached_entry:
            cache_age = (now - cached_entry['timestamp']).total_seconds()
            # PERFORMANCE OPTIMIZATION: Für Toggle-Operationen verwende längere Cache-TTL
            effective_ttl = self.cache_ttl_seconds * 2 if allow_toggle else self.cache_ttl_seconds
            if cache_age < effective_ttl:
                logger.debug(f"[_GEN_EMBED] Using fresh cached status for '{display_name}' (age: {cache_age:.1f}s, TTL: {effective_ttl}s)")
            else:
                logger.debug(f"[_GEN_EMBED] Using STALE cached status for '{display_name}' (age: {cache_age:.1f}s > TTL: {effective_ttl}s)")
            status_result = cached_entry['data']
        else:
            logger.debug(f"[_GEN_EMBED] No cache entry for '{display_name}'. Fetching status directly...")
            current_server_conf_for_fetch = next((s for s in all_servers_config if s.get('name', s.get('docker_name')) == display_name), None)
            if current_server_conf_for_fetch:
                status_result = await self.get_status(current_server_conf_for_fetch)
                if not isinstance(status_result, Exception):
                    self.status_cache[display_name] = {'data': status_result, 'timestamp': now}
                    logger.debug(f"[_GEN_EMBED] Successfully fetched and cached status for '{display_name}'.")
                else:
                    logger.warning(f"[_GEN_EMBED] Error fetching live status for '{display_name}', exception stored as status_result: {status_result}")
            else:
                logger.warning(f"[_GEN_EMBED] No server configuration found for '{display_name}' during cache miss direct fetch. status_result remains None.")
                status_result = None # Explicitly None if server config not found for fetch

        # --- Process status_result and generate embed ---
        if status_result is None:
            logger.warning(f"[_GEN_EMBED] Status result for '{display_name}' is None. Server config likely not found or initial fetch failed.")
            embed = discord.Embed(
                title=f"⚠️ {display_name}", 
                description=_("Error: Could not retrieve status. Configuration for this server might be missing or an initial fetch failed."), 
                color=discord.Color.red()
            )
            # running remains False, view remains None

        elif isinstance(status_result, Exception):
            logger.error(f"[_GEN_EMBED] Status for '{display_name}' is an exception: {status_result}", exc_info=False) 
            embed = discord.Embed(
                title=f"⚠️ {display_name}", 
                description=_("Error: An exception occurred while trying to fetch status details. Please check logs."), 
                color=discord.Color.red()
            )
            # running remains False, view remains None

        elif isinstance(status_result, tuple) and len(status_result) == 6:
            # --- Valid Data: Generate Box Embed ---
            display_name_from_status, running, cpu, ram, uptime, details_allowed = status_result # 'running' is updated here
            status_color = 0x00b300 if running else 0xe74c3c
            
            # PERFORMANCE OPTIMIZATION: Verwende gecachte Übersetzungen
            cached_translations = self._get_cached_translations(lang)
            online_text = cached_translations['online_text']
            offline_text = cached_translations['offline_text']
            status_text = online_text if running else offline_text
            current_emoji = "🟢" if running else "🔴"

            # Check if we should always collapse
            is_expanded = self.expanded_states.get(display_name, False) and not force_collapse

            # PERFORMANCE OPTIMIZATION: Verwende gecachte Übersetzungen
            cpu_text = cached_translations['cpu_text']
            ram_text = cached_translations['ram_text']
            uptime_text = cached_translations['uptime_text']
            detail_denied_text = cached_translations['detail_denied_text']
            
            # PERFORMANCE OPTIMIZATION: Verwende gecachte Box-Elemente
            BOX_WIDTH = 28
            cached_box = self._get_cached_box_elements(display_name, BOX_WIDTH)
            header_line = cached_box['header_line']
            footer_line = cached_box['footer_line']
            
            # String builder for description - more efficient than multiple concatenations
            description_parts = [
                "```\n",
                header_line,
                f"\n│ {current_emoji} {status_text}"
            ]

            # Add different lines depending on status and state
            if running:
                if details_allowed and is_expanded:
                    description_parts.extend([
                        f"\n│ {cpu_text}: {cpu}",
                        f"\n│ {ram_text}: {ram}",
                        f"\n│ {uptime_text}: {uptime}",
                        f"\n{footer_line}"
                    ])
                elif not details_allowed and is_expanded:
                    description_parts.extend([
                        f"\n│ ⚠️ *{detail_denied_text}*",
                        f"\n│ {uptime_text}: {uptime}",
                        f"\n{footer_line}"
                    ])
                else:
                    description_parts.append(f"\n{footer_line}")
            else:  # Offline
                description_parts.append(f"\n{footer_line}")
            
            description_parts.append("\n```")
            
            # Combine description
            description = "".join(description_parts)

            # Use passed config
            current_server_conf = next((s for s in all_servers_config if s.get('docker_name') == server_conf.get('docker_name')), None)
            has_control_rights = False
            if current_server_conf:
                has_control_rights = any(action in current_server_conf.get('allowed_actions', []) for action in ["start", "stop", "restart"])

            if not running and not details_allowed and not has_control_rights:
                description += f"\n⚠️ *{detail_denied_text}*"

            embed = discord.Embed(description=description, color=status_color)
            now_footer = datetime.now(timezone.utc)
            last_update_text = cached_translations['last_update_text']
            current_time = format_datetime_with_timezone(now_footer, timezone_str, fmt="%H:%M:%S")
            
            # Insert timestamp above the code block
            timestamp_line = f"{last_update_text}: {current_time}"
            embed.description = f"{timestamp_line}\n{description}" # Place timestamp before the description
            
            # Adjusted footer: Only the URL now
            embed.set_footer(text=f"https://ddc.bot")
            # --- End Valid Data Embed ---
        else:
            # Fallback for any other unexpected type of status_result
            logger.error(f"[_GEN_EMBED] Unexpected data type for status_result for '{display_name}': {type(status_result)}")
            embed = discord.Embed(
                title=f"⚠️ {display_name}", 
                description=_("Internal error: Unexpected data format for server status."), 
                color=discord.Color.orange()
            )
            # running remains False, view remains None

        # --- Generate View (only if embed exists) ---
        # Embed should ideally always be set by this point due to the comprehensive handling above.
        if embed is None: # Should ideally not be reached
             logger.critical(f"[_GEN_EMBED] CRITICAL: Embed is None for '{display_name}' after all status processing. This indicates a flaw in embed generation logic.")
             embed = discord.Embed(title=f"🆘 {display_name}", description=_("Critical internal error generating status display. Please contact support or check logs immediately."), color=discord.Color.dark_red())
             view = None # No view for critical error
        elif not (isinstance(status_result, tuple) and len(status_result) == 6 and running is True): # Only add full controls if running and status is valid tuple
            # For error embeds or offline statuses, we might want a simplified or no view.
            # If status_result was an error or None, 'running' is False. If it was a valid tuple but server offline, 'running' is False.
            # For now, ControlView handles 'running' status to show appropriate buttons. If view is problematic for errors, adjust here.
            pass # Let ControlView decide based on 'running' status for now.

        # Only create ControlView if we have a valid server_conf for it and not a critical error embed
        if embed and server_conf and not (embed.title and embed.title.startswith("🆘")):
            channel_has_control = _channel_has_permission(channel_id, 'control', current_config)
            actual_server_conf = next((s for s in all_servers_config if s.get('name', s.get('docker_name')) == display_name), server_conf)
            view = ControlView(self, actual_server_conf, running, channel_has_control_permission=channel_has_control, allow_toggle=allow_toggle)
        else:
            view = None # Ensure view is None if server_conf is missing or critical error

        return embed, view, running
        
    async def send_server_status(self, channel: discord.TextChannel, server_conf: Dict[str, Any], current_config: dict, allow_toggle: bool = True, force_collapse: bool = False) -> Optional[discord.Message]:
        """
        Sends or updates status information for a server in a channel.
        ALWAYS reads from the cache and respects pending status.
        
        Parameters:
        - channel: The Discord text channel to send the message to
        - server_conf: Configuration for the specific server
        - current_config: The full bot configuration
        - allow_toggle: Whether to allow toggle button in the view
        - force_collapse: Whether to force the status to be collapsed
        
        Returns:
        - The sent/edited Discord message, or None if no message was sent/edited
        """
        display_name = server_conf.get('name', server_conf.get('docker_name'))
        if not display_name:
             logger.error("[SEND_STATUS] Server config missing name or docker_name.")
             return None
        logger.debug(f"[SEND_STATUS] Processing server '{display_name}' for channel {channel.id}, allow_toggle={allow_toggle}, force_collapse={force_collapse}")
        msg = None
        try:
            embed, view, _ = await self._generate_status_embed_and_view(channel.id, display_name, server_conf, current_config, allow_toggle, force_collapse)

            if embed:
                existing_msg_id = None
                if channel.id in self.channel_server_message_ids:
                     existing_msg_id = self.channel_server_message_ids[channel.id].get(display_name)
                should_edit = existing_msg_id is not None

                is_pending_check = display_name in self.pending_actions
                if is_pending_check:
                    logger.debug(f"[SEND_STATUS_PENDING_CHECK] Server '{display_name}' is marked as pending. Trying to { 'edit' if should_edit else 'send' } message.")

                if should_edit:
                    try:
                        existing_message = await channel.fetch_message(existing_msg_id)
                        await existing_message.edit(embed=embed, view=view if view and view.children else None)
                        msg = existing_message
                        logger.debug(f"[SEND_STATUS] Edited message {existing_msg_id} for '{display_name}' in channel {channel.id}")
                        
                        # Update last edit time
                        if channel.id not in self.last_message_update_time:
                            self.last_message_update_time[channel.id] = {}
                        self.last_message_update_time[channel.id][display_name] = datetime.now(timezone.utc)
                        
                        if is_pending_check: logger.debug(f"[SEND_STATUS_PENDING_CHECK] Successfully edited pending message for '{display_name}'.")
                    except discord.NotFound:
                         logger.warning(f"[SEND_STATUS] Message {existing_msg_id} for '{display_name}' not found. Will send new.")
                         if channel.id in self.channel_server_message_ids and display_name in self.channel_server_message_ids[channel.id]:
                              del self.channel_server_message_ids[channel.id][display_name]
                         existing_msg_id = None
                    except Exception as e:
                         logger.error(f"[SEND_STATUS] Failed to edit message {existing_msg_id} for '{display_name}': {e}", exc_info=True)
                         if is_pending_check: logger.error(f"[SEND_STATUS_PENDING_CHECK] Failed to EDIT pending message for '{display_name}'. Error: {e}")
                         existing_msg_id = None

                if not existing_msg_id:
                     try:
                          msg = await channel.send(embed=embed, view=view if view and view.children else None)
                          if channel.id not in self.channel_server_message_ids:
                               self.channel_server_message_ids[channel.id] = {}
                          self.channel_server_message_ids[channel.id][display_name] = msg.id
                          logger.info(f"[SEND_STATUS] Sent new message {msg.id} for '{display_name}' in channel {channel.id}")
                          
                          # Set last edit time for new messages
                          if channel.id not in self.last_message_update_time:
                              self.last_message_update_time[channel.id] = {}
                          self.last_message_update_time[channel.id][display_name] = datetime.now(timezone.utc)
                          
                          if is_pending_check: logger.debug(f"[SEND_STATUS_PENDING_CHECK] Successfully sent new pending message for '{display_name}'.")
                     except Exception as e:
                          logger.error(f"[SEND_STATUS] Failed to send new message for '{display_name}' in channel {channel.id}: {e}", exc_info=True)
                          if is_pending_check: logger.error(f"[SEND_STATUS_PENDING_CHECK] Failed to SEND new pending message for '{display_name}'. Error: {e}")
            else:
                logger.warning(f"[SEND_STATUS] No embed generated for '{display_name}' (likely error in helper?), cannot send/edit.")

        except Exception as e:
            logger.error(f"[SEND_STATUS] Outer error processing server '{display_name}' for channel {channel.id}: {e}", exc_info=True)
        return msg

    # Wrapper to set the update time (must accept allow_toggle)
    async def _edit_single_message_wrapper(self, channel_id: int, display_name: str, message_id: int, current_config: dict, allow_toggle: bool):
        result = await self._edit_single_message(channel_id, display_name, message_id, current_config)
        if result is True:
            now = datetime.now(timezone.utc)
            if channel_id not in self.last_message_update_time:
                self.last_message_update_time[channel_id] = {}
            self.last_message_update_time[channel_id][display_name] = now
            logger.debug(f"Updated last_message_update_time for '{display_name}' in {channel_id} to {now}")
        return result

    # Helper function for editing a single message (must accept allow_toggle)
    async def _edit_single_message(self, channel_id: int, display_name: str, message_id: int, current_config: dict) -> Union[bool, Exception, None]:
        """Edits a single status message based on cache and Pending-Status."""
        logger.debug(f"Attempting to edit message {message_id} for '{display_name}' in channel {channel_id}")
        server_conf = next((s for s in current_config.get('servers', []) if s.get('name', s.get('docker_name')) == display_name), None)
        if not server_conf:
            logger.warning(f"[_EDIT_SINGLE] Config for '{display_name}' not found during edit.")
            if channel_id in self.channel_server_message_ids and display_name in self.channel_server_message_ids[channel_id]:
                del self.channel_server_message_ids[channel_id][display_name]
            return False

        try:
            # Set flags based on channel permissions
            channel_has_control_permission = _channel_has_permission(channel_id, 'control', current_config)
            allow_toggle = channel_has_control_permission  # Only allow toggle in control channels
            force_collapse = not channel_has_control_permission # Force collapse in non-control channels

            # Pass flags to the generation function
            embed, view, _ = await self._generate_status_embed_and_view(channel_id, display_name, server_conf, current_config, allow_toggle=allow_toggle, force_collapse=force_collapse)

            if not embed:
                logger.warning(f"_edit_single_message: No embed generated for '{display_name}', cannot edit.")
                return None

            channel = await self.bot.fetch_channel(channel_id)
            if not isinstance(channel, discord.TextChannel):
                logger.warning(f"_edit_single_message: Channel {channel_id} is not a text channel.")
                if channel_id in self.channel_server_message_ids and display_name in self.channel_server_message_ids[channel_id]:
                     del self.channel_server_message_ids[channel_id][display_name]
                return TypeError(f"Channel {channel_id} not text channel")

            message_to_edit = await channel.fetch_message(message_id)

            await message_to_edit.edit(embed=embed, view=view if view and view.children else None)
            logger.info(f"_edit_single_message: Successfully edited message {message_id} for '{display_name}'")
            await asyncio.sleep(0.1) # Add a small delay to yield control
            return True # Success

        except discord.NotFound:
            logger.warning(f"_edit_single_message: Message {message_id} or Channel {channel_id} not found. Removing from cache.")
            if channel_id in self.channel_server_message_ids and display_name in self.channel_server_message_ids[channel_id]:
                del self.channel_server_message_ids[channel_id][display_name]
            return False # NotFound
        except discord.Forbidden:
            logger.error(f"_edit_single_message: Missing permissions to fetch/edit message {message_id} in channel {channel_id}.")
            return discord.Forbidden(f"Permissions error for {message_id}")
        except Exception as e:
            logger.error(f"_edit_single_message: Failed to edit message {message_id} for '{display_name}': {e}", exc_info=True)
            return e 