#!/usr/bin/env python3
"""
Main entry point for NLM tool
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cli.cli_interface import CLIInterface
from utils.config import ConfigManager


def main():
    """Main entry point"""
    # Initialize config manager with default settings
    config_manager = ConfigManager()
    cli = CLIInterface(config_manager)
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
