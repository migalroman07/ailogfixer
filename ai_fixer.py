#!/usr/bin/env python3
import sys

from src.tui import main_menu

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nBye")
        sys.exit(0)
