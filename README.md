# SysHealerAI

An AI-powered system administration tool for Linux that automatically analyzes system logs, diagnoses issues, and generates bash scripts to resolve incidents.

## Overview

SysHealerAI monitors your Linux system for errors by collecting logs from `journalctl`, analyzing them with Large Language Models (LLMs), and providing actionable fix scripts. It operates in two modes: manual interactive mode via a TUI (Terminal User Interface) and automatic background monitoring via a systemd daemon.

## Features

- **Automated Log Collection**: Periodically scans system logs for errors (priority 3 and above).
- **AI-Powered Diagnosis**: Uses OpenAI-compatible APIs to analyze log context and identify root causes.
- **Script Generation**: Automatically generates bash scripts to fix identified issues.
- **Smart Placeholders**: When dynamic values are needed (e.g., PIDs, IPs), the AI inserts placeholders and provides instructions on how to find them.
- **Feedback Loop**: Allows users to report script success or failure, enabling the AI to retry with error context.
- **Background Daemon**: Runs as a systemd service to continuously monitor and pre-analyze incidents.
- **Interactive TUI**: Menu-driven interface to review, configure, and execute fixes.
- **Configurable Providers**: Supports multiple AI providers (OpenAI, local LLMs, etc.) via API keys.

## Requirements

- Linux OS with `systemd` and `journalctl`
- Python 3.10+
- PostgreSQL database
- Root access (required for reading system logs and managing services)
- API key for an OpenAI-compatible LLM provider

## Installation

1. Clone the repository or download the source code.

2. Create a `.env` file in the project root based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/ailogs
   ```

3. Run the installation script as root:
   ```bash
   sudo bash install.sh
   ```

   The installer will:
   - Create a Python virtual environment.
   - Install dependencies.
   - Set up the `syshealer` global command.
   - Configure and start the systemd daemon.

## Usage

### Interactive Mode

Run the main application from anywhere:
```bash
sudo syshealer
```

The TUI provides options to:
- View pending, waiting, or resolved incidents.
- Generate and execute fix scripts.
- Configure AI providers and features.
- Clean up the database.

### Background Daemon

The daemon runs automatically after installation. It:
- Collects logs at configured intervals.
- Pre-analyzes incidents and generates scripts.
- Marks incidents as "waiting" for user review.

To check daemon status:
```bash
systemctl status syshealer
```

To restart or stop:
```bash
sudo systemctl restart syshealer
sudo systemctl stop syshealer
```

### Force Scan

Trigger an immediate log scan without opening the TUI:
```bash
sudo syshealer --scan
```

## Configuration

Run `sudo syshealer` and select "Configure" to adjust:

- **Mode**: Manual or automatic scanning intervals.
- **AI Provider**: Select provider and enter API keys.
- **Features**:
  - `system_snapshot`: Include RAM/disk usage in AI context.
  - `auto_capture`: Automatically capture script output for error analysis.
  - `autonomous_mode`: Allow AI to generate fully dynamic scripts without placeholders.
  - `auto_summary`: Generate short descriptions for incidents.
  - `circuit_breaker`: Limit AI retry attempts to prevent loops.
  - `smart_placeholders`: Enable interactive placeholder resolution.
- **System**: Adjust log collection interval and max log length.

Configuration is stored in `config.json`.

## Project Structure

```
.
├── main.py              # Entry point and CLI arguments
├── install.sh           # Installation script
├── uninstall.sh         # Uninstallation script
├── requirements.txt     # Python dependencies
├── config.json          # Runtime configuration (generated)
├── .env                 # Environment variables (database, API keys)
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

To remove SysHealerAI:
```bash
sudo bash uninstall.sh
```

This stops the daemon, removes the systemd service, deletes the CLI command, and cleans the virtual environment. Your database and configuration files are preserved.

## Security Notice

This tool requires root privileges and executes AI-generated bash scripts. Use with caution:
- Review generated scripts before execution.
- Ensure your AI API key is kept secure.
- Do not use in production environments without thorough testing.
- The authors are not responsible for any system damage caused by automated scripts.

## License

See the LICENCE file for details.

## Contributing

Contributions are welcome. Please submit pull requests or open issues for bugs and feature requests.
