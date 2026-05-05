#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this uninstaller as root: sudo bash uninstall.sh"
  exit 1
fi

echo "[*] 1. Stopping and removing systemd daemon..."
systemctl stop syshealer.service 2>/dev/null || true
systemctl disable syshealer.service 2>/dev/null || true
rm -f /etc/systemd/system/syshealer.service
systemctl daemon-reload

echo "[*] 2. Removing global CLI command..."
rm -f /usr/local/bin/syshealer

echo "[*] 3. Cleaning up Python virtual environment..."
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
rm -rf "$PROJECT_DIR/ai_env"

echo "[+] SysHealer-AI system components have been removed."
echo "    Your database config is kept safe."
echo "    To delete the project completely, just remove this folder."
