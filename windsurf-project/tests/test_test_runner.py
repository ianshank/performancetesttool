"""
Unit tests for TestRunner class
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.test_runner import LoadTestRunner
from src.utils.config import ConfigManager


class TestTestRunner:
    """Test the TestRunner class"""

    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager"""
        return Mock(spec=ConfigManager)

    @pytest.fixture
    def test_runner(self, config_manager):
        """Create a TestRunner instance"""
        return LoadTestRunner(config_manager)

    def test_initialization(self, test_runner):
        """Test TestRunner initialization"""
        assert test_runner is not None
        assert test_runner.current_test is None
        assert test_runner.test_engine is not None
        assert test_runner.logger is not None

    def test_build_test_config(self, test_runner):
        """Test test configuration building"""
        test_config = {
            "test_name": "Test API",
            "environment": "dev",
            "targets": [
                {
                    "type": "http",
                    "url": "http://example.com",
                    "method": "GET",
                    "expected_status": 200,
                }
            ],
            "load_profile": {
                "users": 10,
                "threads": 4,
                "ramp_up": 30,
                "duration": 60,
                "think_time": 1,
            },
        }

        # Test that the config is properly structured
        assert test_config["test_name"] == "Test API"
        assert test_config["environment"] == "dev"
        assert len(test_config["targets"]) == 1
        assert test_config["targets"][0]["type"] == "http"
        assert test_config["load_profile"]["users"] == 10
        assert test_config["load_profile"]["threads"] == 4

    @pytest.mark.asyncio
    async def test_run_test_http(self, test_runner):
        """Test running an HTTP test"""
        test_config = {
            "test_name": "HTTP Test",
            "environment": "dev",
            "targets": [
                {
                    "type": "http",
                    "url": "http://httpbin.org/get",
                    "method": "GET",
                    "expected_status": 200,
                }
            ],
            "load_profile": {
                "users": 2,
                "threads": 2,
                "ramp_up": 5,
                "duration": 10,
                "think_time": 1,
            },
        }
        # Mock the test engine to avoid actual HTTP calls
        with patch.object(test_runner.test_engine, "execute_http_test") as mock_execute:
            mock_execute.return_value = [
                {"timestamp": 1000, "response_time": 0.1, "success": True, "status_code": 200}
            ]
            results = await test_runner.run_test(test_config)
            assert results is not None
            assert "test_name" in results
            assert "start_time" in results
            assert "end_time" in results
            assert "duration" in results
            assert "results" in results
            assert results["test_name"] == "HTTP Test"
            # Enhanced summary fields
            assert "total_requests" in results
            assert "percentiles" in results
            assert "error_analysis" in results
            assert "performance_insights" in results
            assert "target_breakdown" in results
            assert "user_breakdown" in results
            assert "time_series_analysis" in results

    @pytest.mark.asyncio
    async def test_run_test_database(self, test_runner):
        """Test running a database test"""
        test_config = {
            "test_name": "Database Test",
            "environment": "dev",
            "targets": [
                {
                    "type": "database",
                    "db_type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "query": "SELECT 1",
                }
            ],
            "load_profile": {
                "users": 2,
                "threads": 2,
                "ramp_up": 5,
                "duration": 10,
                "think_time": 1,
            },
        }

        # Mock the test engine
        with patch.object(test_runner.test_engine, "execute_database_test") as mock_execute:
            mock_execute.return_value = [
                {"timestamp": 1000, "response_time": 0.05, "success": True, "db_type": "postgresql"}
            ]

            results = await test_runner.run_test(test_config)

            assert results is not None
            assert results["test_name"] == "Database Test"
            assert "results" in results

    @pytest.mark.asyncio
    async def test_run_test_message_queue(self, test_runner):
        """Test running a message queue test"""
        test_config = {
            "test_name": "MQ Test",
            "environment": "dev",
            "targets": [
                {
                    "type": "message_queue",
                    "mq_type": "rabbitmq",
                    "host": "localhost",
                    "port": 5672,
                    "queue": "test_queue",
                }
            ],
            "load_profile": {
                "users": 2,
                "threads": 2,
                "ramp_up": 5,
                "duration": 10,
                "think_time": 1,
            },
        }

        # Mock the test engine
        with patch.object(test_runner.test_engine, "execute_message_queue_test") as mock_execute:
            mock_execute.return_value = [
                {"timestamp": 1000, "response_time": 0.02, "success": True, "mq_type": "rabbitmq"}
            ]

            results = await test_runner.run_test(test_config)

            assert results is not None
            assert results["test_name"] == "MQ Test"
            assert "results" in results

    @pytest.mark.asyncio
    async def test_run_test_multiple_targets(self, test_runner):
        """Test running a test with multiple targets"""
        test_config = {
            "test_name": "Multi-Target Test",
            "environment": "dev",
            "targets": [
                {
                    "type": "http",
                    "url": "http://httpbin.org/get",
                    "method": "GET",
                    "expected_status": 200,
                },
                {
                    "type": "database",
                    "db_type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "query": "SELECT 1",
                },
            ],
            "load_profile": {
                "users": 2,
                "threads": 2,
                "ramp_up": 5,
                "duration": 10,
                "think_time": 1,
            },
        }

        # Mock the test engine methods
        with patch.object(test_runner.test_engine, "execute_http_test") as mock_http, patch.object(
            test_runner.test_engine, "execute_database_test"
        ) as mock_db:

            mock_http.return_value = [{"timestamp": 1000, "response_time": 0.1, "success": True}]
            mock_db.return_value = [{"timestamp": 1001, "response_time": 0.05, "success": True}]

            results = await test_runner.run_test(test_config)

            assert results is not None
            assert results["test_name"] == "Multi-Target Test"
            assert len(results["results"]) == 2  # One result per target

    @pytest.mark.asyncio
    async def test_run_test_unknown_target_type(self, test_runner):
        """Test running a test with unknown target type"""
        test_config = {
            "test_name": "Unknown Target Test",
            "environment": "dev",
            "targets": [{"type": "unknown_type", "url": "http://example.com"}],
            "load_profile": {
                "users": 2,
                "threads": 2,
                "ramp_up": 5,
                "duration": 10,
                "think_time": 1,
            },
        }

        with pytest.raises(ValueError, match="Unsupported target type"):
            await test_runner.run_test(test_config)

    def test_stop_test(self, test_runner):
        """Test stopping a running test"""
        test_runner.current_test = "test_id"
        test_runner.stop_test()
        assert test_runner.current_test is None
        assert test_runner.test_engine.running == False

    def test_get_test_status(self, test_runner):
        """Test getting test status"""
        # Test when no test is running
        status = test_runner.get_test_status()
        assert status["running"] == False
        assert status["current_test"] is None

        # Test when test is running
        test_runner.current_test = "test_id"
        test_runner.test_engine.running = True
        status = test_runner.get_test_status()
        assert status["running"] == True
        assert status["current_test"] == "test_id"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
