"""
Command Line Interface for NLM Performance Testing Tool
"""

import asyncio
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.config import ConfigManager
from src.core.test_runner import TestRunner
from src.ai.analysis_engine import AIAnalysisEngine
from src.exporters.csv_exporter import CSVExporter

logger = get_logger(__name__)

class CLIInterface:
    """Command Line Interface for the NLM Performance Testing Tool"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.test_runner = TestRunner(self.config)
        self.ai_engine = AIAnalysisEngine(self.config)
        self.exporter = CSVExporter()
        
    def run(self):
        """Run the CLI interface"""
        self._show_welcome()
        
        while True:
            try:
                choice = self._show_menu()
                
                if choice == "1":
                    self._run_quick_test()
                elif choice == "2":
                    self._run_custom_test()
                elif choice == "3":
                    self._view_reports()
                elif choice == "4":
                    self._configure_settings()
                elif choice == "5":
                    self._validate_credentials()
                elif choice == "6":
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("\n❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"CLI error: {e}")
                print(f"\n❌ Error: {e}")
    
    def _show_welcome(self):
        """Display welcome message"""
        print("""
🚀 NLM Performance Testing Tool - CLI
=====================================
Welcome to the Neural Load Manager CLI interface!
This tool helps you run performance tests and analyze results.
        """)
    
    def _show_menu(self) -> str:
        """Display main menu and get user choice"""
        print("""
📋 Main Menu:
1. Run Quick Test (HTTP API)
2. Run Custom Test
3. View Reports
4. Configure Settings
5. Validate Credentials
6. Exit

