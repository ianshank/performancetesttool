# NLM Performance Testing Tool - Makefile
# Provides convenient targets for development, testing, and deployment

.PHONY: help test test-unit test-regression test-quick install clean setup-dev
.PHONY: lint format check-format type-check pre-commit
.PHONY: regression-stage regression-prod regression-quick
.PHONY: build package deploy-prep

# Default target
.DEFAULT_GOAL := help

# Python and virtual environment setup
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# Project paths
SRC_DIR := src
TESTS_DIR := tests
SCRIPTS_DIR := scripts

help: ## Show this help message
	@echo "NLM Performance Testing Tool - Available Commands"
	@echo "================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Setup and Installation
install: ## Install dependencies
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

setup-dev: $(VENV) ## Setup development environment
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov pytest-json-report pytest-html
	$(PIP) install black flake8 mypy isort
	@echo "Development environment ready!"

$(VENV):
	$(PYTHON) -m venv $(VENV)

# Testing Targets
test: test-unit ## Run all tests (alias for test-unit)

test-unit: ## Run unit tests
	$(PYTHON) -m pytest $(TESTS_DIR)/ -v --tb=short \
		--ignore=$(TESTS_DIR)/test_regression.py \
		--ignore=$(TESTS_DIR)/test_functional.py \
		--ignore=$(TESTS_DIR)/test_integration.py

test-coverage: ## Run tests with coverage report
	$(PYTHON) -m pytest $(TESTS_DIR)/ -v --tb=short \
		--cov=$(SRC_DIR) --cov-report=html --cov-report=term \
		--ignore=$(TESTS_DIR)/test_regression.py \
		--ignore=$(TESTS_DIR)/test_functional.py \
		--ignore=$(TESTS_DIR)/test_integration.py

# Regression Testing Targets
regression-stage: ## Run full regression tests in stage environment
	@echo "🧪 Running regression tests in STAGE environment..."
	$(PYTHON) $(SCRIPTS_DIR)/run_regression_tests.py --env stage --verbose

regression-prod: ## Run regression tests in production environment (careful!)
	@echo "⚠️  Running regression tests in PRODUCTION environment..."
	@read -p "Are you sure you want to run tests against PROD? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(PYTHON) $(SCRIPTS_DIR)/run_regression_tests.py --env prod --verbose; \
	else \
		echo "Cancelled."; \
	fi

regression-quick: ## Run quick regression test subset
	@echo "⚡ Running quick regression tests..."
	$(PYTHON) $(SCRIPTS_DIR)/run_regression_tests.py --env stage --quick --verbose

regression-dev: ## Run regression tests in dev environment
	@echo "🧪 Running regression tests in DEV environment..."
	$(PYTHON) $(SCRIPTS_DIR)/run_regression_tests.py --env dev --verbose

test-regression: ## Run regression tests (default: stage)
	$(PYTHON) -m pytest $(TESTS_DIR)/test_regression.py -v --tb=short

# Code Quality Targets
lint: ## Run linting checks
	@echo "🔍 Running linting checks..."
	flake8 $(SRC_DIR) $(TESTS_DIR) --max-line-length=100 --ignore=E203,W503
	@echo "✅ Linting passed!"

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR) --line-length=100
	isort $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR) --profile black
	@echo "✅ Code formatted!"

check-format: ## Check if code is properly formatted
	@echo "🔍 Checking code formatting..."
	black $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR) --line-length=100 --check
	isort $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR) --profile black --check-only
	@echo "✅ Code formatting is correct!"

type-check: ## Run type checking with mypy
	@echo "🔍 Running type checks..."
	mypy $(SRC_DIR) --ignore-missing-imports
	@echo "✅ Type checking passed!"

pre-commit: check-format lint type-check test-unit ## Run all pre-commit checks
	@echo "✅ All pre-commit checks passed!"

# Application Targets
run-cli: ## Run CLI interface
	$(PYTHON) $(SRC_DIR)/main.py --cli

run-gui: ## Run GUI interface
	$(PYTHON) $(SRC_DIR)/main.py --gui

