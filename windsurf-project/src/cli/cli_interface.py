"""
Command Line Interface for NLM Performance Testing Tool
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.analysis_engine import AIAnalysisEngine
from core.test_engine import LoadTestEngine
from core.test_runner import LoadTestRunner
from exporters.csv_exporter import CSVExporter
from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class CLIInterface:
    """Command-line interface for the NLM tool"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger("nlm.cli")
        self.test_engine = LoadTestEngine(config_manager)
        self.test_runner = LoadTestRunner(config_manager)

    def run(self) -> int:
        """Run the CLI interface"""
        if len(sys.argv) > 1:
            # Parse command line arguments
            args = self.parse_arguments()
            if args.quick:
                return self.quick_run(args)
            elif args.config:
                config = self.load_test_config(args.config)
            else:
                config = self.build_test_config_from_args(args)

            try:
                # Run test synchronously
                results = self.test_runner.run_test_sync(config)
                if args.output:
                    self.export_results(results, args.output, format="csv")
                else:
                    self.display_results_summary(results)
                return 0
            except Exception as e:
                print(f"Error running test: {e}")
                return 1
        else:
            # Interactive mode
            return self.interactive_mode()

    def _show_banner(self):
        """Display NLM tool banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    NLM Performance Testing Tool              ║
║                    Neural Load Manager v1.0.0                ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def _show_menu(self):
        """Display main menu options"""
        menu = """
