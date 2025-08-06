import discord
from discord.ext import commands, tasks
import asyncio
import os
import subprocess
import datetime
import pytz
from collections import deque
import logging

# --- Configure logging to a file ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='a'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)


# =====================================================================
#                          C U S T O M   C O N F I G U R A T I O N
# =====================================================================

# Discord Bot Token: Obtain this from your Discord Developer Portal
# IMPORTANT: DO NOT SHARE THIS TOKEN.
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE" 

# Game Server Configuration
# Replace these with the actual commands and process name for your game server.
# Use the full path for your executable if necessary.
GAME_SERVER_START_COMMAND = r'start /B "" "C:\Path\To\Your\Game\Server.exe" -unattended -log'
GAME_SERVER_STOP_COMMAND = "taskkill /IM YourGameServerProcessName.exe /F"
GAME_SERVER_PROCESS_NAME = "YourGameServerProcessName.exe" # The exact process name to check for

# Discord Channel and Message IDs
# The Discord channel where the bot will operate and send persistent messages
SERVER_CHANNEL_ID = 1234567890123456789 # Replace with your actual channel ID

# File paths to store persistent message IDs (these files will be created/updated)
PERSISTENT_VIEW_MESSAGE_ID_FILE = "persistent_view_message_id.txt"
PERSISTENT_HISTORY_MESSAGE_ID_FILE = "persistent_history_message_id.txt"
PERSISTENT_STATUS_MESSAGE_ID_FILE = "persistent_status_message_id.txt"

# Server Automation Timings
SHUTDOWN_DELAY_HOURS = 12 # Hours until the server automatically shuts down after starting
STATUS_UPDATE_INTERVAL_MINUTES = 1 # How often the server status message is updated (in minutes)
DAILY_CLEAR_HOUR = 3 # Hour (24-hour format) for the daily channel clear task
DAILY_CLEAR_MINUTE = 0 # Minute for the daily channel clear task

# Timezone for logging and scheduling (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')
TARGET_TIMEZONE = pytz.timezone('America/Chicago')

# Bot Behavior Settings
MAX_COMMAND_HISTORY = 5 # Maximum number of recent commands to display in the history message
HELP_MESSAGE_DELETE_DELAY_SECONDS = 30 # How long the !serverhelp message stays before deleting itself and the command

# =====================================================================
#                      E N D   C U S T O M   C O N F I G U R A T I O N
# =====================================================================


# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

bot.current_panel_message_id = None
bot.current_history_message_id = None
bot.current_status_message_id = None
bot.command_history_list = deque(maxlen=MAX_COMMAND_HISTORY)
bot.server_start_time = None
bot.shutdown_task = None

# --- Helper Functions (attached to bot in on_ready for better scope) ---

async def check_server_process_func():
    """Checks if the game server process is currently running."""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {GAME_SERVER_PROCESS_NAME}', '/NH', '/FO', 'CSV'],
            capture_output=True,
            text=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return GAME_SERVER_PROCESS_NAME.lower() in result.stdout.lower() and "no tasks are running" not in result.stdout.lower()
    except Exception as e:
        logging.error(f"ERROR in check_server_process: {e}")
        return False

async def get_server_status_string_func():
    """Generates the formatted server status string content (without the leading title)."""
    server_running_status = await bot.check_server_process() 

    status_lines = []
    if server_running_status:
        status_lines.append("🟢 **Status:** Running")
        if bot.server_start_time:
            if bot.server_start_time.tzinfo is None:
                bot.server_start_time = TARGET_TIMEZONE.localize(bot.server_start_time)

            shutdown_time_ct = bot.server_start_time + datetime.timedelta(hours=SHUTDOWN_DELAY_HOURS)
            now_ct = datetime.datetime.now(TARGET_TIMEZONE)
            time_remaining = shutdown_time_ct - now_ct

            hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)

            status_lines.append(f"⏰ **Started At:** {bot.server_start_time.strftime('%m/%d/%y %H:%M:%S %Z')}")
            status_lines.append(f"🗓️ **Auto-Shutdown At:** {shutdown_time_ct.strftime('%m/%d/%y %H:%M:%S %Z')}")
            status_lines.append(f"⏳ **Time Remaining:** {hours}h {minutes}m")
        else:
            status_lines.append("⏰ **Started At:** Unknown (Bot may have restarted)")
            status_lines.append("🗓️ **Auto-Shutdown At:** Unknown")
            status_lines.append("⏳ **Time Remaining:** Unknown")
    else:
        status_lines.append("🔴 **Status:** Stopped")
        status_lines.append("Use `!serverhelp` for advanced commands.")
    
    return "\n".join(status_lines)

