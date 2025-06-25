"""
Splunk integration for NLM tool
"""

import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from utils.logger import get_logger


class SplunkIntegration:
    """Integration with Splunk for logs and metrics collection"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = get_logger("nlm.splunk")
        self.host = None
        self.username = None
        self.password = None
        self.base_url = None
        self.session = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Splunk client"""
        try:
            credentials = self.config_manager.get_credentials("splunk")
            env_config = self.config_manager.get_environment_config()

            self.host = credentials.get("host") or env_config.get("splunk_host", "localhost:8089")
            self.username = credentials.get("username")
            self.password = credentials.get("password")

            # Ensure protocol is included
            if not self.host.startswith(("http://", "https://")):
                self.host = f"https://{self.host}"

            self.base_url = self.host

            if not self.username or not self.password:
                self.logger.warning("Splunk credentials not fully configured")

            self.logger.info(f"Splunk client initialized for host: {self.host}")

        except Exception as e:
            self.logger.error(f"Failed to initialize Splunk client: {e}")
            raise

    def _authenticate(self) -> bool:
        """Authenticate with Splunk"""
        if not self.username or not self.password:
            self.logger.error("Splunk credentials not configured")
            return False

        try:
            auth_url = f"{self.base_url}/services/auth/login"
            auth_data = {"username": self.username, "password": self.password}

            response = requests.post(auth_url, data=auth_data, verify=False, timeout=30)
            response.raise_for_status()

            # Extract session key from response
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)
            session_key = root.find(".//sessionKey")

            if session_key is not None:
                self.session = requests.Session()
                self.session.headers.update(
                    {
                        "Authorization": f"Splunk {session_key.text}",
                        "Content-Type": "application/json",
                    }
                )
                self.logger.info("Splunk authentication successful")
                return True
            else:
                self.logger.error("Failed to extract session key from Splunk response")
                return False

        except Exception as e:
            self.logger.error(f"Splunk authentication failed: {e}")
            return False

    def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make HTTP request to Splunk API"""
        if not self.session:
            if not self._authenticate():
                return None

        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method, url=url, params=params, json=data, timeout=30
            )

            response.raise_for_status()

            # Handle different response formats
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                # For non-JSON responses, return text
                return {"text": response.text}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Splunk API request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error making Splunk request: {e}")
            return None

    def search_logs(self, query: str, hours: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search logs in Splunk

        Args:
            query: Splunk search query
            hours: Number of hours to look back
            limit: Maximum number of results to return

        Returns:
            List of log entries
        """
        # Add time range to query
        time_range = f"earliest=-{hours}h latest=now"
        full_query = f"{query} | head {limit}"

        data = {"search": full_query, "exec_mode": "oneshot", "output_mode": "json"}

        response = self._make_request("POST", "/services/search/jobs/export", data=data)

        if response and "results" in response:
            return response["results"]
        elif response and isinstance(response, list):
            return response
        else:
            return []

    def get_error_logs(self, index: str = "main", hours: int = 1) -> List[Dict[str, Any]]:
        """Get error logs from Splunk"""
        query = f"search index={index} level=ERROR OR level=error OR level=FATAL OR level=fatal"
        return self.search_logs(query, hours=hours)

    def get_slow_queries(self, index: str = "main", hours: int = 1) -> List[Dict[str, Any]]:
        """Get slow database queries from logs"""
        query = f"search index={index} (database OR sql) duration>1000"
        return self.search_logs(query, hours=hours)

    def get_http_logs(self, index: str = "main", hours: int = 1) -> List[Dict[str, Any]]:
        """Get HTTP access logs"""
        query = f"search index={index} sourcetype=access_combined"
        return self.search_logs(query, hours=hours)

    def get_application_logs(
        self, application: str, index: str = "main", hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get application-specific logs"""
        query = f"search index={index} app={application}"
        return self.search_logs(query, hours=hours)

    def get_metrics(self, query: str, hours: int = 1) -> List[Dict[str, Any]]:
        """
        Get metrics from Splunk using stats commands

        Args:
            query: Splunk query with stats commands
            hours: Number of hours to look back

        Returns:
            List of metric data points
        """
        # Add time range and stats to query
        time_range = f"earliest=-{hours}h latest=now"
        full_query = f"{query} | stats count by _time"

        data = {"search": full_query, "exec_mode": "oneshot", "output_mode": "json"}

        response = self._make_request("POST", "/services/search/jobs/export", data=data)

        if response and "results" in response:
            return response["results"]
        else:
            return []

    def get_request_count_metrics(
        self, index: str = "main", hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get request count metrics"""
        query = f"search index={index} sourcetype=access_combined"
        return self.get_metrics(query, hours=hours)

    def get_response_time_metrics(
        self, index: str = "main", hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get response time metrics"""
        query = (
            f"search index={index} sourcetype=access_combined | stats avg(response_time) by _time"
        )
        return self.get_metrics(query, hours=hours)

    def get_error_rate_metrics(self, index: str = "main", hours: int = 1) -> List[Dict[str, Any]]:
        """Get error rate metrics"""
        query = f"search index={index} | stats count(eval(status>=400)) as errors, count as total by _time"
        return self.get_metrics(query, hours=hours)

    def send_log_event(self, index: str, sourcetype: str, event: Dict[str, Any]) -> bool:
        """
        Send log event to Splunk

        Args:
            index: Splunk index name
            sourcetype: Source type for the event
            event: Event data to send

        Returns:
            True if successful, False otherwise
        """
        if not self.session:
            if not self._authenticate():
                return False

        try:
            # Convert event to JSON string
            import json

            event_data = json.dumps(event)

            # Prepare the request
            url = f"{self.base_url}/services/receivers/simple"
            params = {"index": index, "sourcetype": sourcetype}

            response = self.session.post(url, params=params, data=event_data, timeout=30)
            response.raise_for_status()

            self.logger.info(f"Log event sent to Splunk index {index}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send log event to Splunk: {e}")
            return False

    def get_index_list(self) -> List[Dict[str, Any]]:
        """Get list of available indexes"""
        response = self._make_request("GET", "/services/data/indexes")

        if response and "entry" in response:
            return response["entry"]

        return []

    def get_sourcetype_list(self) -> List[Dict[str, Any]]:
        """Get list of available sourcetypes"""
        response = self._make_request("GET", "/services/saved/searches")

        if response and "entry" in response:
            return response["entry"]

        return []

    def test_connection(self) -> bool:
        """Test Splunk connection"""
        try:
            # Try to get index list to test connection
            response = self._make_request("GET", "/services/data/indexes")
            return response is not None
        except Exception as e:
            self.logger.error(f"Splunk connection test failed: {e}")
            return False

    def get_server_info(self) -> Dict[str, Any]:
        """Get Splunk server information"""
        response = self._make_request("GET", "/services/server/info")

        if response and "entry" in response:
            return response["entry"][0]["content"]

        return {}

    def create_saved_search(
        self, name: str, query: str, cron_schedule: Optional[str] = None
    ) -> bool:
        """
        Create a saved search in Splunk

        Args:
            name: Name of the saved search
            query: Search query
            cron_schedule: Optional cron schedule for the search

        Returns:
            True if successful, False otherwise
        """
        data = {"name": name, "search": query, "enableSched": "1" if cron_schedule else "0"}

        if cron_schedule:
            data["cron_schedule"] = cron_schedule

        response = self._make_request("POST", "/services/saved/searches", data=data)

        if response:
            self.logger.info(f"Saved search '{name}' created successfully")
            return True
        else:
            self.logger.error(f"Failed to create saved search '{name}'")
            return False
