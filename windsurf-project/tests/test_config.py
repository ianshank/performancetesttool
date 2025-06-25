"""
Unit tests for ConfigManager class
"""

import pytest
import sys
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.config import ConfigManager


class TestConfigManager:
    """Test the ConfigManager class"""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration data"""
        return {
            "environments": {
                "dev": {
                    "aws_region": "us-east-1",
                    "datadog_api_key": "dev_key",
                    "splunk_host": "dev-splunk.example.com"
                },
                "prod": {
                    "aws_region": "us-west-2",
                    "datadog_api_key": "prod_key",
                    "splunk_host": "prod-splunk.example.com"
                }
            },
            "credentials": {
                "aws": {
                    "access_key_id": "test_access_key",
                    "secret_access_key": "test_secret_key"
                },
                "datadog": {
                    "api_key": "test_datadog_key",
                    "app_key": "test_datadog_app_key"
                },
                "splunk": {
                    "username": "test_user",
                    "password": "test_password"
                },
                "ai": {
                    "openai_api_key": "test_openai_key",
                    "anthropic_api_key": "test_anthropic_key"
                }
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, sample_config):
        """Create a temporary config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    def test_initialization_default(self):
        """Test ConfigManager initialization with default config"""
        config = ConfigManager()
        assert config is not None
        assert config.environment == "dev"
        assert "environments" in config.config
        assert "credentials" in config.config
    
    def test_initialization_with_file(self, temp_config_file):
        """Test ConfigManager initialization with config file"""
        config = ConfigManager(config_file=temp_config_file)
        assert config is not None
        assert config.environment == "dev"
        assert config.config["environments"]["dev"]["aws_region"] == "us-east-1"
    
    def test_initialization_with_environment(self, temp_config_file):
        """Test ConfigManager initialization with specific environment"""
        config = ConfigManager(config_file=temp_config_file, environment="prod")
        assert config.environment == "prod"
        assert config.config["environments"]["prod"]["aws_region"] == "us-west-2"
    
    def test_get_environment_config(self, temp_config_file):
        """Test getting environment configuration"""
        config = ConfigManager(config_file=temp_config_file)
        
        dev_config = config.get_environment_config("dev")
        assert dev_config is not None
        assert dev_config["aws_region"] == "us-east-1"
        assert dev_config["datadog_api_key"] == "dev_key"
        
        prod_config = config.get_environment_config("prod")
        assert prod_config is not None
        assert prod_config["aws_region"] == "us-west-2"
        assert prod_config["splunk_host"] == "prod-splunk.example.com"
    
    def test_get_environment_config_invalid(self, temp_config_file):
        """Test getting invalid environment configuration"""
        config = ConfigManager(config_file=temp_config_file)
        
        with pytest.raises(ValueError, match="Environment 'invalid' not found"):
            config.get_environment_config("invalid")
    
    def test_set_environment(self, temp_config_file):
        """Test setting environment"""
        config = ConfigManager(config_file=temp_config_file)
        
        # Initially dev
        assert config.environment == "dev"
        
        # Set to prod
        config.set_environment("prod")
        assert config.environment == "prod"
        
        # Set to invalid environment
        with pytest.raises(ValueError, match="Environment 'invalid' not found"):
            config.set_environment("invalid")
    
    def test_get_credential(self, temp_config_file):
        """Test getting credentials"""
        config = ConfigManager(config_file=temp_config_file)
        
        aws_creds = config.get_credential("aws")
        assert aws_creds is not None
        assert aws_creds["access_key_id"] == "test_access_key"
        assert aws_creds["secret_access_key"] == "test_secret_key"
        
        datadog_creds = config.get_credential("datadog")
        assert datadog_creds is not None
        assert datadog_creds["api_key"] == "test_datadog_key"
    
    def test_get_credential_invalid(self, temp_config_file):
        """Test getting invalid credentials"""
        config = ConfigManager(config_file=temp_config_file)
        
        with pytest.raises(ValueError, match="Credential 'invalid' not found"):
            config.get_credential("invalid")
    
    def test_validate_credentials(self, temp_config_file):
        """Test credential validation"""
        config = ConfigManager(config_file=temp_config_file)
        
        validation = config.validate_credentials()
        
        assert isinstance(validation, dict)
        assert "aws" in validation
        assert "datadog" in validation
        assert "splunk" in validation
        assert "ai" in validation
        
        # All credentials should be valid in this test
        assert all(validation.values())
    
    def test_validate_credentials_missing(self):
        """Test credential validation with missing credentials"""
        config = ConfigManager()
        
        validation = config.validate_credentials()
        
        assert isinstance(validation, dict)
        assert "aws" in validation
        assert "datadog" in validation
        assert "splunk" in validation
        assert "ai" in validation
        
        # Some credentials might be missing in default config
        assert isinstance(validation["aws"], bool)
        assert isinstance(validation["datadog"], bool)
        assert isinstance(validation["splunk"], bool)
        assert isinstance(validation["ai"], bool)
    
    def test_save_config(self, temp_config_file):
        """Test saving configuration"""
        config = ConfigManager(config_file=temp_config_file)
        
        # Modify config
        config.config["test_key"] = "test_value"
        
        # Save to new file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            new_config_file = f.name
        
        try:
            config.save_config(new_config_file)
            
            # Load the saved config
            new_config = ConfigManager(config_file=new_config_file)
            assert new_config.config["test_key"] == "test_value"
            
        finally:
            # Cleanup
            os.unlink(new_config_file)
    
    def test_reload_config(self, temp_config_file):
        """Test reloading configuration"""
        config = ConfigManager(config_file=temp_config_file)
        
        # Modify config in memory
        config.config["test_key"] = "test_value"
        
        # Reload from file
        config.reload_config()
        
        # Should not have the test key anymore
        assert "test_key" not in config.config
    
    def test_get_current_environment_config(self, temp_config_file):
        """Test getting current environment configuration"""
        config = ConfigManager(config_file=temp_config_file)
        
        current_config = config.get_current_environment_config()
        assert current_config is not None
        assert current_config["aws_region"] == "us-east-1"  # dev environment
        
        # Change environment
        config.set_environment("prod")
        current_config = config.get_current_environment_config()
        assert current_config["aws_region"] == "us-west-2"  # prod environment


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 