#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this uninstaller as root: sudo bash uninstall.sh"
  exit 1
fi

echo "[*] 1. Stopping and removing systemd daemon..."
systemctl stop aifixer.service 2>/dev/null || true
systemctl disable aifixer.service 2>/dev/null || true
rm -f /etc/systemd/system/aifixer.service
systemctl daemon-reload

echo "[*] 2. Removing global CLI command..."
rm -f /usr/local/bin/aifixer

echo "[*] 3. Cleaning up Python virtual environment..."
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
rm -rf "$PROJECT_DIR/ai_env"

echo "[+] AIFixer system components have been removed."
echo "    Your database config is kept safe."
echo "    To delete the project completely, just remove this folder."