Main Menu:
1. Run Quick Test
2. Run Custom Test
3. Configure Environment
4. Validate Credentials
5. Test History
6. Export Results
7. Help
8. Exit
        """
        print(menu)

    def _run_quick_test(self):
        print("[DEBUG] Entered _run_quick_test")
        print("\n=== Quick Test ===")

        # Get target URL
        print("[DEBUG] Prompting for target URL")
        url = input("Enter target URL (default: http://localhost:8080/health): ").strip()
        if not url:
            url = "http://localhost:8080/health"
        print(f"[DEBUG] Got URL: {url}")

        # Get number of users
        print("[DEBUG] Prompting for number of users")
        users_input = input("Enter number of users (default: 10): ").strip()
        users = int(users_input) if users_input.isdigit() else 10
        print(f"[DEBUG] Got users: {users}")

        # Get test duration
        print("[DEBUG] Prompting for test duration")
        duration_input = input("Enter test duration in seconds (default: 60): ").strip()
        duration = int(duration_input) if duration_input.isdigit() else 60
        print(f"[DEBUG] Got duration: {duration}")

        # Create test configuration
        test_config = {
            "test_name": f"Quick Test - {url}",
            "targets": [{"type": "http", "url": url, "method": "GET", "expected_status": 200}],
            "load_profile": {"users": users, "ramp_up": 10, "duration": duration, "think_time": 1},
        }

        print(f"\nStarting quick test with {users} users for {duration} seconds...")
        print("[DEBUG] Calling _execute_test")
        self._execute_test(test_config)
        print("[DEBUG] Finished _execute_test")

    def _run_custom_test(self):
        """Run a custom test with detailed configuration"""
        print("\n=== Custom Test ===")

        # Get test name
        test_name = input("Enter test name: ").strip()
        if not test_name:
            print("Test name is required.")
            return

        # Get test type
        print("\nTest types:")
        print("1. HTTP API")
        print("2. Database")
        print("3. Message Queue")
        print("4. Mixed")

        test_type = input("Select test type (1-4): ").strip()

        # Configure based on test type
        if test_type == "1":
            test_config = self._configure_http_test(test_name)
        elif test_type == "2":
            test_config = self._configure_database_test(test_name)
        elif test_type == "3":
            test_config = self._configure_mq_test(test_name)
        elif test_type == "4":
            test_config = self._configure_mixed_test(test_name)
        else:
            print("Invalid test type.")
            return

        if test_config:
            self._execute_test(test_config)

    def _configure_http_test(self, test_name: str) -> dict:
        """Configure HTTP API test"""
        url = input("Enter target URL: ").strip()
        method = input("Enter HTTP method (default: GET): ").strip().upper() or "GET"

        # Get headers
        headers = {}
        while True:
            header_key = input("Enter header key (or press Enter to finish): ").strip()
            if not header_key:
                break
            header_value = input(f"Enter value for {header_key}: ").strip()
            headers[header_key] = header_value

        if not url:
            print("Invalid URL.")
            return {}
        return {
            "test_name": test_name,
            "targets": [
                {
                    "type": "http",
                    "url": url,
                    "method": method,
                    "headers": headers,
                    "expected_status": 200,
                }
            ],
            "load_profile": self._get_load_profile(),
        }

    def _configure_database_test(self, test_name: str) -> dict:
        """Configure database test"""
        print("\nDatabase types:")
        print("1. PostgreSQL")
        print("2. MySQL")
        print("3. MongoDB")

        db_type = input("Select database type (1-3): ").strip()

        if db_type == "1":
            db_type = "postgresql"
        elif db_type == "2":
            db_type = "mysql"
        elif db_type == "3":
            db_type = "mongodb"
        else:
            print("Invalid database type.")
            return {}

        host = input("Enter database host: ").strip()
        port = input("Enter database port: ").strip()
        database = input("Enter database name: ").strip()
        query = input("Enter SQL query: ").strip()

        return {
            "test_name": test_name,
            "targets": [
                {
                    "type": "database",
                    "db_type": db_type,
                    "host": host,
                    "port": int(port) if port.isdigit() else 5432,
                    "database": database,
                    "query": query,
                }
            ],
            "load_profile": self._get_load_profile(),
        }

    def _configure_mq_test(self, test_name: str) -> dict:
        """Configure message queue test"""
        print("\nMessage queue types:")
        print("1. RabbitMQ")
        print("2. Redis")

        mq_type = input("Select message queue type (1-2): ").strip()

        if mq_type == "1":
            mq_type = "rabbitmq"
        elif mq_type == "2":
            mq_type = "redis"
        else:
            print("Invalid message queue type.")
            return {}

        host = input("Enter message queue host: ").strip()
        port = input("Enter message queue port: ").strip()
        queue = input("Enter queue name: ").strip()

        return {
            "test_name": test_name,
            "targets": [
                {
                    "type": "message_queue",
                    "mq_type": mq_type,
                    "host": host,
                    "port": int(port) if port.isdigit() else 5672,
                    "queue": queue,
                }
            ],
            "load_profile": self._get_load_profile(),
        }

    def _configure_mixed_test(self, test_name: str) -> dict:
        """Configure mixed test with multiple targets"""
        targets = []

        while True:
            print("\nAdd target:")
            print("1. HTTP API")
            print("2. Database")
            print("3. Message Queue")
            print("4. Done")

            choice = input("Select target type (1-4): ").strip()

            if choice == "1":
                target = self._configure_http_target()
            elif choice == "2":
                target = self._configure_database_target()
            elif choice == "3":
                target = self._configure_mq_target()
            elif choice == "4":
                break
            else:
                print("Invalid choice.")
                continue

            if target:
                targets.append(target)

        if not targets:
            print("No targets configured.")
            return None

        return {
            "test_name": test_name,
            "targets": targets,
            "load_profile": self._get_load_profile(),
        }

    def _configure_http_target(self) -> dict:
        """Configure HTTP target for mixed test"""
        url = input("Enter target URL: ").strip()
        method = input("Enter HTTP method (default: GET): ").strip().upper() or "GET"
        if not url:
            print("Invalid HTTP target configuration.")
            return {}
        return {"type": "http", "url": url, "method": method, "expected_status": 200}

    def _configure_database_target(self) -> dict:
        """Configure database target for mixed test"""
        print("\nDatabase types: 1=PostgreSQL, 2=MySQL, 3=MongoDB")
        db_type = input("Select database type (1-3): ").strip()

        if db_type == "1":
            db_type = "postgresql"
        elif db_type == "2":
            db_type = "mysql"
        elif db_type == "3":
            db_type = "mongodb"
        else:
            print("Invalid database type.")
            return {}

        host = input("Enter database host: ").strip()
        database = input("Enter database name: ").strip()
        query = input("Enter SQL query: ").strip()

        if not host or not database or not query:
            print("Invalid database target configuration.")
            return {}
        return {
            "type": "database",
            "db_type": db_type,
            "host": host,
            "database": database,
            "query": query,
        }

    def _configure_mq_target(self) -> dict:
        """Configure message queue target for mixed test"""
        print("\nMessage queue types: 1=RabbitMQ, 2=Redis")
        mq_type = input("Select message queue type (1-2): ").strip()

        if mq_type == "1":
            mq_type = "rabbitmq"
        elif mq_type == "2":
            mq_type = "redis"
        else:
            print("Invalid message queue type.")
            return {}

        host = input("Enter message queue host: ").strip()
        queue = input("Enter queue name: ").strip()
        if not host or not queue:
            print("Invalid message queue target configuration.")
            return {}
        return {"type": "message_queue", "mq_type": mq_type, "host": host, "queue": queue}

    def _get_load_profile(self) -> dict:
        """Get load profile configuration"""
        users = int(input("Enter number of users: ").strip() or "10")
        ramp_up = int(input("Enter ramp-up time in seconds: ").strip() or "30")
        duration = int(input("Enter test duration in seconds: ").strip() or "60")
        think_time = int(input("Enter think time in seconds: ").strip() or "1")

        return {"users": users, "ramp_up": ramp_up, "duration": duration, "think_time": think_time}

    def _execute_test(self, test_config: dict):
        print("[DEBUG] Entered _execute_test")
        try:
            print(f"\nExecuting test: {test_config['test_name']}")
            print("Press Ctrl+C to stop the test early.")

            # Run the test synchronously and get summary
            print("[DEBUG] Running test_runner.run_test_sync")
            results = self.test_runner.run_test_sync(test_config)
            print("[DEBUG] Got results from test_runner")

            # Display results
            print("[DEBUG] Calling _display_results")
            self._display_results(results)
            print("[DEBUG] Finished _display_results")

            # Export results to CSV in 'reports' directory
            print("[DEBUG] Preparing to export results to CSV")
            exporter = CSVExporter()
            import os
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.csv"
            output_dir = "reports"
            os.makedirs(output_dir, exist_ok=True)
            csv_path = exporter.export_results(
                results.get("results", []), results, filename=filename
            )
            print(f"\nResults exported to: {csv_path}")
            print("[DEBUG] Finished exporting results to CSV")

        except KeyboardInterrupt:
            print("\nTest stopped by user.")
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            print(f"Test failed: {e}")
        print("[DEBUG] Exiting _execute_test")

    def _display_results(self, results: dict):
        """Display test results"""
        print("\n=== Test Results ===")
        print(f"Test Name: {results.get('test_name', 'Unknown')}")
        print(f"Duration: {results.get('duration', 0):.2f} seconds")
        print(f"Total Requests: {results.get('total_requests', 0)}")
        print(f"Successful Requests: {results.get('successful_requests', 0)}")
        print(f"Failed Requests: {results.get('failed_requests', 0)}")
        print(f"Average Response Time: {results.get('avg_response_time', 0):.3f} seconds")
        print(f"Throughput: {results.get('throughput', 0):.2f} requests/second")

        if results.get("errors"):
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")

    def _configure_environment(self):
        """Configure environment settings"""
        print("\n=== Environment Configuration ===")

        envs = ["dev", "qa", "stage", "prod"]
        current_env = self.config_manager.environment

        print(f"Current environment: {current_env}")
        print("Available environments:")

        for i, env in enumerate(envs, 1):
            print(f"{i}. {env}")

        choice = input(f"Select environment (1-{len(envs)}): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(envs):
            selected_env = envs[int(choice) - 1]
            self.config_manager.set_environment(selected_env)
            print(f"Environment set to: {selected_env}")
        else:
            print("Invalid choice.")

    def _validate_credentials(self):
        """Validate service credentials"""
        print("\n=== Credential Validation ===")

        validation = self.config_manager.validate_credentials()

        for service, is_valid in validation.items():
            status = "✓ Valid" if is_valid else "✗ Invalid/Missing"
            print(f"{service.upper()}: {status}")

        if not any(validation.values()):
            print("\nNo valid credentials found. Please configure your credentials.")

    def _show_test_history(self):
        """Show test history"""
        print("\n=== Test History ===")
        print("Feature not implemented yet.")

    def _export_results(
        self, results: Optional[Dict[str, Any]] = None, file_path: Optional[str] = None
    ) -> None:
        """Export test results to a file"""
        if not results:
            print("No results available to export")
            return

        if not file_path:
            file_path = input("Enter output file path: ").strip()
            if not file_path:
                print("No file path provided")
                return

        format = "csv"
        if file_path.endswith(".json"):
            format = "json"

        try:
            self.export_results(results, file_path, format=format)
            print(f"Results exported to {file_path}")
        except Exception as e:
            print(f"Error exporting results: {e}")

    def _show_help(self):
        """Show help information"""
        help_text = """
