#!/usr/bin/env python3
"""
Main entry point for the NLM Performance Testing Tool
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cli.cli_interface import CLIInterface
from gui.gui_interface import GUIInterface
from utils.config import ConfigManager
from utils.logger import setup_logging


def main():
    """Main entry point for the NLM tool"""
    parser = argparse.ArgumentParser(
        description="NLM (Neural Load Manager) Performance Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py --gui                    # Launch GUI
  python src/main.py --cli --config test.yaml # Run CLI with config
  python src/main.py --dashboard              # Launch Streamlit dashboard
        """
    )
    
    parser.add_argument(
        "--gui", 
        action="store_true", 
        help="Launch the PyQt5 GUI interface"
    )
    
    parser.add_argument(
        "--cli", 
        action="store_true", 
        help="Use command-line interface"
    )
    
    parser.add_argument(
        "--dashboard", 
        action="store_true", 
        help="Launch Streamlit dashboard"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to test configuration file"
    )
    
    parser.add_argument(
        "--env", 
        type=str, 
        choices=["dev", "qa", "stage", "prod"],
        default="dev",
        help="Environment to run tests against"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # Load configuration
    config_manager = ConfigManager()
    
    try:
        if args.config:
            config_manager.load_config(args.config)
        
        if args.gui:
            # Launch GUI
            from PyQt5.QtWidgets import QApplication
            from gui.gui_interface import GUIInterface
            qt_app = QApplication(sys.argv)
            app = GUIInterface(config_manager)
            app.show()
            qt_app.exec_()
            
        elif args.cli:
            # Launch CLI
            cli = CLIInterface(config_manager)
            cli.run()
            
        elif args.dashboard:
            # Launch Streamlit dashboard
            import subprocess
            dashboard_path = Path(__file__).parent / "dashboard" / "streamlit_app.py"
            subprocess.run(["streamlit", "run", str(dashboard_path)])
            
        else:
            # Default to GUI if no interface specified
            from PyQt5.QtWidgets import QApplication
            from gui.gui_interface import GUIInterface
            qt_app = QApplication(sys.argv)
            app = GUIInterface(config_manager)
            app.show()
            qt_app.exec_()
            
    except KeyboardInterrupt:
        print("\nExiting NLM tool...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 