"""
Unit tests for TestEngine class
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.test_engine import LoadTestEngine
from src.utils.config import ConfigManager


class TestTestEngine:
    """Test the core TestEngine class"""

    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager"""
        return Mock(spec=ConfigManager)

    @pytest.fixture
    def test_engine(self, config_manager):
        """Create a LoadTestEngine instance"""
        return LoadTestEngine(config_manager)

    def test_initialization(self, test_engine):
        """Test TestEngine initialization"""
        assert test_engine is not None
        assert test_engine.running == False
        assert test_engine.results == []
        assert test_engine.logger is not None

    def test_get_default_port(self, test_engine):
        """Test default port retrieval for different database types"""
        assert test_engine._get_default_port("postgresql") == 5432
        assert test_engine._get_default_port("mysql") == 3306
        assert test_engine._get_default_port("mongodb") == 27017
        assert test_engine._get_default_port("sqlite") == 0
        assert test_engine._get_default_port("redis") == 6379
        assert test_engine._get_default_port("elasticsearch") == 9200
        assert test_engine._get_default_port("unknown") == 5432  # Default

    def test_get_mq_default_port(self, test_engine):
        """Test default port retrieval for different message queue types"""
        assert test_engine._get_mq_default_port("rabbitmq") == 5672
        assert test_engine._get_mq_default_port("kafka") == 9092
        assert test_engine._get_mq_default_port("redis") == 6379
        assert test_engine._get_mq_default_port("activemq") == 61616
        assert test_engine._get_mq_default_port("sqs") == 0
        assert test_engine._get_mq_default_port("pubsub") == 0
        assert test_engine._get_mq_default_port("unknown") == 5672  # Default

    def test_simulate_database_query(self, test_engine):
        """Test database query simulation"""
        # Test different database types
        postgresql_time = test_engine._simulate_database_query("postgresql", "SELECT 1")
        mysql_time = test_engine._simulate_database_query("mysql", "SELECT 1")
        mongodb_time = test_engine._simulate_database_query("mongodb", "SELECT 1")

        assert 0 < postgresql_time < 0.1
        assert 0 < mysql_time < 0.1
        assert 0 < mongodb_time < 0.1

        # Test query complexity - run multiple times to account for randomness
        simple_times = []
        complex_times = []
        write_times = []
        for _ in range(5):
            simple_times.append(test_engine._simulate_database_query("postgresql", "SELECT 1"))
            complex_times.append(
                test_engine._simulate_database_query(
                    "postgresql", "SELECT COUNT(*) FROM users JOIN orders"
                )
            )
            write_times.append(
                test_engine._simulate_database_query(
                    "postgresql", 'INSERT INTO users VALUES (1, "test")'
                )
            )

        # Use average times for comparison
        avg_simple = sum(simple_times) / len(simple_times)
        avg_complex = sum(complex_times) / len(complex_times)
        avg_write = sum(write_times) / len(write_times)

        assert avg_complex > avg_simple  # Join queries should take longer
        assert avg_write > avg_simple  # Write operations should take longer

    def test_simulate_mq_operation(self, test_engine):
        """Test message queue operation simulation"""
        # Test different MQ types
        rabbitmq_time = test_engine._simulate_mq_operation("rabbitmq")
        kafka_time = test_engine._simulate_mq_operation("kafka")
        redis_time = test_engine._simulate_mq_operation("redis")

        assert 0 < rabbitmq_time < 0.05
        assert 0 < kafka_time < 0.05
        assert 0 < redis_time < 0.05

        # Redis should be faster than RabbitMQ
        assert redis_time < rabbitmq_time

    def test_stop(self, test_engine):
        """Test stopping the test engine"""
        test_engine.running = True
        test_engine.stop()
        assert test_engine.running == False

    def test_get_results_summary_empty(self, test_engine):
        """Test results summary with empty results"""
        summary = test_engine.get_results_summary([])
        assert summary["total_requests"] == 0
        assert summary["successful_requests"] == 0
        assert summary["failed_requests"] == 0
        assert summary["success_rate"] == 0.0
        assert summary["avg_response_time"] == 0.0
        assert summary["min_response_time"] == 0.0
        assert summary["max_response_time"] == 0.0
        # New fields
        assert "percentiles" in summary
        assert "response_time_distribution" in summary
        assert "error_analysis" in summary
        assert "performance_insights" in summary
        assert "target_breakdown" in summary
        assert "user_breakdown" in summary
        assert "time_series_analysis" in summary

    def test_get_results_summary_with_data(self, test_engine):
        """Test results summary with sample data"""
        results = [
            {"timestamp": 1000, "response_time": 0.1, "success": True},
            {"timestamp": 1001, "response_time": 0.2, "success": True},
            {"timestamp": 1002, "response_time": 0.3, "success": False},
            {"timestamp": 1003, "response_time": 0.05, "success": True},
        ]
        summary = test_engine.get_results_summary(results)
        assert summary["total_requests"] == 4
        assert summary["successful_requests"] == 3
        assert summary["failed_requests"] == 1
        assert summary["success_rate"] == 0.75
        assert summary["avg_response_time"] == 0.1625
        assert summary["min_response_time"] == 0.05
        assert summary["max_response_time"] == 0.3
        # New fields
        assert "percentiles" in summary
        assert isinstance(summary["percentiles"], dict)
        assert "response_time_distribution" in summary
        assert isinstance(summary["response_time_distribution"], dict)
        assert "error_analysis" in summary
        assert isinstance(summary["error_analysis"], dict)
        assert "performance_insights" in summary
        assert isinstance(summary["performance_insights"], dict)
        assert "target_breakdown" in summary
        assert isinstance(summary["target_breakdown"], dict)
        assert "user_breakdown" in summary
        assert isinstance(summary["user_breakdown"], dict)
        assert "time_series_analysis" in summary
        assert isinstance(summary["time_series_analysis"], dict)

    def test_get_results_summary_enhanced(self, test_engine):
        """Test enhanced results summary generation with new metrics"""
        # Test data with timestamps and user IDs
        results = [
            {
                "timestamp": 1000,
                "response_time": 0.1,
                "success": True,
                "user_id": 1,
                "method": "GET",
                "url": "http://test.com/api",
                "status_code": 200,
            },
            {
                "timestamp": 1001,
                "response_time": 0.2,
                "success": True,
                "user_id": 1,
                "method": "GET",
                "url": "http://test.com/api",
                "status_code": 200,
            },
            {
                "timestamp": 1002,
                "response_time": 2.0,
                "success": False,
                "user_id": 2,
                "method": "GET",
                "url": "http://test.com/api",
                "error": "Timeout",
                "status_code": 500,
            },
        ]

        summary = test_engine.get_results_summary(results)

        # Basic metrics
        assert summary["total_requests"] == 3
        assert summary["successful_requests"] == 2
        assert summary["failed_requests"] == 1
        assert summary["success_rate"] == pytest.approx(0.6667, 0.001)
        assert summary["avg_response_time"] == pytest.approx(0.7667, 0.001)

        # New metrics
        assert "percentiles" in summary
        assert "response_time_distribution" in summary
        assert "error_analysis" in summary
        assert "performance_insights" in summary
        assert "target_breakdown" in summary
        assert "user_breakdown" in summary
        assert "time_series_analysis" in summary

        # Verify percentiles
        percentiles = summary["percentiles"]
        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles

        # Verify response time distribution
        dist = summary["response_time_distribution"]
        assert "buckets" in dist
        assert "distribution_percentages" in dist

        # Verify target breakdown
        target = summary["target_breakdown"]["GET http://test.com/api"]
        assert target["total_requests"] == 3
        assert target["successful_requests"] == 2
        assert target["failed_requests"] == 1

        # Verify user breakdown
        assert 1 in summary["user_breakdown"]  # User IDs are integers
        assert 2 in summary["user_breakdown"]
        assert summary["user_breakdown"][1]["successful_requests"] == 2
        assert summary["user_breakdown"][2]["failed_requests"] == 1

        # Verify time series analysis
        time_series = summary["time_series_analysis"]
        assert "time_buckets" in time_series
        assert "trend_analysis" in time_series

    def test_performance_insights_generation(self, test_engine):
        """Test performance insights generation"""
        response_times = [0.1, 0.2, 0.3, 2.0, 0.15]
        success_rate = 0.95
        duration = 10
        total_requests = 5

        insights = test_engine._generate_performance_insights(
            response_times, success_rate, duration, total_requests
        )

        assert "overall_assessment" in insights
        assert "strengths" in insights
        assert "concerns" in insights
        assert "recommendations" in insights

        # Verify assessment logic
        assert insights["overall_assessment"] in ["Excellent", "Good", "Acceptable", "Poor"]

        # Should identify high success rate as strength
        assert any("success rate" in s.lower() for s in insights["strengths"])

        # Should identify performance issues somewhere in the analysis
        all_messages = []
        for key in ["strengths", "concerns", "recommendations"]:
            all_messages.extend(insights.get(key, []))

        # Look for any performance-related terms
        performance_terms = [
            "slow",
            "fast",
            "response time",
            "latency",
            "throughput",
            "performance",
            "delay",
        ]
        assert any(
            any(term in msg.lower() for term in performance_terms) for msg in all_messages
        ), "No performance-related terms found in insights"

    def test_analyze_target_performance(self, test_engine):
        """Test target performance analysis"""
        results = [
            {"method": "GET", "url": "/api/v1/users", "response_time": 0.1, "success": True},
            {
                "method": "POST",
                "url": "/api/v1/users",
                "response_time": 0.3,
                "success": False,
                "error": "Validation Error",
            },
        ]

        target_stats = test_engine._analyze_target_performance(results)

        # Verify GET endpoint stats
        get_stats = target_stats["GET /api/v1/users"]
        assert get_stats["total_requests"] == 1
        assert get_stats["successful_requests"] == 1
        assert get_stats["failed_requests"] == 0
        assert get_stats["avg_response_time"] == 0.1

        # Verify POST endpoint stats
        post_stats = target_stats["POST /api/v1/users"]
        assert post_stats["total_requests"] == 1
        assert post_stats["successful_requests"] == 0
        assert post_stats["failed_requests"] == 1
        assert post_stats["avg_response_time"] == 0.3
        assert "Validation Error" in post_stats["errors"]

    def test_analyze_user_performance(self, test_engine):
        """Test user performance analysis"""
        results = [
            {"user_id": 1, "response_time": 0.1, "success": True},
            {"user_id": 1, "response_time": 0.2, "success": True},
            {"user_id": 2, "response_time": 0.5, "success": False, "error": "Timeout"},
        ]

        user_stats = test_engine._analyze_user_performance(results)

        # Verify user 1 stats
        assert 1 in user_stats  # User IDs are integers
        user1_stats = user_stats[1]
        assert user1_stats["total_requests"] == 2
        assert user1_stats["successful_requests"] == 2
        assert user1_stats["failed_requests"] == 0
        assert pytest.approx(user1_stats["avg_response_time"], 0.001) == 0.15

        # Verify user 2 stats
        assert 2 in user_stats
        user2_stats = user_stats[2]
        assert user2_stats["total_requests"] == 1
        assert user2_stats["successful_requests"] == 0
        assert user2_stats["failed_requests"] == 1
        assert pytest.approx(user2_stats["avg_response_time"], 0.001) == 0.5
        assert "Timeout" in user2_stats["errors"]

    def test_analyze_time_series(self, test_engine):
        """Test time series analysis"""
        results = [
            {"timestamp": 1000, "response_time": 0.1, "success": True},
            {"timestamp": 1030, "response_time": 0.2, "success": True},
            {"timestamp": 1090, "response_time": 0.3, "success": False},
        ]

        time_series = test_engine._analyze_time_series(results)

        assert "time_buckets" in time_series
        assert "trend_analysis" in time_series

        # Verify time buckets
        buckets = time_series["time_buckets"]
        assert len(buckets) > 0
        assert all(isinstance(b["timestamp"], int) for b in buckets)
        assert all(isinstance(b["requests"], int) for b in buckets)
        assert all(isinstance(b["success_rate"], float) for b in buckets)
        assert all(isinstance(b["avg_response_time"], float) for b in buckets)

        # Verify trend analysis
        trends = time_series["trend_analysis"]
        assert "response_time_trend" in trends
        assert "success_rate_trend" in trends
        assert "performance_degradation" in trends
        assert "stability_score" in trends


