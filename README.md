# Discord Game Server Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
## Project Description

A versatile Discord bot for managing any game server. Features start/stop, auto-shutdown, persistent status, and command history.
This bot aims to provide a simple, centralized control panel within Discord for game administrators and community members.

## Features

* 🎮   **Universal Game Server Control:** Configurable to start/stop any game server application.
* 🚀   **Discord Integration:** Manage your server directly from a designated Discord channel.
* 📊   **Real-time Status Display:** Shows server running status, uptime, and estimated shutdown time.
* ⏰   **Automated Shutdown:** Automatically shuts down the server after a configurable period of inactivity/uptime.
* 📜   **Command History:** Logs recent bot commands and who issued them.
* 🖲️   **Button-based Controls:** Easy-to-use buttons for starting and stopping the server.
* 🧹   **Automated Channel Cleanup:** Keeps the control channel tidy by deleting old messages.
* 🔄   **Persistent Messages:** Key bot messages (panel, status, history) persist across bot restarts.

## Installation and Setup

### Prerequisites

* Python 3.8+ installed on your server machine.
* `pip` (Python package installer).
* A Discord account and a Discord Server where the bot will operate.
* A Discord Bot Application and Token (see instructions below).
* Admin permissions for your bot on your Discord server.

### 1. Clone the Repository

```bash
git clone [https://github.com/gittygitlab/DiscordGameServerManager.git](https://github.com/gittygitlab/DiscordGameServerManager.git)
cd DiscordGameServerManager
