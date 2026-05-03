#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e
echo "Setting up aifixer daemon as a systemd service."

# Get exact paths
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [ -n "$SUDO_USER" ]; then 
  USER_NAME="$SUDO_USER"
else
  USER_NAME=$(whoami)
fi

# If virtual environment exists use its python instead of the global one
if [ -f "$PROJECT_DIR/ai_env/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_DIR/ai_env/bin/python3"
elif [ -f "$PROJECT_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_DIR/venv/bin/python3"
else
    PYTHON_BIN=$(which python3)
fi

# Generate systemd service file dynamically
SERVICE_FILE="/tmp/aifixer.service"
cat << EOF > /etc/systemd/system/aifixer.service
[Unit]
Description=AIFixer Background Daemon
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
# PYTHONUNBUFFERED=1 forces python to write logs to journalctl immediately
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=$PYTHON_BIN $PROJECT_DIR/src/daemon.py

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Install and activate
systemctl daemon-reload
systemctl enable --now aifixer.service

echo "AIfixer daemon has been started"
#!/bin/bash
