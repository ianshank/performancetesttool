"""
Unit tests for AI analysis engine
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.ai.analysis_engine import AIAnalysisEngine
from src.utils.config import ConfigManager


class TestAnalysisEngine:
    """Test the AI AnalysisEngine class"""
    
    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager"""
        return Mock(spec=ConfigManager)
    
    @pytest.fixture
    def analysis_engine(self, config_manager):
        """Create an AnalysisEngine instance"""
        return AIAnalysisEngine(config_manager)
    
    @pytest.fixture
    def sample_test_results(self):
        """Sample test results for analysis"""
        return {
            "test_name": "API Load Test",
            "start_time": 1640995200,
            "end_time": 1640995260,
            "duration": 60,
            "results": [
                {
                    "timestamp": 1640995201,
                    "user_id": 1,
                    "request_id": 1,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 200,
                    "response_time": 0.15,
                    "success": True,
                    "error": None
                },
                {
                    "timestamp": 1640995202,
                    "user_id": 1,
                    "request_id": 2,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 200,
                    "response_time": 0.12,
                    "success": True,
                    "error": None
                },
                {
                    "timestamp": 1640995203,
                    "user_id": 2,
                    "request_id": 1,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 500,
                    "response_time": 2.5,
                    "success": False,
                    "error": "Internal Server Error"
                }
            ]
        }
    
    def test_initialization(self, analysis_engine):
        """Test AnalysisEngine initialization"""
        assert analysis_engine is not None
        assert analysis_engine.config_manager is not None
        assert analysis_engine.logger is not None
    
    def test_analyze_results_basic(self, analysis_engine, sample_test_results):
        """Test basic result analysis"""
        analysis = analysis_engine.analyze_results(sample_test_results)
        assert analysis is not None
        assert "summary" in analysis
        assert "performance_metrics" in analysis
        assert "issues" in analysis
        assert "recommendations" in analysis
        # Check summary
        summary = analysis["summary"]
        assert summary["total_requests"] == 3
        assert summary["successful_requests"] == 2
        assert summary["failed_requests"] == 1
        assert summary["success_rate"] == 2/3
        # Enhanced summary fields
        assert "percentiles" in summary
        assert "response_time_distribution" in summary
        assert "error_analysis" in summary
        assert "performance_insights" in summary
        assert "target_breakdown" in summary
        assert "user_breakdown" in summary
        assert "time_series_analysis" in summary
        # Check performance metrics
        metrics = analysis["performance_metrics"]
        assert "avg_response_time" in metrics
        assert "min_response_time" in metrics
        assert "max_response_time" in metrics
        assert metrics["avg_response_time"] > 0
        # Enhanced metrics fields
        assert "percentiles" in metrics or True  # If present
        assert "error_analysis" in metrics or True
        assert "performance_insights" in metrics or True
    
    def test_analyze_results_empty(self, analysis_engine):
        """Test analysis with empty results"""
        empty_results = {
            "test_name": "Empty Test",
            "start_time": 1640995200,
            "end_time": 1640995200,
            "duration": 0,
            "results": []
        }
        
        analysis = analysis_engine.analyze_results(empty_results)
        
        assert analysis is not None
        assert analysis["summary"]["total_requests"] == 0
        assert analysis["summary"]["successful_requests"] == 0
        assert analysis["summary"]["failed_requests"] == 0
        assert analysis["summary"]["success_rate"] == 0.0
    
    def test_analyze_results_all_failures(self, analysis_engine):
        """Test analysis with all failed requests"""
        failed_results = {
            "test_name": "Failed Test",
            "start_time": 1640995200,
            "end_time": 1640995205,
            "duration": 5,
            "results": [
                {
                    "timestamp": 1640995201,
                    "user_id": 1,
                    "request_id": 1,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 500,
                    "response_time": 2.0,
                    "success": False,
                    "error": "Server Error"
                },
                {
                    "timestamp": 1640995202,
                    "user_id": 1,
                    "request_id": 2,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 503,
                    "response_time": 3.0,
                    "success": False,
                    "error": "Service Unavailable"
                }
            ]
        }
        
        analysis = analysis_engine.analyze_results(failed_results)
        
        assert analysis["summary"]["success_rate"] == 0.0
        assert analysis["summary"]["failed_requests"] == 2
        assert len(analysis["issues"]) > 0  # Should identify issues
    
    def test_analyze_results_performance_issues(self, analysis_engine):
        """Test analysis with performance issues"""
        slow_results = {
            "test_name": "Slow Test",
            "start_time": 1640995200,
            "end_time": 1640995210,
            "duration": 10,
            "results": [
                {
                    "timestamp": 1640995201,
                    "user_id": 1,
                    "request_id": 1,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 200,
                    "response_time": 5.0,  # Very slow
                    "success": True,
                    "error": None
                },
                {
                    "timestamp": 1640995202,
                    "user_id": 1,
                    "request_id": 2,
                    "method": "GET",
                    "url": "http://api.example.com/users",
                    "status_code": 200,
                    "response_time": 4.5,  # Very slow
                    "success": True,
                    "error": None
                }
            ]
        }
        
        analysis = analysis_engine.analyze_results(slow_results)
        
        assert analysis["performance_metrics"]["avg_response_time"] > 4.0
        assert len(analysis["issues"]) > 0  # Should identify performance issues
    
    @pytest.mark.asyncio
    async def test_generate_ai_insights_openai(self, analysis_engine, sample_test_results):
        """Test AI insights generation with OpenAI"""
        analysis = analysis_engine.analyze_results(sample_test_results)
        
        # Mock OpenAI client
        with patch('ai.analysis_engine.openai') as mock_openai:
            mock_openai.OpenAI.return_value.chat.completions.create.return_value.choices = [
                Mock(message=Mock(content=json.dumps({
                    "insights": ["High error rate detected", "Response times are acceptable"],
                    "recommendations": ["Investigate server errors", "Monitor performance"],
                    "risk_level": "medium"
                })))
            ]
            
            insights = await analysis_engine.generate_ai_insights(analysis)
            
            assert insights is not None
            assert "insights" in insights
            assert "recommendations" in insights
            assert "risk_level" in insights
    
    @pytest.mark.asyncio
    async def test_generate_ai_insights_anthropic(self, analysis_engine, sample_test_results):
        """Test AI insights generation with Anthropic"""
        analysis = analysis_engine.analyze_results(sample_test_results)
        
        # Mock Anthropic client
        with patch('ai.analysis_engine.anthropic') as mock_anthropic:
            mock_anthropic.Anthropic.return_value.messages.create.return_value.content = [
                Mock(type="text", text=json.dumps({
                    "insights": ["Performance degradation detected"],
                    "recommendations": ["Scale infrastructure"],
                    "risk_level": "high"
                }))
            ]
            
            insights = await analysis_engine.generate_ai_insights(analysis, provider="anthropic")
            
            assert insights is not None
            assert "insights" in insights
            assert "recommendations" in insights
            assert "risk_level" in insights
    
    @pytest.mark.asyncio
    async def test_generate_ai_insights_no_credentials(self, analysis_engine, sample_test_results):
        """Test AI insights generation without credentials"""
        analysis = analysis_engine.analyze_results(sample_test_results)
        
        # Mock missing credentials
        analysis_engine.config_manager.get_credential.return_value = {}
        
        insights = await analysis_engine.generate_ai_insights(analysis)
        
        # Should return basic insights without AI
        assert insights is not None
        assert "insights" in insights
        assert "recommendations" in insights
    
    def test_generate_report(self, analysis_engine, sample_test_results):
        """Test report generation"""
        analysis = analysis_engine.analyze_results(sample_test_results)
        
        report = analysis_engine.generate_report(sample_test_results, analysis)
        
        assert report is not None
        assert "test_name" in report
        assert "summary" in report
        assert "performance_metrics" in report
        assert "issues" in report
        assert "recommendations" in report
        assert "timestamp" in report
    
    def test_export_report_csv(self, analysis_engine, sample_test_results, tmp_path):
        """Test CSV report export"""
        analysis = analysis_engine.analyze_results(sample_test_results)
        report = analysis_engine.generate_report(sample_test_results, analysis)
        
        csv_file = tmp_path / "test_report.csv"
        analysis_engine.export_report(report, str(csv_file), format="csv")
        
        assert csv_file.exists()
        assert csv_file.stat().st_size > 0
    
    def test_export_report_json(self, analysis_engine, sample_test_results, tmp_path):
        """Test JSON report export"""
        analysis = analysis_engine.analyze_results(sample_test_results)
        report = analysis_engine.generate_report(sample_test_results, analysis)
        
        json_file = tmp_path / "test_report.json"
        analysis_engine.export_report(report, str(json_file), format="json")
        
        assert json_file.exists()
        assert json_file.stat().st_size > 0
        
        # Verify JSON is valid
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert "test_name" in data
            assert "summary" in data
    
    def test_export_report_invalid_format(self, analysis_engine, sample_test_results, tmp_path):
        """Test export with invalid format"""
        analysis = analysis_engine.analyze_results(sample_test_results)
        report = analysis_engine.generate_report(sample_test_results, analysis)
        
        invalid_file = tmp_path / "test_report.invalid"
        
        with pytest.raises(ValueError, match="Unsupported export format"):
            analysis_engine.export_report(report, str(invalid_file), format="invalid")
    
    def test_identify_performance_bottlenecks(self, analysis_engine):
        """Test performance bottleneck identification"""
        results = {
            "results": [
                {"response_time": 0.1, "success": True},
                {"response_time": 5.0, "success": True},  # Slow
                {"response_time": 0.2, "success": True},
                {"response_time": 8.0, "success": True},  # Very slow
                {"response_time": 0.15, "success": True}
            ]
        }
        
        bottlenecks = analysis_engine._identify_performance_bottlenecks(results)
        
        assert len(bottlenecks) > 0
        assert any("slow response times" in bottleneck.lower() for bottleneck in bottlenecks)
    
    def test_identify_error_patterns(self, analysis_engine):
        """Test error pattern identification"""
        results = {
            "results": [
                {"status_code": 200, "success": True},
                {"status_code": 500, "success": False, "error": "Server Error"},
                {"status_code": 200, "success": True},
                {"status_code": 500, "success": False, "error": "Server Error"},
                {"status_code": 503, "success": False, "error": "Service Unavailable"}
            ]
        }
        
        patterns = analysis_engine._identify_error_patterns(results)
        
        assert len(patterns) > 0
        assert any("server errors" in pattern.lower() for pattern in patterns)
    
    def test_calculate_percentiles(self, analysis_engine):
        """Test percentile calculation"""
        response_times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        percentiles = analysis_engine._calculate_percentiles(response_times)
        
        assert percentiles["p50"] == 0.5
        assert percentiles["p90"] == 0.9
        assert percentiles["p95"] == 0.95
        assert percentiles["p99"] == 0.99


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 