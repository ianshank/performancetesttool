#!/usr/bin/env python3
"""
Demo script for NLM Performance Testing Tool
This script demonstrates how to use the NLM tool programmatically
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config import ConfigManager
from utils.logger import setup_logging
from core.test_runner import TestRunner
from ai.analysis_engine import AIAnalysisEngine
from exporters.csv_exporter import CSVExporter


def main():
    """Main demo function"""
    print("🚀 NLM Performance Testing Tool Demo")
    print("=" * 50)
    
    # Setup logging
    logger = setup_logging(verbose=True)
    logger.info("Starting NLM demo")
    
    try:
        # Initialize configuration
        print("\n1. Initializing configuration...")
        config = ConfigManager()
        print(f"   Environment: {config.environment}")
        
        # Validate credentials
        print("\n2. Validating credentials...")
        validation = config.validate_credentials()
        for service, is_valid in validation.items():
            status = "✓" if is_valid else "✗"
            print(f"   {service.upper()}: {status}")
        
        # Create test configuration
        print("\n3. Creating test configuration...")
        test_config = {
            "test_name": "Demo API Load Test",
            "targets": [
                {
                    "type": "http",
                    "url": "https://httpbin.org/get",
                    "method": "GET",
                    "expected_status": 200
                },
                {
                    "type": "http",
                    "url": "https://httpbin.org/delay/1",
                    "method": "GET",
                    "expected_status": 200
                }
            ],
            "load_profile": {
                "users": 5,
                "ramp_up": 10,
                "duration": 30,
                "think_time": 1
            }
        }
        
        print(f"   Test name: {test_config['test_name']}")
        print(f"   Targets: {len(test_config['targets'])}")
        print(f"   Users: {test_config['load_profile']['users']}")
        print(f"   Duration: {test_config['load_profile']['duration']}s")
        
        # Initialize test runner
        print("\n4. Initializing test runner...")
        runner = TestRunner(config)
        
        # Run the test
        print("\n5. Running load test...")
        print("   This will take about 30 seconds...")
        start_time = time.time()
        
        results = runner.run_test(test_config)
        
        duration = time.time() - start_time
        print(f"   Test completed in {duration:.2f} seconds")
        
        # Display results
        print("\n6. Test Results:")
        print(f"   Test Name: {results.get('test_name', 'Unknown')}")
        print(f"   Duration: {results.get('duration', 0):.2f} seconds")
        print(f"   Total Requests: {results.get('total_requests', 0)}")
        print(f"   Successful: {results.get('successful_requests', 0)}")
        print(f"   Failed: {results.get('failed_requests', 0)}")
        print(f"   Avg Response Time: {results.get('avg_response_time', 0):.3f}s")
        print(f"   Throughput: {results.get('throughput', 0):.2f} req/s")
        
        # AI Analysis
        print("\n7. Running AI analysis...")
        ai_engine = AIAnalysisEngine(config)
        analysis = ai_engine.analyze_test_results(results)
        
        print(f"   Analysis Provider: {analysis.get('llm_provider', 'basic')}")
        print(f"   Summary: {analysis.get('summary', 'No summary available')}")
        
        # Display key findings
        key_findings = analysis.get('key_findings', [])
        if key_findings:
            print("   Key Findings:")
            for finding in key_findings[:3]:  # Show first 3 findings
                print(f"     • {finding}")
        
        # Risk assessment
        risk = analysis.get('risk_assessment', {})
        if risk:
            severity = risk.get('severity', 'unknown')
            description = risk.get('description', 'No description')
            print(f"   Risk Level: {severity.upper()}")
            print(f"   Risk Description: {description}")
        
        # Export results
        print("\n8. Exporting results...")
        exporter = CSVExporter()
        
        # Create reports directory
        reports_dir = Path("demo_reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Export summary
        summary_file = reports_dir / "demo_summary.csv"
        exporter.export_summary_report(results, str(summary_file))
        print(f"   Summary exported to: {summary_file}")
        
        # Export AI analysis
        analysis_file = reports_dir / "demo_analysis.csv"
        exporter.export_ai_analysis(analysis, str(analysis_file))
        print(f"   Analysis exported to: {analysis_file}")
        
        # Create comprehensive report
        comprehensive_file = exporter.create_comprehensive_report(
            test_results=[],  # Raw results not available in this demo
            summary=results,
            ai_analysis=analysis,
            output_dir="demo_reports"
        )
        print(f"   Comprehensive report: {comprehensive_file}")
        
        print("\n✅ Demo completed successfully!")
        print("\nNext steps:")
        print("1. Review the generated reports in the 'demo_reports' directory")
        print("2. Try running the GUI: python src/main.py --gui")
        print("3. Try running the CLI: python src/main.py --cli")
        print("4. Try the dashboard: streamlit run src/dashboard/streamlit_app.py")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("This might be due to missing dependencies or configuration.")
        print("Please check the README.md for setup instructions.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 