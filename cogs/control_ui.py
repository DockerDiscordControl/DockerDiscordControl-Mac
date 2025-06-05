# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC)                                                  #
# https://ddc.bot                                                              #
# Copyright (c) 2023-2025 MAX                                                  #
# Licensed under the MIT License                                               #
# ============================================================================ #

import discord
from discord.ui import View, Button, Select
from discord import Interaction, ButtonStyle, SelectOption
import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
import sys
import time
import os

# Import helper functions and types
from utils.config_loader import load_config
from utils.config_cache import get_cached_config  # Performance optimization
from utils.docker_utils import docker_action
from .translation_manager import _, get_translations # Import translation functions
from .control_helpers import _channel_has_permission, _get_pending_embed # Import permission helper
# Import the time utility function (replaces the old import)
from utils.time_utils import format_datetime_with_timezone
from utils.logging_utils import setup_logger # <<< Import hinzugefügt
# Importiere die zentrale log_user_action Funktion aus dem neuen Modul
from utils.action_logger import log_user_action

# Setup standard logger for this module
logger = setup_logger('ddc.control_ui', level=logging.DEBUG)

# Get the action logger instance (it must be configured elsewhere, e.g., web_ui or bot.py)
user_action_logger = logging.getLogger('user_actions')

# Constants
INTERACTION_TIMEOUT = 180.0 # 3 minutes for view timeout
PENDING_TIMEOUT_SECONDS = 120 # How long before a pending state times out

