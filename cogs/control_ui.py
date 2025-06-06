# -*- coding: utf-8 -*-
"""Control UI components for Discord interaction."""

import asyncio
import discord
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from discord.ui import View, Button

from utils.config_cache import get_cached_config
from utils.time_utils import format_datetime_with_timezone
from .control_helpers import _channel_has_permission, _get_pending_embed
from utils.logging_utils import get_module_logger
from utils.action_logger import log_user_action
from .translation_manager import _

logger = get_module_logger('control_ui')

# Global caches for performance optimization
_timestamp_format_cache = {}  # Cache für formatierte Timestamps
_permission_cache = {}        # Cache für Channel-Permissions
_view_cache = {}             # Cache für View-Objekte

def _clear_caches():
    """Clears all performance caches - called periodically."""
    global _timestamp_format_cache, _permission_cache, _view_cache
    _timestamp_format_cache.clear()
    _permission_cache.clear()
    _view_cache.clear()
    logger.debug("Performance caches cleared")

def _get_cached_formatted_timestamp(timestamp: datetime, timezone_str: str, fmt: str = "%H:%M:%S") -> str:
    """Ultra-fast cached timestamp formatting."""
    # Create cache key from timestamp seconds + timezone + format
    cache_key = f"{int(timestamp.timestamp())}_{timezone_str}_{fmt}"
    
    if cache_key not in _timestamp_format_cache:
        # Only format on cache miss
        _timestamp_format_cache[cache_key] = format_datetime_with_timezone(timestamp, timezone_str, fmt)
        
        # Prevent cache from growing too large (keep last 100 entries)
        if len(_timestamp_format_cache) > 100:
            # Remove oldest 20 entries
            keys_to_remove = list(_timestamp_format_cache.keys())[:20]
            for key in keys_to_remove:
                del _timestamp_format_cache[key]
    
    return _timestamp_format_cache[cache_key]

def _get_cached_channel_permission(channel_id: int, permission_key: str, current_config: dict) -> bool:
    """Ultra-fast cached channel permission checking."""
    # Create cache key from channel_id + permission + config timestamp
    config_timestamp = current_config.get('_cache_timestamp', 0)  # Use config cache timestamp
    cache_key = f"{channel_id}_{permission_key}_{config_timestamp}"
    
    if cache_key not in _permission_cache:
        # Only check permission on cache miss
        _permission_cache[cache_key] = _channel_has_permission(channel_id, permission_key, current_config)
        
        # Prevent cache from growing too large
        if len(_permission_cache) > 50:
            keys_to_remove = list(_permission_cache.keys())[:10]
            for key in keys_to_remove:
                del _permission_cache[key]
    
    return _permission_cache[cache_key]

