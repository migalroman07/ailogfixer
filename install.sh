#!/bin/bash
set -e

echo "=========================================="
echo "          AIFixer - Installation          "
echo "=========================================="

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this installer as root: sudo bash install.sh"
  exit 1
fi

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REAL_USER=${SUDO_USER:-$(whoami)}

echo "[*] 1. Preparing local Python environment..."
if [ ! -d "$PROJECT_DIR/ai_env" ]; then
    sudo -u "$REAL_USER" python3 -m venv "$PROJECT_DIR/ai_env"
fi

sudo -u "$REAL_USER" "$PROJECT_DIR/ai_env/bin/pip" install --upgrade pip -q
sudo -u "$REAL_USER" "$PROJECT_DIR/ai_env/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q

echo "[*] 2. Creating global CLI command 'aifixer'..."
cat << EOF > /usr/local/bin/aifixer
#!/bin/bash
cd "$PROJECT_DIR"
exec "$PROJECT_DIR/ai_env/bin/python3" "$PROJECT_DIR/ai_fixer.py" "\$@"
EOF
chmod +x /usr/local/bin/aifixer

echo "[*] 3. Setting up Systemd Background Daemon..."
cat << EOF > /etc/systemd/system/aifixer.service
[Unit]
Description=AIFixer Background AI Daemon
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$PROJECT_DIR/ai_env/bin/python3 $PROJECT_DIR/src/daemon.py

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now aifixer.service

echo "=========================================="
echo "[+] Success! AIFixer is ready to use."
echo "    Background daemon is active and monitoring."
echo ""
echo "You can now launch the app from anywhere by typing:"
echo "    aifixer"
echo "=========================================="