# --- UI Classes ---
class ActionButton(Button):
    """Button for Start, Stop, Restart actions."""
    # Type hint for cog_instance
    cog: 'DockerControlCog'

    def __init__(self, cog_instance: 'DockerControlCog', server_config: dict, action: str, style: discord.ButtonStyle, label: str, emoji: str, row: int):
        self.cog = cog_instance # Store reference to the Cog
        self.docker_name = server_config.get('docker_name')
        self.display_name = server_config.get('name', self.docker_name)
        self.action = action

        # Use passed values instead of redefining them here
        # (The logic to determine label/style/emoji should be in the calling code,
        # e.g., in ControlView, to maintain consistency)

        super().__init__(label=None, style=style, custom_id=f"action_{action}_{self.docker_name}", row=row, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        """Executes the Docker action and sets/shows pending status."""
        user = interaction.user
        channel = interaction.channel

        logger.info(f"[ACTION_BTN] Action '{self.action}' for '{self.display_name}' triggered by {user.name} in channel {channel.name if channel else 'N/A'}.")

        # Log to user_actions.log using the centralized function
        try:
            log_user_action(
                action="COMMAND", 
                target=f"{self.display_name} ({self.action})", 
                user=str(user), 
                source="Discord Button", 
                details=f"Channel: {channel.name if channel else 'N/A'}"
            )
        except Exception as log_e:
             logger.error(f"Failed to write to action log in ActionButton callback: {log_e}")

        try:
            # --- FIX: Defer interaction IMMEDIATELY --- #
            await interaction.response.defer(ephemeral=False)
            logger.info(f"[BUTTON_CALLBACK_DEFERRED] Action '{self.action}' for '{self.display_name}' deferred successfully.")

            # --- Proceed with original logic (Ensure this is INSIDE the try block) --- #
            current_config = get_cached_config()  # Performance optimization: use cache instead of load_config()
            if not interaction.channel:
                logger.error(f"[BUTTON] Channel not found for interaction from {interaction.user}")
                return

            # Permission checks
            channel_has_control = _channel_has_permission(interaction.channel.id, 'control', current_config)
            if not channel_has_control:
                logger.warning(f"Action button {self.action} for {self.display_name} clicked in channel {interaction.channel.name} ({interaction.channel.id}) by {interaction.user} without control permission.")
                await interaction.followup.send(_("This action is not allowed in this channel."), ephemeral=True)
                return

            # Server config check (Ensure correct indentation)
            servers_config = current_config.get('servers', [])
            server_conf = next((s for s in servers_config if s.get('docker_name') == self.docker_name), None)
            if not server_conf:
                logger.error(f"[BUTTON] Server configuration for {self.display_name} not found.")
                await interaction.followup.send(_("Error: Server configuration for {server_name} not found.").format(server_name=self.display_name), ephemeral=True)
                return

            # Allowed action check (Ensure correct indentation)
            allowed_actions = server_conf.get('allowed_actions', [])
            if self.action not in allowed_actions:
                logger.warning(f"Action '{self.action}' not allowed for {self.display_name} (requested by {interaction.user}).")
                await interaction.followup.send(_("Error: Action '{action}' is not allowed for {server_name}.").format(action=self.action, server_name=self.display_name), ephemeral=True)
                return

            # Set Pending State
            now = datetime.now(timezone.utc)
            self.cog.pending_actions[self.display_name] = {'timestamp': now, 'action': self.action}
            logger.debug(f"[BUTTON] Set pending state for '{self.display_name}' at {now} with action '{self.action}'")

            # --- START: Change - Edit main message instead of original response --- #
            # Get channel and message ID
            channel = interaction.channel
            message_id = None
            if channel and channel.id in self.cog.channel_server_message_ids:
                message_id = self.cog.channel_server_message_ids[channel.id].get(self.display_name)

            if message_id and channel:
                try:
                    message_to_edit = await channel.fetch_message(message_id)
                    pending_embed = _get_pending_embed(self.display_name) # Generate embed here

                    # --- START: Additional Logging --- #
                    if pending_embed:
                        logger.debug(f"[BUTTON_EDIT_ATTEMPT] Editing message {message_id} for '{self.display_name}'. Embed type: {type(pending_embed)}, Embed dict: {pending_embed.to_dict()}")
                    else:
                        logger.error(f"[BUTTON_EDIT_ATTEMPT] Cannot edit message {message_id} for '{self.display_name}'. pending_embed is None!")
                    # --- END: Additional Logging --- #

                    # Create an empty view or a special "Pending" view to prevent interactions
                    # Or keep the old view, but disable the buttons? Simpler: Empty view.
                    # empty_view = View(timeout=None) # Empty view without buttons <-- Removed for testing

                    # --- Change: Pass view=None --- #
                    await message_to_edit.edit(embed=pending_embed, view=None)
                    logger.info(f"[BUTTON] Edited main message {message_id} to show pending for '{self.display_name}' (view removed).") # Log adjusted

                except discord.NotFound:
                    logger.warning(f"[BUTTON] Main status message {message_id} for '{self.display_name}' not found. Cannot set pending state on it.")
                except Exception as e_edit_main:
                    logger.error(f"[BUTTON] Failed to edit main message {message_id} to pending state for '{self.display_name}': {e_edit_main}")
            else:
                logger.warning(f"[BUTTON] Could not find message ID for '{self.display_name}' in channel {channel.id if channel else 'N/A'}. Cannot visually set pending state on main message.")
            # --- END: Change --- #

            # Execute Docker action in background
            logger.info(f"[BUTTON] Creating background task for Docker action: {self.action} for {self.docker_name} (requested by {interaction.user.name})")
            async def run_docker_action():
                success = await docker_action(self.docker_name, self.action)
                if success:
                    logger.info(f"[BUTTON_TASK] Docker action '{self.action}' succeeded for {self.display_name}.")
                else:
                    logger.error(f"[BUTTON_TASK] Docker action '{self.action}' failed for {self.display_name}.")
                    if self.display_name in self.cog.pending_actions:
                        try:
                            del self.cog.pending_actions[self.display_name]
                            logger.debug(f"[BUTTON_TASK] Removed pending state for '{self.display_name}' due to action failure.")
                        except KeyError:
                            pass

            self.cog.bot.loop.create_task(run_docker_action())

            # Send public followup confirming initiation
            action_process_keys = {
                "start": "started_process",
                "stop": "stopped_process",
                "restart": "restarted_process"
            }
            action_process_text = _(action_process_keys.get(self.action, self.action))
            followup_embed = discord.Embed(
                title=_("✅ Server Action Initiated"),
                description=_("Server **{server_name}** is being processed {action_process_text}.").format(server_name=self.display_name, action_process_text=action_process_text),
                color=discord.Color.green()
            )
            followup_embed.add_field(name=_("Action"), value=f"`{self.action.upper()}`", inline=True)
            followup_embed.add_field(name=_("Initiated by"), value=interaction.user.mention, inline=True)
            try:
                await interaction.followup.send(embed=followup_embed, ephemeral=False)
                logger.info(f"[BUTTON] Sent public followup for action '{self.action}' on '{self.display_name}'.")
            except Exception as e_followup:
                logger.error(f"[BUTTON] Failed to send followup message for '{self.display_name}': {e_followup}")

        # This except block now correctly corresponds to the outer try
        except Exception as e_outer:
             logger.error(f"[BUTTON_CALLBACK_ERROR] Unexpected error in outer callback for '{self.display_name}': {e_outer}", exc_info=True)
             try:
                 if not interaction.response.is_done():
                     await interaction.response.send_message(_("An unexpected error occurred."), ephemeral=True)
                 else:
                     await interaction.followup.send(_("An unexpected error occurred."), ephemeral=True)
             except Exception:
                 pass

        # Update last activity time for the channel
        if interaction.channel:
            self.cog.last_channel_activity[interaction.channel.id] = datetime.now(timezone.utc)
            logger.debug(f"Updated last_channel_activity for channel {interaction.channel.id} after action {self.action}")

class ToggleButton(Button):
    """A button that toggles between expanding and collapsing."""
    cog: 'DockerControlCog'

    def __init__(self, cog_instance: 'DockerControlCog', server_config: dict, is_running: bool, row: int):
        self.cog = cog_instance
        self.docker_name = server_config.get('docker_name')
        self.display_name = server_config.get('name', self.docker_name)
        self.server_config = server_config  # Cache der Server-Konfiguration für performantere Nutzung
        self.is_expanded = cog_instance.expanded_states.get(self.display_name, False)
        if self.is_expanded:
            emoji = "➖"
            style = discord.ButtonStyle.primary
        else:
            emoji = "➕"
            style = discord.ButtonStyle.primary
        # Disable button if server is not running (details can't be shown/toggled)
        super().__init__(style=style, label=None, custom_id=f"toggle_{self.docker_name}", row=row, emoji=emoji, disabled=not is_running)

    async def callback(self, interaction: discord.Interaction):
        """Optimized toggle function - cache-based only, no Docker queries."""
        # Immediately acknowledge interaction to improve UI response time
        await interaction.response.defer()
        
        # Status change in Cog state
        start_time = time.time()
        self.is_expanded = not self.is_expanded
        self.cog.expanded_states[self.display_name] = self.is_expanded
        
        logger.debug(f"[TOGGLE_BTN] Toggle for '{self.display_name}' by {interaction.user}. New status: {self.is_expanded}")

        # Efficiently retrieve server configuration (only once per button interaction)
        channel_id = interaction.channel.id if interaction.channel else None
        
        try:
            # Use the message directly from the interaction (no API query needed)
            message = interaction.message
            if not message or not channel_id:
                logger.error(f"[TOGGLE_BTN] Message or channel missing for '{self.display_name}'")
                return
            
            # PERFORMANCE OPTIMIZATION: Use cached config instead of self.cog.config
            current_config = get_cached_config()
            
            # PERFORMANCE OPTIMIZATION: Check if container is in pending status
            # If yes, show pending embed without Docker query
            if self.display_name in self.cog.pending_actions:
                logger.debug(f"[TOGGLE_BTN] '{self.display_name}' is in pending status, show pending embed")
                pending_embed = _get_pending_embed(self.display_name)
                if pending_embed:
                    await message.edit(embed=pending_embed, view=None)
                    elapsed_time = (time.time() - start_time) * 1000
                    logger.debug(f"[TOGGLE_BTN] Pending message for '{self.display_name}' updated in {elapsed_time:.1f}ms")
                return
            
            # ULTRA-FAST OPTIMIZATION: Use ONLY cached data
            # No more Docker queries - Background loop (every 30s) provides current data
            cached_entry = self.cog.status_cache.get(self.display_name)
            
            if cached_entry and cached_entry.get('data'):
                # Use cached data for lightning-fast toggle operation
                status_result = cached_entry['data']
                
                # Fast embed generation only with cached data
                embed, view = await self._generate_fast_toggle_embed_and_view(
                    channel_id=channel_id,
                    status_result=status_result,
                    current_config=current_config,
                    cached_entry=cached_entry  # BUGFIX: Pass cached_entry for correct timestamp
                )
                
                if embed and view:
                    await message.edit(embed=embed, view=view)
                    elapsed_time = (time.time() - start_time) * 1000
                    logger.debug(f"[TOGGLE_BTN] Ultra-fast toggle message for '{self.display_name}' updated in {elapsed_time:.1f}ms")
                else:
                    logger.warning(f"[TOGGLE_BTN] Fast toggle generation failed for '{self.display_name}'")
            else:
                # NO FALLBACK ANYMORE: If no cache available, show hint and wait for background update
                logger.info(f"[TOGGLE_BTN] No cache entry for '{self.display_name}' - Background loop will update in ~30s")
                
                # Show temporary "loading" status
                temp_embed = discord.Embed(
                    description="```\n┌── Loading Status ───────────\n│ 🔄 Refreshing container data...\n│ ⏱️ Please wait a moment\n└─────────────────────────────\n```",
                    color=0x3498db
                )
                temp_embed.set_footer(text="Background update in progress • https://ddc.bot")
                
                # Simple view without buttons during loading
                temp_view = discord.ui.View(timeout=None)
                
                await message.edit(embed=temp_embed, view=temp_view)
                elapsed_time = (time.time() - start_time) * 1000
                logger.debug(f"[TOGGLE_BTN] Loading message for '{self.display_name}' shown in {elapsed_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"[TOGGLE_BTN] Error toggling '{self.display_name}': {e}", exc_info=True)
        
        # Update timestamp of last channel activity
        if interaction.channel:
            self.cog.last_channel_activity[interaction.channel.id] = datetime.now(timezone.utc)

    async def _generate_fast_toggle_embed_and_view(self, channel_id: int, status_result: tuple, current_config: dict, cached_entry: dict) -> tuple[Optional[discord.Embed], Optional[discord.ui.View]]:
        """
        Fast embed/view generation only for toggle operations.
        Uses only cached data without Docker queries.
        """
        try:
            if not isinstance(status_result, tuple) or len(status_result) != 6:
                logger.warning(f"[FAST_TOGGLE] Invalid status_result format for '{self.display_name}'")
                return None, None
            
            display_name_from_status, running, cpu, ram, uptime, details_allowed = status_result
            
            # Use the same embed generation as in status_handlers.py, but optimized
            status_color = 0x00b300 if running else 0xe74c3c
            
            # PERFORMANCE OPTIMIZATION: Use cached translations if available
            lang = current_config.get('language', 'de')
            if hasattr(self.cog, '_get_cached_translations'):
                cached_translations = self.cog._get_cached_translations(lang)
                online_text = cached_translations['online_text']
                offline_text = cached_translations['offline_text']
                cpu_text = cached_translations['cpu_text']
                ram_text = cached_translations['ram_text']
                uptime_text = cached_translations['uptime_text']
                detail_denied_text = cached_translations['detail_denied_text']
                last_update_text = cached_translations['last_update_text']
            else:
                # Fallback to direct translations
                online_text = _("**Online**")
                offline_text = _("**Offline**")
                cpu_text = _("CPU")
                ram_text = _("RAM")
                uptime_text = _("Uptime")
                detail_denied_text = _("Detailed status not allowed.")
                last_update_text = _("Last update")
            
            status_text = online_text if running else offline_text
            current_emoji = "🟢" if running else "🔴"
            
            # Check expanded status
            is_expanded = self.is_expanded
            
            # PERFORMANCE OPTIMIZATION: Use cached box elements if available
            BOX_WIDTH = 28
            if hasattr(self.cog, '_get_cached_box_elements'):
                cached_box = self.cog._get_cached_box_elements(self.display_name, BOX_WIDTH)
                header_line = cached_box['header_line']
                footer_line = cached_box['footer_line']
            else:
                # Fallback to direct box generation
                header_text = f"── {self.display_name} "
                max_name_len = BOX_WIDTH - 4
                if len(header_text) > max_name_len:
                    header_text = header_text[:max_name_len-1] + "… "
                padding_width = max(1, BOX_WIDTH - 1 - len(header_text))
                header_line = f"┌{header_text}{'─' * padding_width}"
                footer_line = f"└{'─' * (BOX_WIDTH - 1)}"
            
            # Build description
            description_parts = [
                "```\n",
                header_line,
                f"\n│ {current_emoji} {status_text}"
            ]
            
            # Details based on status and expanded state
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
            description = "".join(description_parts)
            
            # Add timestamp
            timezone_str = current_config.get('timezone')
            current_time = format_datetime_with_timezone(cached_entry['timestamp'], timezone_str, fmt="%H:%M:%S")
            timestamp_line = f"{last_update_text}: {current_time}"
            
            embed = discord.Embed(description=f"{timestamp_line}\n{description}", color=status_color)
            embed.set_footer(text="https://ddc.bot")
            
            # Generate view
            channel_has_control = _channel_has_permission(channel_id, 'control', current_config)
            view = ControlView(self.cog, self.server_config, running, channel_has_control_permission=channel_has_control, allow_toggle=True)
            
            return embed, view
            
        except Exception as e:
            logger.error(f"[FAST_TOGGLE] Error in fast toggle generation for '{self.display_name}': {e}", exc_info=True)
            return None, None

    # --- Add: Method to create a new view with allow_toggle=True (for ToggleButton) --- #
    def get_refreshed_view(self, server_config: dict, is_running: bool, channel_has_control_permission: bool) -> 'ControlView':
        """Creates a new instance of this View, but forces allow_toggle=True."""
        return ControlView(self.cog, server_config, is_running, channel_has_control_permission, allow_toggle=True)

class ControlView(View):
    """View with control buttons for a Docker container."""
    cog: 'DockerControlCog'

    # --- FIX: Allow None for cog_instance and server_config for registration --- #
    # --- NEW: Parameter allow_toggle added --- #
    def __init__(self, cog_instance: Optional['DockerControlCog'], server_config: Optional[dict], is_running: bool, channel_has_control_permission: bool, allow_toggle: bool = True):
        super().__init__(timeout=None)
        self.cog = cog_instance
        self.allow_toggle = allow_toggle

        # DEBUG LOG ADDED
        display_name_log = server_config.get('name', server_config.get('docker_name', 'N/A')) if server_config else 'N/A'
        logger.debug(f"[ControlView.__init__] Initializing for '{display_name_log}'. is_running={is_running}, channel_has_control={channel_has_control_permission}, received allow_toggle={allow_toggle}")
        # END DEBUG LOG

        # START: Add specific logging for flags
        if not allow_toggle:
             logger.debug(f"[ControlView.__init__] '{display_name_log}': allow_toggle=False received. ToggleButton will NOT be added.")

        # If called just for registration (cog or config is None), do not add items
        if not self.cog or not server_config:
            return

        # Existing logic
        docker_name = server_config.get('docker_name')
        display_name = server_config.get('name', docker_name)

        # Check for Pending Status
        if display_name in self.cog.pending_actions:
             logger.debug(f"[ControlView] Server '{display_name}' is pending. No buttons will be added.")
             return # Stop initialization, add no buttons

        allowed_actions = server_config.get('allowed_actions', [])
        details_allowed = server_config.get('allow_detailed_status', True)
        is_expanded = cog_instance.expanded_states.get(display_name, False)

        # Determine which buttons to add based on state and permissions (only if not pending)
        if is_running:
            # Toggle Button (+/-) is always on row 0, when allowed
            if details_allowed and self.allow_toggle:
                 self.add_item(ToggleButton(cog_instance, server_config, is_running=True, row=0))

            # Action Buttons (Stop/Restart)
            if channel_has_control_permission and is_expanded:
                button_row = 0 
                if "stop" in allowed_actions:
                    self.add_item(ActionButton(cog_instance, server_config, "stop", discord.ButtonStyle.secondary, None, "⏹️", row=button_row))
                if "restart" in allowed_actions:
                    self.add_item(ActionButton(cog_instance, server_config, "restart", discord.ButtonStyle.secondary, None, "🔄", row=button_row))

        else: # Server is not running
            # Only show start button, no toggle button for offline servers
            if channel_has_control_permission and "start" in allowed_actions:
                 self.add_item(ActionButton(cog_instance, server_config, "start", discord.ButtonStyle.secondary, None, "▶️", row=0))

class TaskDeleteButton(Button):
    """Button for deleting a specific scheduled task."""
    
    def __init__(self, cog_instance: 'DockerControlCog', task_id: str, task_description: str, row: int):
        self.cog = cog_instance
        self.task_id = task_id
        self.task_description = task_description
        
        super().__init__(
            style=discord.ButtonStyle.danger,
            label=task_description,
            custom_id=f"task_delete_{task_id}",
            row=row
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Deletes the scheduled task."""
        user = interaction.user
        
        logger.info(f"[TASK_DELETE_BTN] Task deletion '{self.task_id}' triggered by {user.name}")
        
        try:
            # Defer interaction
            await interaction.response.defer(ephemeral=True)
            
            # Import necessary modules
            from utils.scheduler import load_tasks, delete_task
            from utils.action_logger import log_user_action
            
            # Check permissions - only channel-level permissions matter
            config = get_cached_config()
            if not _channel_has_permission(interaction.channel.id, 'schedule', config):
                await interaction.followup.send(_("You do not have permission to delete tasks in this channel."), ephemeral=True)
                return
            
            # Find the task
            all_tasks = load_tasks()
            task_to_delete = None
            
            for task in all_tasks:
                if task.task_id == self.task_id:
                    task_to_delete = task
                    break
            
            if not task_to_delete:
                await interaction.followup.send(_("Task with ID '{task_id}' not found.").format(task_id=self.task_id), ephemeral=True)
                return
            
            # Delete the task
            if delete_task(self.task_id):
                # Log the action
                log_user_action(
                    action="TASK_DELETE_PANEL", 
                    target=f"{task_to_delete.container_name} ({task_to_delete.action})", 
                    user=str(user),
                    source="Discord Panel Button",
                    details=f"Deleted task: {self.task_id}, Cycle: {task_to_delete.cycle}"
                )
                
                await interaction.followup.send(_("✅ Successfully deleted scheduled task!\n**Task ID:** {task_id}\n**Container:** {container}\n**Action:** {action}\n**Cycle:** {cycle}").format(
                    task_id=self.task_id,
                    container=task_to_delete.container_name,
                    action=task_to_delete.action,
                    cycle=task_to_delete.cycle
                ), ephemeral=True)
                
                # Update the original message by disabling this button and showing it as deleted
                # We'll disable this button and change its style
                self.disabled = True
                self.style = discord.ButtonStyle.secondary
                self.label = "Deleted"
                
                # Edit the original message to reflect the change
                try:
                    await interaction.edit_original_response(view=self.view)
                except:
                    pass  # If editing fails, that's okay
                    
            else:
                await interaction.followup.send(_("❌ Failed to delete task. The task might not exist or there was an error."), ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in TaskDeleteButton callback: {e}", exc_info=True)
            await interaction.followup.send(_("An error occurred: {error}").format(error=str(e)), ephemeral=True)


class TaskDeletePanelView(View):
    """View with delete buttons for each active scheduled task."""
    
    def __init__(self, cog_instance: 'DockerControlCog', active_tasks: list):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog_instance
        
        # Add a delete button for each task (max 25 components: 5 rows × 5 buttons per row)
        for i, task in enumerate(active_tasks[:25]):  # Discord limit: 25 components total
            try:
                # Action emoji mapping
                action_emojis = {
                    'start': '▶️',
                    'stop': '⏹️', 
                    'restart': '🔄'
                }
                
                # Cycle abbreviations
                cycle_abbrevs = {
                    'once': 'O',
                    'daily': 'D', 
                    'weekly': 'W',
                    'monthly': 'M',
                    'yearly': 'Y'
                }
                
                # Get emoji and cycle abbreviation
                emoji = action_emojis.get(task.action, '❓')
                cycle_abbrev = cycle_abbrevs.get(task.cycle, task.cycle[:1])
                
                # Format date/time based on cycle
                time_part = ""
                try:
                    next_run_dt = task.get_next_run_datetime()
                    if next_run_dt:
                        if task.cycle == 'once':
                            # Full date and time: 29.05.2025 17:00
                            time_part = next_run_dt.strftime("%d.%m.%Y %H:%M")
                        elif task.cycle == 'daily':
                            # Just time: 17:00
                            time_part = next_run_dt.strftime("%H:%M")
                        elif task.cycle == 'weekly':
                            # Weekday and time: tuesday 17:00
                            weekday = next_run_dt.strftime("%A").lower()
                            time_part = f"{weekday} {next_run_dt.strftime('%H:%M')}"
                        elif task.cycle == 'monthly':
                            # Day and time: 29 17:00
                            time_part = f"{next_run_dt.day} {next_run_dt.strftime('%H:%M')}"
                        elif task.cycle == 'yearly':
                            # Month.day and time: 29.05 17:00
                            time_part = f"{next_run_dt.day:02d}.{next_run_dt.month:02d} {next_run_dt.strftime('%H:%M')}"
                        else:
                            # Fallback
                            time_part = next_run_dt.strftime("%H:%M")
                    else:
                        time_part = "No schedule"
                except Exception:
                    time_part = "Unknown"
                
                # Build the button label: Emoji + Cycle + Time + Container
                # Format: "🔄 d 17:00 nginx"
                base_label = f"{emoji} {cycle_abbrev} {time_part} {task.container_name}"
                
                # Ensure label fits Discord's 80 character limit
                if len(base_label) > 78:
                    # Calculate available space for container name
                    prefix_length = len(f"{emoji} {cycle_abbrev} {time_part} ")
                    available_for_container = 75 - prefix_length  # Leave 3 chars for "..."
                    
                    if available_for_container > 3:
                        truncated_container = task.container_name[:available_for_container] + "..."
                        task_description = f"{emoji} {cycle_abbrev} {time_part} {truncated_container}"
                    else:
                        # If even truncation doesn't fit, use minimal format
                        task_description = f"{emoji} {cycle_abbrev} {task.container_name[:10]}..."
                else:
                    task_description = base_label

                # 5 buttons per row (horizontal layout)
                row = i // 5
                if row > 4:  # Discord allows max 5 rows
                    break
                    
                button = TaskDeleteButton(cog_instance, task.task_id, task_description, row)
                self.add_item(button)
                
            except Exception as e:
                logger.error(f"Error creating delete button for task {getattr(task, 'task_id', 'unknown')}: {e}")
                continue