class ActionButton(Button):
    """Ultra-optimized button for Start, Stop, Restart actions."""
    cog: 'DockerControlCog'

    def __init__(self, cog_instance: 'DockerControlCog', server_config: dict, action: str, style: discord.ButtonStyle, label: str, emoji: str, row: int):
        self.cog = cog_instance
        self.action = action
        self.server_config = server_config
        self.docker_name = server_config.get('docker_name')
        self.display_name = server_config.get('name', self.docker_name)
        super().__init__(style=style, label=label, custom_id=f"{action}_{self.docker_name}", row=row, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        """Ultra-optimized action button handler."""
        user = interaction.user
        # Immediately defer the interaction for better perceived performance
        await interaction.response.defer()
        
        # Quick permission and config checks
        current_config = get_cached_config()
        channel_has_control = _get_cached_channel_permission(interaction.channel.id, 'control', current_config)
        
        if not channel_has_control:
            await interaction.followup.send(_("This action is not allowed in this channel."), ephemeral=True)
            return

        # Check if the action is allowed for this container
        allowed_actions = self.server_config.get('allowed_actions', [])
        if self.action not in allowed_actions:
            await interaction.followup.send(f"❌ Action '{self.action}' is not allowed for container '{self.display_name}'.", ephemeral=True)
            return

        logger.info(f"[ACTION_BTN] {self.action.upper()} action for '{self.display_name}' triggered by {user.name}")
        
        # Set pending status immediately
        self.cog.pending_actions[self.display_name] = {
            'action': self.action,
            'timestamp': datetime.now(timezone.utc),
            'user': str(user)
        }
        
        try:
            # Generate pending message first (ultra-fast response)
            pending_embed = _get_pending_embed(self.display_name)
            await interaction.edit_original_response(embed=pending_embed, view=None)
            
            # Log the action
            log_user_action(
                action=f"DOCKER_{self.action.upper()}", 
                target=self.display_name, 
                user=str(user),
                source="Discord Button",
                details=f"Container: {self.docker_name}"
            )

            # Start background Docker action
            async def run_docker_action():
                """Background task for the actual Docker operation."""
                try:
                    # Use the existing docker_action function from utils.docker_utils
                    from utils.docker_utils import docker_action
                    
                    # Perform the Docker action using the existing function
                    success = await docker_action(self.docker_name, self.action)
                    
                    logger.info(f"[ACTION_BTN] Docker {self.action} for '{self.display_name}' completed: success={success}")
                    
                    # Clear pending status
                    if self.display_name in self.cog.pending_actions:
                        del self.cog.pending_actions[self.display_name]
                    
                    # Force status cache update for this container
                    server_config_for_update = next((s for s in self.cog.config.get('servers', []) if s.get('name') == self.display_name), None)
                    if server_config_for_update:
                        fresh_status = await self.cog.get_status(server_config_for_update)
                        if not isinstance(fresh_status, Exception):
                            self.cog.status_cache[self.display_name] = {
                                'data': fresh_status,
                                'timestamp': datetime.now(timezone.utc)
                            }
                    
                    # Update the message with fresh status
                    try:
                        if hasattr(self.cog, '_generate_status_embed_and_view'):
                            embed, view, _ = await self.cog._generate_status_embed_and_view(
                                interaction.channel.id, 
                                self.display_name, 
                                self.server_config, 
                                current_config, 
                                allow_toggle=True, 
                                force_collapse=False
                            )
                            
                            if embed:
                                await interaction.edit_original_response(embed=embed, view=view)
                    except Exception as e:
                        logger.error(f"[ACTION_BTN] Error updating message after {self.action}: {e}")
                        
                except Exception as e:
                    logger.error(f"[ACTION_BTN] Error in background Docker {self.action}: {e}")
                    # Clear pending status on error
                    if self.display_name in self.cog.pending_actions:
                        del self.cog.pending_actions[self.display_name]
            
            # Start background task
            asyncio.create_task(run_docker_action())
            
        except Exception as e:
            logger.error(f"[ACTION_BTN] Error handling {self.action} for '{self.display_name}': {e}")
            # Clear pending status on error
            if self.display_name in self.cog.pending_actions:
                del self.cog.pending_actions[self.display_name]

class ToggleButton(Button):
    """Ultra-optimized toggle button for expanding/collapsing container details."""
    cog: 'DockerControlCog'

    def __init__(self, cog_instance: 'DockerControlCog', server_config: dict, is_running: bool, row: int):
        self.cog = cog_instance
        self.docker_name = server_config.get('docker_name')
        self.display_name = server_config.get('name', self.docker_name)
        self.server_config = server_config
        self.is_expanded = cog_instance.expanded_states.get(self.display_name, False)
        
        # Cache channel permissions for this button
        self._channel_permissions_cache = {}
        
        emoji = "➖" if self.is_expanded else "➕"
        super().__init__(style=discord.ButtonStyle.primary, label=None, custom_id=f"toggle_{self.docker_name}", row=row, emoji=emoji, disabled=not is_running)

    def _get_cached_channel_permission_for_toggle(self, channel_id: int, current_config: dict) -> bool:
        """Cached channel permission specifically for this toggle button."""
        if channel_id not in self._channel_permissions_cache:
            self._channel_permissions_cache[channel_id] = _get_cached_channel_permission(channel_id, 'control', current_config)
        return self._channel_permissions_cache[channel_id]

    async def callback(self, interaction: discord.Interaction):
        """ULTRA-OPTIMIZED toggle function with extensive caching."""
        await interaction.response.defer()
        
        start_time = time.time()
        self.is_expanded = not self.is_expanded
        self.cog.expanded_states[self.display_name] = self.is_expanded
        
        logger.debug(f"[TOGGLE_BTN] Toggle for '{self.display_name}' by {interaction.user}. New status: {self.is_expanded}")

        channel_id = interaction.channel.id if interaction.channel else None
        
        try:
            message = interaction.message
            if not message or not channel_id:
                logger.error(f"[TOGGLE_BTN] Message or channel missing for '{self.display_name}'")
                return
            
            current_config = get_cached_config()
            
            # Check if container is in pending status
            if self.display_name in self.cog.pending_actions:
                logger.debug(f"[TOGGLE_BTN] '{self.display_name}' is in pending status, show pending embed")
                pending_embed = _get_pending_embed(self.display_name)
                if pending_embed:
                    await message.edit(embed=pending_embed, view=None)
                    elapsed_time = (time.time() - start_time) * 1000
                    logger.debug(f"[TOGGLE_BTN] Pending message for '{self.display_name}' updated in {elapsed_time:.1f}ms")
                return
            
            # Use cached data for ultra-fast operation
            cached_entry = self.cog.status_cache.get(self.display_name)
            
            if cached_entry and cached_entry.get('data'):
                status_result = cached_entry['data']
                
                embed, view = await self._generate_ultra_fast_toggle_embed_and_view(
                    channel_id=channel_id,
                    status_result=status_result,
                    current_config=current_config,
                    cached_entry=cached_entry
                )
                
                if embed and view:
                    await message.edit(embed=embed, view=view)
                    elapsed_time = (time.time() - start_time) * 1000
                    logger.debug(f"[TOGGLE_BTN] ULTRA-FAST toggle message for '{self.display_name}' updated in {elapsed_time:.1f}ms")
                else:
                    logger.warning(f"[TOGGLE_BTN] Ultra-fast toggle generation failed for '{self.display_name}'")
            else:
                # Show loading status if no cache available
                logger.info(f"[TOGGLE_BTN] No cache entry for '{self.display_name}' - Background loop will update")
                
                temp_embed = discord.Embed(
                    description="```\n┌── Loading Status ───────────\n│ 🔄 Refreshing container data...\n│ ⏱️ Please wait a moment\n└─────────────────────────────\n```",
                    color=0x3498db
                )
                temp_embed.set_footer(text="Background update in progress • https://ddc.bot")
                
                temp_view = discord.ui.View(timeout=None)
                await message.edit(embed=temp_embed, view=temp_view)
                elapsed_time = (time.time() - start_time) * 1000
                logger.debug(f"[TOGGLE_BTN] Loading message for '{self.display_name}' shown in {elapsed_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"[TOGGLE_BTN] Error toggling '{self.display_name}': {e}", exc_info=True)
        
        # Update channel activity timestamp
        if interaction.channel:
            self.cog.last_channel_activity[interaction.channel.id] = datetime.now(timezone.utc)

    async def _generate_ultra_fast_toggle_embed_and_view(self, channel_id: int, status_result: tuple, current_config: dict, cached_entry: dict) -> tuple[Optional[discord.Embed], Optional[discord.ui.View]]:
        """Ultra-fast embed/view generation with extensive caching."""
        try:
            if not isinstance(status_result, tuple) or len(status_result) != 6:
                logger.warning(f"[ULTRA_FAST_TOGGLE] Invalid status_result format for '{self.display_name}'")
                return None, None
            
            display_name_from_status, running, cpu, ram, uptime, details_allowed = status_result
            status_color = 0x00b300 if running else 0xe74c3c
            
            # Use cached translations if available
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
                # Fallback to hardcoded strings for ultra-fast performance
                online_text = "**Online**"
                offline_text = "**Offline**"
                cpu_text = "CPU"
                ram_text = "RAM"
                uptime_text = "Uptime"
                detail_denied_text = "Detailed status not allowed."
                last_update_text = "Last update"
            
            status_text = online_text if running else offline_text
            current_emoji = "🟢" if running else "🔴"
            is_expanded = self.is_expanded
            
            # Use cached box elements if available
            BOX_WIDTH = 28
            if hasattr(self.cog, '_get_cached_box_elements'):
                cached_box = self.cog._get_cached_box_elements(self.display_name, BOX_WIDTH)
                header_line = cached_box['header_line']
                footer_line = cached_box['footer_line']
            else:
                # Fallback box generation
                header_text = f"── {self.display_name} "
                max_name_len = BOX_WIDTH - 4
                if len(header_text) > max_name_len:
                    header_text = header_text[:max_name_len-1] + "… "
                padding_width = max(1, BOX_WIDTH - 1 - len(header_text))
                header_line = f"┌{header_text}{'─' * padding_width}"
                footer_line = f"└{'─' * (BOX_WIDTH - 1)}"
            
            # Build description efficiently
            description_parts = [
                "```\n",
                header_line,
                f"\n│ {current_emoji} {status_text}"
            ]
            
            # Add details based on status and expanded state
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
            else:
                description_parts.append(f"\n{footer_line}")
            
            description_parts.append("\n```")
            description = "".join(description_parts)
            
            # Ultra-fast cached timestamp formatting
            timezone_str = current_config.get('timezone')
            current_time = _get_cached_formatted_timestamp(cached_entry['timestamp'], timezone_str, fmt="%H:%M:%S")
            timestamp_line = f"{last_update_text}: {current_time}"
            
            embed = discord.Embed(description=f"{timestamp_line}\n{description}", color=status_color)
            embed.set_footer(text="https://ddc.bot")
            
            # Ultra-fast cached channel permission
            channel_has_control = self._get_cached_channel_permission_for_toggle(channel_id, current_config)
            
            # Create optimized view
            view = self._create_optimized_control_view(running, channel_has_control)
            
            return embed, view
            
        except Exception as e:
            logger.error(f"[ULTRA_FAST_TOGGLE] Error in ultra-fast toggle generation for '{self.display_name}': {e}", exc_info=True)
            return None, None

    def _create_optimized_control_view(self, is_running: bool, channel_has_control_permission: bool) -> 'ControlView':
        """Creates an optimized ControlView with smart caching."""
        # FIXED: Don't use caching for views with mutable state
        # Instead, create fresh views but optimize the creation process
        return ControlView(
            self.cog, 
            self.server_config, 
            is_running, 
            channel_has_control_permission=channel_has_control_permission, 
            allow_toggle=True
        )

class ControlView(View):
    """Ultra-optimized view with control buttons for a Docker container."""
    cog: 'DockerControlCog'

    def __init__(self, cog_instance: Optional['DockerControlCog'], server_config: Optional[dict], is_running: bool, channel_has_control_permission: bool, allow_toggle: bool = True):
        super().__init__(timeout=None)
        self.cog = cog_instance
        self.allow_toggle = allow_toggle

        # If called for registration only, don't add items
        if not self.cog or not server_config:
            return

        docker_name = server_config.get('docker_name')
        display_name = server_config.get('name', docker_name)

        # Check for pending status
        if display_name in self.cog.pending_actions:
            logger.debug(f"[ControlView] Server '{display_name}' is pending. No buttons will be added.")
            return

        allowed_actions = server_config.get('allowed_actions', [])
        details_allowed = server_config.get('allow_detailed_status', True)
        is_expanded = cog_instance.expanded_states.get(display_name, False)

        # Add buttons based on state and permissions
        if is_running:
            # Toggle button for running containers with details allowed
            if details_allowed and self.allow_toggle:
                self.add_item(ToggleButton(cog_instance, server_config, is_running=True, row=0))

            # Action buttons when expanded and channel has control
            if channel_has_control_permission and is_expanded:
                button_row = 0
                if "stop" in allowed_actions:
                    self.add_item(ActionButton(cog_instance, server_config, "stop", discord.ButtonStyle.secondary, None, "⏹️", row=button_row))
                if "restart" in allowed_actions:
                    self.add_item(ActionButton(cog_instance, server_config, "restart", discord.ButtonStyle.secondary, None, "🔄", row=button_row))
        else:
            # Start button for offline containers
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
            await interaction.response.defer(ephemeral=True)
            
            from utils.scheduler import load_tasks, delete_task
            
            config = get_cached_config()
            if not _get_cached_channel_permission(interaction.channel.id, 'schedule', config):
                await interaction.followup.send(_("You do not have permission to delete tasks in this channel."), ephemeral=True)
                return
            
            if delete_task(self.task_id):
                log_user_action(
                    action="TASK_DELETE", 
                    target=f"Task {self.task_id}", 
                    user=str(user),
                    source="Discord Button",
                    details=f"Task: {self.task_description}"
                )
                
                await interaction.followup.send(
                    _("✅ Task **{task_description}** has been deleted successfully.").format(task_description=self.task_description),
                    ephemeral=True
                )
                logger.info(f"[TASK_DELETE_BTN] Task '{self.task_id}' deleted successfully by {user.name}")
            else:
                await interaction.followup.send(
                    _("❌ Failed to delete task **{task_description}**. It may no longer exist.").format(task_description=self.task_description),
                    ephemeral=True
                )
                logger.warning(f"[TASK_DELETE_BTN] Failed to delete task '{self.task_id}' for {user.name}")
                
        except Exception as e:
            logger.error(f"[TASK_DELETE_BTN] Error deleting task '{self.task_id}': {e}", exc_info=True)
            await interaction.followup.send(_("An error occurred while deleting the task."), ephemeral=True)

class TaskDeletePanelView(View):
    """View containing task delete buttons."""
    
    def __init__(self, cog_instance: 'DockerControlCog', active_tasks: list):
        super().__init__(timeout=600)  # 10 minute timeout for task panels
        self.cog = cog_instance
        
        # Add delete buttons for each task (max 25 due to Discord limits)
        max_tasks = min(len(active_tasks), 25)
        for i, task in enumerate(active_tasks[:max_tasks]):
            task_id = task.task_id
            
            # Create abbreviated description for button
            container_name = task.container_name
            action = task.action.upper()
            cycle_abbrev = {
                'once': 'O',
                'daily': 'D', 
                'weekly': 'W',
                'monthly': 'M',
                'yearly': 'Y'
            }.get(task.cycle, '?')
            
            task_description = f"{cycle_abbrev}: {container_name} {action}"
            
            # Limit description length for button
            if len(task_description) > 40:
                task_description = task_description[:37] + "..."
            
            row = i // 5  # 5 buttons per row
            self.add_item(TaskDeleteButton(cog_instance, task_id, task_description, row))