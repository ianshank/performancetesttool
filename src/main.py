#!/usr/bin/env python3
"""
Main entry point for NLM Performance Testing Tool
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.utils.config import ConfigManager

def main():
    app = QApplication(sys.argv)
    from src.gui.gui_interface import GUIInterface
    config = ConfigManager()
    window = GUIInterface(config)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 