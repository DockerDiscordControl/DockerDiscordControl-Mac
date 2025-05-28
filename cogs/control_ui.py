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
            self.cog.pending_actions[self.display_name] = now
            logger.debug(f"[BUTTON] Set pending state for '{self.display_name}' at {now}")

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
        """Optimierte Toggle-Funktion - schnellere Umschaltung mit weniger API-Anfragen."""
        # Sofort Interaktion bestätigen, um UI-Reaktionszeit zu verbessern
        await interaction.response.defer()
        
        # Statusänderung im Cog-State
        start_time = time.time()
        self.is_expanded = not self.is_expanded
        self.cog.expanded_states[self.display_name] = self.is_expanded
        
        logger.debug(f"[TOGGLE_BTN] Toggle für '{self.display_name}' von {interaction.user}. Neuer Status: {self.is_expanded}")

        # Server-Konfiguration effizient abrufen (nur einmal pro Button-Interaktion)
        channel_id = interaction.channel.id if interaction.channel else None
        
        try:
            # Direkt die Nachricht aus der Interaktion verwenden (keine API-Abfrage nötig)
            message = interaction.message
            if not message or not channel_id:
                logger.error(f"[TOGGLE_BTN] Nachricht oder Kanal fehlt für '{self.display_name}'")
                return
                
            # Aktuellen Status aus dem Cache holen statt neu abzufragen
            cached_entry = self.cog.status_cache.get(self.display_name)
            if not cached_entry or not cached_entry.get('data'):
                logger.warning(f"[TOGGLE_BTN] Kein Cache-Eintrag für '{self.display_name}', nutze bestehende Embed/View")
                # Da kein Status verfügbar ist, fügen wir trotzdem ein leeres Embed hinzu
                embed, view, _ = await self.cog._generate_status_embed_and_view(
                    channel_id=channel_id,
                    display_name=self.display_name,
                    server_conf=self.server_config,
                    current_config=self.cog.config,  # Nutze im Cog gespeicherte Config statt neu zu laden
                    allow_toggle=True,
                    force_collapse=False
                )
            else:
                # Optimierte Embed/View-Generierung mit gecachten Daten
                embed, view, _ = await self.cog._generate_status_embed_and_view(
                    channel_id=channel_id,
                    display_name=self.display_name,
                    server_conf=self.server_config,
                    current_config=self.cog.config,  # Nutze im Cog gespeicherte Config statt neu zu laden
                    allow_toggle=True,
                    force_collapse=False
                )
            
            # Nachricht bearbeiten
            if message and embed:
                await message.edit(embed=embed, view=view)
                elapsed_time = (time.time() - start_time) * 1000
                logger.debug(f"[TOGGLE_BTN] Nachricht für '{self.display_name}' aktualisiert in {elapsed_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"[TOGGLE_BTN] Fehler beim Umschalten von '{self.display_name}': {e}", exc_info=True)
        
        # Aktualisiere den Zeitstempel der letzten Kanalaktivität
        if interaction.channel:
            self.cog.last_channel_activity[interaction.channel.id] = datetime.now(timezone.utc)

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

        # <<< DEBUG LOG HINZUGEFÜGT >>>
        display_name_log = server_config.get('name', server_config.get('docker_name', 'N/A')) if server_config else 'N/A'
        logger.debug(f"[ControlView.__init__] Initializing for '{display_name_log}'. is_running={is_running}, channel_has_control={channel_has_control_permission}, received allow_toggle={allow_toggle}")
        # <<< ENDE DEBUG LOG >>>

        # --- START: Add specific logging for flags ---
        # display_name_log = server_config.get('name', server_config.get('docker_name', 'N/A')) if server_config else 'N/A' # Bereits oben definiert
        if not allow_toggle:
             logger.debug(f"[ControlView.__init__] '{display_name_log}': allow_toggle=False received. ToggleButton will NOT be added.")

        # If called just for registration (cog or config is None), do not add items
        if not self.cog or not server_config:
            return

        # --- Existing logic --- #
        docker_name = server_config.get('docker_name')
        display_name = server_config.get('name', docker_name)

        # Check for Pending Status
        if self.cog.pending_actions.get(display_name):
             logger.debug(f"[ControlView] Server '{display_name}' is pending. No buttons will be added.")
             return # Stop initialization, add no buttons

        allowed_actions = server_config.get('allowed_actions', [])
        details_allowed = server_config.get('allow_detailed_status', True)
        is_expanded = cog_instance.expanded_states.get(display_name, False)

        # Determine which buttons to add based on state and permissions (only if not pending)
        if is_running:
            # Toggle Button (+/-) ist immer auf Reihe 0, wenn erlaubt
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
            # Nur Start-Button anzeigen, kein Toggle-Button für offline Server
            if channel_has_control_permission and "start" in allowed_actions:
                 self.add_item(ActionButton(cog_instance, server_config, "start", discord.ButtonStyle.secondary, None, "▶️", row=0))