#!/usr/bin/env python3
import argparse as ap
import sys

from src.tui import main_menu


def main():
    parser = ap.ArgumentParser(description="SysHealerAI")
    parser.add_argument(
        "-v", "--version", action="version", version="SysHealerAI v1.0.0"
    )
    parser.add_argument(
        "--scan", action="store_true", help="Force system scan in background."
    )

    args = parser.parse_args()

    if args.scan:
        from src.collector import collect_logs

        print("[*] Force scanning journalctl for the last 24 hours...")
        collect_logs(custom_since="24 hours ago")
        print("[+] Scan complete. Run 'syshealer' to review new incidents.")
        sys.exit(0)

    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting... Daemon will continue working.")
        sys.exit(0)


if __name__ == "__main__":
    main()
