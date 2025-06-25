# Regression Testing System

## Overview

The regression testing system ensures that critical functionality works correctly before production deployment. It runs comprehensive tests in the stage environment and blocks deployment if any critical tests fail.

## Architecture

### Test Suites

1. **Critical Functionality** (`TestCriticalFunctionality`)
   - Core system initialization
   - Basic operations that must work
   - Configuration management
   - **Required for deployment**

2. **Configuration Regression** (`TestConfigurationRegression`) 
   - Environment configuration validation
   - Credential validation
   - Configuration file access
   - **Required for deployment**

3. **Integration Regression** (`TestIntegrationRegression`)
   - End-to-end workflows
   - AI analysis integration
   - Export functionality
   - **Required for deployment**

4. **Performance Regression** (`TestPerformanceRegression`)
   - Simulation performance benchmarks
   - Results processing performance
   - Optional but recommended

5. **Stress Regression** (`TestStressRegression`)
   - Concurrent operations
   - Large result set handling
   - Optional, helps with capacity planning

### Deployment Gating

- **REQUIRED tests must pass** for deployment approval
- **OPTIONAL tests** generate warnings but don't block deployment
- Tests run automatically on main branch pushes/PRs
- Manual execution available for ad-hoc validation

## Usage

### Command Line

```bash
# Run all regression tests in stage environment
python scripts/run_regression_tests.py

# Quick test subset (skip slow tests)
python scripts/run_regression_tests.py --quick

# Test against specific environment
python scripts/run_regression_tests.py --env prod

# Custom report location
python scripts/run_regression_tests.py --report-file custom_report.json
```

### Makefile Targets

```bash
# Quick regression tests
make regression-quick

# Full stage environment tests
make regression-stage

# Production environment (with confirmation)
make regression-prod

# Development environment
make regression-dev

# Complete deployment preparation
make deploy-prep
```

### GitHub Actions

The regression testing workflow automatically runs on:

- **Push to main branch** - Full regression tests
- **Pull requests to main** - Full regression tests with PR comments
- **Manual trigger** - Configurable environment and quick mode

#### Manual Workflow Trigger

1. Go to GitHub Actions tab
2. Select "Regression Tests" workflow
3. Click "Run workflow"
4. Choose environment (`stage` or `prod`)
5. Optionally enable quick mode

## Test Categories

### Critical Tests

These tests **MUST PASS** or deployment will be blocked:

- ✅ Configuration manager initialization
- ✅ Test engine basic operations
- ✅ Test runner configuration handling
- ✅ HTTP test execution
- ✅ CLI argument parsing
- ✅ Results summary generation
- ✅ CSV export functionality

### Performance Benchmarks

Performance tests validate that the system meets baseline requirements:

- **Simulation Performance**: 100 operations in < 1 second
- **Result Processing**: 1000 results processed in < 5 seconds
- **Concurrent Operations**: 5 threads × 10 operations without errors

### Integration Validation

Integration tests ensure critical workflows function end-to-end:

- Complete test execution workflow
- AI analysis integration availability
- Export system integration
- Environment configuration access

## Reports

### Report Structure

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "environment": "stage",
  "quick_mode": false,
  "summary": {
    "total_suites": 5,
    "passed_suites": 5,
    "failed_suites": 0,
    "success_rate": 1.0,
    "total_duration": 45.2,
    "deployment_approved": true
  },
  "suites": { /* individual test results */ },
  "recommendations": [
    "APPROVE DEPLOYMENT: All tests passed"
  ]
}
```

### Report Locations

- **Local**: `reports/regression_report_TIMESTAMP.json`
- **CI**: Uploaded as GitHub Actions artifacts
- **Console**: Human-readable summary printed

## Integration with CI/CD

### Deployment Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Code      │───▶│  Regression  │───▶│ Production  │
│   Changes   │    │   Tests      │    │ Deployment  │
└─────────────┘    └──────────────┘    └─────────────┘
                          │
                   ┌──────▼──────┐
                   │  BLOCK if   │
                   │ tests fail  │
                   └─────────────┘
```

### Exit Codes

- **0**: All tests passed - deployment approved
- **1**: Tests failed - deployment blocked  
- **2**: Environment setup failed

