"""
Regression tests for stage environment validation before production deployment.

These tests validate core functionality, integrations, and performance to ensure
the system is ready for production. If any of these tests fail, production
deployment should be blocked.

Run with: python -m pytest tests/test_regression.py -v --tb=short
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.ai.analysis_engine import AIAnalysisEngine
from src.cli.cli_interface import CLIInterface
from src.core.test_engine import LoadTestEngine
from src.core.test_runner import LoadTestRunner
from src.exporters.csv_exporter import CSVExporter
from src.utils.config import ConfigManager


class TestCriticalFunctionality:
    """Test critical system functionality that must work in production"""

    @pytest.fixture
    def config_manager(self):
        """Create a config manager for testing"""
        return ConfigManager()

    @pytest.fixture
    def test_engine(self, config_manager):
        """Create a test engine instance"""
        return LoadTestEngine(config_manager)

    @pytest.fixture
    def test_runner(self, config_manager):
        """Create a test runner instance"""
        return LoadTestRunner(config_manager)

    @pytest.fixture
    def cli_interface(self, config_manager):
        """Create a CLI interface instance"""
        return CLIInterface(config_manager)

    def test_config_manager_initialization(self, config_manager):
        """Regression: ConfigManager must initialize correctly"""
        assert config_manager is not None
        assert hasattr(config_manager, "config")
        assert hasattr(config_manager, "environment")
        assert config_manager.environment in ["dev", "qa", "stage", "prod"]

        # Validate config structure
        assert "environments" in config_manager.config
        assert "credentials" in config_manager.config

        # Validate environment configs exist
        for env in ["dev", "qa", "stage", "prod"]:
            env_config = config_manager.get_environment_config(env)
            assert env_config is not None
            assert "aws_region" in env_config

    def test_test_engine_basic_operations(self, test_engine):
        """Regression: TestEngine core operations must work"""
        # Test initialization
        assert test_engine is not None
        assert test_engine.running == False
        assert isinstance(test_engine.results, list)

        # Test port resolution
        assert test_engine._get_default_port("postgresql") == 5432
        assert test_engine._get_default_port("mysql") == 3306
        assert test_engine._get_default_port("mongodb") == 27017

        # Test MQ port resolution
        assert test_engine._get_mq_default_port("rabbitmq") == 5672
        assert test_engine._get_mq_default_port("kafka") == 9092

        # Test database simulation
        response_time = test_engine._simulate_database_query("postgresql", "SELECT 1")
        assert 0 < response_time < 0.1

        # Test MQ simulation
        mq_time = test_engine._simulate_mq_operation("rabbitmq")
        assert 0 < mq_time < 0.05

    def test_test_runner_configuration(self, test_runner):
        """Regression: TestRunner must handle configurations correctly"""
        # Test initialization
        assert test_runner is not None
        assert test_runner.current_test is None

        # Test valid HTTP configuration
        http_config = {
            "test_name": "Regression HTTP Test",
            "targets": [
                {
                    "type": "http",
                    "url": "https://httpbin.org/get",
                    "method": "GET",
                    "expected_status": 200,
                }
            ],
            "load_profile": {
                "users": 1,
                "threads": 1,
                "duration": 5,
                "think_time": 1,
                "ramp_up": 1,
            },
        }

        # Test configuration validation (should not raise)
        validated_config = test_runner.config_manager.get_environment_config("stage")
        assert validated_config is not None

    @pytest.mark.asyncio
    async def test_http_test_execution(self, test_engine):
        """Regression: HTTP tests must execute successfully"""
        target = {
            "url": "https://httpbin.org/get",
            "method": "GET",
            "expected_status": 200,
            "headers": {"User-Agent": "NLM-Regression-Test"},
        }
        load_profile = {"users": 2, "threads": 1, "duration": 5, "think_time": 1, "ramp_up": 1}

        test_engine.running = True
        results = await test_engine.execute_http_test(target, load_profile)

        # Validate results structure
        assert len(results) >= 1
        for result in results:
            assert "timestamp" in result
            assert "response_time" in result
            assert "success" in result
            assert "method" in result
            assert "url" in result

        # Validate performance expectations
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) >= 1, "At least one request should succeed"

        # Response times should be reasonable
        avg_response_time = sum(r["response_time"] for r in successful_results) / len(
            successful_results
        )
        assert avg_response_time < 5.0, f"Average response time too high: {avg_response_time}s"

    def test_cli_argument_parsing(self, cli_interface):
        """Regression: CLI argument parsing must work correctly"""
        # Test basic argument parsing
        args = ["--test-name", "Regression Test", "--users", "5", "--duration", "30"]
        parsed = cli_interface.parse_arguments(args)

        assert parsed.test_name == "Regression Test"
        assert parsed.users == 5
        assert parsed.duration == 30

        # Test HTTP target configuration
        http_args = Mock()
        http_args.test_name = "HTTP Regression"
        http_args.target_url = "https://httpbin.org/get"
        http_args.method = "GET"
        http_args.expected_status = 200
        http_args.users = 3
        http_args.threads = 1
        http_args.duration = 10
        http_args.think_time = 1
        http_args.ramp_up = 2
        # Set other attributes to None
        http_args.db_type = None
        http_args.mq_type = None
        http_args.url = None

        config = cli_interface.build_test_config_from_args(http_args)

        assert config["test_name"] == "HTTP Regression"
        assert config["targets"][0]["type"] == "http"
        assert config["targets"][0]["url"] == "https://httpbin.org/get"
        assert config["load_profile"]["users"] == 3

    def test_results_summary_generation(self, test_engine):
        """Regression: Results summary generation must be accurate"""
        # Create sample results data
        sample_results = [
            {
                "timestamp": 1000,
                "response_time": 0.1,
                "success": True,
                "method": "GET",
                "url": "/api/test",
                "status_code": 200,
                "user_id": 1,
            },
            {
                "timestamp": 1001,
                "response_time": 0.2,
                "success": True,
                "method": "GET",
                "url": "/api/test",
                "status_code": 200,
                "user_id": 1,
            },
            {
                "timestamp": 1002,
                "response_time": 1.5,
                "success": False,
                "method": "GET",
                "url": "/api/test",
                "status_code": 500,
                "user_id": 2,
                "error": "Internal Server Error",
            },
        ]

        summary = test_engine.get_results_summary(sample_results)

        # Validate basic metrics
        assert summary["total_requests"] == 3
        assert summary["successful_requests"] == 2
        assert summary["failed_requests"] == 1
        assert summary["success_rate"] == pytest.approx(0.6667, 0.01)
        assert summary["avg_response_time"] == pytest.approx(0.6, 0.01)

        # Validate enhanced metrics exist
        assert "percentiles" in summary
        assert "response_time_distribution" in summary
        assert "error_analysis" in summary
        assert "performance_insights" in summary
        assert "target_breakdown" in summary
        assert "user_breakdown" in summary
        assert "time_series_analysis" in summary

    def test_csv_export_functionality(self):
        """Regression: CSV export must work correctly"""
        # Create test data
        test_results = [
            {
                "timestamp": 1640995200,
                "method": "GET",
                "url": "https://api.example.com/test",
                "status_code": 200,
                "response_time": 0.15,
                "success": True,
                "user_id": 1,
            },
            {
                "timestamp": 1640995201,
                "method": "POST",
                "url": "https://api.example.com/test",
                "status_code": 500,
                "response_time": 2.5,
                "success": False,
                "error": "Server Error",
                "user_id": 2,
            },
        ]

        summary_data = {
            "test_name": "Regression Test",
            "total_requests": 2,
            "successful_requests": 1,
            "failed_requests": 1,
            "success_rate": 0.5,
            "avg_response_time": 1.325,
            "min_response_time": 0.15,
            "max_response_time": 2.5,
            "percentiles": {"p50": 1.325, "p95": 2.5, "p99": 2.5},
            "response_time_distribution": {},
            "error_analysis": {},
            "performance_insights": {},
            "target_breakdown": {},
            "user_breakdown": {},
            "time_series_analysis": {},
        }

        exporter = CSVExporter()

        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp_file:
            csv_path = exporter.export_results(test_results, summary_data, filename=tmp_file.name)

            # Verify files were created
            assert os.path.exists(csv_path)
            summary_path = csv_path.replace(".csv", "_summary.csv")
            assert os.path.exists(summary_path)

            # Verify content
            with open(csv_path, "r") as f:
                content = f.read()
                assert "timestamp" in content
                assert "response_time" in content
                assert "GET" in content
                assert "POST" in content

            with open(summary_path, "r") as f:
                summary_content = f.read()
                assert "Total Requests" in summary_content
                assert "Success Rate" in summary_content
                assert "2" in summary_content  # total requests

            # Cleanup
            os.unlink(csv_path)
            os.unlink(summary_path)


class TestPerformanceRegression:
    """Test performance benchmarks that must be met"""

    @pytest.fixture
    def config_manager(self):
        return ConfigManager()

    @pytest.fixture
    def test_engine(self, config_manager):
        return LoadTestEngine(config_manager)

    def test_simulation_performance(self, test_engine):
        """Regression: Simulation functions must perform within acceptable limits"""
        # Test database simulation performance
        start_time = time.time()
        for _ in range(100):
            test_engine._simulate_database_query("postgresql", "SELECT 1")
        db_duration = time.time() - start_time

        assert db_duration < 1.0, f"Database simulation too slow: {db_duration}s for 100 calls"

        # Test MQ simulation performance
        start_time = time.time()
        for _ in range(100):
            test_engine._simulate_mq_operation("rabbitmq")
        mq_duration = time.time() - start_time

        assert mq_duration < 1.0, f"MQ simulation too slow: {mq_duration}s for 100 calls"

    def test_results_processing_performance(self, test_engine):
        """Regression: Results processing must handle large datasets efficiently"""
        # Create large result set
        large_results = []
        for i in range(1000):
            large_results.append(
                {
                    "timestamp": 1000 + i,
                    "response_time": 0.1 + (i % 10) * 0.01,
                    "success": i % 10 != 0,  # 90% success rate
                    "method": "GET",
                    "url": f"/api/test/{i}",
                    "status_code": 200 if i % 10 != 0 else 500,
                    "user_id": i % 50,
                }
            )

        # Time the summary generation
        start_time = time.time()
        summary = test_engine.get_results_summary(large_results)
        processing_time = time.time() - start_time

        assert (
            processing_time < 5.0
        ), f"Results processing too slow: {processing_time}s for 1000 results"

        # Validate results are still accurate
        assert summary["total_requests"] == 1000
        assert summary["successful_requests"] == 900
        assert summary["failed_requests"] == 100
        assert summary["success_rate"] == 0.9


class TestConfigurationRegression:
    """Test configuration handling and validation"""

    def test_environment_configurations(self):
        """Regression: All environment configurations must be valid"""
        config_manager = ConfigManager()

        # Test all environments
        for env in ["dev", "qa", "stage", "prod"]:
            env_config = config_manager.get_environment_config(env)
            assert env_config is not None, f"Missing configuration for {env}"

            # Required fields
            assert "aws_region" in env_config, f"Missing aws_region in {env}"
            assert "log_level" in env_config, f"Missing log_level in {env}"

            # Validate AWS region format
            aws_region = env_config["aws_region"]
            assert isinstance(aws_region, str), f"Invalid aws_region type in {env}"
            assert len(aws_region) > 0, f"Empty aws_region in {env}"

    def test_credential_validation(self):
        """Regression: Credential validation must work correctly"""
        config_manager = ConfigManager()
        validation = config_manager.validate_credentials()

        # Should return validation results for all services
        expected_services = ["aws", "datadog", "splunk", "ai"]
        for service in expected_services:
            assert service in validation, f"Missing validation for {service}"
            assert isinstance(validation[service], bool), f"Invalid validation type for {service}"

    def test_config_file_access(self):
        """Regression: Configuration file access must work"""
        config_manager = ConfigManager()

        # Test config loading doesn't crash
        assert hasattr(config_manager, "config")
        assert isinstance(config_manager.config, dict)

        # Test environment switching
        original_env = config_manager.environment
        config_manager.set_environment("stage")
        assert config_manager.environment == "stage"

        # Reset to original
        config_manager.set_environment(original_env)


class TestIntegrationRegression:
    """Test integration points that are critical for production"""

    @pytest.fixture
    def config_manager(self):
        return ConfigManager()

    @pytest.fixture
    def cli_interface(self, config_manager):
        return CLIInterface(config_manager)

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, cli_interface):
        """Regression: End-to-end workflow must complete successfully"""
        # Create a simple test configuration
        test_config = {
            "test_name": "E2E Regression Test",
            "targets": [
                {
                    "type": "http",
                    "url": "https://httpbin.org/get",
                    "method": "GET",
                    "expected_status": 200,
                }
            ],
            "load_profile": {
                "users": 1,
                "threads": 1,
                "duration": 3,
                "think_time": 1,
                "ramp_up": 1,
            },
        }

        # Mock the test runner to avoid external dependencies
        mock_runner = AsyncMock()
        mock_runner.run_test.return_value = {
            "test_name": "E2E Regression Test",
            "total_requests": 3,
            "successful_requests": 3,
            "failed_requests": 0,
            "success_rate": 1.0,
            "avg_response_time": 0.2,
            "results": [
                {"timestamp": 1000, "success": True, "response_time": 0.2},
                {"timestamp": 1001, "success": True, "response_time": 0.18},
                {"timestamp": 1002, "success": True, "response_time": 0.22},
            ],
        }
        cli_interface.test_runner = mock_runner

        # Execute the test
        result = await cli_interface.run_test(test_config)

        # Validate the workflow completed
        assert result is not None
        assert result["test_name"] == "E2E Regression Test"
        assert result["total_requests"] == 3
        assert result["success_rate"] == 1.0
        assert "results" in result

    def test_ai_analysis_integration(self, config_manager):
        """Regression: AI analysis integration must be available"""
        # Test AI analysis engine initialization
        ai_engine = AIAnalysisEngine(config_manager)
        assert ai_engine is not None

        # Test basic analysis functionality (without external AI calls)
        sample_results = {
            "results": [
                {"timestamp": 1000, "response_time": 0.1, "success": True},
                {"timestamp": 1001, "response_time": 0.2, "success": True},
                {"timestamp": 1002, "response_time": 1.5, "success": False},
            ]
        }

        analysis = ai_engine.analyze_results(sample_results)

        # Basic analysis should work without AI
        assert "summary" in analysis
        assert "performance_metrics" in analysis
        assert "issues" in analysis
        assert "recommendations" in analysis

    def test_export_integration(self):
        """Regression: Export functionality must be available"""
        exporter = CSVExporter()
        assert exporter is not None

        # Test export methods exist
        assert hasattr(exporter, "export_results")
        assert callable(exporter.export_results)


@pytest.mark.slow
class TestStressRegression:
    """Stress tests for production readiness"""

    @pytest.fixture
    def test_engine(self):
        return LoadTestEngine(ConfigManager())

    def test_concurrent_operations(self, test_engine):
        """Regression: System must handle concurrent operations"""
        import threading

        results = []
        errors = []

        def worker():
            try:
                for _ in range(10):
                    response_time = test_engine._simulate_database_query("postgresql", "SELECT 1")
                    results.append(response_time)
            except Exception as e:
                errors.append(e)

        # Run 5 concurrent workers
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Validate no errors and reasonable results
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 50  # 5 threads * 10 operations each
        assert all(0 < r < 0.1 for r in results), "Response times out of expected range"

    @pytest.mark.parametrize("result_count", [100, 500, 1000])
    def test_large_result_sets(self, test_engine, result_count):
        """Regression: System must handle large result sets efficiently"""
        # Generate large result set
        large_results = []
        for i in range(result_count):
            large_results.append(
                {
                    "timestamp": 1000 + i,
                    "response_time": 0.1 + (i % 100) * 0.001,
                    "success": i % 20 != 0,  # 95% success rate
                    "user_id": i % 10,
                }
            )

        # Process results
        start_time = time.time()
        summary = test_engine.get_results_summary(large_results)
        processing_time = time.time() - start_time

        # Performance expectations scale with data size
        max_time = result_count * 0.005  # 5ms per result max
        assert (
            processing_time < max_time
        ), f"Processing {result_count} results took {processing_time}s (max: {max_time}s)"

        # Validate accuracy
        assert summary["total_requests"] == result_count
        expected_successful = result_count - (result_count // 20)
        assert summary["successful_requests"] == expected_successful


if __name__ == "__main__":
    # Run regression tests with detailed output
    pytest.main([__file__, "-v", "--tb=short", "--durations=10", "-x"])  # Stop on first failure
