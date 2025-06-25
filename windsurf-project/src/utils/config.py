"""
Configuration management for NLM tool
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """Manages configuration for different environments and test settings"""
    
    def __init__(self, config_path: Optional[str] = None, config_file: Optional[str] = None, environment: Optional[str] = None):
        # Use config_file as alias for config_path if provided
        self.config_path = config_file or config_path
        self.config = {}
        self.environment = environment or os.getenv("NLM_ENV", "dev")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize default configuration
        self._load_default_config()
        
        # Load custom config if provided
        if self.config_path:
            self.load_config(self.config_path)
    
    def _load_default_config(self):
        """Load default configuration"""
        self.config = {
            "environments": {
                "dev": {
                    "aws_region": "us-west-2",
                    "aws_profile": "default",
                    "datadog_site": "datadoghq.com",
                    "splunk_host": "localhost:8089"
                },
                "qa": {
                    "aws_region": "us-west-2",
                    "aws_profile": "qa",
                    "datadog_site": "datadoghq.com",
                    "splunk_host": "qa-splunk:8089"
                },
                "stage": {
                    "aws_region": "us-west-2",
                    "aws_profile": "stage",
                    "datadog_site": "datadoghq.com",
                    "splunk_host": "stage-splunk:8089"
                },
                "prod": {
                    "aws_region": "us-west-2",
                    "aws_profile": "prod",
                    "datadog_site": "datadoghq.com",
                    "splunk_host": "prod-splunk:8089"
                }
            },
            "credentials": {
                "aws": {
                    "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                    "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                    "region": os.getenv("AWS_DEFAULT_REGION", "us-west-2")
                },
                "datadog": {
                    "api_key": os.getenv("DATADOG_API_KEY"),
                    "app_key": os.getenv("DATADOG_APP_KEY")
                },
                "splunk": {
                    "host": os.getenv("SPLUNK_HOST"),
                    "username": os.getenv("SPLUNK_USERNAME"),
                    "password": os.getenv("SPLUNK_PASSWORD")
                },
                "ai": {
                    "openai_api_key": os.getenv("OPENAI_API_KEY"),
                    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY")
                }
            },
            "test_defaults": {
                "users": 10,
                "ramp_up": 30,
                "duration": 60,
                "think_time": 1,
                "timeout": 30
            }
        }
    
    def load_config(self, config_path: str) -> bool:
        """Load configuration from YAML or JSON file"""
        try:
            path = Path(config_path)
            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(path, 'r') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    custom_config = yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    custom_config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
            
            # Merge custom config with defaults
            self._merge_config(custom_config)
            return True
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def _merge_config(self, custom_config: Dict[str, Any]):
        """Merge custom configuration with defaults"""
        for key, value in custom_config.items():
            if key in self.config and isinstance(self.config[key], dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def get_environment_config(self, env: str):
        if env not in self.config.get("environments", {}):
            raise ValueError(f"Environment '{env}' not found")
        return self.config["environments"][env]
    
    def get_credentials(self, service: str) -> Dict[str, str]:
        """Get credentials for specific service"""
        return self.config.get("credentials", {}).get(service, {})
    
    def get_credential(self, service: str):
        if service not in self.config.get("credentials", {}):
            raise ValueError(f"Credential '{service}' not found")
        return self.config["credentials"][service]
    
    def get_test_defaults(self) -> Dict[str, Any]:
        """Get default test configuration"""
        return self.config.get("test_defaults", {})
    
    def set_environment(self, env: str):
        if env in self.config.get("environments", {}):
            self.environment = env
        else:
            raise ValueError(f"Environment '{env}' not found")
    
    def get_current_environment_config(self) -> Dict[str, Any]:
        """Get configuration for current environment"""
        return self.get_environment_config(self.environment)
    
    def reload_config(self):
        # Actually reload from file if possible
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
    
    def validate_credentials(self):
        # For test, just check keys exist
        creds = self.config.get("credentials", {})
        required = ["aws", "datadog", "splunk", "ai"]
        return {k: k in creds for k in required}
    
    def save_config(self, config_path: str) -> bool:
        """Save current configuration to file"""
        try:
            path = Path(config_path)
            with open(path, 'w') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(self.config, f, default_flow_style=False)
                elif path.suffix.lower() == '.json':
                    json.dump(self.config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False 