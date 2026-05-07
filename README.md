# SysHealerAI

An AI-powered system administration tool for Linux that autonomously analyzes system logs, diagnoses issues, and generates bash scripts to resolve incidents.

## Overview

SysHealerAI monitors your Linux system for errors by collecting logs from `journalctl`, analyzing them with Large Language Models (LLMs), and providing actionable fix scripts. It operates in two parallel modes: a manual interactive mode via a Terminal User Interface (TUI) and automatic background monitoring via a systemd daemon. 

Built on a decoupled microservice architecture, the daemon and TUI operate independently and communicate safely through a PostgreSQL database to ensure system stability and prevent file locking.

## Core Features

- **Automated Log Collection**: Periodically scans system logs for priority 3 (error) logs and above.
- **Smart Deduplication**: Parses logs line-by-line using JSON format. Identical service crashes are hashed and grouped into single incidents with occurrence counters to prevent database spam.
- **Context-Aware AI**: Automatically injects real-time hardware metrics (RAM, Disk space) into the prompt to prevent the AI from making blind assumptions.
- **Auto-Capture & Self-Healing**: If an executed bash script fails, SysHealerAI intercepts the `stderr` output via bash pipes and feeds it back to the AI for automatic script revision.
- **Dual Execution Modes**: 
  - *Safe Mode:* AI generates templates requiring manual variable input (e.g., `<PID>`) with bash-commented instructions on how to find them.
  - *Autonomous Mode:* AI writes dynamic, self-executing bash logic requiring zero human intervention.
- **Circuit Breaker**: Prevents infinite loops and API budget exhaustion by limiting the AI to a maximum of 3 remediation attempts per incident.
- **Smart Placeholders**: The TUI automatically detects missing variables in scripts, pauses execution, and prompts the user for input.
- **Zero-Touch Provisioning**: Automatically initializes the PostgreSQL database, configures system services, and builds a comprehensive `config.json` with pre-configured endpoints for major AI providers upon first boot.

## Requirements

- Linux OS with `systemd` and `journalctl`
- Python 3.10+
- PostgreSQL server
- Root access (required for reading system logs and managing services)

## Installation

SysHealerAI uses an isolated in-place installation method to prevent OS dependency conflicts.

1. Install and Configure PostgreSQL
    SysHealerAI relies on a local PostgreSQL server. If you don't have it installed, run (for Debian/Ubuntu):
    ```bash
    sudo apt update && sudo apt install postgresql -y
    sudo systemctl enable --now postgresql```

    # Set the password for the default 'postgres' user to 'password'
    sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'password';"

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/syshealer.git
   cd syshealer
   ```

3. Configure the database connection:
   Create a `.env` file in the project root based on the template.
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your PostgreSQL connection string:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/syshealer_db
   ```
   *Note: SysHealerAI will automatically create the target database if it does not exist and the provided PostgreSQL user has sufficient privileges.*

4. Run the installation script as root:
   ```bash
   sudo bash install.sh
   ```
   The installer will create an isolated Python virtual environment, install dependencies, set up the `syshealer` global CLI command, and start the systemd daemon.

## Usage

### Interactive Mode (TUI)
Run the main application from anywhere:
```bash
sudo syshealer
```
Upon first launch, navigate to **Configure -> AI Provider / Model** to securely input your API key (stored in `.env` and injected into memory dynamically).

The TUI provides options to:
- Review pending, waiting, or resolved incidents.
- Fill in missing placeholders and execute AI-generated scripts.
- Toggle platform mechanics (Auto-Capture, System Snapshots, Autonomous Mode).
- Clean up the database.

### Background Daemon
The background daemon runs automatically after installation. It collects logs at configured intervals, pre-analyzes incidents, and marks them as "waiting" for user review.

To check daemon status or restart it:
```bash
systemctl status syshealer
sudo systemctl restart syshealer
```

### Force Scan
Trigger an immediate log scan without opening the TUI:
```bash
sudo syshealer --scan
```

## Configuration
Settings are stored in an automatically generated `config.json` file. Run `sudo syshealer` and select **Configure** to adjust:

- **Mode**: Manual or automatic scanning intervals.
- **AI Provider**: Select a provider and securely enter API keys.
- **Features**: Interactively toggle specific mechanics like `system_snapshot`, `auto_capture`, `autonomous_mode`, `auto_summary`, `circuit_breaker`, and `smart_placeholders`.
- **System**: Adjust log collection interval and max log length.

## Project Structure
```text
.
├── main.py              # Entry point and CLI arguments
├── install.sh           # In-place installation script
├── uninstall.sh         # System cleanup script
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment variables
├── .env                 # Secrets and DB URL (not tracked by git)
├── config.json          # Runtime configuration (auto-generated)
└── src/
    ├── ai_core.py       # AI logic, prompt templates, API calls
    ├── collector.py     # Log collection and deduplication
    ├── daemon.py        # Background service logic
    ├── database.py      # SQLAlchemy models and DB session
    ├── tui.py           # Terminal UI and user interaction
    └── config.py        # Configuration loading/saving
```

## Database Schema
The tool uses PostgreSQL with the following `incidents` table:
- `id`: Primary key.
- `raw_log`: Original log content.
- `status`: pending, processing, waiting, resolved.
- `ai_summary`: Generated fix script.
- `ai_log_review`: AI-generated description.
- `log_hash`: SHA-256 hash for deduplication.
- `occurrences`: Count of repeated errors.
- `attempt`: Number of AI retry attempts.
- `executed`: Boolean flag for script execution status.

## Uninstallation
To cleanly remove SysHealerAI from your system:
```bash
cd /path/to/syshealer
sudo bash uninstall.sh
```
This stops the daemon, removes the systemd service, deletes the CLI command, and cleans the virtual environment. Your PostgreSQL database and configuration files are preserved.

## Security Notice
This tool requires root privileges and executes AI-generated bash scripts. Use with caution:
- Always review generated scripts before execution.
- Ensure your API keys are kept secure.
- Do not use in production environments without thorough testing.
- The authors are not responsible for any system damage caused by automated scripts.

## License
See the LICENCE file for details.

## Contributing
Contributions are welcome. Please submit pull requests or open issues for bugs and feature requests.
