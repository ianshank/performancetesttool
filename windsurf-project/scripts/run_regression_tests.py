#!/usr/bin/env python3
"""
Regression Test Runner for Stage Environment Validation

This script runs comprehensive regression tests to validate the system
before production deployment. It includes:
- Environment validation
- Critical functionality tests
- Performance benchmarks
- Integration tests
- Stress tests

Usage:
    python scripts/run_regression_tests.py [--env ENVIRONMENT] [--quick] [--report-file FILE]

Exit codes:
    0: All tests passed
    1: Tests failed
    2: Environment setup failed
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from utils.config import ConfigManager
    from utils.logger import get_logger
except ImportError:
    # Fallback for different path structures
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.config import ConfigManager
    from src.utils.logger import get_logger


class RegressionTestRunner:
    """Manages regression test execution and reporting"""

    def __init__(self, environment: str = "stage", quick: bool = False):
        self.environment = environment
        self.quick = quick
        self.logger = get_logger("regression")
        self.start_time = None
        self.results = {}

    def setup_environment(self) -> bool:
        """Setup and validate test environment"""
        self.logger.info(f"Setting up regression test environment: {self.environment}")

        try:
            # Validate environment configuration
            config_manager = ConfigManager()
            config_manager.set_environment(self.environment)

            env_config = config_manager.get_environment_config(self.environment)
            if not env_config:
                self.logger.error(f"Invalid environment configuration: {self.environment}")
                return False

            # Set environment variables
            os.environ["NLM_ENVIRONMENT"] = self.environment
            os.environ["PYTHONPATH"] = str(PROJECT_ROOT / "src")

            # Create required directories
            (PROJECT_ROOT / "reports").mkdir(exist_ok=True)
            (PROJECT_ROOT / "logs").mkdir(exist_ok=True)

            self.logger.info("Environment setup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Environment setup failed: {e}")
            return False

    def run_test_suite(
        self, test_type: str, test_path: str, markers: Optional[List[str]] = None
    ) -> Dict:
        """Run a specific test suite and return results"""
        self.logger.info(f"Running {test_type} tests...")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_path,
            "-v",
            "--tb=short",
            "--durations=10",
            "--json-report",
            f"--json-report-file={PROJECT_ROOT}/reports/regression_{test_type}_{int(time.time())}.json",
        ]

        # Add markers if specified
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        # Quick mode - skip slow tests
        if self.quick and test_type != "critical":
            cmd.extend(["-m", "not slow"])

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=600,  # 10 minute timeout per suite
            )

            duration = time.time() - start_time

            return {
                "type": test_type,
                "exit_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            self.logger.error(f"{test_type} tests timed out after 10 minutes")
            return {
                "type": test_type,
                "exit_code": 124,  # Timeout exit code
                "duration": 600,
                "stdout": "",
                "stderr": "Tests timed out",
                "passed": False,
            }
        except Exception as e:
            self.logger.error(f"Failed to run {test_type} tests: {e}")
            return {
                "type": test_type,
                "exit_code": 1,
                "duration": time.time() - start_time,
                "stdout": "",
                "stderr": str(e),
                "passed": False,
            }

    def run_all_tests(self) -> bool:
        """Run all regression test suites"""
        self.start_time = time.time()
        self.logger.info("Starting regression test execution")

        # Define test suites in order of importance
        test_suites = [
            {
                "name": "critical",
                "path": "tests/test_regression.py::TestCriticalFunctionality",
                "required": True,
                "description": "Critical functionality that must work",
            },
            {
                "name": "configuration",
                "path": "tests/test_regression.py::TestConfigurationRegression",
                "required": True,
                "description": "Configuration and environment validation",
            },
            {
                "name": "integration",
                "path": "tests/test_regression.py::TestIntegrationRegression",
                "required": True,
                "description": "Integration points and workflows",
            },
            {
                "name": "performance",
                "path": "tests/test_regression.py::TestPerformanceRegression",
                "required": False,
                "description": "Performance benchmarks",
            },
        ]

        # Add stress tests if not in quick mode
        if not self.quick:
            test_suites.append(
                {
                    "name": "stress",
                    "path": "tests/test_regression.py::TestStressRegression",
                    "required": False,
                    "description": "Stress and load tests",
                    "markers": ["slow"],
                }
            )

        all_passed = True

        for suite in test_suites:
            result = self.run_test_suite(suite["name"], suite["path"], suite.get("markers"))

            self.results[suite["name"]] = result

            if not result["passed"]:
                self.logger.error(f"{suite['name']} tests failed!")
                if suite["required"]:
                    self.logger.error("Required test suite failed - deployment should be blocked")
                    all_passed = False
                else:
                    self.logger.warning("Optional test suite failed - review recommended")
            else:
                self.logger.info(f"{suite['name']} tests passed in {result['duration']:.2f}s")

        total_duration = time.time() - self.start_time
        self.logger.info(f"Regression tests completed in {total_duration:.2f}s")

        return all_passed

    def generate_report(self, report_file: Optional[str] = None) -> str:
        """Generate detailed test report"""
        if not report_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"reports/regression_report_{timestamp}.json"

        report_path = PROJECT_ROOT / report_file

        # Calculate summary statistics
        total_suites = len(self.results)
        passed_suites = sum(1 for r in self.results.values() if r["passed"])
        total_duration = time.time() - self.start_time if self.start_time else 0

        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "quick_mode": self.quick,
            "summary": {
                "total_suites": total_suites,
                "passed_suites": passed_suites,
                "failed_suites": total_suites - passed_suites,
                "success_rate": passed_suites / total_suites if total_suites > 0 else 0,
                "total_duration": total_duration,
                "deployment_approved": passed_suites == total_suites
                or self._check_required_passed(),
            },
            "suites": self.results,
            "recommendations": self._generate_recommendations(),
        }

        # Write report
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Generate human-readable summary
        self._print_summary(report)

        return str(report_path)

    def _check_required_passed(self) -> bool:
        """Check if all required test suites passed"""
        required_suites = ["critical", "configuration", "integration"]
        return all(self.results.get(suite, {}).get("passed", False) for suite in required_suites)

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        for suite_name, result in self.results.items():
            if not result["passed"]:
                if suite_name == "critical":
                    recommendations.append("BLOCK DEPLOYMENT: Critical functionality tests failed")
                elif suite_name == "configuration":
                    recommendations.append("BLOCK DEPLOYMENT: Configuration validation failed")
                elif suite_name == "integration":
                    recommendations.append("BLOCK DEPLOYMENT: Integration tests failed")
                elif suite_name == "performance":
                    recommendations.append(
                        "WARNING: Performance benchmarks not met - review required"
                    )
                elif suite_name == "stress":
                    recommendations.append("INFO: Stress tests failed - consider capacity planning")

        if not recommendations:
            recommendations.append("APPROVE DEPLOYMENT: All tests passed")

        return recommendations

    def _print_summary(self, report: Dict):
        """Print human-readable test summary"""
        print("\n" + "=" * 60)
        print("REGRESSION TEST SUMMARY")
        print("=" * 60)
        print(f"Environment: {report['environment']}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Quick Mode: {report['quick_mode']}")
        print(f"Duration: {report['summary']['total_duration']:.2f}s")
        print()

        print("TEST SUITES:")
        for suite_name, result in report["suites"].items():
            status = "PASS" if result["passed"] else "FAIL"
            duration = result["duration"]
            print(f"  {suite_name:15} {status:4} ({duration:6.2f}s)")

        print()
        print(f"SUCCESS RATE: {report['summary']['success_rate']:.1%}")
        print(
            f"DEPLOYMENT: {'APPROVED' if report['summary']['deployment_approved'] else 'BLOCKED'}"
        )

        print("\nRECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")

        print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run regression tests for stage environment validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_regression_tests.py                    # Run all tests in stage
  python scripts/run_regression_tests.py --quick            # Run quick test subset
  python scripts/run_regression_tests.py --env prod         # Run in prod environment  
  python scripts/run_regression_tests.py --report-file custom.json  # Custom report file
        """,
    )

    parser.add_argument(
        "--env",
        choices=["dev", "qa", "stage", "prod"],
        default="stage",
        help="Target environment (default: stage)",
    )

    parser.add_argument(
        "--quick", action="store_true", help="Run quick test subset (skip slow tests)"
    )

    parser.add_argument("--report-file", type=str, help="Custom report file path")

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        import logging

        logging.basicConfig(level=logging.INFO)

    # Create test runner
    runner = RegressionTestRunner(environment=args.env, quick=args.quick)

    try:
        # Setup environment
        if not runner.setup_environment():
            print("ERROR: Environment setup failed")
            return 2

        # Run tests
        all_passed = runner.run_all_tests()

        # Generate report
        report_path = runner.generate_report(args.report_file)
        print(f"\nDetailed report saved to: {report_path}")

        # Return appropriate exit code
        if all_passed:
            print("\n✅ All regression tests passed - deployment approved")
            return 0
        else:
            print("\n❌ Regression tests failed - deployment blocked")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Regression tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Regression test execution failed: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
