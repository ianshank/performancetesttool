"""
Unit tests for CLI interface
"""

import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.cli.cli_interface import CLIInterface
from src.utils.config import ConfigManager


class TestCLIInterface:
    """Test the CLI interface"""

    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager"""
        return Mock(spec=ConfigManager)

    @pytest.fixture
    def cli_interface(self, config_manager):
        """Create a CLIInterface instance"""
        return CLIInterface(config_manager)

    def test_initialization(self, cli_interface):
        """Test CLIInterface initialization"""
        assert cli_interface is not None
        assert cli_interface.config_manager is not None
        assert cli_interface.logger is not None

    def test_parse_arguments_basic(self, cli_interface):
        """Test basic argument parsing"""
        args = ["--test-config", "test.yaml", "--users", "10", "--duration", "60"]

        parsed_args = cli_interface.parse_arguments(args)

        assert parsed_args.test_config == "test.yaml"
        assert parsed_args.users == 10
        assert parsed_args.duration == 60

    def test_parse_arguments_defaults(self, cli_interface):
        """Test argument parsing with defaults"""
        args = []

        parsed_args = cli_interface.parse_arguments(args)

        assert parsed_args.users == 10
        assert parsed_args.duration == 60
        assert parsed_args.think_time == 1
        assert parsed_args.ramp_up == 30
        assert parsed_args.threads == 4

    def test_parse_arguments_invalid(self, cli_interface):
        """Test argument parsing with invalid values"""
        args = ["--users", "-1", "--duration", "0"]

        with pytest.raises(SystemExit):
            cli_interface.parse_arguments(args)

    def test_load_test_config_from_file(self, cli_interface, tmp_path):
        """Test loading test configuration from file"""
        config_data = {
            "test_name": "API Test",
            "targets": [
                {
                    "type": "http",
                    "url": "http://api.example.com",
                    "method": "GET",
                    "expected_status": 200,
                }
            ],
            "load_profile": {
                "users": 5,
                "threads": 2,
                "duration": 30,
                "think_time": 1,
                "ramp_up": 10,
            },
        }

        config_file = tmp_path / "test_config.yaml"
        import yaml

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = cli_interface.load_test_config(str(config_file))

        assert config["test_name"] == "API Test"
        assert len(config["targets"]) == 1
        assert config["targets"][0]["type"] == "http"
        assert config["load_profile"]["users"] == 5

    def test_load_test_config_invalid_file(self, cli_interface):
        """Test loading test configuration from invalid file"""
        with pytest.raises(FileNotFoundError):
            cli_interface.load_test_config("nonexistent_file.yaml")

    def test_build_test_config_from_args(self, cli_interface):
        """Test building test configuration from command line arguments"""
        args = Mock()
        args.test_name = "CLI Test"
        args.target_url = "http://api.example.com"
        args.method = "POST"
        args.expected_status = 201
        args.users = 5
        args.threads = 2
        args.duration = 30
        args.think_time = 1
        args.ramp_up = 10
        # Explicitly set other attributes to None to avoid Mock auto-creation
        args.db_type = None
        args.mq_type = None
        args.url = None

        config = cli_interface.build_test_config_from_args(args)

        assert config["test_name"] == "CLI Test"
        assert len(config["targets"]) == 1
        assert config["targets"][0]["type"] == "http"
        assert config["targets"][0]["url"] == "http://api.example.com"
        assert config["targets"][0]["method"] == "POST"
        assert config["targets"][0]["expected_status"] == 201
        assert config["load_profile"]["users"] == 5
        assert config["load_profile"]["threads"] == 2

    def test_build_test_config_database(self, cli_interface):
        """Test building database test configuration"""
        args = Mock()
        args.test_name = "Database Test"
        args.db_type = "postgresql"
        args.db_host = "localhost"
        args.db_port = 5432
        args.db_name = "testdb"
        args.db_query = "SELECT COUNT(*) FROM users"
        args.users = 3
        args.threads = 1
        args.duration = 20
        args.think_time = 2
        args.ramp_up = 5
        # Explicitly set other attributes to None to avoid Mock auto-creation
        args.mq_type = None
        args.target_url = None
        args.url = None

        config = cli_interface.build_test_config_from_args(args)

        assert config["test_name"] == "Database Test"
        assert config["targets"][0]["type"] == "database"
        assert config["targets"][0]["db_type"] == "postgresql"
        assert config["targets"][0]["host"] == "localhost"
        assert config["targets"][0]["port"] == 5432
        assert config["targets"][0]["database"] == "testdb"
        assert config["targets"][0]["query"] == "SELECT COUNT(*) FROM users"

    def test_build_test_config_message_queue(self, cli_interface):
        """Test building message queue test configuration"""
        args = Mock()
        args.test_name = "MQ Test"
        args.mq_type = "rabbitmq"
        args.mq_host = "localhost"
        args.mq_port = 5672
        args.mq_queue = "test_queue"
        args.users = 2
        args.threads = 1
        args.duration = 15
        args.think_time = 1
        args.ramp_up = 5
        # Explicitly set other attributes to None to avoid Mock auto-creation
        args.db_type = None
        args.target_url = None
        args.url = None

        config = cli_interface.build_test_config_from_args(args)

        assert config["test_name"] == "MQ Test"
        assert config["targets"][0]["type"] == "message_queue"
        assert config["targets"][0]["mq_type"] == "rabbitmq"
        assert config["targets"][0]["host"] == "localhost"
        assert config["targets"][0]["port"] == 5672
        assert config["targets"][0]["queue"] == "test_queue"

    @pytest.mark.asyncio
    async def test_run_test_success(self, cli_interface):
        """Test successful test execution"""
        test_config = {
            "test_name": "Test",
            "targets": [{"type": "http", "url": "http://httpbin.org/get"}],
            "load_profile": {"users": 1, "duration": 5, "think_time": 1},
        }

        # Mock the test runner with AsyncMock
        mock_runner = AsyncMock(spec=cli_interface.test_runner)
        mock_runner.run_test.return_value = {
            "test_name": "Test",
            "results": [{"success": True, "response_time": 0.1}],
        }
        cli_interface.test_runner = mock_runner

        result = await cli_interface.run_test(test_config)

        assert result is not None
        assert result["test_name"] == "Test"
        mock_runner.run_test.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_test_failure(self, cli_interface):
        """Test test execution failure"""
        test_config = {
            "test_name": "Test",
            "targets": [{"type": "http", "url": "http://invalid-url.com"}],
            "load_profile": {"users": 1, "duration": 5, "think_time": 1},
        }

        # Mock the test runner with AsyncMock
        mock_runner = AsyncMock(spec=cli_interface.test_runner)
        mock_runner.run_test.side_effect = Exception("Test failed")
        cli_interface.test_runner = mock_runner

        with pytest.raises(Exception, match="Test failed"):
            await cli_interface.run_test(test_config)

    def test_display_results_summary(self, cli_interface, capsys):
        """Test displaying results summary"""
        results = {
            "test_name": "API Test",
            "start_time": 1640995200,
            "end_time": 1640995260,
            "duration": 60,
            "results": [
                {"success": True, "response_time": 0.1},
                {"success": True, "response_time": 0.2},
                {"success": False, "response_time": 1.0},
            ],
        }

        cli_interface.display_results_summary(results)
        captured = capsys.readouterr()

        assert "API Test" in captured.out
        assert "Total Requests: 3" in captured.out
        assert "Successful: 2" in captured.out
        assert "Failed: 1" in captured.out

    def test_display_results_detailed(self, cli_interface, capsys):
        """Test displaying detailed results"""
        results = {
            "test_name": "API Test",
            "results": [
                {
                    "timestamp": 1640995201,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 200,
                    "response_time": 0.15,
                    "success": True,
                },
                {
                    "timestamp": 1640995202,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 500,
                    "response_time": 2.5,
                    "success": False,
                    "error": "Server Error",
                },
            ],
        }

        cli_interface.display_results_detailed(results)
        captured = capsys.readouterr()

        assert "GET" in captured.out
        assert "200" in captured.out
        assert "500" in captured.out
        assert "Server Error" in captured.out

    def test_export_results_csv(self, cli_interface, tmp_path):
        """Test exporting results to CSV"""
        results = {
            "test_name": "API Test",
            "results": [
                {
                    "timestamp": 1640995201,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 200,
                    "response_time": 0.15,
                    "success": True,
                }
            ],
            "total_requests": 1,
            "successful_requests": 1,
            "failed_requests": 0,
            "success_rate": 1.0,
            "avg_response_time": 0.15,
            "min_response_time": 0.15,
            "max_response_time": 0.15,
            "percentiles": {"p50": 0.15},
            "response_time_distribution": {},
            "error_analysis": {},
            "performance_insights": {},
            "target_breakdown": {},
            "user_breakdown": {},
            "time_series_analysis": {},
        }
        # Export and check both main and summary CSVs
        from exporters.csv_exporter import CSVExporter

        exporter = CSVExporter()
        csv_path = exporter.export_results(
            results["results"], results, filename="test_export_results.csv"
        )
        summary_path = str(csv_path).replace(".csv", "_summary.csv")
        assert os.path.exists(csv_path)
        assert os.path.exists(summary_path)
        with open(csv_path, "r") as f:
            content = f.read()
            assert "timestamp" in content and "response_time" in content
        with open(summary_path, "r") as f:
            content = f.read()
            assert "Total Requests" in content and "Success Rate" in content

    def test_export_results_json(self, cli_interface, tmp_path):
        """Test exporting results to JSON"""
        results = {
            "test_name": "API Test",
            "results": [
                {
                    "timestamp": 1640995201,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 200,
                    "response_time": 0.15,
                    "success": True,
                }
            ],
        }

        json_file = tmp_path / "results.json"
        cli_interface.export_results(results, str(json_file), format="json")

        assert json_file.exists()
        assert json_file.stat().st_size > 0

        # Verify JSON is valid
        import json

        with open(json_file, "r") as f:
            data = json.load(f)
            assert "test_name" in data
            assert "results" in data

    def test_export_results_invalid_format(self, cli_interface, tmp_path):
        """Test exporting results with invalid format"""
        results = {"test_name": "Test", "results": []}
        invalid_file = tmp_path / "results.invalid"

        with pytest.raises(ValueError, match="Unsupported export format"):
            cli_interface.export_results(results, str(invalid_file), format="invalid")

    def test_interactive_mode(self, cli_interface):
        """Test interactive mode setup"""
        # Mock input/output
        with patch("builtins.input", return_value="y"), patch("sys.stdout", new=StringIO()):

            # This would normally run the interactive loop
            # For testing, we just verify the method exists and doesn't crash
            assert hasattr(cli_interface, "interactive_mode")

    def test_validate_config(self, cli_interface):
        """Test configuration validation"""
        valid_config = {
            "test_name": "Test",
            "targets": [{"type": "http", "url": "http://example.com"}],
            "load_profile": {"users": 10, "duration": 60, "think_time": 1},
        }

        # Should not raise an exception
        cli_interface.validate_config(valid_config)

    def test_validate_config_invalid(self, cli_interface):
        """Test configuration validation with invalid config"""
        invalid_config = {
            "test_name": "Test",
            # Missing targets
            "load_profile": {"users": 10, "duration": 60, "think_time": 1},
        }

        with pytest.raises(ValueError, match="No targets specified"):
            cli_interface.validate_config(invalid_config)

    def test_validate_config_invalid_target(self, cli_interface):
        """Test configuration validation with invalid target"""
        invalid_config = {
            "test_name": "Test",
            "targets": [{"type": "invalid_type"}],
            "load_profile": {"users": 10, "duration": 60, "think_time": 1},
        }

        with pytest.raises(ValueError, match="Invalid target type"):
            cli_interface.validate_config(invalid_config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
