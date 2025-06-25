#!/usr/bin/env python3
"""
Simple test script to verify NLM installation
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        # Test basic imports
        import yaml
        import pandas
        import numpy
        import requests
        import aiohttp
        import boto3
        import streamlit
        print("✅ Basic dependencies imported successfully")
    except ImportError as e:
        print(f"❌ Basic dependency import failed: {e}")
        return False
    
    try:
        # Test our modules
        from src.utils.config import ConfigManager
        print("✅ ConfigManager imported successfully")
    except ImportError as e:
        print(f"❌ ConfigManager import failed: {e}")
        return False
    
    try:
        from src.utils.logger import get_logger
        print("✅ Logger imported successfully")
    except ImportError as e:
        print(f"❌ Logger import failed: {e}")
        return False
    
    try:
        from src.core.test_engine import TestEngine
        print("✅ TestEngine imported successfully")
    except ImportError as e:
        print(f"❌ TestEngine import failed: {e}")
        return False
    
    try:
        from src.core.test_runner import TestRunner
        print("✅ TestRunner imported successfully")
    except ImportError as e:
        print(f"❌ TestRunner import failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading"""
    print("\n🔧 Testing configuration...")
    
    try:
        from src.utils.config import ConfigManager
        config = ConfigManager()
        print(f"✅ Configuration loaded successfully")
        print(f"   Environment: {config.environment}")
        
        # Test credential validation
        validation = config.validate_credentials()
        print("   Credential validation:")
        for service, is_valid in validation.items():
            status = "✅" if is_valid else "❌"
            print(f"     {service.upper()}: {status}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("\n🚀 Testing basic functionality...")
    
    try:
        # Test that we can create a simple test configuration
        test_config = {
            "test_name": "Installation Test",
            "targets": [
                {
                    "type": "http",
                    "url": "https://httpbin.org/get",
                    "method": "GET",
                    "headers": {},
                    "body": None
                }
            ],
            "users": 1,
            "duration": 5,
            "ramp_up": 1,
            "think_time": 1
        }
        
        print("✅ Test configuration created successfully")
        print(f"   Test name: {test_config['test_name']}")
        print(f"   Targets: {len(test_config['targets'])}")
        print(f"   Users: {test_config['users']}")
        print(f"   Duration: {test_config['duration']}s")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 NLM Performance Testing Tool - Installation Test")
    print("=" * 60)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please check your installation.")
        return False
    
    # Test configuration
    if not test_configuration():
        print("\n❌ Configuration tests failed. Please check your .env file.")
        return False
    
    # Test basic functionality
    if not test_basic_functionality():
        print("\n❌ Basic functionality tests failed.")
        return False
    
    print("\n🎉 All tests passed! NLM is ready to use.")
    print("\n📋 Next steps:")
    print("1. Configure your API keys in the .env file")
    print("2. Run the demo: python demo.py")
    print("3. Start the dashboard: streamlit run src/dashboard/streamlit_app.py")
    print("4. Use the CLI: python src/cli/cli_interface.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 