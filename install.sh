#!/bin/bash
set -e

echo "=========================================="
echo "    AIFixer - System-Wide Installation    "
echo "=========================================="

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this installer as root: sudo bash install.sh"
  exit 1
fi

if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
else
    REAL_USER=$(whoami)
fi

INSTALL_DIR="/opt/aifixer"
BIN_PATH="/usr/local/bin/aifixer"
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

echo "[*] 1. Copying core files to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r "$PROJECT_DIR/src" "$INSTALL_DIR/" 2>/dev/null || true
cp "$PROJECT_DIR/main.py" "$INSTALL_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/"

if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$INSTALL_DIR/"
fi

chown -R "$REAL_USER:$REAL_USER" "$INSTALL_DIR"

echo "[*] 2. Setting up isolated Python environment..."
apt-get update -yqq && apt-get install python3-venv -yqq >/dev/null 2>&1 || true

sudo -u "$REAL_USER" python3 -m venv "$INSTALL_DIR/ai_env"
sudo -u "$REAL_USER" "$INSTALL_DIR/ai_env/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet

echo "[*] 3. Creating global CLI command 'aifixer'..."
cat << 'EOF' > "$BIN_PATH"
#!/bin/bash
cd /opt/aifixer
exec /opt/aifixer/ai_env/bin/python3 main.py "$@"
EOF
chmod +x "$BIN_PATH"

echo "[*] 4. Setting up Background Daemon..."
cat << EOF > /etc/systemd/system/aifixer.service
[Unit]
Description=AIFixer Background AI Daemon
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$INSTALL_DIR/ai_env/bin/python3 $INSTALL_DIR/src/daemon.py

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now aifixer.service

echo "=========================================="
echo "[+] Success! AIFixer is now installed globally."
echo "    - Background daemon is active and monitoring."
echo ""
echo "Launch the UI from anywhere in your terminal by typing:"
echo "    aifixer"
echo "=========================================="
