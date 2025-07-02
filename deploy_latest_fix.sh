#!/bin/bash

echo "🚀 Deploying Latest Fix via GitHub Actions CI/CD"
echo "================================================"

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN is not set"
    echo ""
    echo "To deploy the latest fix, you need to:"
    echo "1. Create a GitHub Personal Access Token with permissions:"
    echo "   - repo (full control of private repositories)"
    echo "   - workflow (update GitHub Action workflows)"
    echo ""
    echo "2. Set the environment variable:"
    echo "   export GITHUB_TOKEN='your_token_here'"
    echo ""
    echo "3. Run this script again:"
    echo "   ./deploy_latest_fix.sh"
    echo ""
    echo "You can create a token at: https://github.com/settings/tokens"
    exit 1
fi

# Set repository (default to current directory name)
REPO_NAME=${GITHUB_REPOSITORY:-"MangoMetrics/NLM"}
echo "📦 Repository: $REPO_NAME"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
echo "🌿 Current branch: $CURRENT_BRANCH"

# Get latest commit hash
LATEST_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
echo "🔗 Latest commit: ${LATEST_COMMIT:0:8}"

# Function to trigger workflow
trigger_workflow() {
    local environment=$1
    local test_type=$2
    
    echo ""
    echo "🚀 Triggering deployment to $environment environment..."
    echo "🧪 Test type: $test_type"
    
    # Prepare workflow dispatch payload
    cat > /tmp/workflow_payload.json << EOF
{
    "ref": "$CURRENT_BRANCH",
    "inputs": {
        "environment": "$environment",
        "test_type": "$test_type",
        "run_tests": "true",
        "deploy_latest": "true"
    }
}
EOF
    
    # Trigger the workflow
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        -d @/tmp/workflow_payload.json \
        "https://api.github.com/repos/$REPO_NAME/actions/workflows/deploy-all-envs.yml/dispatches")
    
    http_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$http_code" = "204" ]; then
        echo "✅ Successfully triggered deployment to $environment"
        
        # Get the workflow run ID
        sleep 2
        runs_response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/$REPO_NAME/actions/runs?per_page=1")
        
        if [ $? -eq 0 ]; then
            run_id=$(echo "$runs_response" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
            if [ -n "$run_id" ]; then
                echo "🔗 Workflow run ID: $run_id"
                echo "📊 Monitor at: https://github.com/$REPO_NAME/actions/runs/$run_id"
            fi
        fi
        
        return 0
    else
        echo "❌ Failed to trigger deployment to $environment"
        echo "HTTP Code: $http_code"
        echo "Response: $response_body"
        return 1
    fi
}

# Function to monitor workflow
monitor_workflow() {
    local run_id=$1
    local environment=$2
    
    echo ""
    echo "👀 Monitoring deployment to $environment..."
    echo "⏳ Checking status every 30 seconds..."
    
    local attempts=0
    local max_attempts=60  # 30 minutes max
    
    while [ $attempts -lt $max_attempts ]; do
        attempts=$((attempts + 1))
        
        # Get workflow status
        status_response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/$REPO_NAME/actions/runs/$run_id")
        
        if [ $? -eq 0 ]; then
            status=$(echo "$status_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            conclusion=$(echo "$status_response" | grep -o '"conclusion":"[^"]*"' | cut -d'"' -f4)
            
            echo "📊 Attempt $attempts: Status=$status, Conclusion=$conclusion"
            
            if [ "$status" = "completed" ]; then
                if [ "$conclusion" = "success" ]; then
                    echo "✅ Deployment to $environment completed successfully!"
                    return 0
                else
                    echo "❌ Deployment to $environment failed!"
                    return 1
                fi
            fi
        fi
        
        sleep 30
    done
    
    echo "⏰ Monitoring timeout for $environment"
    return 1
}

# Deploy to environments in sequence
echo ""
echo "🎯 Starting deployment sequence..."

# Deploy to Dev (unit tests only)
if trigger_workflow "dev" "unit"; then
    echo "✅ Dev deployment triggered successfully"
else
    echo "❌ Failed to trigger Dev deployment"
    exit 1
fi

# Wait before next environment
echo ""
echo "⏳ Waiting 60 seconds before QA deployment..."
sleep 60

# Deploy to QA (functional + integration tests)
if trigger_workflow "qa" "functional,integration"; then
    echo "✅ QA deployment triggered successfully"
else
    echo "❌ Failed to trigger QA deployment"
    exit 1
fi

# Wait before next environment
echo ""
echo "⏳ Waiting 60 seconds before Stage deployment..."
sleep 60

# Deploy to Stage (regression + E2E tests)
if trigger_workflow "stage" "regression,e2e"; then
    echo "✅ Stage deployment triggered successfully"
else
    echo "❌ Failed to trigger Stage deployment"
    exit 1
fi

echo ""
echo "🎉 All deployments triggered successfully!"
echo ""
echo "📊 Monitor all workflows at: https://github.com/$REPO_NAME/actions"
echo ""
echo "📝 Deployment Summary:"
echo "   - Dev: Unit tests only"
echo "   - QA: Functional + Integration tests"
echo "   - Stage: Regression + E2E tests"
echo ""
echo "🔗 Latest commit: ${LATEST_COMMIT:0:8}"
echo "🌿 Branch: $CURRENT_BRANCH"
echo ""

# Cleanup
rm -f /tmp/workflow_payload.json 