=== NLM Tool Help ===

Quick Test: Run a simple HTTP load test with minimal configuration
Custom Test: Create detailed test configurations for various protocols
Environment: Switch between dev, qa, stage, and prod environments
Credentials: Validate your AWS, Datadog, and Splunk credentials
History: View previous test results
Export: Export test results to CSV format

For more information, visit the project documentation.
        """
        print(help_text)

    def _exit(self):
        """Exit the CLI"""
        print("Thank you for using NLM Performance Testing Tool!")

    def parse_arguments(self, args=None):
        """Parse command-line arguments for CLI interface."""
        parser = argparse.ArgumentParser(description="NLM CLI Interface")

        # Test configuration
        parser.add_argument("--test-config", type=str, help="Path to test configuration file")
        parser.add_argument("--test-name", type=str, default="Test", help="Name of the test")

        # HTTP target
        parser.add_argument("--target-url", type=str, help="Target URL for HTTP test")
        parser.add_argument("--method", type=str, default="GET", help="HTTP method")
        parser.add_argument(
            "--expected-status", type=int, default=200, help="Expected HTTP status code"
        )

        # Database target
        parser.add_argument("--db-type", type=str, help="Database type")
        parser.add_argument("--db-host", type=str, help="Database host")
        parser.add_argument("--db-port", type=int, help="Database port")
        parser.add_argument("--db-name", type=str, help="Database name")
        parser.add_argument("--db-query", type=str, help="Database query")

        # Message queue target
        parser.add_argument("--mq-type", type=str, help="Message queue type")
        parser.add_argument("--mq-host", type=str, help="Message queue host")
        parser.add_argument("--mq-port", type=int, help="Message queue port")
        parser.add_argument("--mq-queue", type=str, help="Message queue name")

        # Load profile
        parser.add_argument("--users", type=int, default=10, help="Number of users")
        parser.add_argument("--threads", type=int, default=4, help="Number of threads")
        parser.add_argument("--duration", type=int, default=60, help="Test duration (seconds)")
        parser.add_argument("--think-time", type=int, default=1, help="Think time (seconds)")
        parser.add_argument("--ramp-up", type=int, default=30, help="Ramp up time (seconds)")

        # Output
        parser.add_argument("--output", type=str, help="Output directory for reports")

        # Quick test mode
        parser.add_argument("--quick", action="store_true", help="Run quick test")
        parser.add_argument("--url", type=str, help="URL for quick test")

        parsed_args = parser.parse_args(args)

        # Validate
        if hasattr(parsed_args, "users") and parsed_args.users <= 0:
            parser.error("Number of users must be positive")
        if hasattr(parsed_args, "duration") and parsed_args.duration <= 0:
            parser.error("Duration must be positive")

        return parsed_args

    def load_test_config(self, file_path):
        """Load test configuration from a YAML file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")
        with open(file_path, "r") as f:
            return yaml.safe_load(f)

    def build_test_config_from_args(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Build test configuration from command line arguments"""
        config = {
            "test_name": getattr(args, "test_name", "Quick Test"),
            "load_profile": {
                "users": getattr(args, "users", 1),
                "threads": getattr(args, "threads", 1),
                "duration": getattr(args, "duration", 60),
                "think_time": getattr(args, "think_time", 1),
                "ramp_up": getattr(args, "ramp_up", 5),
            },
        }

        # Configure target based on type - check for specific values, not just presence
        db_type = getattr(args, "db_type", None)
        mq_type = getattr(args, "mq_type", None)
        target_url = getattr(args, "target_url", None)
        url = getattr(args, "url", None)

        if db_type:
            # Database target
            config["targets"] = [
                {
                    "type": "database",
                    "db_type": db_type,
                    "host": getattr(args, "db_host", None),
                    "port": getattr(args, "db_port", None),
                    "database": getattr(args, "db_name", None),
                    "query": getattr(args, "db_query", None),
                }
            ]
        elif mq_type:
            # Message queue target
            config["targets"] = [
                {
                    "type": "message_queue",
                    "mq_type": mq_type,
                    "host": getattr(args, "mq_host", None),
                    "port": getattr(args, "mq_port", None),
                    "queue": getattr(args, "mq_queue", None),
                }
            ]
        elif target_url:
            # HTTP target with target_url
            config["targets"] = [
                {
                    "type": "http",
                    "url": target_url,
                    "method": getattr(args, "method", "GET"),
                    "expected_status": getattr(args, "expected_status", 200),
                }
            ]
        elif url:
            # HTTP target with url (for quick run)
            config["targets"] = [
                {
                    "type": "http",
                    "url": url,
                    "method": getattr(args, "method", "GET"),
                    "expected_status": getattr(args, "expected_status", 200),
                }
            ]
        else:
            # Default to HTTP target with localhost
            config["targets"] = [
                {
                    "type": "http",
                    "url": "http://localhost:8080",
                    "method": "GET",
                    "expected_status": 200,
                }
            ]

        return config

    def quick_run(self, args) -> int:
        """Run a quick test with minimal configuration"""
        config = self.build_test_config_from_args(args)
        try:
            results = self.test_runner.run_test_sync(config)
            if args.output:
                self.export_results(results, args.output, format="csv")
            else:
                self.display_results_summary(results)
            return 0
        except Exception as e:
            print(f"Error running quick test: {e}")
            return 1

    def display_results_summary(self, results):
        """Display a summary of test results."""
        summary = results.copy()
        if "successful_requests" not in summary or "failed_requests" not in summary:
            total = len(results.get("results", []))
            successful = sum(1 for r in results.get("results", []) if r.get("success"))
            failed = total - successful
            summary["total_requests"] = total
            summary["successful_requests"] = successful
            summary["failed_requests"] = failed
            summary["success_rate"] = round(successful / total, 4) if total > 0 else 0.0
            response_times = [r.get("response_time", 0.0) for r in results.get("results", [])]
            summary["avg_response_time"] = (
                round(sum(response_times) / total, 4) if total > 0 else 0.0
            )
            summary["min_response_time"] = round(min(response_times), 4) if response_times else 0.0
            summary["max_response_time"] = round(max(response_times), 4) if response_times else 0.0
        print(f"Test Name: {summary.get('test_name', '')}")
        print(f"Total Requests: {summary.get('total_requests', 0)}")
        print(f"Successful: {summary.get('successful_requests', 0)}")
        print(f"Failed: {summary.get('failed_requests', 0)}")
        print(f"Success Rate: {round(summary.get('success_rate', 0.0), 2):.2f}")
        print(f"Avg Response Time: {round(summary.get('avg_response_time', 0.0), 3):.3f}s")
        print(f"Min Response Time: {round(summary.get('min_response_time', 0.0), 3):.3f}s")
        print(f"Max Response Time: {round(summary.get('max_response_time', 0.0), 3):.3f}s")

    def display_results_detailed(self, results):
        """Display detailed test results."""
        print(json.dumps(results, indent=2))

    def interactive_mode(self) -> int:
        """Run in interactive mode"""
        self._show_banner()
        while True:
            self._show_menu()
            choice = input("\nEnter your choice (1-8): ").strip()

            if choice == "1":
                self._run_quick_test()
            elif choice == "2":
                self._run_custom_test()
            elif choice == "3":
                self._configure_environment()
            elif choice == "4":
                self._validate_credentials()
            elif choice == "5":
                self._show_test_history()
            elif choice == "6":
                self._export_results()
            elif choice == "7":
                self._show_help()
            elif choice == "8":
                print("\nExiting NLM tool. Goodbye!")
                return 0
            else:
                print("\nInvalid choice. Please try again.")

        return 0

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test configuration"""
        if not config:
            raise ValueError("Configuration is empty")

        if not config.get("test_name"):
            config["test_name"] = "Unnamed Test"

        if not config.get("targets"):
            raise ValueError("No targets specified in configuration")

        # Validate target types
        valid_types = ["http", "database", "message_queue"]
        for target in config["targets"]:
            if not target.get("type"):
                raise ValueError("Target missing type")
            if target["type"] not in valid_types:
                raise ValueError("Invalid target type")

            # Validate required fields for each type
            if target["type"] == "http":
                if not target.get("url"):
                    raise ValueError("HTTP target missing URL")
            elif target["type"] == "database":
                if not target.get("db_type"):
                    raise ValueError("Database target missing db_type")
                if not target.get("host"):
                    raise ValueError("Database target missing host")
            elif target["type"] == "message_queue":
                if not target.get("mq_type"):
                    raise ValueError("Message queue target missing mq_type")
                if not target.get("host"):
                    raise ValueError("Message queue target missing host")

        if not config.get("load_profile"):
            config["load_profile"] = {
                "users": 1,
                "threads": 1,
                "duration": 60,
                "think_time": 1,
                "ramp_up": 5,
            }

        return config

    async def run_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a test asynchronously"""
        try:
            # Validate configuration
            test_config = self.validate_config(test_config)

            # Run the test
            result = await self.test_runner.run_test(test_config)
            if result is None:
                raise Exception("Test failed to return results")
            return result
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            raise  # Re-raise the exception to be caught by test

    def export_results(self, results: Dict[str, Any], file_path: str, format: str = "csv") -> None:
        """Export test results to a file in the specified format."""
        if format == "csv":
            exporter = CSVExporter()
            exporter.export_results(results.get("results", []), results, filename=file_path)
        elif format == "json":
            with open(file_path, "w") as f:
                json.dump(results, f, indent=2)
        else:
            raise ValueError("Unsupported export format")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NLM CLI Interface")
    parser.add_argument("--config", type=str, help="Path to test config YAML")
    parser.add_argument("--output", type=str, help="Output directory for reports")
    args, unknown = parser.parse_known_args()

    config_manager = ConfigManager()
    cli = CLIInterface(config_manager)

    if args.config and args.output:
        # Non-interactive mode for integration test
        import os

        import yaml

        from exporters.csv_exporter import CSVExporter

        with open(args.config, "r") as f:
            test_config = yaml.safe_load(f)
        results = cli.test_runner.run_test_sync(test_config)
        exporter = CSVExporter()
        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)
        csv_path = exporter.export_results(
            results.get("results", []),
            results,
            filename=os.path.join(output_dir, "integration_test_results.csv"),
        )
        print(f"Results exported to: {csv_path}")
    else:
        cli.run()
