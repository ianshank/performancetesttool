#!/usr/bin/env python3
"""
CI/CD Agent Launcher for MangoMetrics NLM Application
Handles deployments to Dev, QA, and Stage environments using GitHub Actions
"""

import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cicd_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CICDAgent:
    def __init__(self):
        self.environments = ['dev', 'qa', 'stage']
        self.max_retries = 10
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPOSITORY', 'MangoMetrics/NLM')
        self.github_api_url = f"https://api.github.com/repos/{self.github_repo}"
        
        if not self.github_token:
            logger.error("GITHUB_TOKEN environment variable not set")
            sys.exit(1)
            
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
    def log_deployment_attempt(self, env, attempt, status, details=""):
        """Log deployment attempt to file"""
        log_file = f"deployment_log_{env}.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a') as f:
            f.write(f"## Attempt {attempt} - {timestamp}\n")
            f.write(f"**Status:** {status}\n")
            if details:
                f.write(f"**Details:** {details}\n")
            f.write("\n---\n\n")
            
    def trigger_workflow(self, environment):
        """Trigger GitHub Actions workflow for specified environment"""
        workflow_file = "deploy-all-envs.yml"
        
        # Set environment-specific inputs
        inputs = {
            "environment": environment,
            "run_tests": "true"
        }
        
        # Set test strategy based on environment
        if environment == "dev":
            inputs["test_type"] = "unit"
        elif environment == "qa":
            inputs["test_type"] = "functional,integration"
        elif environment == "stage":
            inputs["test_type"] = "regression,e2e"
            
        payload = {
            "ref": "main",
            "inputs": inputs
        }
        
        url = f"{self.github_api_url}/actions/workflows/{workflow_file}/dispatches"
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # Get the workflow run ID
            runs_url = f"{self.github_api_url}/actions/runs"
            runs_response = requests.get(runs_url, headers=self.headers)
            runs_response.raise_for_status()
            
            runs = runs_response.json()['workflow_runs']
            if runs:
                return runs[0]['id']
            else:
                logger.error("No workflow runs found")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger workflow: {e}")
            return None
            
    def monitor_workflow(self, run_id):
        """Monitor workflow run status"""
        url = f"{self.github_api_url}/actions/runs/{run_id}"
        
        while True:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                run_data = response.json()
                status = run_data['status']
                conclusion = run_data.get('conclusion')
                
                logger.info(f"Workflow status: {status}, conclusion: {conclusion}")
                
                if status == 'completed':
                    return conclusion == 'success', run_data
                    
                time.sleep(30)  # Check every 30 seconds
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to monitor workflow: {e}")
                return False, None
                
    def analyze_failure(self, run_data):
        """Analyze workflow failure and categorize"""
        if not run_data:
            return "unknown", "No run data available"
            
        # Get workflow logs
        logs_url = f"{self.github_api_url}/actions/runs/{run_data['id']}/logs"
        
        try:
            logs_response = requests.get(logs_url, headers=self.headers)
            logs_response.raise_for_status()
            logs = logs_response.text
            
            # Analyze logs for failure patterns
            if "test failure" in logs.lower() or "assertion" in logs.lower():
                return "test_failure", logs
            elif "dependency" in logs.lower() or "package" in logs.lower():
                return "dependency_error", logs
            elif "configuration" in logs.lower() or "yaml" in logs.lower():
                return "ci_misconfiguration", logs
            elif "code" in logs.lower() or "syntax" in logs.lower():
                return "code_defect", logs
            else:
                return "infrastructure_error", logs
                
        except requests.exceptions.RequestException as e:
            return "unknown", f"Failed to get logs: {e}"
            
    def create_hotfix_branch(self, environment, issue_type):
        """Create hotfix branch for fixes"""
        branch_name = f"hotfix/cicd-{environment}-{datetime.now().strftime('%Y%m%d')}"
        
        # Get latest commit from main
        try:
            main_response = requests.get(f"{self.github_api_url}/git/ref/heads/main", headers=self.headers)
            main_response.raise_for_status()
            main_sha = main_response.json()['object']['sha']
            
            # Create new branch
            branch_payload = {
                "ref": f"refs/heads/{branch_name}",
                "sha": main_sha
            }
            
            branch_response = requests.post(f"{self.github_api_url}/git/refs", headers=self.headers, json=branch_payload)
            branch_response.raise_for_status()
            
            logger.info(f"Created hotfix branch: {branch_name}")
            return branch_name
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create hotfix branch: {e}")
            return None
            
    def create_github_issue(self, environment, issue_type, details):
        """Create GitHub issue for bugs"""
        title = f"[AutoBug][{environment.upper()}] {issue_type.replace('_', ' ').title()}"
        
        body = f"""
## Environment
{environment.upper()}

## Issue Type
{issue_type.replace('_', ' ').title()}

## Root Cause
{details[:500]}...

## Steps to Reproduce
1. Trigger deployment to {environment} environment
2. Monitor workflow execution
3. Observe failure

## Priority
Medium

## Labels
bug, cicd, {environment}
        """
        
        payload = {
            "title": title,
            "body": body,
            "labels": ["bug", "cicd", environment]
        }
        
        try:
            response = requests.post(f"{self.github_api_url}/issues", headers=self.headers, json=payload)
            response.raise_for_status()
            
            issue_data = response.json()
            logger.info(f"Created GitHub issue: {issue_data['html_url']}")
            return issue_data['html_url']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return None
            
    def deploy_environment(self, environment):
        """Deploy to specific environment with retry logic"""
        logger.info(f"Starting deployment to {environment.upper()} environment")
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Attempt {attempt}/{self.max_retries} for {environment}")
            
            # Trigger workflow
            run_id = self.trigger_workflow(environment)
            if not run_id:
                self.log_deployment_attempt(environment, attempt, "FAILED", "Failed to trigger workflow")
                continue
                
            # Monitor workflow
            success, run_data = self.monitor_workflow(run_id)
            
            if success:
                logger.info(f"✅ Deployment to {environment} successful!")
                self.log_deployment_attempt(environment, attempt, "SUCCESS")
                return True
            else:
                # Analyze failure
                issue_type, details = self.analyze_failure(run_data)
                logger.warning(f"❌ Deployment to {environment} failed: {issue_type}")
                
                # Create hotfix branch
                hotfix_branch = self.create_hotfix_branch(environment, issue_type)
                
                # Create GitHub issue
                issue_url = self.create_github_issue(environment, issue_type, details)
                
                # Log attempt
                self.log_deployment_attempt(
                    environment, attempt, "FAILED", 
                    f"Issue type: {issue_type}, Issue: {issue_url}, Branch: {hotfix_branch}"
                )
                
                # If same error 3 times in a row, break
                if attempt >= 3 and attempt < self.max_retries:
                    logger.warning(f"Same error pattern detected, continuing to next attempt...")
                    
        # All attempts failed
        logger.error(f"❌ All {self.max_retries} attempts failed for {environment}")
        return False
        
    def create_final_report(self, failed_environments):
        """Create final failure report"""
        report_content = f"""
# FINAL FAILURE REPORT - CI/CD Deployment

## Summary
Deployment failed for the following environments: {', '.join(failed_environments)}

## Failed Environments
"""
        
        for env in failed_environments:
            log_file = f"deployment_log_{env}.md"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    report_content += f"\n### {env.upper()}\n{f.read()}\n"
                    
        report_content += f"""
## Recommendations
1. Review all GitHub issues created during deployment
2. Check hotfix branches for potential fixes
3. Verify GitHub Actions workflow configuration
4. Review test suite for flaky tests
5. Consider infrastructure improvements

## Next Steps
- Manual intervention required
- Review logs in deployment_log_*.md files
- Check GitHub issues for detailed analysis
- Consider rolling back recent changes if necessary

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        with open("FINAL_FAILURE_REPORT.md", 'w') as f:
            f.write(report_content)
            
        logger.info("Created FINAL_FAILURE_REPORT.md")
        
    def run(self):
        """Main deployment orchestration"""
        logger.info("🚀 Starting CI/CD Agent for MangoMetrics NLM")
        logger.info(f"Target environments: {', '.join(self.environments)}")
        
        failed_environments = []
        
        for environment in self.environments:
            logger.info(f"\n{'='*50}")
            logger.info(f"Deploying to {environment.upper()}")
            logger.info(f"{'='*50}")
            
            success = self.deploy_environment(environment)
            
            if not success:
                failed_environments.append(environment)
                
            # Wait between environments
            if environment != self.environments[-1]:
                logger.info("Waiting 60 seconds before next environment...")
                time.sleep(60)
                
        # Final report if any failures
        if failed_environments:
            logger.error(f"❌ Deployment completed with failures: {', '.join(failed_environments)}")
            self.create_final_report(failed_environments)
            
            # TODO: Send email to ianshank@gmail.com
            logger.info("📧 Final failure report created. Manual email notification required.")
        else:
            logger.info("✅ All deployments completed successfully!")
            
        logger.info("🏁 CI/CD Agent completed")

def main():
    """Main entry point"""
    agent = CICDAgent()
    agent.run()

if __name__ == "__main__":
    main() 