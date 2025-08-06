# Discord Game Server Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

## Project Description

A versatile Discord bot for managing any game server. This bot provides a persistent panel with start/stop buttons, scheduled shutdowns, and activity logs, allowing you to control and automate your game server directly from Discord. It's designed to be easily configurable for a wide range of game server applications.

## Features

* 🎮   **Universal Game Server Control:** Configurable to start/stop virtually any game server application.
* 🚀   **Discord Integration:** Manage your server directly from a designated Discord channel.
* 📊   **Real-time Status Display:** Shows server running status, uptime, and estimated automatic shutdown time.
* ⏰   **Automated Shutdown:** Automatically shuts down the server after a configurable period of activity/uptime.
* 📜   **Command History:** Logs recent bot commands and who issued them for easy tracking.
* 🖲️   **Button-based Controls:** Intuitive Discord UI buttons for starting and stopping the server.
* 🧹   **Automated Channel Cleanup:** Keeps the control channel tidy by deleting old messages and non-command chat.
* 🔄   **Persistent Messages:** Key bot messages (control panel, status, history) automatically reappear and update across bot restarts.

---

## Installation and Setup

### Prerequisites

Before you begin, ensure you have the following:

* **Python 3.8+** installed on the machine where you intend to run the bot (this is typically your game server machine).
* **`pip`** (Python package installer), which usually comes with Python.
* A **Discord account** and a **Discord Server** where the bot will operate.
* **Administrator permissions** for your bot on your Discord server to manage messages and channels.

### 1. Clone the Repository

Open your terminal or command prompt and run:

```bash
git clone [https://github.com/gittygitlab/DiscordGameServerManager.git](https://github.com/gittygitlab/DiscordGameServerManager.git)
cd DiscordGameServerManager
```

### 2. Install Dependencies

Install the required Python libraries:
```Bash
pip install discord.py pytz
```
(Optional: After running the bot successfully, you can generate a requirements.txt file for easier future setup by running pip freeze > requirements.txt in your project directory.)
