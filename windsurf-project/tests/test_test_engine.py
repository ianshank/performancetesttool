"""
Unit tests for TestEngine class
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.test_engine import TestEngine
from src.utils.config import ConfigManager


class TestTestEngine:
    """Test the core TestEngine class"""
    
    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager"""
        return Mock(spec=ConfigManager)
    
    @pytest.fixture
    def test_engine(self, config_manager):
        """Create a TestEngine instance"""
        return TestEngine(config_manager)
    
    def test_initialization(self, test_engine):
        """Test TestEngine initialization"""
        assert test_engine is not None
        assert test_engine.running == False
        assert test_engine.results == []
        assert test_engine.logger is not None
    
    def test_get_default_port(self, test_engine):
        """Test default port retrieval for different database types"""
        assert test_engine._get_default_port('postgresql') == 5432
        assert test_engine._get_default_port('mysql') == 3306
        assert test_engine._get_default_port('mongodb') == 27017
        assert test_engine._get_default_port('sqlite') == 0
        assert test_engine._get_default_port('redis') == 6379
        assert test_engine._get_default_port('elasticsearch') == 9200
        assert test_engine._get_default_port('unknown') == 5432  # Default
    
    def test_get_mq_default_port(self, test_engine):
        """Test default port retrieval for different message queue types"""
        assert test_engine._get_mq_default_port('rabbitmq') == 5672
        assert test_engine._get_mq_default_port('kafka') == 9092
        assert test_engine._get_mq_default_port('redis') == 6379
        assert test_engine._get_mq_default_port('activemq') == 61616
        assert test_engine._get_mq_default_port('sqs') == 0
        assert test_engine._get_mq_default_port('pubsub') == 0
        assert test_engine._get_mq_default_port('unknown') == 5672  # Default
    
    def test_simulate_database_query(self, test_engine):
        """Test database query simulation"""
        # Test different database types
        postgresql_time = test_engine._simulate_database_query('postgresql', 'SELECT 1')
        mysql_time = test_engine._simulate_database_query('mysql', 'SELECT 1')
        mongodb_time = test_engine._simulate_database_query('mongodb', 'SELECT 1')
        
        assert 0 < postgresql_time < 0.1
        assert 0 < mysql_time < 0.1
        assert 0 < mongodb_time < 0.1
        
        # Test query complexity
        simple_query = test_engine._simulate_database_query('postgresql', 'SELECT 1')
        complex_query = test_engine._simulate_database_query('postgresql', 'SELECT COUNT(*) FROM users JOIN orders')
        write_query = test_engine._simulate_database_query('postgresql', 'INSERT INTO users VALUES (1, "test")')
        
        assert complex_query > simple_query  # Join queries should take longer
        assert write_query > simple_query    # Write operations should take longer
    
    def test_simulate_mq_operation(self, test_engine):
        """Test message queue operation simulation"""
        # Test different MQ types
        rabbitmq_time = test_engine._simulate_mq_operation('rabbitmq')
        kafka_time = test_engine._simulate_mq_operation('kafka')
        redis_time = test_engine._simulate_mq_operation('redis')
        
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
            {"timestamp": 1003, "response_time": 0.05, "success": True}
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


class TestHTTPTestExecution:
    """Test HTTP test execution"""
    
    @pytest.fixture
    def test_engine(self):
        """Create a TestEngine instance"""
        config_manager = Mock(spec=ConfigManager)
        return TestEngine(config_manager)
    
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
            "expected_status": 200
        }
        load_profile = {
            "users": 2,
            "threads": 2,
            "duration": 5,
            "think_time": 1,
            "ramp_up": 2
        }
        
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
            "expected_status": 200
        }
        load_profile = {
            "users": 1,
            "threads": 1,
            "duration": 2,
            "think_time": 1,
            "ramp_up": 1
        }
        
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
        """Create a TestEngine instance"""
        config_manager = Mock(spec=ConfigManager)
        return TestEngine(config_manager)
    
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
            "query": "SELECT COUNT(*) FROM users"
        }
        load_profile = {
            "users": 2,
            "threads": 2,
            "duration": 5,
            "think_time": 1,
            "ramp_up": 2
        }
        
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
        """Create a TestEngine instance"""
        config_manager = Mock(spec=ConfigManager)
        return TestEngine(config_manager)
    
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
        target = {
            "mq_type": "rabbitmq",
            "host": "localhost",
            "port": 5672,
            "queue": "test_queue"
        }
        load_profile = {
            "users": 2,
            "threads": 2,
            "duration": 5,
            "think_time": 1,
            "ramp_up": 2
        }
        
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