Enter your choice (1-6): """, end="")
        return input().strip()
    
    def _run_quick_test(self):
        """Run a quick HTTP API test"""
        print("\n🚀 Quick HTTP API Test")
        print("=" * 30)
        
        # Get test parameters
        url = input("Enter target URL (default: https://httpbin.org/get): ").strip()
        if not url:
            url = "https://httpbin.org/get"
        
        users = input("Enter number of users (default: 5): ").strip()
        users = int(users) if users.isdigit() else 5
        
        duration = input("Enter test duration in seconds (default: 30): ").strip()
        duration = int(duration) if duration.isdigit() else 30
        
        print(f"\n🎯 Test Configuration:")
        print(f"   URL: {url}")
        print(f"   Users: {users}")
        print(f"   Duration: {duration}s")
        
        confirm = input("\nStart test? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Test cancelled.")
            return
        
        # Run test
        print(f"\n⏳ Running test... This will take about {duration} seconds.")
        
        test_config = {
            "test_name": f"Quick Test - {url}",
            "targets": [
                {
                    "type": "http",
                    "url": url,
                    "method": "GET",
                    "headers": {},
                    "body": None
                }
            ],
            "users": users,
            "duration": duration,
            "ramp_up": 5,
            "think_time": 1
        }
        
        try:
            results = asyncio.run(self.test_runner.run_test(test_config))
            self._display_results(results)
            
            # Ask if user wants AI analysis
            if input("\n🤖 Run AI analysis? (y/N): ").strip().lower() == 'y':
                analysis = asyncio.run(self.ai_engine.analyze_results(results))
                self._display_analysis(analysis)
            
            # Ask if user wants to export
            if input("\n💾 Export results? (y/N): ").strip().lower() == 'y':
                self._export_results(results)
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
            print(f"❌ Test failed: {e}")
    
    def _run_custom_test(self):
        """Run a custom test with configuration file"""
        print("\n🔧 Custom Test")
        print("=" * 20)
        
        config_file = input("Enter path to test configuration file: ").strip()
        
        if not config_file:
            print("❌ No configuration file specified.")
            return
        
        if not Path(config_file).exists():
            print(f"❌ Configuration file not found: {config_file}")
            return
        
        try:
            # Load and run test
            print(f"\n⏳ Loading configuration from {config_file}...")
            results = asyncio.run(self.test_runner.run_test_from_file(config_file))
            self._display_results(results)
            
            # AI analysis and export options
            if input("\n🤖 Run AI analysis? (y/N): ").strip().lower() == 'y':
                analysis = asyncio.run(self.ai_engine.analyze_results(results))
                self._display_analysis(analysis)
            
            if input("\n💾 Export results? (y/N): ").strip().lower() == 'y':
                self._export_results(results)
                
        except Exception as e:
            logger.error(f"Custom test failed: {e}")
            print(f"❌ Custom test failed: {e}")
    
    def _view_reports(self):
        """View available reports"""
        print("\n📊 Reports")
        print("=" * 10)
        
        reports_dir = Path("demo_reports")
        if not reports_dir.exists():
            print("❌ No reports directory found.")
            return
        
        reports = list(reports_dir.glob("*.csv"))
        if not reports:
            print("❌ No reports found.")
            return
        
        print(f"Found {len(reports)} reports:")
        for i, report in enumerate(reports, 1):
            print(f"  {i}. {report.name}")
        
        choice = input(f"\nSelect report to view (1-{len(reports)}) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            return
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(reports):
                self._view_report(reports[choice_idx])
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Invalid input.")
    
    def _view_report(self, report_path: Path):
        """View a specific report"""
        print(f"\n📄 Viewing: {report_path.name}")
        print("=" * 50)
        
        try:
            with open(report_path, 'r') as f:
                lines = f.readlines()
                
            if len(lines) <= 1:
                print("❌ Report is empty.")
                return
            
            # Show header
            print("Headers:")
            print(lines[0].strip())
            
            # Show first few data rows
            print(f"\nFirst 5 data rows:")
            for i, line in enumerate(lines[1:6], 1):
                print(f"{i}. {line.strip()}")
            
            if len(lines) > 6:
                print(f"... and {len(lines) - 6} more rows")
                
        except Exception as e:
            print(f"❌ Error reading report: {e}")
    
    def _configure_settings(self):
        """Configure tool settings"""
        print("\n⚙️  Configuration")
        print("=" * 20)
        
        print("Current settings:")
        print(f"  Environment: {self.config.environment}")
        print(f"  AWS Region: {self.config.get_credentials('aws').get('region', 'Not set')}")
        print(f"  Datadog Site: {self.config.get_environment_config().get('datadog_site', 'Not set')}")
        print(f"  Splunk Host: {self.config.get_environment_config().get('splunk_host', 'Not set')}")
        
        print("\nTo modify settings:")
        print("1. Edit the .env file directly")
        print("2. Use environment variables")
        print("3. Create a custom config file")
        
        input("\nPress Enter to continue...")
    
    def _validate_credentials(self):
        """Validate configured credentials"""
        print("\n🔐 Credential Validation")
        print("=" * 25)
        
        validation = self.config.validate_credentials()
        
        print("Credential Status:")
        for service, is_valid in validation.items():
            status = "✅ Valid" if is_valid else "❌ Invalid/Missing"
            print(f"  {service.upper()}: {status}")
        
        if not any(validation.values()):
            print("\n⚠️  No valid credentials found.")
            print("Please configure your credentials in the .env file.")
        
        input("\nPress Enter to continue...")
    
    def _display_results(self, results: Dict[str, Any]):
        """Display test results"""
        print("\n📊 Test Results")
        print("=" * 20)
        print(f"Test Name: {results.get('test_name', 'Unknown')}")
        print(f"Duration: {results.get('duration', 0):.2f} seconds")
        print(f"Total Requests: {results.get('total_requests', 0)}")
        print(f"Successful: {results.get('successful_requests', 0)}")
        print(f"Failed: {results.get('failed_requests', 0)}")
        print(f"Avg Response Time: {results.get('avg_response_time', 0):.3f}s")
        print(f"Throughput: {results.get('throughput', 0):.2f} req/s")
    
    def _display_analysis(self, analysis: Dict[str, Any]):
        """Display AI analysis results"""
        print("\n🤖 AI Analysis")
        print("=" * 15)
        print(f"Provider: {analysis.get('provider', 'Unknown')}")
        print(f"Summary: {analysis.get('summary', 'No summary')}")
        
        findings = analysis.get('key_findings', [])
        if findings:
            print("Key Findings:")
            for finding in findings:
                print(f"  • {finding}")
        
        print(f"Risk Level: {analysis.get('risk_level', 'Unknown')}")
        print(f"Risk Description: {analysis.get('risk_description', 'No description')}")
    
    def _export_results(self, results: Dict[str, Any]):
        """Export test results"""
        print("\n💾 Exporting Results")
        print("=" * 20)
        
        try:
            timestamp = results.get('timestamp', 'unknown')
            test_name = results.get('test_name', 'test').replace(' ', '_')
            
            # Export summary
            summary_path = self.exporter.export_summary(results, f"{test_name}_summary_{timestamp}")
            print(f"✅ Summary exported to: {summary_path}")
            
            # Export analysis if available
            if 'analysis' in results:
                analysis_path = self.exporter.export_analysis(results['analysis'], f"{test_name}_analysis_{timestamp}")
                print(f"✅ Analysis exported to: {analysis_path}")
            
            print("✅ Export completed successfully!")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    cli = CLIInterface()
    cli.run() 