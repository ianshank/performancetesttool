#!/usr/bin/env python3
"""
Demo API Test Script for NLM Tool
Performs a mocked load test against a simulated API endpoint
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config import ConfigManager
from core.test_engine import TestEngine
from core.test_runner import TestRunner
from ai.analysis_engine import AIAnalysisEngine
from exporters.csv_exporter import CSVExporter


async def run_mocked_api_test():
    """Run a mocked API load test"""
    print("🚀 Starting NLM Mocked API Load Test")
    print("=" * 50)
    
    # Initialize components
    config = ConfigManager()
    test_engine = TestEngine(config)
    test_runner = TestRunner(config)
    analysis_engine = AIAnalysisEngine(config)
    
    # Define test configuration
    test_config = {
        "test_name": "Mocked API Load Test",
        "environment": "demo",
        "targets": [
            {
                "type": "http",
                "url": "https://httpbin.org/get",
                "method": "GET",
                "headers": {
                    "User-Agent": "NLM-Test-Tool/1.0",
                    "Accept": "application/json"
                },
                "expected_status": 200
            },
            {
                "type": "http", 
                "url": "https://httpbin.org/post",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "NLM-Test-Tool/1.0"
                },
                "expected_status": 200
            }
        ],
        "load_profile": {
            "users": 5,
            "threads": 2,
            "ramp_up": 10,
            "duration": 30,
            "think_time": 2
        }
    }
    
    print(f"📋 Test Configuration:")
    print(f"   Test Name: {test_config['test_name']}")
    print(f"   Targets: {len(test_config['targets'])} endpoints")
    print(f"   Users: {test_config['load_profile']['users']}")
    print(f"   Threads: {test_config['load_profile']['threads']}")
    print(f"   Duration: {test_config['load_profile']['duration']} seconds")
    print(f"   Ramp-up: {test_config['load_profile']['ramp_up']} seconds")
    print()
    
    # Run the test
    print("🔄 Executing load test...")
    start_time = time.time()
    
    try:
        results = await test_runner.run_test(test_config)
        test_duration = time.time() - start_time
        
        print(f"✅ Test completed in {test_duration:.2f} seconds")
        print()
        
        # Generate summary
        summary = test_engine.get_results_summary(results)
        
        # Display results
        print("📊 Test Results Summary:")
        print("=" * 30)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful: {summary['successful_requests']}")
        print(f"Failed: {summary['failed_requests']}")
        print(f"Success Rate: {summary['success_rate']:.2%}")
        print(f"Average Response Time: {summary['avg_response_time']:.3f}s")
        print(f"Min Response Time: {summary['min_response_time']:.3f}s")
        print(f"Max Response Time: {summary['max_response_time']:.3f}s")
        print(f"Throughput: {summary['throughput']:.2f} req/s")
        print(f"Test Duration: {summary['test_duration']:.2f}s")
        print(f"Requests/Second: {summary['requests_per_second']:.2f}")
        
        # Display percentiles
        if summary.get('percentiles'):
            print(f"\n📈 Response Time Percentiles:")
            print("=" * 30)
            for p, value in summary['percentiles'].items():
                print(f"  {p}: {value:.3f}s")
        
        # Display response time distribution
        if summary.get('response_time_distribution'):
            dist = summary['response_time_distribution']
            print(f"\n📊 Response Time Distribution:")
            print("=" * 30)
            print(f"  Very Fast (<100ms): {dist['distribution_percentages']['very_fast']:.1f}%")
            print(f"  Fast (100-500ms): {dist['distribution_percentages']['fast']:.1f}%")
            print(f"  Moderate (500ms-1s): {dist['distribution_percentages']['moderate']:.1f}%")
            print(f"  Slow (1-3s): {dist['distribution_percentages']['slow']:.1f}%")
            print(f"  Very Slow (>3s): {dist['distribution_percentages']['very_slow']:.1f}%")
        
        # Display error analysis
        if summary.get('error_analysis'):
            error_analysis = summary['error_analysis']
            print(f"\n🚨 Error Analysis:")
            print("=" * 30)
            print(f"  Error Count: {error_analysis['error_count']}")
            print(f"  Error Rate: {error_analysis['error_rate']:.2%}")
            
            if error_analysis['common_errors']:
                print(f"  Most Common Errors:")
                for error, count in error_analysis['common_errors'][:3]:
                    print(f"    - {error}: {count} occurrences")
            
            if error_analysis['status_codes']:
                print(f"  Status Code Distribution:")
                for status, count in error_analysis['status_codes'].items():
                    print(f"    - {status}: {count} requests")
        
        # Display performance insights
        if summary.get('performance_insights'):
            insights = summary['performance_insights']
            print(f"\n🎯 Performance Insights:")
            print("=" * 30)
            print(f"  Overall Assessment: {insights['overall_assessment']}")
            
            if insights['strengths']:
                print(f"  ✅ Strengths:")
                for strength in insights['strengths']:
                    print(f"    - {strength}")
            
            if insights['concerns']:
                print(f"  ⚠️  Concerns:")
                for concern in insights['concerns']:
                    print(f"    - {concern}")
            
            if insights['recommendations']:
                print(f"  💡 Recommendations:")
                for rec in insights['recommendations']:
                    print(f"    - {rec}")
        
        # Display target breakdown
        if summary.get('target_breakdown'):
            print(f"\n🎯 Target Performance Breakdown:")
            print("=" * 40)
            for target, stats in summary['target_breakdown'].items():
                print(f"  {target}:")
                print(f"    Requests: {stats['total_requests']}")
                print(f"    Success Rate: {stats['success_rate']:.2%}")
                print(f"    Avg Response Time: {stats['avg_response_time']:.3f}s")
        
        # Display user breakdown
        if summary.get('user_breakdown'):
            print(f"\n👥 User Performance Breakdown:")
            print("=" * 35)
            for user_id, stats in summary['user_breakdown'].items():
                print(f"  User {user_id}:")
                print(f"    Requests: {stats['total_requests']}")
                print(f"    Success Rate: {stats['success_rate']:.2%}")
                print(f"    Avg Response Time: {stats['avg_response_time']:.3f}s")
        
        # Display time series analysis
        if summary.get('time_series_analysis'):
            time_analysis = summary['time_series_analysis']
            if time_analysis.get('trend_analysis'):
                trends = time_analysis['trend_analysis']
                print(f"\n📈 Performance Trends:")
                print("=" * 25)
                print(f"  Response Time Trend: {trends.get('response_time_trend', 'N/A')}")
                print(f"  Success Rate Trend: {trends.get('success_rate_trend', 'N/A')}")
                print(f"  Performance Degradation: {'Yes' if trends.get('performance_degradation') else 'No'}")
                print(f"  Stability Score: {trends.get('stability_score', 0):.2f}")
        
        if summary['errors']:
            print(f"\n❌ Errors: {len(summary['errors'])} unique errors")
            for error in summary['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        print()
        
        # AI Analysis
        print("🤖 AI Analysis & Insights:")
        print("=" * 30)
        
        try:
            analysis = analysis_engine.analyze_test_results(summary, results)
            
            if 'summary' in analysis:
                print(f"Summary: {analysis['summary']}")
            
            if 'performance_analysis' in analysis:
                perf = analysis['performance_analysis']
                print(f"Response Time Assessment: {perf.get('response_time_assessment', 'N/A')}")
                print(f"Throughput Assessment: {perf.get('throughput_assessment', 'N/A')}")
                
                bottlenecks = perf.get('bottlenecks', [])
                if bottlenecks:
                    print("Potential Bottlenecks:")
                    for bottleneck in bottlenecks:
                        print(f"  - {bottleneck}")
                
                recommendations = perf.get('recommendations', [])
                if recommendations:
                    print("Recommendations:")
                    for rec in recommendations:
                        print(f"  - {rec}")
            
            if 'key_findings' in analysis:
                print("Key Findings:")
                for finding in analysis['key_findings'][:3]:  # Show first 3 findings
                    print(f"  - {finding}")
            
            if 'risk_assessment' in analysis:
                risk = analysis['risk_assessment']
                print(f"Risk Level: {risk.get('severity', 'N/A')}")
                print(f"Risk Description: {risk.get('description', 'N/A')}")
            
        except Exception as e:
            print(f"AI Analysis failed: {e}")
            print("Using basic analysis...")
        
        print()
        
        # Export results
        print("\n📁 Exporting results...")
        exporter = CSVExporter()
        csv_file = exporter.export_results(results, summary)
        print(f"Results exported to: {csv_file}")
        
        # Export AI analysis
        if analysis:
            ai_file = exporter.export_ai_analysis(analysis, f"demo_ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            print(f"AI analysis exported to: {ai_file}")
        
        print()
        print("🎉 Mocked API Test Completed Successfully!")
        
        return {
            'test_config': test_config,
            'summary': summary,
            'analysis': analysis if 'analysis' in locals() else None,
            'results_count': len(results)
        }
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


def display_sample_results():
    """Display sample results for demonstration"""
    print("\n📈 Sample Performance Metrics:")
    print("=" * 40)
    
    sample_data = {
        "test_name": "Sample API Load Test",
        "total_requests": 150,
        "successful_requests": 142,
        "failed_requests": 8,
        "success_rate": 0.947,
        "avg_response_time": 0.234,
        "min_response_time": 0.089,
        "max_response_time": 1.456,
        "throughput": 5.0,
        "errors": ["Connection timeout", "HTTP 500", "DNS resolution failed"]
    }
    
    print(f"📊 Test Summary:")
    print(f"   Total Requests: {sample_data['total_requests']}")
    print(f"   Success Rate: {sample_data['success_rate']:.1%}")
    print(f"   Average Response Time: {sample_data['avg_response_time']:.3f}s")
    print(f"   Throughput: {sample_data['throughput']:.1f} req/s")
    print(f"   Errors: {len(sample_data['errors'])} types")
    
    print(f"\n🎯 Performance Assessment:")
    if sample_data['success_rate'] > 0.95:
        print("   ✅ Excellent reliability (>95% success rate)")
    elif sample_data['success_rate'] > 0.90:
        print("   ⚠️  Good reliability (90-95% success rate)")
    else:
        print("   ❌ Poor reliability (<90% success rate)")
    
    if sample_data['avg_response_time'] < 0.5:
        print("   ✅ Fast response times (<0.5s average)")
    elif sample_data['avg_response_time'] < 1.0:
        print("   ⚠️  Moderate response times (0.5-1.0s average)")
    else:
        print("   ❌ Slow response times (>1.0s average)")
    
    if sample_data['throughput'] > 10:
        print("   ✅ High throughput (>10 req/s)")
    elif sample_data['throughput'] > 5:
        print("   ⚠️  Moderate throughput (5-10 req/s)")
    else:
        print("   ❌ Low throughput (<5 req/s)")


if __name__ == "__main__":
    print("🧪 NLM Tool - Mocked API Test Demo")
    print("=" * 50)
    
    # Show sample results first
    display_sample_results()
    
    print("\n" + "=" * 50)
    
    # Run actual test
    try:
        result = asyncio.run(run_mocked_api_test())
        if result:
            print(f"\n📋 Test completed with {result['results_count']} data points")
        else:
            print("\n❌ Test failed to complete")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print("\n🏁 Demo completed!") 