class TestHTTPTestExecution:
    """Test HTTP test execution"""

    @pytest.fixture
    def test_engine(self):
        """Create a LoadTestEngine instance"""
        config_manager = Mock(spec=ConfigManager)
        return LoadTestEngine(config_manager)

    def test_http_test_validation_missing_url(self, test_engine):
        """Test HTTP test validation with missing URL"""
        target = {"method": "GET"}
        load_profile = {"users": 10, "duration": 60, "think_time": 1}

        with pytest.raises(ValueError, match="HTTP target must have a URL"):
            asyncio.run(test_engine.execute_http_test(target, load_profile))

    @pytest.mark.asyncio
    async def test_http_test_execution_success(self, test_engine):
        """Test successful HTTP test execution"""
        target = {
            "url": "http://httpbin.org/get",
            "method": "GET",
            "headers": {"User-Agent": "NLM-Test"},
            "expected_status": 200,
        }
        load_profile = {"users": 2, "threads": 2, "duration": 5, "think_time": 1, "ramp_up": 2}

        test_engine.running = True
        results = await test_engine.execute_http_test(target, load_profile)

        assert len(results) > 0
        assert all("timestamp" in result for result in results)
        assert all("response_time" in result for result in results)
        assert all("success" in result for result in results)

    @pytest.mark.asyncio
    async def test_http_test_execution_failure(self, test_engine):
        """Test HTTP test execution with invalid URL"""
        target = {
            "url": "http://invalid-domain-that-does-not-exist-12345.com",
            "method": "GET",
            "expected_status": 200,
        }
        load_profile = {"users": 1, "threads": 1, "duration": 2, "think_time": 1, "ramp_up": 1}

        test_engine.running = True
        results = await test_engine.execute_http_test(target, load_profile)

        assert len(results) > 0
        # Should have some failed requests
        failed_requests = [r for r in results if not r["success"]]
        assert len(failed_requests) > 0


