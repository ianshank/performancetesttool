#!/usr/bin/env python3
"""
Enterprise Deployment Pipeline for NLM Performance Testing Tool

This script implements a comprehensive deployment pipeline following best practices:
dev -> qa -> stage -> prod

Features:
- Automated validation at each environment
- Regression testing before promotion
- Rollback capabilities
- Deployment reporting
- Branch management
- Tag creation for releases
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DeploymentManager:
    """Manages the deployment pipeline across environments"""
    
    ENVIRONMENTS = ["dev", "qa", "stage", "prod"]
    BRANCH_MAPPING = {
        "dev": "dev",
        "qa": "qa", 
        "stage": "stage",
        "prod": "main"
    }
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.deployment_id = f"deploy_{int(time.time())}"
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
    def run_command(self, cmd: str, check: bool = True) -> Tuple[int, str, str]:
        """Execute shell command with optional dry-run"""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would execute: {cmd}")
            # Return realistic values for common commands in dry run mode
            if "git branch --show-current" in cmd:
                return 0, "dev", ""
            elif "git status --porcelain" in cmd:
                return 0, "", ""
            return 0, "", ""
            
        self.logger.debug(f"Executing: {cmd}")
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
        
        if check and result.returncode != 0:
            self.logger.error(f"Command failed: {cmd}")
            self.logger.error(f"Error: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
        return result.returncode, result.stdout, result.stderr
        
    def validate_prerequisites(self) -> bool:
        """Validate deployment prerequisites"""
        self.logger.info("🔍 Validating deployment prerequisites...")
        
        try:
            # Check git status
            returncode, stdout, _ = self.run_command("git status --porcelain")
            if stdout.strip():
                self.logger.warning("⚠️  Working directory has uncommitted changes")
                if not self.dry_run:
                    response = input("Continue anyway? (y/N): ")
                    if response.lower() != 'y':
                        return False
                        
            # Check if we're on dev branch
            returncode, current_branch, _ = self.run_command("git branch --show-current")
            current_branch = current_branch.strip()
            
            if current_branch != "dev":
                self.logger.error(f"❌ Must start deployment from 'dev' branch, currently on '{current_branch}'")
                return False
                
            # Validate all required branches exist
            for env in self.ENVIRONMENTS:
                branch = self.BRANCH_MAPPING[env]
                returncode, _, _ = self.run_command(f"git rev-parse --verify {branch}", check=False)
                if returncode != 0:
                    self.logger.info(f"📝 Creating missing branch: {branch}")
                    if env == "dev":
                        continue  # dev branch should exist
                    self.run_command(f"git checkout -b {branch}")
                    self.run_command(f"git push -u origin {branch}")
                    
            # Return to dev branch
            self.run_command("git checkout dev")
            
            self.logger.info("✅ Prerequisites validated")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Prerequisites validation failed: {e}")
            return False
            
    def run_regression_tests(self, environment: str) -> bool:
        """Run regression tests for specific environment"""
        self.logger.info(f"🧪 Running regression tests for {environment} environment...")
        
        try:
            # Use quick mode for dev, full for others
            mode_flag = "--quick" if environment == "dev" else ""
            
            returncode, stdout, stderr = self.run_command(
                f"python scripts/run_regression_tests.py --env {environment} {mode_flag} --verbose",
                check=False
            )
            
            if returncode == 0:
                self.logger.info(f"✅ Regression tests passed for {environment}")
                return True
            else:
                self.logger.error(f"❌ Regression tests failed for {environment}")
                self.logger.error(f"Output: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Regression tests failed: {e}")
            return False
            
    def deploy_to_environment(self, environment: str) -> bool:
        """Deploy to specific environment"""
        branch = self.BRANCH_MAPPING[environment]
        self.logger.info(f"🚀 Deploying to {environment} environment (branch: {branch})...")
        
        try:
            # Switch to target branch
            self.run_command(f"git checkout {branch}")
            
            # Merge from previous environment (or dev for qa)
            if environment == "qa":
                source_branch = "dev"
            elif environment == "stage":
                source_branch = "qa"
            elif environment == "prod":
                source_branch = "stage"
            else:  # dev
                source_branch = "dev"  # already on dev
                
            if environment != "dev":
                self.logger.info(f"📋 Merging {source_branch} -> {branch}")
                self.run_command(f"git merge {source_branch} --no-ff -m 'chore: Deploy to {environment} environment'")
                
            # Push changes
            self.logger.info(f"📤 Pushing to {branch}")
            self.run_command(f"git push origin {branch}")
            
            # Run environment-specific regression tests
            if not self.run_regression_tests(environment):
                self.logger.error(f"❌ Deployment blocked: regression tests failed for {environment}")
                return False
                
            # Create deployment tag for production
            if environment == "prod":
                tag = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.logger.info(f"🏷️  Creating release tag: {tag}")
                self.run_command(f"git tag -a {tag} -m 'Production release {tag}'")
                self.run_command(f"git push origin {tag}")
                
            self.logger.info(f"✅ Successfully deployed to {environment}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Deployment to {environment} failed: {e}")
            return False
            
    def rollback_environment(self, environment: str, target_commit: Optional[str] = None) -> bool:
        """Rollback specific environment"""
        branch = self.BRANCH_MAPPING[environment]
        self.logger.info(f"🔄 Rolling back {environment} environment...")
        
        try:
            self.run_command(f"git checkout {branch}")
            
            if target_commit:
                self.run_command(f"git reset --hard {target_commit}")
            else:
                # Rollback to previous commit
                self.run_command("git reset --hard HEAD~1")
                
            self.run_command(f"git push origin {branch} --force-with-lease")
            
            self.logger.info(f"✅ Successfully rolled back {environment}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Rollback failed for {environment}: {e}")
            return False
            
    def generate_deployment_report(self, environments: List[str], results: Dict[str, bool]) -> Dict:
        """Generate deployment report"""
        report = {
            "deployment_id": self.deployment_id,
            "timestamp": datetime.now().isoformat(),
            "environments": environments,
            "results": results,
            "success_rate": sum(results.values()) / len(results) if results else 0,
            "overall_status": "SUCCESS" if all(results.values()) else "PARTIAL" if any(results.values()) else "FAILED"
        }
        
        # Save report
        report_path = Path("reports") / f"deployment_report_{self.deployment_id}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"📊 Deployment report saved: {report_path}")
        return report
        
    def deploy_pipeline(self, target_environment: str = "prod", start_from: str = "dev") -> bool:
        """Execute full deployment pipeline"""
        self.logger.info(f"🎯 Starting deployment pipeline: {start_from} → {target_environment}")
        
        # Validate target environment
        if target_environment not in self.ENVIRONMENTS:
            self.logger.error(f"❌ Invalid target environment: {target_environment}")
            return False
            
        # Determine environments to deploy
        start_idx = self.ENVIRONMENTS.index(start_from)
        end_idx = self.ENVIRONMENTS.index(target_environment)
        
        if start_idx > end_idx:
            self.logger.error(f"❌ Cannot deploy backwards: {start_from} → {target_environment}")
            return False
            
        environments = self.ENVIRONMENTS[start_idx:end_idx + 1]
        results = {}
        
        self.logger.info(f"📋 Deployment pipeline: {' → '.join(environments)}")
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            return False
            
        # Deploy to each environment
        for env in environments:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"🎯 Deploying to {env.upper()} environment")
            self.logger.info(f"{'='*60}")
            
            success = self.deploy_to_environment(env)
            results[env] = success
            
            if not success:
                self.logger.error(f"❌ Deployment pipeline stopped at {env}")
                
                # Offer rollback
                if not self.dry_run and env != "dev":
                    response = input(f"Rollback {env}? (y/N): ")
                    if response.lower() == 'y':
                        self.rollback_environment(env)
                        
                break
                
            self.logger.info(f"✅ {env.upper()} deployment completed")
            
            # Add delay between environments for safety
            if env != environments[-1]:
                self.logger.info("⏳ Waiting 30 seconds before next deployment...")
                if not self.dry_run:
                    time.sleep(30)
                    
        # Generate report
        report = self.generate_deployment_report(environments, results)
        
        # Final status
        if all(results.values()):
            self.logger.info(f"\n🎉 DEPLOYMENT SUCCESSFUL!")
            self.logger.info(f"✅ All environments deployed: {' → '.join(environments)}")
            return True
        else:
            self.logger.error(f"\n💥 DEPLOYMENT FAILED!")
            failed_envs = [env for env, success in results.items() if not success]
            self.logger.error(f"❌ Failed environments: {', '.join(failed_envs)}")
            return False


def main():
    parser = argparse.ArgumentParser(description="NLM Deployment Pipeline")
    
    # Deployment commands
    subparsers = parser.add_subparsers(dest="command", help="Deployment commands")
    
    # Global options (add before subparsers)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to environments")
    deploy_parser.add_argument("--target", default="prod", choices=["dev", "qa", "stage", "prod"],
                              help="Target environment (default: prod)")
    deploy_parser.add_argument("--start-from", default="dev", choices=["dev", "qa", "stage"],
                              help="Starting environment (default: dev)")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback environment")
    rollback_parser.add_argument("environment", choices=["dev", "qa", "stage", "prod"],
                                help="Environment to rollback")
    rollback_parser.add_argument("--commit", help="Target commit (default: previous commit)")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show deployment status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    # Initialize deployment manager
    deployment = DeploymentManager(dry_run=args.dry_run, verbose=args.verbose)
    
    try:
        if args.command == "deploy":
            success = deployment.deploy_pipeline(args.target, args.start_from)
            return 0 if success else 1
            
        elif args.command == "rollback":
            success = deployment.rollback_environment(args.environment, args.commit)
            return 0 if success else 1
            
        elif args.command == "status":
            # Show current branch status for all environments
            for env in deployment.ENVIRONMENTS:
                branch = deployment.BRANCH_MAPPING[env]
                try:
                    _, commit, _ = deployment.run_command(f"git log -1 --format='%h %s' {branch}")
                    deployment.logger.info(f"{env:>5}: {branch:>6} -> {commit.strip()}")
                except:
                    deployment.logger.info(f"{env:>5}: {branch:>6} -> Not found")
            return 0
            
    except KeyboardInterrupt:
        deployment.logger.info("\n🛑 Deployment cancelled by user")
        return 130
    except Exception as e:
        deployment.logger.error(f"💥 Deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 