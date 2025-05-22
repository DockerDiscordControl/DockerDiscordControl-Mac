# DockerDiscordControl (DDC)

**Homepage:** [https://ddc.bot](https://ddc.bot)

Control your Docker containers directly from Discord! This application provides a Discord bot and a web interface to manage specified Docker containers (start, stop, restart, view status) and view container logs.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/DockerDiscordControl/DockerDiscordControl)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/DockerDiscordControl/DockerDiscordControl/blob/main/LICENSE)

## Features

*   **Discord Bot:**
    *   View status of configured containers (Online/Offline, CPU/RAM/Uptime if enabled).
    *   Start, stop, and restart permitted containers via buttons or slash commands.
    *   Expand/collapse detailed status information.
    *   Slash commands (`/serverstatus`, `/ss`, `/command`, `/control`, `/help`, `/ping`).
    *   Comprehensive scheduling system (see details below).
    *   Permission system per channel (Control Panel vs. Status-Only).
    *   Automatic status message updates.
    *   Optional heartbeat monitoring integration.
    *   Configurable bot language (English, German, French).
    
### Scheduling System

DDC includes a powerful scheduling system to automate container management:

* **One-time Tasks**: `/schedule_once` - Run actions on specific date and time
* **Recurring Tasks**:
  * `/schedule_daily` - Run actions every day at specified times
  * `/schedule_weekly` - Run actions on selected days of the week
  * `/schedule_monthly` - Run actions on selected days of the month
  * `/schedule_yearly` - Run actions on specific dates each year
* **Management Commands**:
  * `/schedule_info` - List all scheduled tasks with filtering options
  * Currently, task management is available through the web interface:
    * Delete tasks in the web UI
    * View complete schedule information
  * **Coming Soon**: Enhanced Discord management with direct buttons for task deletion and editing

**Examples of use cases:**
* Restart game servers at specific times
* Start backup containers at night and stop them after completion
* Schedule regular maintenance tasks at times with low server usage
* Automatically restart services that require periodic refreshes

**Note on Day Selection:** Due to Discord's 25-option limit for autocomplete, the day selection in scheduling commands shows a strategic subset of days (1-5, 7, 9, 10, 12-15, 17, 18, 20-22, 24-28, 30, 31). You can still type any valid day manually.
*   **Web Interface:**
    *   Configure bot token, server ID, language, timezone, and update intervals.
    *   Select which Docker containers the bot should manage.
    *   Set permissions for each container (status, start, stop, restart).
    *   Configure channel permissions for Discord commands.
    *   View recent container logs (with level filtering).
    *   View persistent user action log (start/stop/restart/save/clear actions).
    *   Download monitor script for heartbeat monitoring.
*   **Persistence:** Configuration and action logs are stored in mounted volumes.
*   **Performance & Security:** 
    *   Optimized Gunicorn worker configuration based on CPU cores.
    *   Efficient resource utilization with 2 CPU cores and 512MB memory allocation.
    *   Rate limiting for login attempts to prevent brute force attacks.
*   Intelligent Docker container caching with background updates.

## Installation

**⚠️ SECURITY WARNING:** Mounting the Docker socket (`/var/run/docker.sock`) into the container grants the application extensive control over your Docker environment. This is necessary for DDC to function, but it represents a significant security risk if the application or the container itself is compromised. Only run this application in trusted environments and ensure your host system is secured. Access to the Web UI should be restricted (see Authentication below).

## Getting Started

### Bot Setup Prerequisites

Before installing DockerDiscordControl, you need to create a Discord bot:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Navigate to the "Bot" tab and click "Add Bot"
4. Under the "Privileged Gateway Intents" section, enable:
   - Server Members Intent
   - Message Content Intent
