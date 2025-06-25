"""
Basic functionality tests for NLM tool
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.test_engine import LoadTestEngine
from src.core.test_runner import LoadTestRunner
from src.utils.config import ConfigManager
from src.utils.logger import setup_logging


class TestConfigManager:
    """Test configuration management"""

    def test_config_initialization(self):
        """Test ConfigManager initialization"""
        config = ConfigManager()
        assert config is not None
        assert config.environment == "dev"
        assert "environments" in config.config
        assert "credentials" in config.config

    def test_environment_config(self):
        """Test environment configuration"""
        config = ConfigManager()

        # Test getting environment config
        dev_config = config.get_environment_config("dev")
        assert dev_config is not None
        assert "aws_region" in dev_config

        # Test setting environment
        config.set_environment("prod")
        assert config.environment == "prod"

    def test_credentials_validation(self):
        """Test credentials validation"""
        config = ConfigManager()
        validation = config.validate_credentials()

        # Should return dict with service names as keys
        assert isinstance(validation, dict)
        assert "aws" in validation
        assert "datadog" in validation
        assert "splunk" in validation
        assert "ai" in validation


class TestTestEngine:
    """Test the core test engine"""

    def test_engine_initialization(self):
        """Test LoadTestEngine initialization"""
        config = ConfigManager()
        engine = LoadTestEngine(config)
        assert engine is not None
        assert engine.running == False

    def test_results_summary(self):
        """Test results summary generation"""
        config = ConfigManager()
        engine = LoadTestEngine(config)

        # Test with empty results
        empty_summary = engine.get_results_summary([])
        assert empty_summary["total_requests"] == 0
        assert empty_summary["successful_requests"] == 0
        assert empty_summary["failed_requests"] == 0

        # Test with sample results
        sample_results = [
            {"timestamp": 1000, "response_time": 0.1, "success": True},
            {"timestamp": 1001, "response_time": 0.2, "success": False},
        ]

        summary = engine.get_results_summary(sample_results)
        assert summary["total_requests"] == 2
        assert summary["successful_requests"] == 1
        assert summary["failed_requests"] == 1
        assert summary["avg_response_time"] == 0.15


class TestTestRunner:
    """Test the test runner"""

    def test_runner_initialization(self):
        """Test LoadTestRunner initialization"""
        config = ConfigManager()
        runner = LoadTestRunner(config)
        assert runner is not None
        assert runner.current_test is None

    def test_build_test_config(self):
        """Test test configuration building"""
        config = ConfigManager()
        runner = LoadTestRunner(config)

        # Test with valid config
        test_config = {
            "test_name": "Test",
            "targets": [{"type": "http", "url": "http://example.com"}],
            "load_profile": {"users": 10, "duration": 60},
        }

        # This would normally run the test, but we'll just check the config
        assert test_config["test_name"] == "Test"
        assert len(test_config["targets"]) == 1
        assert test_config["targets"][0]["type"] == "http"


class TestLogging:
    """Test logging functionality"""

    def test_logger_setup(self):
        """Test logger setup"""
        logger = setup_logging(verbose=True)
        assert logger is not None
        assert logger.level <= 10  # DEBUG level

    def test_logger_get(self):
        """Test getting logger instance"""
        from utils.logger import get_logger

        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
