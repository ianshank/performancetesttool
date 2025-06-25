# NLM (Neural Load Manager) Performance Testing Tool

A comprehensive Python-based load testing tool with AI-powered analysis and enterprise-grade regression testing capabilities, designed for production environments with seamless deployment workflows.

## 🚀 Features

### Core Testing
- **Multi-Protocol Testing**: HTTP APIs, databases (SQL/NoSQL), and message queues
- **Enterprise Integration**: AWS CloudWatch, Datadog, and Splunk metrics collection
- **Dual Interface**: PyQt6 GUI and CLI for flexible usage
- **Real-time Visualization**: Streamlit dashboards with interactive charts
- **AI Analysis**: LLM-powered test result interpretation with enhanced insights

### 🧪 Regression Testing System
- **Pre-deployment Validation**: Comprehensive regression test suite for stage environment
- **Multi-Environment Support**: Dev, QA, Stage, and Production environment testing
- **Deployment Gating**: Automatic deployment blocking on critical test failures
- **Performance Benchmarks**: SLA validation with configurable thresholds
- **Detailed Reporting**: JSON reports with deployment recommendations

### 🔧 DevOps & CI/CD
- **GitHub Actions Integration**: Automated regression testing on PRs and deployments
- **Makefile Automation**: One-command deployment preparation and testing
- **Code Quality**: Automated formatting with black and isort
- **Linting**: flake8 and mypy static analysis

### 📊 Enhanced Analytics
- **Detailed Performance Insights**: Comprehensive bottleneck detection
- **User and Target Breakdown**: Per-endpoint and per-user analysis
- **Time Series Analysis**: Trend detection and performance degradation alerts
- **Percentile-based Metrics**: P50, P95, P99 response time analysis
- **Response Time Distribution**: Categorized performance buckets
- **Error Pattern Recognition**: Automated failure analysis

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd windsurf-project
```

2. Set up development environment:
```bash
make setup  # Automated setup with virtual environment
```

Or manually:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
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

#### Regression Testing
```bash
# Quick regression tests (< 30 seconds)
make regression-quick

# Full regression tests for stage environment
make regression-stage

# Complete deployment preparation
make deploy-prep
```

## 🧪 Regression Testing

### Overview
The regression testing system provides comprehensive pre-deployment validation with five test suites:

1. **Critical Functionality** (REQUIRED): Core system operations
2. **Configuration Regression** (REQUIRED): Environment and credential validation
3. **Integration Regression** (REQUIRED): End-to-end workflows
4. **Performance Regression** (OPTIONAL): Benchmark validation
5. **Stress Regression** (OPTIONAL): Concurrent operations and large datasets

### Running Regression Tests

```bash
# Run for specific environment
python scripts/run_regression_tests.py --env stage --verbose

# Quick mode (critical tests only, <30s)
python scripts/run_regression_tests.py --env stage --quick

# Full test suite with all optional tests
python scripts/run_regression_tests.py --env stage

# Development shortcuts
make regression-dev     # Dev environment
make regression-qa      # QA environment  
make regression-stage   # Stage environment (recommended for pre-prod)
```

### Test Results and Deployment Gating

```bash
============================================================
REGRESSION TEST SUMMARY
============================================================
Environment: stage
Timestamp: 2025-06-25T15:21:19.503935
Quick Mode: False
Duration: 14.73s

TEST SUITES:
  critical        PASS ( 12.59s)
  configuration   PASS (  0.50s)
  integration     PASS (  0.64s)
  performance     PASS (  0.50s)
  stress          PASS (  0.50s)

SUCCESS RATE: 100.0%
DEPLOYMENT: APPROVED

RECOMMENDATIONS:
  • APPROVE DEPLOYMENT: All tests passed
============================================================
```

**Deployment Decision Logic:**
- ✅ **APPROVED**: All required tests (critical, configuration, integration) pass
- ❌ **BLOCKED**: Any required test fails
- ⚠️ **WARNING**: Optional tests fail (review recommended but deployment allowed)

### CI/CD Integration

The project includes GitHub Actions workflow for automated testing:

```yaml
# Automatic execution on:
# - Push to main branch
# - Pull requests
# - Manual workflow dispatch

# Features:
# - Multi-environment testing
# - PR comment with results
# - Deployment gating
# - Artifact collection
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

