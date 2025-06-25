#!/usr/bin/env python3
"""
Comprehensive test runner for NLM tool
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_pytest_tests(test_paths, verbose=False, coverage=False):
    """Run pytest tests with specified options"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    cmd.extend(test_paths)
    
    print(f"Running tests with command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_specific_test_suite(suite_name, verbose=False, coverage=False):
    """Run a specific test suite"""
    test_files = {
        "core": [
            "tests/test_test_engine.py",
            "tests/test_test_runner.py"
        ],
        "utils": [
            "tests/test_config.py"
        ],
        "ai": [
            "tests/test_ai_analysis.py"
        ],
        "cli": [
            "tests/test_cli.py"
        ],
        "basic": [
            "tests/test_basic_functionality.py"
        ],
        "all": [
            "tests/"
        ]
    }
    
    if suite_name not in test_files:
        print(f"Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(test_files.keys())}")
        return False
    
    return run_pytest_tests(test_files[suite_name], verbose, coverage)


def run_integration_tests():
    """Run integration tests"""
    print("Running integration tests...")
    print("=" * 60)
    
    # Test basic functionality
    try:
        from utils.config import ConfigManager
        config = ConfigManager()
        print("✓ ConfigManager initialization successful")
    except Exception as e:
        print(f"✗ ConfigManager initialization failed: {e}")
        return False
    
    try:
        from core.test_engine import TestEngine
        engine = TestEngine(config)
        print("✓ TestEngine initialization successful")
    except Exception as e:
        print(f"✗ TestEngine initialization failed: {e}")
        return False
    
    try:
        from core.test_runner import TestRunner
        runner = TestRunner(config)
        print("✓ TestRunner initialization successful")
    except Exception as e:
        print(f"✗ TestRunner initialization failed: {e}")
        return False
    
    try:
        from ai.analysis_engine import AnalysisEngine
        analysis = AnalysisEngine(config)
        print("✓ AnalysisEngine initialization successful")
    except Exception as e:
        print(f"✗ AnalysisEngine initialization failed: {e}")
        return False
    
    print("✓ All integration tests passed")
    return True


def check_dependencies():
    """Check if all required dependencies are available"""
    print("Checking dependencies...")
    print("=" * 60)
    
    required_packages = [
        "pytest",
        "aiohttp",
        "yaml",
        "pandas",
        "streamlit",
        "plotly",
        "openai",
        "anthropic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✓ All dependencies available")
    return True


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="NLM Tool Test Runner")
    parser.add_argument("--suite", choices=["core", "utils", "ai", "cli", "basic", "all"], 
                       default="all", help="Test suite to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--integration", "-i", action="store_true", help="Run integration tests")
    parser.add_argument("--deps", "-d", action="store_true", help="Check dependencies")
    parser.add_argument("--file", "-f", help="Run specific test file")
    
    args = parser.parse_args()
    
    print("NLM Tool Test Runner")
    print("=" * 60)
    
    # Check dependencies if requested
    if args.deps:
        if not check_dependencies():
            return 1
    
    # Run integration tests if requested
    if args.integration:
        if not run_integration_tests():
            return 1
    
    # Run specific test file if provided
    if args.file:
        if not run_pytest_tests([args.file], args.verbose, args.coverage):
            return 1
    else:
        # Run test suite
        if not run_specific_test_suite(args.suite, args.verbose, args.coverage):
            return 1
    
    print("=" * 60)
    print("Test run completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 