run-dashboard: ## Run Streamlit dashboard
	streamlit run $(SRC_DIR)/dashboard/streamlit_app.py

# Deployment Preparation
deploy-prep: pre-commit regression-stage ## Prepare for deployment (run all checks)
	@echo "🚀 Deployment preparation complete!"
	@echo "✅ All tests passed"
	@echo "✅ Code quality checks passed"
	@echo "✅ Regression tests passed"
	@echo ""
	@echo "Ready for production deployment! 🎉"

build: ## Build distribution packages
	$(PYTHON) setup.py sdist bdist_wheel

package: clean build ## Create clean package
	@echo "📦 Package created in dist/"

# Cleanup Targets
clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf reports/*.json
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete!"

clean-all: clean ## Clean up everything including venv
	rm -rf $(VENV)

# Utility Targets
logs: ## View recent logs
	@echo "📋 Recent logs:"
	@find logs/ -name "*.log" -mtime -1 2>/dev/null | head -5 | xargs tail -n 20

reports: ## Show recent test reports
	@echo "📊 Recent test reports:"
	@ls -la reports/ | head -10

env-info: ## Show environment information
	@echo "🔧 Environment Information:"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "Pip version: $$($(PYTHON) -m pip --version)"
	@echo "Current directory: $$(pwd)"
	@echo "PYTHONPATH: $$PYTHONPATH"
	@echo "Virtual env: $$(which python || echo 'Not in virtual env')"

# Development Workflow Targets
dev-setup: setup-dev ## Complete development setup
	@echo "🎯 Development environment is ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  make test          - Run unit tests"
	@echo "  make regression-quick - Run quick regression tests"
	@echo "  make pre-commit    - Run all code quality checks"

ci-test: ## Run tests as in CI environment
	@echo "🤖 Running CI-style tests..."
	$(PYTHON) -m pytest $(TESTS_DIR)/ -v --tb=short \
		--ignore=$(TESTS_DIR)/test_functional.py \
		--ignore=$(TESTS_DIR)/test_integration.py \
		--cov=$(SRC_DIR) --cov-report=xml

# ============================================================================
# DEPLOYMENT COMMANDS
# ============================================================================

# Deploy to all environments (dev -> qa -> stage -> prod)
deploy-all: ## Deploy to all environments: dev -> qa -> stage -> prod
	@echo "🚀 Starting full deployment pipeline: dev -> qa -> stage -> prod"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py --verbose deploy --target prod

# Deploy to specific environment
deploy-dev: ## Deploy to DEV environment
	@echo "🚀 Deploying to DEV environment"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py --verbose deploy --target dev

deploy-qa: ## Deploy to QA environment  
	@echo "🚀 Deploying to QA environment"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py --verbose deploy --target qa

deploy-stage: ## Deploy to STAGE environment
	@echo "🚀 Deploying to STAGE environment"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py --verbose deploy --target stage

deploy-prod: ## Deploy to PRODUCTION environment
	@echo "🚀 Deploying to PRODUCTION environment"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py --verbose deploy --target prod

# Deployment status and management
deploy-status: ## Show deployment status across environments
	@echo "📊 Deployment status across environments"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py status

# Rollback commands
rollback-dev: ## Rollback DEV environment
	@echo "🔄 Rolling back DEV environment"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py rollback dev

rollback-qa: ## Rollback QA environment
	@echo "🔄 Rolling back QA environment"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py rollback qa

rollback-stage: ## Rollback STAGE environment
	@echo "🔄 Rolling back STAGE environment"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py rollback stage

rollback-prod: ## Rollback PRODUCTION environment
	@echo "🔄 Rolling back PRODUCTION environment"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py rollback prod

# Dry run deployments (for testing)
deploy-dry-run: ## Dry run: Full deployment pipeline
	@echo "🧪 Dry run: Full deployment pipeline"
	$(PYTHON) $(SCRIPTS_DIR)/deploy.py --dry-run --verbose deploy --target prod

# Quick Commands
quick: regression-quick ## Quick regression test (alias)
stage: regression-stage ## Stage regression test (alias)
check: pre-commit ## Pre-commit check (alias) 