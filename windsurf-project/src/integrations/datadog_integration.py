"""
Datadog integration for NLM tool
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from utils.logger import get_logger


class DatadogIntegration:
    """Integration with Datadog for metrics and logs collection"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = get_logger("nlm.datadog")
        self.api_key = None
        self.app_key = None
        self.site = "datadoghq.com"
        self.base_url = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Datadog client"""
        try:
            credentials = self.config_manager.get_credentials("datadog")
            env_config = self.config_manager.get_environment_config()

            self.api_key = credentials.get("api_key")
            self.app_key = credentials.get("app_key")
            self.site = env_config.get("datadog_site", "datadoghq.com")
            self.base_url = f"https://api.{self.site}"

            if not self.api_key:
                self.logger.warning("Datadog API key not configured")
            if not self.app_key:
                self.logger.warning("Datadog App key not configured")

            self.logger.info(f"Datadog client initialized for site: {self.site}")

        except Exception as e:
            self.logger.error(f"Failed to initialize Datadog client: {e}")
            raise

    def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make HTTP request to Datadog API"""
        if not self.api_key:
            self.logger.error("Datadog API key not configured")
            return None

        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json", "DD-API-KEY": self.api_key}

        if self.app_key:
            headers["DD-APPLICATION-KEY"] = self.app_key

        try:
            response = requests.request(
                method=method, url=url, headers=headers, params=params, json=data, timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Datadog API request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error making Datadog request: {e}")
            return None

    def get_metrics(self, metric_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """
        Get Datadog metrics

        Args:
            metric_name: Metric name to retrieve
            hours: Number of hours to look back

        Returns:
            List of metric data points
        """
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())

        params = {"query": metric_name, "from": start_time, "to": end_time}

        response = self._make_request("GET", "/api/v1/query", params=params)

        if response and "series" in response:
            series = response["series"]
            if series:
                return series[0].get("pointlist", [])

        return []

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get common system metrics"""
        metrics = {}

        # CPU metrics
        cpu_data = self.get_metrics("system.cpu.user", hours=1)
        metrics["cpu_user"] = cpu_data

        cpu_system = self.get_metrics("system.cpu.system", hours=1)
        metrics["cpu_system"] = cpu_system

        # Memory metrics
        memory_used = self.get_metrics("system.mem.used", hours=1)
        metrics["memory_used"] = memory_used

        memory_free = self.get_metrics("system.mem.free", hours=1)
        metrics["memory_free"] = memory_free

        # Network metrics
        network_in = self.get_metrics("system.net.bytes_rcvd", hours=1)
        metrics["network_in"] = network_in

        network_out = self.get_metrics("system.net.bytes_sent", hours=1)
        metrics["network_out"] = network_out

        # Disk metrics
        disk_used = self.get_metrics("system.disk.used", hours=1)
        metrics["disk_used"] = disk_used

        disk_free = self.get_metrics("system.disk.free", hours=1)
        metrics["disk_free"] = disk_free

        return metrics

    def get_application_metrics(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get application-specific metrics"""
        metrics = {}

        # HTTP metrics
        http_requests = self.get_metrics("http.requests", hours=1)
        metrics["http_requests"] = http_requests

        http_response_time = self.get_metrics("http.response_time", hours=1)
        metrics["http_response_time"] = http_response_time

        # Database metrics
        db_connections = self.get_metrics("database.connections", hours=1)
        metrics["db_connections"] = db_connections

        db_query_time = self.get_metrics("database.query_time", hours=1)
        metrics["db_query_time"] = db_query_time

        return metrics

    def search_metrics(self, query: str) -> List[Dict[str, Any]]:
        """Search for metrics by query"""
        params = {"q": query}
        response = self._make_request("GET", "/api/v1/search", params=params)

        if response and "results" in response:
            return response["results"].get("metrics", [])

        return []

    def get_logs(self, query: str, hours: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get logs from Datadog

        Args:
            query: Log search query
            hours: Number of hours to look back
            limit: Maximum number of logs to return

        Returns:
            List of log entries
        """
        if not self.app_key:
            self.logger.error("Datadog App key required for log queries")
            return []

        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())

        data = {"query": query, "time": {"from": start_time, "to": end_time}, "limit": limit}

        response = self._make_request("POST", "/api/v1/logs-queries/list", data=data)

        if response and "logs" in response:
            return response["logs"]

        return []

    def get_error_logs(
        self, service_name: Optional[str] = None, hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get error logs"""
        query = "status:error"
        if service_name:
            query += f" service:{service_name}"

        return self.get_logs(query, hours=hours)

    def get_slow_queries(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get slow database queries"""
        query = "service:database duration:>1000"
        return self.get_logs(query, hours=hours)

    def send_custom_metric(
        self, metric_name: str, value: float, tags: Optional[List[str]] = None
    ) -> bool:
        """
        Send custom metric to Datadog

        Args:
            metric_name: Metric name
            value: Metric value
            tags: Optional tags for the metric

        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            self.logger.error("Datadog API key not configured")
            return False

        data = {
            "series": [
                {
                    "metric": metric_name,
                    "points": [[int(datetime.now().timestamp()), value]],
                    "type": "gauge",
                }
            ]
        }

        if tags:
            data["series"][0]["tags"] = tags

        response = self._make_request("POST", "/api/v1/series", data=data)

        if response and response.get("status") == "ok":
            self.logger.info(f"Custom metric {metric_name} sent successfully")
            return True
        else:
            self.logger.error(f"Failed to send custom metric {metric_name}")
            return False

    def send_event(
        self, title: str, text: str, alert_type: str = "info", tags: Optional[List[str]] = None
    ) -> bool:
        """
        Send event to Datadog

        Args:
            title: Event title
            text: Event description
            alert_type: Event type (info, warning, error, success)
            tags: Optional tags for the event

        Returns:
            True if successful, False otherwise
        """
        data = {"title": title, "text": text, "alert_type": alert_type}

        if tags:
            data["tags"] = tags

        response = self._make_request("POST", "/api/v1/events", data=data)

        if response and "event" in response:
            self.logger.info(f"Event '{title}' sent successfully")
            return True
        else:
            self.logger.error(f"Failed to send event '{title}'")
            return False

    def test_connection(self) -> bool:
        """Test Datadog connection"""
        try:
            # Try to get a simple metric to test connection
            response = self._make_request("GET", "/api/v1/validate")
            return response is not None
        except Exception as e:
            self.logger.error(f"Datadog connection test failed: {e}")
            return False

    def get_dashboard_list(self) -> List[Dict[str, Any]]:
        """Get list of available dashboards"""
        response = self._make_request("GET", "/api/v1/dashboard")

        if response and "dashboards" in response:
            return response["dashboards"]

        return []

    def get_monitor_list(self) -> List[Dict[str, Any]]:
        """Get list of active monitors"""
        params = {"monitor_tags": "env:production"}
        response = self._make_request("GET", "/api/v1/monitor", params=params)

        if response:
            return response
        return []