class TestDatabaseTestExecution:
    """Test database test execution"""

    @pytest.fixture
    def test_engine(self):
        """Create a LoadTestEngine instance"""
        config_manager = Mock(spec=ConfigManager)
        return LoadTestEngine(config_manager)

    def test_database_test_validation_missing_type(self, test_engine):
        """Test database test validation with missing db_type"""
        target = {"host": "localhost"}
        load_profile = {"users": 10, "duration": 60, "think_time": 1}

        with pytest.raises(ValueError, match="Database target must have a db_type"):
            asyncio.run(test_engine.execute_database_test(target, load_profile))

    def test_database_test_validation_missing_host(self, test_engine):
        """Test database test validation with missing host"""
        target = {"db_type": "postgresql"}
        load_profile = {"users": 10, "duration": 60, "think_time": 1}

        with pytest.raises(ValueError, match="Database target must have a host"):
            asyncio.run(test_engine.execute_database_test(target, load_profile))

    @pytest.mark.asyncio
    async def test_database_test_execution(self, test_engine):
        """Test database test execution"""
        target = {
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "query": "SELECT COUNT(*) FROM users",
        }
        load_profile = {"users": 2, "threads": 2, "duration": 5, "think_time": 1, "ramp_up": 2}

        test_engine.running = True
        results = await test_engine.execute_database_test(target, load_profile)

        assert len(results) > 0
        assert all("timestamp" in result for result in results)
        assert all("response_time" in result for result in results)
        assert all("success" in result for result in results)
        assert all("db_type" in result for result in results)
        assert all("host" in result for result in results)
        assert all("query" in result for result in results)


