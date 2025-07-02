#!/bin/bash

echo "🚀 CI/CD Agent Setup for MangoMetrics NLM"
echo "=========================================="

# Check if GitHub token is already set
if [ -n "$GITHUB_TOKEN" ]; then
    echo "✅ GITHUB_TOKEN is already set"
else
    echo "❌ GITHUB_TOKEN is not set"
    echo ""
    echo "To set up the CI/CD agent, you need to:"
    echo "1. Create a GitHub Personal Access Token with the following permissions:"
    echo "   - repo (full control of private repositories)"
    echo "   - workflow (update GitHub Action workflows)"
    echo "   - issues (create issues)"
    echo ""
    echo "2. Set the environment variable:"
    echo "   export GITHUB_TOKEN='your_token_here'"
    echo ""
    echo "3. Optionally set the repository:"
    echo "   export GITHUB_REPOSITORY='MangoMetrics/NLM'"
    echo ""
    echo "You can create a token at: https://github.com/settings/tokens"
fi

echo ""
echo "📋 Current Configuration:"
echo "GITHUB_TOKEN: ${GITHUB_TOKEN:0:10}..."
echo "GITHUB_REPOSITORY: ${GITHUB_REPOSITORY:-'MangoMetrics/NLM'}"
echo ""

echo "🔧 To launch the CI/CD agent:"
echo "   python3 cicd_agent_launcher.py"
echo ""
echo "📝 The agent will:"
echo "   - Deploy to Dev (unit tests only)"
echo "   - Deploy to QA (functional + integration tests)"
echo "   - Deploy to Stage (regression + E2E tests)"
echo "   - Handle failures with automatic retries"
echo "   - Create hotfix branches and GitHub issues"
echo "   - Generate detailed logs and reports"
echo "" 