async def update_persistent_message(channel, message_id_attr, file_path, content_func, view=None):
    """Generic function to update or send a persistent message."""
    message_id = getattr(bot, message_id_attr)
    content = await content_func() if asyncio.iscoroutinefunction(content_func) else content_func()

    existing_message = None
    if message_id:
        try:
            existing_message = await channel.fetch_message(message_id)
        except discord.NotFound:
            logging.warning(f"Message {message_id} for {message_id_attr} not found. Will send a new one.")
            setattr(bot, message_id_attr, None) # Clear ID to ensure a new message is sent
        except discord.Forbidden:
            logging.error(f"Bot lacks permission to fetch/edit message {message_id} for {message_id_attr}. Will send a new one.")
            setattr(bot, message_id_attr, None)
        except Exception as e:
            logging.error(f"Failed to fetch message for {message_id_attr}: {e}. Will send a new one.")
            setattr(bot, message_id_attr, None)

    if existing_message:
        try:
            await existing_message.edit(content=content, view=view)
            logging.debug(f"Edited existing message {message_id} for {message_id_attr}.")
        except Exception as e:
            logging.error(f"Failed to edit existing message {message_id} for {message_id_attr}: {e}. Attempting to send a new one.")
            setattr(bot, message_id_attr, None) # Clear ID to force new message
            # Fall through to send a new message
            try:
                new_message = await channel.send(content=content, view=view)
                setattr(bot, message_id_attr, new_message.id)
                with open(file_path, "w") as f:
                    f.write(str(new_message.id))
                logging.debug(f"Sent new message and saved ID for {message_id_attr}: {new_message.id}.")
            except Exception as send_e:
                logging.error(f"Failed to send new message for {message_id_attr} after edit failure: {send_e}")
    else: # If no existing_message or ID was cleared
        try:
            new_message = await channel.send(content=content, view=view)
            setattr(bot, message_id_attr, new_message.id)
            with open(file_path, "w") as f:
                f.write(str(new_message.id))
            logging.debug(f"Sent new message and saved ID for {message_id_attr}: {new_message.id}.")
        except Exception as e:
            logging.error(f"Failed to send new persistent message for {message_id_attr}: {e}")


