# NLM (Neural Load Manager) Performance Testing Tool

A comprehensive Python-based load testing tool with AI-powered analysis, designed for enterprise environments with integration to AWS, Datadog, and Splunk.

## Features

- **Multi-Protocol Testing**: HTTP APIs, databases (SQL/NoSQL), and message queues
- **Enterprise Integration**: AWS CloudWatch, Datadog, and Splunk metrics collection
- **Dual Interface**: PyQt6 GUI and CLI for flexible usage
- **Real-time Visualization**: Streamlit dashboards with interactive charts
- **AI Analysis**: LLM-powered test result interpretation with enhanced insights
- **Multi-Environment Support**: Dev, QA, Stage, and Production environments
- **Secure Authentication**: IAM roles, credentials, and AWS profiles
- **Export Capabilities**: CSV export for offline analysis
- **Enhanced Analytics**: 
  - Detailed performance insights
  - User and target breakdown analysis
  - Time series analysis with trend detection
  - Percentile-based performance metrics
  - Response time distribution analysis
  - Error pattern recognition

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd windsurf-project
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Usage

#### GUI Mode
```bash
python src/main.py --gui
```

#### CLI Mode
```bash
python src/main.py --cli --config test_config.yaml
```

#### Streamlit Dashboard
```bash
streamlit run src/dashboard/streamlit_app.py
```

## Configuration

### Environment Setup

Create a `.env` file with your credentials:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-west-2

# Datadog Configuration
DATADOG_API_KEY=your_datadog_api_key
DATADOG_APP_KEY=your_datadog_app_key

# Splunk Configuration
SPLUNK_HOST=your_splunk_host
SPLUNK_USERNAME=your_username
SPLUNK_PASSWORD=your_password

# AI/LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### Test Configuration

Example test configuration in YAML:

```yaml
test_name: "API Load Test"
environment: "production"
targets:
  - type: "http"
    url: "https://api.example.com/health"
    method: "GET"
    headers:
      Authorization: "Bearer token"
    expected_status: 200

load_profile:
  users: 100
  ramp_up: 60
  duration: 300
  think_time: 1

monitoring:
  - provider: "aws"
    metrics: ["CPUUtilization", "RequestCount"]
  - provider: "datadog"
    metrics: ["custom.metric"]
  - provider: "splunk"
    query: "index=main sourcetype=api"
```

## Architecture

```
src/
├── core/           # Core testing engine
├── gui/            # PyQt6 GUI components
├── cli/            # Command-line interface
├── dashboard/      # Streamlit visualization
├── integrations/   # AWS, Datadog, Splunk connectors
├── ai/             # LLM analysis module
├── exporters/      # Data export utilities
└── utils/          # Common utilities
```

## Test Results Analysis

### Performance Metrics

The tool now provides comprehensive performance analysis:

```python
{
    "total_requests": 1000,
    "successful_requests": 950,
    "failed_requests": 50,
    "success_rate": 0.95,
    "avg_response_time": 0.234,
    "percentiles": {
        "p50": 0.2,
        "p95": 0.5,
        "p99": 0.8
    },
    "response_time_distribution": {
        "very_fast": 200,    # < 100ms
        "fast": 500,         # 100-500ms
        "moderate": 200,     # 500ms-1s
        "slow": 80,          # 1-3s
        "very_slow": 20      # > 3s
    }
}
```

### User Analysis

Track performance by user:

```python
{
    "user_1": {
        "total_requests": 100,
        "successful_requests": 95,
        "failed_requests": 5,
        "avg_response_time": 0.2,
        "errors": ["Timeout", "Server Error"]
    }
}
```

### Target Analysis

Monitor performance by endpoint:

```python
{
    "GET /api/v1/users": {
        "total_requests": 500,
        "successful_requests": 480,
        "failed_requests": 20,
        "avg_response_time": 0.15,
        "error_patterns": {
            "Timeout": 15,
            "Validation Error": 5
        }
    }
}
```

### Time Series Analysis

Track performance trends:

```python
{
    "time_buckets": [
        {
            "timestamp": "2025-01-01T10:00:00",
            "requests": 100,
            "success_rate": 0.95,
            "avg_response_time": 0.2
        }
    ],
    "trend_analysis": {
        "response_time_trend": "stable",
        "success_rate_trend": "improving",
        "performance_degradation": false,
        "stability_score": 0.95
    }
}
```

## Testing

### Running Tests

The project includes comprehensive unit tests for all components. To run the test suite:

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run with coverage report
pytest --cov=src tests/

# Run specific test suite
pytest tests/test_test_engine.py    # Test engine tests
pytest tests/test_ai_analysis.py    # AI analysis tests
pytest tests/test_functional.py     # Functional tests

# Run integration tests
python tests/run_tests.py --integration

# Check dependencies
python tests/run_tests.py --deps
```

### Test Coverage

The test suite now includes:

- **Core Engine Tests**:
  - Enhanced results summary generation
  - Performance insights analysis
  - User and target breakdown analysis
  - Time series analysis with trend detection
  - Database query simulation
  - Message queue operation simulation

- **AI Analysis Tests**:
  - Raw data analysis
  - Performance bottleneck detection
  - Error pattern recognition
  - Test run comparison
  - Trend analysis
  - Risk assessment

- **Functional Tests**:
  - End-to-end test execution
  - Dashboard integration
  - GUI functionality
  - CLI operations
  - Data export

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Async Tests**: Test asynchronous functionality
- **Mock Tests**: Test with mocked external dependencies
- **Functional Tests**: End-to-end functionality testing
- **Performance Tests**: Test timing and resource usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 