# Environment
NLM_ENV=dev  # dev, qa, stage, prod
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
├── core/           # Core testing engine and runners
├── gui/            # PyQt6 GUI components
├── cli/            # Command-line interface
├── dashboard/      # Streamlit visualization
├── integrations/   # AWS, Datadog, Splunk connectors
├── ai/             # LLM analysis module
├── exporters/      # Data export utilities
└── utils/          # Common utilities and configuration

tests/
├── test_regression.py  # Regression test suite
├── test_*.py          # Unit and integration tests
└── run_tests.py       # Test runner

scripts/
├── run_regression_tests.py  # Regression test runner
└── ...

.github/workflows/
└── regression-tests.yml     # CI/CD automation

docs/
└── regression-testing.md    # Comprehensive testing guide
```

## 📊 Test Results Analysis

### Performance Metrics

The tool provides comprehensive performance analysis:

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

## 🧪 Testing

### Development Testing

```bash
# Run all unit tests (91 tests)
make test

# Run with verbose output
make test-verbose

# Run with coverage report
make test-coverage

# Run specific test categories
pytest tests/test_test_engine.py     # Core engine tests
pytest tests/test_ai_analysis.py     # AI analysis tests
pytest tests/test_cli.py             # CLI interface tests
pytest tests/test_integration.py     # Integration tests
```

### Regression Testing

```bash
# Quick regression tests (< 30 seconds)
make regression-quick

# Environment-specific regression tests
make regression-dev      # Development environment
make regression-qa       # QA environment
make regression-stage    # Stage environment (pre-production)

# Full regression suite with stress tests
python scripts/run_regression_tests.py --env stage
```

### Code Quality

```bash
# Format code
make format

# Check formatting
make check-format

# Run linting
make lint

# Type checking
make typecheck

# Complete quality check
make quality
```

### Deployment Preparation

```bash
# Complete pre-deployment validation
make deploy-prep

# This runs:
# 1. Code formatting checks
# 2. Linting validation
# 3. Type checking
# 4. Unit tests
# 5. Full regression tests
# 6. Security checks
```

### Test Categories

- **Unit Tests** (91 tests): Test individual components in isolation
- **Integration Tests**: Test component interactions and end-to-end workflows
- **Regression Tests**: Pre-deployment validation with deployment gating
- **Performance Tests**: Benchmark validation and SLA compliance
- **Stress Tests**: Concurrent operations and large dataset handling
- **Configuration Tests**: Environment and credential validation
- **AI Analysis Tests**: LLM integration and analysis functionality

### Test Coverage

The comprehensive test suite includes:

- **Core Engine Tests**: Enhanced results, performance insights, user/target analysis
- **AI Analysis Tests**: Raw data analysis, bottleneck detection, error patterns
- **CLI Tests**: Command-line interface, argument parsing, configuration
- **Integration Tests**: End-to-end workflows, dashboard integration
- **Regression Tests**: Critical functionality, configuration, integration validation
- **Functional Tests**: GUI functionality, export capabilities, real-time features

## 🚀 Development Workflow

### Pre-commit Workflow
```bash
# Before committing
make quality        # Run all quality checks
make test          # Run unit tests
make regression-dev # Quick regression validation
```

### Pre-deployment Workflow
```bash
# Before deploying to production
make deploy-prep   # Complete deployment preparation
                   # - Includes all tests, formatting, linting
                   # - Runs stage environment regression tests
                   # - Generates deployment report
```

### CI/CD Pipeline
The project includes automated GitHub Actions that:
- Run regression tests on every PR
- Validate code quality and formatting
- Generate test reports and deployment recommendations
- Block deployments if critical tests fail

## 📚 Documentation

- **[Regression Testing Guide](docs/regression-testing.md)**: Comprehensive guide to regression testing
- **[Quick Reference](README-regression-tests.md)**: Quick start guide for regression tests
- **[Makefile Commands](Makefile)**: All available automation commands

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (unit and regression as appropriate)
5. Run quality checks: `make quality`
6. Submit a pull request

### Development Setup
```bash
# One-command setup
make setup

# Install development dependencies
pip install black flake8 mypy isort pytest-json-report

# Run pre-commit validation
make pre-commit
```

## License

MIT License - see LICENSE file for details. 