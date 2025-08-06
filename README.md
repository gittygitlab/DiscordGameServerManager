Discord Game Server Manager

Project Description

A versatile Discord bot for managing any game server. This bot provides a persistent panel with start/stop buttons, scheduled shutdowns, and activity logs, allowing you to control and automate your game server directly from Discord. It's designed to be easily configurable for a wide range of game server applications.

Features

    🎮   Universal Game Server Control: Configurable to start/stop virtually any game server application.

    🚀   Discord Integration: Manage your server directly from a designated Discord channel.

    📊   Real-time Status Display: Shows server running status, uptime, and estimated automatic shutdown time.

    ⏰   Automated Shutdown: Automatically shuts down the server after a configurable period of activity/uptime.

    📜   Command History: Logs recent bot commands and who issued them for easy tracking.

    🖲️   Button-based Controls: Intuitive Discord UI buttons for starting and stopping the server.

    🧹   Automated Channel Cleanup: Keeps the control channel tidy by deleting old messages and non-command chat.

    🔄   Persistent Messages: Key bot messages (control panel, status, history) automatically reappear and update across bot restarts.

Installation and Setup

Prerequisites

Before you begin, ensure you have the following:

    Python 3.8+ installed on the machine where you intend to run the bot (this is typically your game server machine).

    pip (Python package installer), which usually comes with Python.

    A Discord account and a Discord Server where the bot will operate.

    Administrator permissions for your bot on your Discord server to manage messages and channels.

1. Clone the Repository

Open your terminal or command prompt and run:
Bash

git clone https://github.com/gittygitlab/DiscordGameServerManager.git
cd DiscordGameServerManager

2. Install Dependencies

Install the required Python libraries:
Bash

pip install discord.py pytz

(Optional: After running the bot successfully, you can generate a requirements.txt file for easier future setup by running pip freeze > requirements.txt in your project directory.)

3. Create Your Discord Bot Application

    Go to the Discord Developer Portal.

    Click "New Application" and give it a descriptive name (e.g., "My Game Server Bot").

    Navigate to the "Bot" tab on the left sidebar.

    Click "Add Bot" then confirm with "Yes, do it!".

    Copy Token: Under "TOKEN", click "Copy Token". This is your bot's secret key. Keep it confidential!

    Enable Intents: Scroll down to "Privileged Gateway Intents" and enable all three:

        PRESENCE INTENT

        SERVER MEMBERS INTENT

        MESSAGE CONTENT INTENT

    Invite Your Bot to Your Server:

        Go to the "OAuth2" -> "URL Generator" tab.

        Under "SCOPES", select bot.

        Under "BOT PERMISSIONS", select the following:

            Read Messages/View Channels

            Send Messages

            Manage Messages (Crucial for channel clearing and updating persistent messages)

        Copy the generated URL at the bottom and paste it into your web browser. Select your Discord server from the dropdown and authorize the bot.

4. Configuration

Open the main.py (or whatever you named your bot script) file in a text editor.

Locate the C U S T O M   C O N F I G U R A T I O N section at the very top and update the variables:

    DISCORD_BOT_TOKEN: Paste the bot token you copied from the Discord Developer Portal here.
    Python

DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE" # Replace this!

SERVER_CHANNEL_ID: This is the ID of the Discord channel where the bot will operate. To get a channel ID, enable Discord's Developer Mode (User Settings > Advanced > Developer Mode), then right-click on the desired channel in Discord and select "Copy ID".
Python

SERVER_CHANNEL_ID = 1234567890123456789 # Replace with your actual channel ID

GAME_SERVER_START_COMMAND: The exact command used to start your game server. This should be the command you would run in your terminal/command prompt to launch the server. Use absolute paths to the executable.

    Example (Windows): r'start /B "" "C:\Games\MyGameServer\Server.exe" -config MyConfig.ini'

    Example (Linux): '/home/user/games/mygameserver/start_server.sh'

Python

GAME_SERVER_START_COMMAND = r'start /B "" "C:\Path\To\Your\Game\Server.exe" -unattended -log' # REPLACE THIS!

GAME_SERVER_STOP_COMMAND: The command to stop your game server. For Windows, taskkill is common. For Linux, pkill or killall might be used with the process name.

    Example (Windows): taskkill /IM MyGameServerProcessName.exe /F

    Example (Linux): pkill -f YourGameServerProcessName

Python

GAME_SERVER_STOP_COMMAND = "taskkill /IM YourGameServerProcessName.exe /F" # REPLACE THIS!

GAME_SERVER_PROCESS_NAME: The exact executable file name of your game server process (e.g., Server.exe, MyGameServer.x86_64). This is used by the bot to check if the server is running.
Python

    GAME_SERVER_PROCESS_NAME = "YourGameServerProcessName.exe" # REPLACE THIS!

    SHUTDOWN_DELAY_HOURS: Set the number of hours after which the server will automatically shut down if it was started by the bot.

    STATUS_UPDATE_INTERVAL_MINUTES: How often the bot will refresh the server status message in the Discord channel.

    DAILY_CLEAR_HOUR and DAILY_CLEAR_MINUTE: The time (24-hour format) when the bot will automatically clear the Discord channel daily.

    TARGET_TIMEZONE: Set your local timezone for accurate scheduling and timestamps (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo'). Find a full list of timezone names here.

    Adjust MAX_COMMAND_HISTORY and HELP_MESSAGE_DELETE_DELAY_SECONDS as desired.

5. Run the Bot

Once configured, you can run the bot from your terminal:
Bash

python main.py # Or whatever you named your bot script, e.g., python game_server_bot.py

For continuous operation, especially on a server, consider using tools like screen (Linux) or setting it up as a Windows Service, or using a process manager like pm2 (via ecosystem.config.js for Python apps).

Bot Commands (in Discord)

Ensure you are in the configured SERVER_CHANNEL_ID for these commands to work.

    !panel - Sends/updates the main control panel, status, and command history messages. (Run this once after setup, or if the messages disappear.)

    !startserver - Starts the game server.

    !stopserver - Stops the game server.

    !serverstatus - Checks and updates the displayed status of the game server.

    !clear_channel - Clears all messages in the channel except the main bot messages (panel, status, history).

    !serverhelp - Displays a list of available bot commands. This message will automatically disappear after 30 seconds, along with your original command message.

Contributing

Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please feel free to open an issue or submit a pull request on the GitHub repository.

License

This project is licensed under the MIT License - see the LICENSE file for details.