### PR Integration

Regression test results are automatically posted as PR comments:

```markdown
## 🧪 Regression Test Results

**Environment:** stage
**Status:** ✅ APPROVED
**Success Rate:** 100.0%
**Duration:** 45.2s

### Test Suites

- ✅ **critical** (12.3s)
- ✅ **configuration** (8.1s)
- ✅ **integration** (15.2s)
- ✅ **performance** (6.4s)
- ✅ **stress** (3.2s)

### Recommendations

- APPROVE DEPLOYMENT: All tests passed
```

## Configuration

### Environment Variables

- `NLM_ENVIRONMENT`: Target environment (`dev`, `qa`, `stage`, `prod`)
- `PYTHONPATH`: Path to source code

### Test Configuration

Tests use the same configuration system as the main application:

```yaml
# config/environments.yml
stage:
  aws_region: us-west-2
  log_level: INFO
  # ... other stage-specific settings

prod:
  aws_region: us-east-1  
  log_level: WARNING
  # ... production settings
```

## Troubleshooting

### Common Issues

#### Environment Setup Failed

```bash
ERROR: Environment setup failed
```

**Solutions:**
- Verify environment configuration exists
- Check PYTHONPATH is set correctly
- Ensure required directories can be created

#### Test Timeouts

```bash
Tests timed out after 10 minutes
```

**Solutions:**
- Check external service availability
- Verify network connectivity
- Consider using `--quick` mode for faster execution

#### Performance Benchmarks Failed

```bash
WARNING: Performance benchmarks not met
```

**Solutions:**
- Review system resources
- Check for competing processes
- Analyze performance trends over time

### Debug Mode

Enable verbose logging for detailed output:

```bash
python scripts/run_regression_tests.py --verbose
```

### Test-Specific Debugging

Run individual test suites:

```bash
# Run only critical tests
pytest tests/test_regression.py::TestCriticalFunctionality -v

# Run with debugging
pytest tests/test_regression.py::TestCriticalFunctionality -v -s --pdb
```

## Maintenance

### Adding New Tests

1. Add test methods to appropriate test class in `tests/test_regression.py`
2. Mark slow tests with `@pytest.mark.slow`
3. Update documentation if adding new test categories

### Updating Performance Benchmarks

1. Review current performance baselines
2. Update benchmark values in test assertions
3. Document changes in performance expectations

### Environment-Specific Configuration

1. Update environment configurations in `config/environments.yml`
2. Test configuration changes across all environments
3. Verify regression tests pass with new configurations

## Best Practices

### Test Design

- **Fast by default**: Keep tests quick unless marked `@pytest.mark.slow`
- **Independent**: Tests should not depend on each other
- **Deterministic**: Avoid flaky tests that pass/fail randomly
- **Representative**: Tests should reflect real usage patterns

### Performance Testing

- **Reasonable baselines**: Set achievable but meaningful performance targets
- **Environment aware**: Consider that CI environments may be slower
- **Trend analysis**: Monitor performance over time, not just absolute values

### Deployment Process

- **Stage first**: Always test in stage before production
- **Quick feedback**: Use quick mode for rapid iteration
- **Full validation**: Run complete suite before major releases
- **Rollback plan**: Have regression tests ready for rollback validation

## Security Considerations

### Credential Management

- Never commit real credentials to tests
- Use environment-specific test credentials
- Rotate test credentials regularly

### Environment Isolation

- Stage tests should not affect production data
- Use isolated test databases/services when possible
- Monitor test impact on shared resources

### Access Control

- Limit who can run production regression tests
- Require approval for production test execution
- Log all regression test executions

## Monitoring and Alerting

### Success Metrics

- **Pass Rate**: Target 100% for required tests
- **Execution Time**: Monitor for performance degradation
- **Deployment Frequency**: Track blocked vs. approved deployments

### Alerting

- Alert on regression test failures
- Monitor execution time trends
- Alert on infrastructure issues affecting tests

### Dashboard

Consider creating a regression test dashboard showing:

- Recent test execution history
- Pass/fail trends over time
- Performance benchmark trends
- Environment-specific results 