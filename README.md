# NLM (Neural Load Manager) Performance Testing Tool

A comprehensive Python-based load testing tool with AI-powered analysis, designed for enterprise environments with integration to AWS, Datadog, and Splunk.

## Features

- **Multi-Protocol Testing**: HTTP APIs, databases (SQL/NoSQL), and message queues
- **Enterprise Integration**: AWS CloudWatch, Datadog, and Splunk metrics collection
- **Dual Interface**: PyQt6 GUI and CLI for flexible usage
- **Real-time Visualization**: Streamlit dashboards with interactive charts
- **AI Analysis**: LLM-powered test result interpretation
- **Multi-Environment Support**: Dev, QA, Stage, and Production environments
- **Secure Authentication**: IAM roles, credentials, and AWS profiles
- **Export Capabilities**: CSV export for offline analysis

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
python tests/run_tests.py --suite core
python tests/run_tests.py --suite utils
python tests/run_tests.py --suite ai
python tests/run_tests.py --suite cli

# Run integration tests
python tests/run_tests.py --integration

# Check dependencies
python tests/run_tests.py --deps
```

### Test Structure

```
tests/
├── test_basic_functionality.py    # Basic functionality tests
├── test_test_engine.py           # Core test engine tests
├── test_test_runner.py           # Test runner tests
├── test_config.py                # Configuration management tests
├── test_ai_analysis.py           # AI analysis engine tests
├── test_cli.py                   # CLI interface tests
└── run_tests.py                  # Test runner script
```

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Async Tests**: Test asynchronous functionality
- **Mock Tests**: Test with mocked external dependencies

### Installing Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Test Configuration

The project uses `pytest.ini` for test configuration:

- Test discovery: `tests/` directory
- Test file pattern: `test_*.py`
- Test class pattern: `Test*`
- Test function pattern: `test_*`
- Markers for categorizing tests
- Warning filters for clean output

### Coverage Reporting

Generate coverage reports:

```bash
# Terminal coverage report
pytest --cov=src --cov-report=term tests/

# HTML coverage report
pytest --cov=src --cov-report=html tests/

# XML coverage report (for CI/CD)
pytest --cov=src --cov-report=xml tests/
```

### Continuous Integration

The test suite is designed to run in CI/CD pipelines:

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run tests with coverage
pytest --cov=src --cov-report=xml --cov-report=term tests/

# Run linting
flake8 src/
black --check src/
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 