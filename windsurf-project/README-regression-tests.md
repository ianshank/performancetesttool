# 🧪 Regression Testing System

**Automated testing to ensure production deployment safety**

## Quick Start

```bash
# Run all regression tests (stage environment)
make regression-stage

# Quick test subset (faster)
make regression-quick

# Full deployment preparation
make deploy-prep
```

## 🚦 Deployment Gating

- **✅ REQUIRED tests must pass** → Deployment approved
- **❌ Required test failure** → Deployment blocked  
- **⚠️ Optional test failure** → Warning only

## 📋 Test Suites

| Suite | Type | Description | Blocks Deployment |
|-------|------|-------------|-------------------|
| **Critical** | Required | Core functionality, config, basic ops | ✅ Yes |
| **Configuration** | Required | Environment validation, credentials | ✅ Yes |
| **Integration** | Required | End-to-end workflows, exports | ✅ Yes |
| **Performance** | Optional | Benchmarks and performance | ⚠️ Warning |
| **Stress** | Optional | Concurrent ops, large datasets | ⚠️ Warning |

## 🚀 CI/CD Integration

### Automatic Triggers
- **Push to main** → Full regression tests
- **Pull requests** → Tests + PR comment with results
- **Manual** → Choose environment and mode

### GitHub Actions
1. Go to "Actions" tab
2. Select "Regression Tests"  
3. Click "Run workflow"
4. Configure environment and options

## 📊 Commands

```bash
# Makefile commands
make regression-stage     # Full stage tests
make regression-quick     # Quick subset
make regression-prod      # Production (with confirmation)
make deploy-prep         # Complete pre-deployment validation

# Direct script usage
python scripts/run_regression_tests.py --env stage
python scripts/run_regression_tests.py --quick
python scripts/run_regression_tests.py --env prod --verbose
```

## 📈 Exit Codes

- **0** = All tests passed → ✅ Deploy
- **1** = Tests failed → ❌ Block deployment
- **2** = Setup failed → 🔧 Fix environment

## 📄 Reports

- **Location**: `reports/regression_report_TIMESTAMP.json`
- **CI Artifacts**: Available for 30 days
- **PR Comments**: Automatic summary posted

## 🔧 Environment Setup

Required environment variables:
- `NLM_ENVIRONMENT` = `dev|qa|stage|prod`
- `PYTHONPATH` = Path to source code

## ⚡ Quick Reference

| Need | Command |
|------|---------|
| Fast validation | `make regression-quick` |
| Stage validation | `make regression-stage` |
| Full deploy prep | `make deploy-prep` |
| Production test | `make regression-prod` |
| Debug failing test | `pytest tests/test_regression.py::TestName -v -s` |

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Environment setup failed | Check config files, PYTHONPATH |
| Tests timeout | Check network, use `--quick` |
| Performance failed | Review system resources |
| Import errors | Verify PYTHONPATH and dependencies |

## 📚 Documentation

- **Full docs**: [`docs/regression-testing.md`](docs/regression-testing.md)
- **Test code**: [`tests/test_regression.py`](tests/test_regression.py)
- **Runner script**: [`scripts/run_regression_tests.py`](scripts/run_regression_tests.py)

---

**🎯 Goal**: Zero production issues through comprehensive pre-deployment validation 