class TestMessageQueueTestExecution:
    """Test message queue test execution"""

    @pytest.fixture
    def test_engine(self):
        """Create a LoadTestEngine instance"""
        config_manager = Mock(spec=ConfigManager)
        return LoadTestEngine(config_manager)

    def test_mq_test_validation_missing_type(self, test_engine):
        """Test MQ test validation with missing mq_type"""
        target = {"host": "localhost"}
        load_profile = {"users": 10, "duration": 60, "think_time": 1}

        with pytest.raises(ValueError, match="Message queue target must have a mq_type"):
            asyncio.run(test_engine.execute_message_queue_test(target, load_profile))

    def test_mq_test_validation_missing_host(self, test_engine):
        """Test MQ test validation with missing host"""
        target = {"mq_type": "rabbitmq"}
        load_profile = {"users": 10, "duration": 60, "think_time": 1}

        with pytest.raises(ValueError, match="Message queue target must have a host"):
            asyncio.run(test_engine.execute_message_queue_test(target, load_profile))

    @pytest.mark.asyncio
    async def test_mq_test_execution(self, test_engine):
        """Test message queue test execution"""
        target = {"mq_type": "rabbitmq", "host": "localhost", "port": 5672, "queue": "test_queue"}
        load_profile = {"users": 2, "threads": 2, "duration": 5, "think_time": 1, "ramp_up": 2}

        test_engine.running = True
        results = await test_engine.execute_message_queue_test(target, load_profile)

        assert len(results) > 0
        assert all("timestamp" in result for result in results)
        assert all("response_time" in result for result in results)
        assert all("success" in result for result in results)
        assert all("mq_type" in result for result in results)
        assert all("host" in result for result in results)
        assert all("queue" in result for result in results)
        assert all("operation" in result for result in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
