"""
AWS CloudWatch integration for NLM tool
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from utils.logger import get_logger


class CloudWatchIntegration:
    """Integration with AWS CloudWatch for metrics collection"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = get_logger("nlm.cloudwatch")
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the CloudWatch client"""
        try:
            credentials = self.config_manager.get_credentials("aws")
            env_config = self.config_manager.get_environment_config()

            # Try to use credentials if available
            if credentials.get("access_key_id") and credentials.get("secret_access_key"):
                self.client = boto3.client(
                    "cloudwatch",
                    aws_access_key_id=credentials["access_key_id"],
                    aws_secret_access_key=credentials["secret_access_key"],
                    region_name=credentials.get(
                        "region", env_config.get("aws_region", "us-west-2")
                    ),
                )
            else:
                # Use default credentials (IAM role, profile, etc.)
                self.client = boto3.client(
                    "cloudwatch", region_name=env_config.get("aws_region", "us-west-2")
                )

            self.logger.info("CloudWatch client initialized successfully")

        except NoCredentialsError:
            self.logger.error("AWS credentials not found")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize CloudWatch client: {e}")
            raise

    def get_metrics(
        self,
        namespace: str = "AWS/EC2",
        metric_name: str = "CPUUtilization",
        period: int = 300,
        hours: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get CloudWatch metrics

        Args:
            namespace: CloudWatch namespace
            metric_name: Metric name to retrieve
            period: Data point period in seconds
            hours: Number of hours to look back

        Returns:
            List of metric data points
        """
        if not self.client:
            self.logger.error("CloudWatch client not initialized")
            return []

        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            response = self.client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=["Average", "Maximum", "Minimum"],
            )

            self.logger.info(
                f"Retrieved {len(response['Datapoints'])} data points for {metric_name}"
            )
            return response["Datapoints"]

        except ClientError as e:
            self.logger.error(f"CloudWatch API error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error retrieving CloudWatch metrics: {e}")
            return []

    def get_ec2_metrics(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get EC2 instance metrics"""
        metrics = {}

        # CPU Utilization
        cpu_data = self.get_metrics(
            namespace="AWS/EC2", metric_name="CPUUtilization", period=300, hours=1
        )
        metrics["cpu_utilization"] = cpu_data

        # Network metrics
        network_in = self.get_metrics(
            namespace="AWS/EC2", metric_name="NetworkIn", period=300, hours=1
        )
        metrics["network_in"] = network_in

        network_out = self.get_metrics(
            namespace="AWS/EC2", metric_name="NetworkOut", period=300, hours=1
        )
        metrics["network_out"] = network_out

        # Disk metrics
        disk_read = self.get_metrics(
            namespace="AWS/EC2", metric_name="DiskReadBytes", period=300, hours=1
        )
        metrics["disk_read"] = disk_read

        disk_write = self.get_metrics(
            namespace="AWS/EC2", metric_name="DiskWriteBytes", period=300, hours=1
        )
        metrics["disk_write"] = disk_write

        return metrics

    def get_rds_metrics(self, db_instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get RDS database metrics"""
        metrics = {}

        # Database connections
        connections = self.get_metrics(
            namespace="AWS/RDS", metric_name="DatabaseConnections", period=300, hours=1
        )
        metrics["database_connections"] = connections

        # CPU utilization
        cpu_data = self.get_metrics(
            namespace="AWS/RDS", metric_name="CPUUtilization", period=300, hours=1
        )
        metrics["cpu_utilization"] = cpu_data

        # Free storage space
        free_storage = self.get_metrics(
            namespace="AWS/RDS", metric_name="FreeStorageSpace", period=300, hours=1
        )
        metrics["free_storage"] = free_storage

        return metrics

    def get_elb_metrics(self, load_balancer_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Elastic Load Balancer metrics"""
        metrics = {}

        # Request count
        request_count = self.get_metrics(
            namespace="AWS/ELB", metric_name="RequestCount", period=300, hours=1
        )
        metrics["request_count"] = request_count

        # Target response time
        response_time = self.get_metrics(
            namespace="AWS/ELB", metric_name="TargetResponseTime", period=300, hours=1
        )
        metrics["target_response_time"] = response_time

        # Healthy host count
        healthy_hosts = self.get_metrics(
            namespace="AWS/ELB", metric_name="HealthyHostCount", period=300, hours=1
        )
        metrics["healthy_hosts"] = healthy_hosts

        return metrics

    def put_custom_metric(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[List[Dict[str, str]]] = None,
    ) -> bool:
        """
        Put custom metric to CloudWatch

        Args:
            namespace: Custom namespace
            metric_name: Metric name
            value: Metric value
            unit: Metric unit
            dimensions: Metric dimensions

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            self.logger.error("CloudWatch client not initialized")
            return False

        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.utcnow(),
            }

            if dimensions:
                metric_data["Dimensions"] = dimensions

            self.client.put_metric_data(Namespace=namespace, MetricData=[metric_data])

            self.logger.info(f"Custom metric {metric_name} published successfully")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to put custom metric: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error putting custom metric: {e}")
            return False

    def list_metrics(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available metrics"""
        if not self.client:
            self.logger.error("CloudWatch client not initialized")
            return []

        try:
            params = {}
            if namespace:
                params["Namespace"] = namespace

            response = self.client.list_metrics(**params)
            return response["Metrics"]

        except ClientError as e:
            self.logger.error(f"Failed to list metrics: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error listing metrics: {e}")
            return []

    def test_connection(self) -> bool:
        """Test CloudWatch connection"""
        try:
            # Try to list metrics to test connection
            self.client.list_metrics(MaxResults=1)
            self.logger.info("CloudWatch connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"CloudWatch connection test failed: {e}")
            return False