async def start_game_server_func(interaction_or_ctx):
    server_running_status = await bot.check_server_process()
    
    response_target = interaction_or_ctx.followup if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx
    channel_for_update = interaction_or_ctx.channel if isinstance(interaction_or_ctx, (discord.Interaction, commands.Context)) else interaction_or_ctx

    if server_running_status:
        bot.server_start_time = datetime.datetime.now(TARGET_TIMEZONE)
        if bot.shutdown_task and not bot.shutdown_task.done():
            bot.shutdown_task.cancel()
            logging.info("Existing shutdown task cancelled as server is already running (timer reset).")
        bot.shutdown_task = bot.loop.create_task(bot.schedule_shutdown(channel_for_update))
        logging.info(f"Shutdown timer reset for {SHUTDOWN_DELAY_HOURS} hours.")
        await response_target.send("The server was already running. Shutdown timer has been reset!", ephemeral=True)
        await bot.update_server_status_message(channel_for_update)
        return

    try:
        subprocess.Popen(GAME_SERVER_START_COMMAND, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        await asyncio.sleep(2)
        server_running_status = await bot.check_server_process()
        
        if server_running_status:
            bot.server_start_time = datetime.datetime.now(TARGET_TIMEZONE)
            await response_target.send("Game server started successfully!", ephemeral=True)
            if bot.shutdown_task and not bot.shutdown_task.done():
                bot.shutdown_task.cancel()
                logging.info("Existing shutdown task cancelled as server is starting.")
            bot.shutdown_task = bot.loop.create_task(bot.schedule_shutdown(channel_for_update))
            logging.info(f"New shutdown task scheduled for {SHUTDOWN_DELAY_HOURS} hours.")
        else:
            await response_target.send("Failed to confirm server started. Please check server logs manually.", ephemeral=True)

        await bot.update_server_status_message(channel_for_update)

    except Exception as e:
        logging.error(f"ERROR in start_game_server: {e}")
        await response_target.send(f"Error starting game server: {e}", ephemeral=True)

async def stop_game_server_func(interaction_or_ctx):
    server_running_status = await bot.check_server_process()

    if not server_running_status:
        response_target = interaction_or_ctx.followup if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx
        await response_target.send("The server is not running.", ephemeral=True)
        await bot.update_server_status_message(interaction_or_ctx.channel if isinstance(interaction_or_ctx, (discord.Interaction, commands.Context)) else interaction_or_ctx)
        return

    try:
        subprocess.run(GAME_SERVER_STOP_COMMAND, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        await asyncio.sleep(2)
        server_running_status = await bot.check_server_process()
        
        response_target = interaction_or_ctx.followup if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx
        channel_for_update = interaction_or_ctx.channel if isinstance(interaction_or_ctx, (discord.Interaction, commands.Context)) else interaction_or_ctx

        if not server_running_status:
            bot.server_start_time = None
            await response_target.send("Game server stopped successfully!", ephemeral=True)
        else:
            await response_target.send("Failed to confirm server stopped. Please check server manually.", ephemeral=True)

        await bot.update_server_status_message(channel_for_update)

        if bot.shutdown_task and not bot.shutdown_task.done():
            bot.shutdown_task.cancel()
            logging.info("Automated shutdown task cancelled as server was manually stopped.")
        bot.shutdown_task = None

    except Exception as e:
        logging.error(f"ERROR in stop_game_server: {e}")
        await response_target.send(f"Error stopping game server: {e}", ephemeral=True)

async def schedule_shutdown_func(channel):
    """
    Schedules an automated shutdown of the game server after SHUTDOWN_DELAY_HOURS.
    """
    try:
        logging.info(f"Automated shutdown scheduled for {SHUTDOWN_DELAY_HOURS} hours from now.")
        await asyncio.sleep(SHUTDOWN_DELAY_HOURS * 3600)

        if await bot.check_server_process():
            bot.command_history_list.append({
                'command': 'Automated Shutdown',
                'user': 'System',
                'timestamp': datetime.datetime.now(TARGET_TIMEZONE).strftime('%m/%d/%y %H:%M:%S %Z')
            })
            await bot.update_command_history_message(channel)
            await bot.stop_game_server(channel)
        else:
            logging.info("Automated shutdown skipped: Server was already stopped.")
    except asyncio.CancelledError:
        logging.info("Automated shutdown task was cancelled.")
    except Exception as e:
        logging.error(f"Error in automated shutdown task: {e}")


# --- Attach helper functions to the bot instance ---
bot.check_server_process = check_server_process_func
bot.start_game_server = start_game_server_func
bot.stop_game_server = stop_game_server_func
bot.schedule_shutdown = schedule_shutdown_func
bot.update_persistent_message = update_persistent_message
bot.get_server_status_string = get_server_status_string_func


async def update_server_status_message_wrapper(channel):
    # Now adds the "Game Server Status:" title here
    status_content = "**Game Server Status:**\n" + await bot.get_server_status_string()
    await bot.update_persistent_message(channel, "current_status_message_id", PERSISTENT_STATUS_MESSAGE_ID_FILE, lambda: status_content)

async def update_command_history_message_wrapper(channel):
    history_content_func = lambda: "**Recent Activity:**\n" + \
                                   ("No activity yet." if not bot.command_history_list else
                                    "\n".join([f"- `{entry['command']}` by {entry['user']} at {entry['timestamp']}"
                                               for entry in bot.command_history_list]))
    await bot.update_persistent_message(channel, "current_history_message_id", PERSISTENT_HISTORY_MESSAGE_ID_FILE, history_content_func)

bot.update_server_status_message = update_server_status_message_wrapper
bot.update_command_history_message = update_command_history_message_wrapper

# --- New: Periodic Status Update Loop ---
@tasks.loop(minutes=STATUS_UPDATE_INTERVAL_MINUTES)
async def status_update_loop():
    channel = bot.get_channel(SERVER_CHANNEL_ID)
    if channel:
        await bot.update_server_status_message(channel)
    else:
        logging.warning(f"Status update loop: Server control channel {SERVER_CHANNEL_ID} not found.")

# --- NEW: Daily Clear Channel Loop ---
@tasks.loop(time=datetime.time(hour=DAILY_CLEAR_HOUR, minute=DAILY_CLEAR_MINUTE, tzinfo=TARGET_TIMEZONE))
async def daily_clear_channel_loop():
    logging.info("Attempting to run daily_clear_channel_loop.")
    channel = bot.get_channel(SERVER_CHANNEL_ID)
    if channel:
        logging.info(f"Executing daily clear_channel in channel {SERVER_CHANNEL_ID}.")
        class DummyContext:
            def __init__(self, bot_instance, channel_obj):
                self.bot = bot_instance
                self.channel = channel_obj
                self.message = None 
                
            async def send(self, content, ephemeral=False, delete_after=None):
                logging.info(f"[Daily Clear Task] Bot would send: {content}")
                pass
        
        dummy_ctx = DummyContext(bot, channel)
        await clear_channel(dummy_ctx)
        logging.info("Daily clear_channel command finished.")
    else:
        logging.warning(f"Daily clear_channel loop: Server control channel {SERVER_CHANNEL_ID} not found.")

# --- Server Control Buttons View ---
class ServerControlView(discord.ui.View):
    def __init__(self, bot_instance, server_channel_id):
        super().__init__(timeout=None)
        self.bot_instance = bot_instance
        self.server_channel_id = server_channel_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.channel_id != self.server_channel_id:
            await interaction.response.send_message("Please use these buttons in the designated server control channel.", ephemeral=True)
            return False
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            return True
        except discord.errors.InteractionResponded:
            logging.debug(f"Interaction for {interaction.data.get('custom_id', 'unknown')} already responded to (e.g., double click).")
            return True
        except Exception as e:
            logging.error(f"Failed to defer interaction for {interaction.data.get('custom_id', 'unknown')}: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Error deferring interaction: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"Error deferring interaction: {e}", ephemeral=True)
            except Exception as fe:
                logging.critical(f"CRITICAL ERROR: Also failed to send followup after deferral failure: {fe}")
            return False

    async def _handle_button_action(self, interaction: discord.Interaction, action_name: str, action_func):
        logging.debug(f"{action_name} button callback initiated.")
        try:
            await action_func(interaction)
            self.bot_instance.command_history_list.append({
                'command': f'{action_name} (Button)',
                'user': interaction.user.display_name,
                'timestamp': datetime.datetime.now(TARGET_TIMEZONE).strftime('%m/%d/%y %H:%M:%S %Z')
            })
            await self.bot_instance.update_command_history_message(interaction.channel)
            logging.debug(f"{action_name} called successfully for button.")
        except Exception as e:
            logging.error(f"An unhandled exception occurred in {action_name} button callback: {e}")
            await interaction.followup.send(f"An unexpected error occurred during server {action_name.lower()}: {e}", ephemeral=True)

    @discord.ui.button(label="Start Server", style=discord.ButtonStyle.success, custom_id="start_server")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button_action(interaction, "Start Server", self.bot_instance.start_game_server)

    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.danger, custom_id="stop_server")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button_action(interaction, "Stop Server", self.bot_instance.stop_game_server)

# --- Bot Events ---
@bot.event
async def on_ready():
    logging.info(f"Bot logged in as {bot.user}")
    logging.info(f"Bot ID: {bot.user.id}")

    channel = bot.get_channel(SERVER_CHANNEL_ID)
    if channel:
        # Step 1: Run clear_channel at script start
        logging.info("Running clear_channel at bot startup.")
        class DummyContextStartup:
            def __init__(self, bot_instance, channel_obj):
                self.bot = bot_instance
                self.channel = channel_obj
                self.message = None 
            async def send(self, content, ephemeral=False, delete_after=None):
                logging.info(f"[Startup Clear Task] Bot would send: {content}")
                pass
        
        dummy_ctx_startup = DummyContextStartup(bot, channel)
        await clear_channel(dummy_ctx_startup)
        logging.info("Startup clear_channel command finished.")

        # Step 2: Load Persistent Message IDs FIRST
        for file_path, attr_name in [
            (PERSISTENT_VIEW_MESSAGE_ID_FILE, "current_panel_message_id"),
            (PERSISTENT_HISTORY_MESSAGE_ID_FILE, "current_history_message_id"),
            (PERSISTENT_STATUS_MESSAGE_ID_FILE, "current_status_message_id")
        ]:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    message_id_str = f.read().strip()
                if message_id_str:
                    try:
                        setattr(bot, attr_name, int(message_id_str))
                    except ValueError:
                        logging.error(f"Invalid message ID stored in {file_path}. Clearing file.")
                        os.remove(file_path)
                        setattr(bot, attr_name, None)
                else:
                    setattr(bot, attr_name, None)

        # Step 3: Initialize/Update all persistent messages sequentially
        logging.info("Initializing/Updating all persistent messages.")
        
        panel_view = ServerControlView(bot, SERVER_CHANNEL_ID)
        await bot.update_persistent_message(
            channel, 
            "current_panel_message_id", 
            PERSISTENT_VIEW_MESSAGE_ID_FILE, 
            lambda: "Use the buttons below to control the game server:", 
            view=panel_view
        )
        
        # Give a small delay to ensure Discord API has time to process the first send
        await asyncio.sleep(0.1) 

        await bot.update_server_status_message(channel)
        
        # Another small delay
        await asyncio.sleep(0.1) 

        await bot.update_command_history_message(channel)
        
        bot.add_view(panel_view) # Register the view for persistence after message is set up
        logging.info("All persistent messages initialized/updated.")

    else:
        logging.warning(f"Server control channel {SERVER_CHANNEL_ID} not found on ready. Cannot initialize panel messages.")

    # Step 4: Initial server status check (for logging and shutdown task)
    if await bot.check_server_process():
        logging.info(f"Detected {GAME_SERVER_PROCESS_NAME} is already running.")
        if channel and bot.shutdown_task is None: 
            bot.server_start_time = datetime.datetime.now(TARGET_TIMEZONE) 
            bot.shutdown_task = bot.loop.create_task(bot.schedule_shutdown(channel))
            logging.info(f"Shutdown task initiated on ready for existing server.")
    else:
        logging.info(f"{GAME_SERVER_PROCESS_NAME} is not detected as running.")
        bot.server_start_time = None
        if bot.shutdown_task and not bot.shutdown_task.done():
            bot.shutdown_task.cancel()
            bot.shutdown_task = None
            logging.info("Existing shutdown task cancelled as server is not running on ready.")

    # Step 5: Start the periodic loops
    if not status_update_loop.is_running():
        status_update_loop.start()
        logging.info("Status update loop started.")

    if not daily_clear_channel_loop.is_running():
        daily_clear_channel_loop.start()
        logging.info("Daily clear channel loop started.")


@bot.event
async def on_command_error(ctx, error):
    if ctx.channel.id == SERVER_CHANNEL_ID and isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Sorry, that command doesn't exist.", delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing arguments. Please check the command usage.", delete_after=10)
    else:
        logging.error(f"An unexpected error occurred during command execution: {error}")
        await ctx.send(f"An unexpected error occurred: {error}", delete_after=10)

    if isinstance(ctx, commands.Context) and ctx.message and \
       ctx.message.id not in {bot.current_panel_message_id, bot.current_history_message_id, bot.current_status_message_id}:
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            logging.error(f"Bot lacks 'manage_messages' permission to delete error-causing command message.")
        except Exception as e:
            logging.error(f"Failed to delete error-causing command message: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != SERVER_CHANNEL_ID:
        await bot.process_commands(message)
        return

    ctx = await bot.get_context(message)
    if ctx.valid:
        bot.command_history_list.append({
            'command': ctx.command.name,
            'user': ctx.author.display_name,
            'timestamp': datetime.datetime.now(TARGET_TIMEZONE).strftime('%m/%d/%y %H:%M:%S %Z')
        })
        await bot.update_command_history_message(message.channel)
        await bot.invoke(ctx)
    else:
        if message.id not in {bot.current_panel_message_id, bot.current_history_message_id, bot.current_status_message_id}:
            logging.debug(f"Deleting non-command message '{message.content}' in control channel.")
            try:
                await message.delete()
            except discord.Forbidden:
                logging.error(f"Bot lacks 'manage_messages' permission to delete user's invalid message.")
            except Exception as e:
                logging.error(f"Failed to delete user's invalid message: {e}")
        else:
            logging.debug(f"Ignoring deletion of persistent message ID {message.id} in on_message.")
    

# --- Bot Commands ---
@bot.command(name="panel", help="Sends/updates the server control panel, status, and command history messages.")
async def panel(ctx):
    if ctx.channel.id != SERVER_CHANNEL_ID:
        await ctx.send("Please use this command in the designated server control channel.", ephemeral=True)
        return
    
    panel_view = ServerControlView(bot, SERVER_CHANNEL_ID)
    
    await bot.update_persistent_message(
        ctx.channel, 
        "current_panel_message_id", 
        PERSISTENT_VIEW_MESSAGE_ID_FILE, 
        lambda: "Use the buttons below to control the game server:", 
        view=panel_view
    )

    await bot.update_server_status_message(ctx.channel)

    await bot.update_command_history_message(ctx.channel)


@bot.command(name="startserver", help="Starts the game server.")
async def startserver(ctx):
    if ctx.channel.id != SERVER_CHANNEL_ID:
        await ctx.send("Please use this command in the designated server control channel.", ephemeral=True)
        return
    await ctx.send("Attempting to start the game server...", ephemeral=True)
    await bot.start_game_server(ctx)


@bot.command(name="stopserver", help="Stops the game server.")
async def stopserver(ctx):
    if ctx.channel.id != SERVER_CHANNEL_ID:
        await ctx.send("Please use this command in the designated server control channel.", ephemeral=True)
        return
    await ctx.send("Attempting to stop the game server...", ephemeral=True)
    await bot.stop_game_server(ctx)

@bot.command(name="serverstatus", help="Checks and updates the status of the game server.")
async def serverstatus(ctx):
    if ctx.channel.id != SERVER_CHANNEL_ID:
        await ctx.send("This command is only available in the designated server control channel.", ephemeral=True)
        return
    await bot.update_server_status_message(ctx.channel)
    await ctx.send("Server status display updated.", ephemeral=True)


@bot.command(name="serverhelp", help="Shows commands specific to this server bot.")
async def serverhelp(ctx):
    if ctx.channel.id != SERVER_CHANNEL_ID:
        await ctx.send("This command is only available in the designated server control channel.", ephemeral=True, delete_after=10)
        return

    help_message_content = """
**Available Server Commands (All Users):**
`!panel` - Sends/updates the server control panel, status, and command history messages.
`!startserver` - Starts the game server.
`!stopserver` - Stops the game server.
`!serverstatus` - Checks and updates the displayed status of the game server.
`!clear_channel` - Clears all messages in this channel except the panel, status, and history messages.
`!serverhelp` - Shows this help message.

**Note:** Buttons on the panel provide easier control for Start/Stop.
"""
    help_msg = await ctx.send(help_message_content)
    
    # Wait for the configured delay
    await asyncio.sleep(HELP_MESSAGE_DELETE_DELAY_SECONDS) 
    
    try:
        # Delete the bot's help message
        await help_msg.delete() 
    except (discord.NotFound, discord.Forbidden) as e:
        logging.warning(f"Could not delete !serverhelp response (bot's message): {e}")
    except Exception as e:
        logging.error(f"Failed to delete !serverhelp response (bot's message): {e}")

    # Delete the original command message from the user
    if ctx.message:
        try:
            await ctx.message.delete()
        except (discord.NotFound, discord.Forbidden) as e:
            logging.warning(f"Could not delete original !serverhelp command message (user's message): {e}")
        except Exception as e:
            logging.error(f"Failed to delete original !serverhelp command message (user's message): {e}")


@bot.command(name="clear_channel", help="Clears all messages in this channel except the panel, status, and history messages.")
async def clear_channel(ctx):
    if ctx.channel.id != SERVER_CHANNEL_ID:
        if isinstance(ctx, commands.Context):
            await ctx.send("This command can only be used in the designated server control channel.", ephemeral=True)
        return

    if isinstance(ctx, commands.Context):
        await ctx.send("Attempting to clear channel history...", ephemeral=True)
    
    ids_to_keep = set()
    if bot.current_panel_message_id: ids_to_keep.add(bot.current_panel_message_id)
    if bot.current_history_message_id: ids_to_keep.add(bot.current_history_message_id)
    if bot.current_status_message_id: ids_to_keep.add(bot.current_status_message_id)
    
    if isinstance(ctx, commands.Context) and ctx.message:
        ids_to_keep.add(ctx.message.id)

    messages_to_bulk_delete = []
    individually_deleted_count = 0
    total_messages_processed = 0

    try:
        async for message in ctx.channel.history(limit=None):
            total_messages_processed += 1
            if message.id not in ids_to_keep:
                if (datetime.datetime.now(datetime.timezone.utc) - message.created_at).days < 14:
                    messages_to_bulk_delete.append(message)
                else:
                    try:
                        await message.delete()
                        individually_deleted_count += 1
                        await asyncio.sleep(0.5)
                    except (discord.Forbidden, discord.HTTPException) as e:
                        logging.warning(f"Could not delete old message {message.id} (older than 14 days): {e}")
                    except Exception as e:
                        logging.error(f"Error deleting old message {message.id}: {e}")

        if messages_to_bulk_delete:
            await ctx.channel.delete_messages(messages_to_bulk_delete)
        
        bulk_deleted_count = len(messages_to_bulk_delete)
        deleted_count = bulk_deleted_count + individually_deleted_count
            
        if isinstance(ctx, commands.Context):
            await ctx.send(
                f"Successfully cleared {deleted_count} messages. "
                f"({bulk_deleted_count} recent messages, {individually_deleted_count} older messages deleted individually).", 
                ephemeral=True, 
                delete_after=15
            )
        else:
            logging.info(f"Startup/Daily clear task: Successfully cleared {deleted_count} messages.")

    except discord.Forbidden:
        logging.error(f"Bot lacks 'manage_messages' permission to clear the channel.")
        if isinstance(ctx, commands.Context):
            await ctx.send("I don't have permission to delete messages in this channel. Please grant 'Manage Messages' permission.", ephemeral=True)
    except Exception as e:
        logging.error(f"ERROR in clear_channel command: {e}")
        if isinstance(ctx, commands.Context):
            await ctx.send(f"An error occurred while trying to clear the channel: {e}", ephemeral=True)


# --- Run the Bot ---
if __name__ == "__main__":
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logging.critical("Bot login failed. Check if DISCORD_BOT_TOKEN is correct and valid. Double-check for typos or if the token was revoked/regenerated elsewhere.")
    except Exception as e:
        logging.critical(f"An unhandled error occurred during bot startup: {e}")