5. Copy your bot token (you'll need it during configuration)
6. Go to the "OAuth2" > "URL Generator" section
7. Select scopes: `bot` and `applications.commands` 
8. Select bot permissions: `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`, `Add Reactions`, `Use Slash Commands`
9. Use the generated URL to invite the bot to your server

Now choose the installation method that suits your system:

### Method 1: Standard Docker (using Docker Compose - Recommended)

This is the recommended method for most users running Docker on Linux, macOS, or Windows.

**Prerequisites:**

*   Docker: [Install Docker](https://docs.docker.com/engine/install/)
*   Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/) (v2 or later recommended)

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DockerDiscordControl/DockerDiscordControl.git
    cd DockerDiscordControl
    ```
2.  **Create necessary directories:**
    *   Create a `config` directory: `mkdir config`
    *   Create a `logs` directory: `mkdir logs`
    *(These will be mounted into the container)*
3.  **Create a `.env` file:**
    *   Create a file named `.env` in the `DockerDiscordControl` directory.
    *   Generate a secure secret key (e.g., using `openssl rand -hex 32` on Linux/macOS or a password generator) and add it to the `.env` file:
        ```dotenv
        # Required - Flask secret key (security critical)
        FLASK_SECRET_KEY=your_generated_32_byte_hex_key_here

        # Optional - Docker configuration
        # DOCKER_SOCKET=unix:///var/run/docker.sock
        # DOCKER_HOST=unix:///var/run/docker.sock

        # Optional - Web UI configuration
        # DDC_ADMIN_PASSWORD=your_secure_admin_password

        # Optional - Performance tuning
        # DDC_DOCKER_CACHE_DURATION=75
        # DDC_BACKGROUND_REFRESH_INTERVAL=30
        ```
        *Example for FLASK_SECRET_KEY:* `FLASK_SECRET_KEY=f236ea1267964ddcf65ab2158569ac3bf8ad7e1dd0d3c872fbe53cc1d5a54589`
4.  **(Optional) Adjust `docker-compose.yml`:**
    *   If your Docker socket is not at `/var/run/docker.sock`, update the volume path.
    *   By default, the `config` and `logs` directories in your project folder are mounted. If you prefer different host paths, change the volume lines. Example using relative paths:
        ```yaml
        volumes:
          - /var/run/docker.sock:/var/run/docker.sock
          - ./config:/app/config # Maps local config folder
          - ./logs:/app/logs     # Maps local logs folder
        ```
5.  **Build and run the container:**
    ```bash
    docker compose up --build -d
    ```
    *(Use `docker-compose` instead of `docker compose` if you have an older version)*
6.  **Access the Web UI:** Open your browser and go to `http://<your-server-ip>:8374`.
7.  **Login:** You will be prompted for a username and password. Use:
    *   **Username:** `admin`
    *   **Password:** `admin` (default)
8.  **Configure:** Follow the instructions in the Web UI. **It is highly recommended to change the default password immediately** via the "Web UI Authentication" section.
9.  **Restart Container:** After saving the initial configuration (especially the bot token and guild ID), restart the container for the bot to pick up the changes:
    ```bash
    docker compose restart
    ```

**Usage:**

*   **Logs:** `docker compose logs -f`
*   **Stop:** `docker compose down`
*   **Start:** `docker compose up -d`

**Resource Allocation:**

By default, the container is configured with the following resource limits:
*   **CPU:** 2.0 cores (can use up to 2 full CPU cores)
*   **Memory:** 512MB maximum with 128MB reservation
*   **Note:** You can adjust these values in the `docker-compose.yml` file if your environment requires different resource allocations.

### Method 2: Unraid (using Community Applications)

This is the easiest method for Unraid users.

**Prerequisites:**

*   Unraid 6.x
*   Community Applications (CA) plugin installed.

**Steps:**

1.  **Install via CA:**
    *   Go to the "Apps" tab in your Unraid web interface.
    *   Search for "DockerDiscordControl" (or the name you choose when submitting).
    *   Click "Install".
2.  **Configure Template:**
    *   **Port:** The default host port is `8374`. Change it if it conflicts with another service.
    *   **Volumes:**
        *   `/app/config`: Map this to a persistent path on your Unraid server where the `config.json` will be stored (e.g., `/mnt/user/appdata/dockerdiscordcontrol/config`). **This is crucial!**
        *   `/app/logs`: Map this to a persistent path for the `user_actions.log` (e.g., `/mnt/user/appdata/dockerdiscordcontrol/logs`).
        *   `/var/run/docker.sock`: Keep this mapping as is to allow container interaction.
    *   **Environment Variable:**
        *   `FLASK_SECRET_KEY`: Generate a secure 32-byte hex key (e.g., using `openssl rand -hex 32` in the Unraid terminal or a password generator) and paste it here. **Do not leave this blank or use a weak key!**
        *   **(Optional) `DDC_ADMIN_PASSWORD`:** You can set the initial Web UI admin password here. If left blank, it defaults to `admin`. It's recommended to change this later via the Web UI.
3.  **Apply:** Click "Apply" or "Done" to start the container.
4.  **Access the Web UI:** Open your browser and go to `http://<your-unraid-ip>:8374` (or the host port you configured).
5.  **Login:** Use username `admin` and the password you set in the template (or the default `admin`).
6.  **Configure:** Follow the instructions in the Web UI. **Change the password if you used the default.**
7.  **Restart Container:** After saving the initial configuration, restart the container from the Unraid Docker tab.

## Configuration

Configuration is primarily done via the **secured** Web UI accessible at `http://<your-server-ip>:8374`. Login with username `admin` and the password you set (default: `admin`).

Key settings include:

*   **Web UI Password:** Change the default password!
*   **Discord Bot Token:** Your bot's secret token from the Discord Developer Portal.
*   **Discord Server (Guild) ID:** The ID of the server where the bot will operate.
*   **Bot Language:** Language for the bot's responses in Discord (en, de, fr).
*   **Timezone:** Timezone for timestamps shown in the Web UI and logs.
*   **Server Selection:** Choose which Docker containers the bot can see and manage.
*   **Permissions:** Define allowed actions (status, start, stop, restart) per container.
*   **Channel Permissions:** Configure which Discord channels can use which commands (`/serverstatus`, `/command`, `/control`).

### Channel-Based Permission System

DDC implements a comprehensive channel-based permission system that lets administrators control which Docker management functions are available in specific Discord channels:

* **Read-Only Status Channels:** Configure channels where users can only view container status but not control them. Perfect for public monitoring channels.
* **Control Channels:** Set up channels where authorized users can execute control commands like start, stop, and restart.
* **Scheduling Control:** Determine which channels can access scheduling functionality.
* **Command Access:** Precisely define which slash commands are available in each channel:
  * `/serverstatus` (or `/ss`) - Display container status messages
  * `/command` (or `/control`) - Execute container control actions
  * `/schedule_once`, `/schedule_daily`, etc. - Create scheduled tasks for containers

This granular permission system allows for scenarios like:
* A public "#server-status" channel where everyone can see server status but not control anything
* A restricted "#admin-controls" channel where server administrators can fully manage containers
* A "#dev-servers" channel where only development-related containers can be controlled

All permissions are easily configured through the web interface, with no coding required.
*   **Intervals:** Configure status update frequency and inactivity timeouts.
*   **Heartbeat Monitoring:** Optional setup to monitor bot health.

**Remember to restart the container after significant configuration changes (like Token, Guild ID, Server Selection) for the bot process to apply them.**

## Logs

*   **Container Log:** View the last 200 lines in the Web UI (with level filtering) or access the full logs via `docker logs ddc` (or `docker compose logs -f`). These logs are managed by Docker's logging driver (json-file by default) and are subject to rotation.
*   **User Action Log:** Viewable and downloadable in the Web UI. This log tracks actions initiated by users (e.g., Start/Stop via Discord, Save Config via Web UI, Clear Action Log). It's stored persistently in the `/app/logs` volume (if mounted) and is *not* automatically rotated. It can be cleared manually via the Web UI.

## Docker Container Caching and Message Updates

DockerDiscordControl employs an intelligent caching mechanism and background tasks to efficiently manage Docker container statuses and update Discord messages, minimizing load on the Docker API and ensuring responsive updates. This system involves two primary background tasks working in concert:

1.  **Background Cache Refresh (`status_update_loop`):**
    *   An internal background task, the `status_update_loop`, automatically refreshes a local cache of container statuses by default **every 30 seconds**.
    *   This task queries the live status (running state, CPU/RAM usage, uptime, etc.) of all configured Docker containers.
    *   The retrieved information is stored in an in-memory cache along with a timestamp.
    *   **Goal:** To maintain a readily available and reasonably fresh snapshot of all container statuses, reducing the need for direct Docker API calls for every status request.

2.  **Periodic Discord Message Updates (`periodic_message_edit_loop`):**
    *   Another internal background task, the `periodic_message_edit_loop`, is responsible for updating the status messages already posted in Discord channels. This loop runs by default **every 1 minute**.
    *   **Cache Utilization:** When preparing to update a Discord message, this loop **primarily consults the internal cache** to generate the message content (embeds).
    *   If the cached data for a specific server is sufficiently recent (not older than a defined Time-To-Live (TTL), defaulting to 75 seconds), this cached data is used directly. **No new live query to Docker is made in this case.**
    *   Only if the cached data for a server is stale (older than the TTL) or missing will a live query be triggered for that specific server. The result of this live query then updates the cache.
    *   **Goal:** To efficiently update Discord messages by minimizing direct Docker API calls, relying mostly on the frequently refreshed cache.

**Benefits of this Architecture:**

*   **Reduced API Load:** Significantly fewer direct requests to the Docker daemon, which is especially beneficial when managing many containers or with frequent message update intervals.
*   **Consistent Data:** Ensures that status displays are based on a consistent and regularly updated set of information.
*   **Configurability:**
    *   The interval for the background cache refresh (`status_update_loop`) can be configured via the `DDC_BACKGROUND_REFRESH_INTERVAL` environment variable (default: 30s).
    *   The Cache TTL (how long cached data is considered "fresh") can be configured via `DDC_DOCKER_CACHE_DURATION` (default: 75s).
    *   The update interval for the `periodic_message_edit_loop` (default: 1 minute) can be configured per Discord channel via the "Update Interval Minutes" setting in the Web UI.
    *   Additional cache-related environment variables (detailed elsewhere or to be added) allow for further fine-tuning.

This system design significantly reduces the API load on the Docker daemon and contributes to consistent and responsive behavior of the bot.

## Development / Contributing

Contributions to DockerDiscordControl are welcome! Here's how you can contribute:

1. **Fork the Repository**: Create your own fork of the repository.
2. **Create a Feature Branch**: `git checkout -b feature/my-new-feature`
3. **Commit Your Changes**: `git commit -am 'Add some feature'`
4. **Push to the Branch**: `git push origin feature/my-new-feature`
5. **Submit a Pull Request**: Open a pull request from your fork to the main repository.

### Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/DockerDiscordControl/DockerDiscordControl.git
   cd DockerDiscordControl
   ```

2. **Install Development Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Running Locally for Development**:
   ```bash
   # Set required environment variables
   export FLASK_APP=app
   export FLASK_ENV=development
   export FLASK_SECRET_KEY=your_dev_secret_key
   
   # Run Flask development server
   flask run --host=0.0.0.0 --port=8374
   
   # In another terminal, run the bot
   python bot.py
   ```

### Testing

Run the test suite:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

*Homepage: [https://ddc.bot](https://ddc.bot)*

## Acknowledgements

This project would not be possible without the following libraries and tools:

- [Py-cord](https://github.com/Pycord-Development/pycord) - Discord API wrapper
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Docker SDK for Python](https://docker-py.readthedocs.io/) - Docker API access
- [APScheduler](https://apscheduler.readthedocs.io/) - Scheduling framework
- [Bootstrap](https://getbootstrap.com/) - Frontend toolkit

Special thanks to all contributors and users who have provided feedback and suggestions to improve this project.
