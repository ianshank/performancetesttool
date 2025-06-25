"""
Core test engine for NLM tool
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import aiohttp

from utils.config import ConfigManager
from utils.logger import get_logger


class LoadTestEngine:
    """Core engine for executing load tests"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = get_logger("nlm.engine")
        self.running = False
        self.results = []

    def _get_default_port(self, db_type: str) -> int:
        """Get default port for database type"""
        default_ports = {
            "postgresql": 5432,
            "mysql": 3306,
            "mongodb": 27017,
            "sqlite": 0,  # SQLite doesn't use a port
            "redis": 6379,
            "elasticsearch": 9200,
        }
        return default_ports.get(db_type.lower(), 5432)

    def _simulate_database_query(self, db_type: str, query: str) -> float:
        """Simulate database query time based on type and complexity"""
        # Base query times for different database types
        base_times = {
            "postgresql": 0.05,
            "mysql": 0.08,
            "mongodb": 0.03,
            "sqlite": 0.02,
            "redis": 0.01,
            "elasticsearch": 0.1,
        }

        base_time = base_times.get(db_type.lower(), 0.05)

        # Add complexity based on query type
        query_lower = query.lower()
        if "select" in query_lower:
            if "count" in query_lower or "sum" in query_lower or "avg" in query_lower:
                base_time *= 1.5  # Aggregation queries take longer
            elif "join" in query_lower:
                base_time *= 2.0  # Join queries take longer
        elif "insert" in query_lower or "update" in query_lower:
            base_time *= 1.2  # Write operations take longer
        elif "delete" in query_lower:
            base_time *= 1.3  # Delete operations take longer

        # Add some randomness to simulate real-world conditions
        import random

        return base_time * random.uniform(0.8, 1.2)

    def _get_mq_default_port(self, mq_type: str) -> int:
        """Get default port for message queue type"""
        default_ports = {
            "rabbitmq": 5672,
            "kafka": 9092,
            "redis": 6379,
            "activemq": 61616,
            "sqs": 0,  # AWS SQS doesn't use a port
            "pubsub": 0,  # Google Pub/Sub doesn't use a port
        }
        return default_ports.get(mq_type.lower(), 5672)

    def _simulate_mq_operation(self, mq_type: str) -> float:
        """Simulate message queue operation time based on type"""
        # Base operation times for different message queue types
        base_times = {
            "rabbitmq": 0.02,
            "kafka": 0.01,
            "redis": 0.005,
            "activemq": 0.03,
            "sqs": 0.05,  # AWS SQS has higher latency
            "pubsub": 0.04,  # Google Pub/Sub has higher latency
        }

        base_time = base_times.get(mq_type.lower(), 0.02)

        # Add some randomness to simulate real-world conditions
        import random

        return base_time * random.uniform(0.8, 1.2)

    async def execute_http_test(
        self, target: Dict[str, Any], load_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute HTTP load test"""
        # Validate required HTTP configuration
        if not target.get("url"):
            raise ValueError("HTTP target must have a URL")

        method = target.get("method", "GET").upper()
        url = target["url"]
        headers = target.get("headers", {})
        expected_status = target.get("expected_status", 200)

        self.logger.info(f"Starting HTTP test for {method} {url}")
        self.logger.info(f"Expected status: {expected_status}, Headers: {headers}")

        results = []
        start_time = time.time()

        # Get thread configuration
        threads = load_profile.get("threads", 4)  # Default to 4 threads if not specified
        users = load_profile.get("users", 10)

        self.logger.info(f"Using {threads} threads for {users} users")

        # Create session for connection pooling with custom configuration
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)

        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector, headers=headers
        ) as session:
            # Create tasks for concurrent requests with thread control
            tasks = []

            # Distribute users across threads
            users_per_thread = max(1, users // threads)
            remaining_users = users % threads

            user_id = 0
            for thread_id in range(threads):
                # Calculate users for this thread
                thread_users = users_per_thread + (1 if thread_id < remaining_users else 0)

                if thread_users > 0:
                    # Create tasks for users in this thread
                    for i in range(thread_users):
                        task = self._http_user_task(session, target, user_id, load_profile)
                        tasks.append(task)
                        user_id += 1

            # Execute all tasks with controlled concurrency
            user_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten results
            for user_result in user_results:
                if isinstance(user_result, list):
                    results.extend(user_result)
                elif isinstance(user_result, Exception):
                    self.logger.error(f"User task failed: {user_result}")

        duration = time.time() - start_time
        self.logger.info(f"HTTP test completed in {duration:.2f} seconds using {threads} threads")

        return results

    async def _http_user_task(
        self,
        session: aiohttp.ClientSession,
        target: Dict[str, Any],
        user_id: int,
        load_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Execute requests for a single user"""
        results = []

        # Get configuration parameters
        method = target.get("method", "GET").upper()
        url = target["url"]
        headers = target.get("headers", {})
        expected_status = target.get("expected_status", 200)

        # Calculate request timing
        total_requests = load_profile["duration"] // load_profile["think_time"]
        ramp_up_requests = load_profile["ramp_up"] // load_profile["think_time"]

        for request_id in range(total_requests):
            if not self.running:
                break

            # Ramp-up delay
            if request_id < ramp_up_requests:
                delay = (request_id + 1) * (load_profile["ramp_up"] / ramp_up_requests)
                await asyncio.sleep(delay)

            # Execute request
            start_time = time.time()
            try:
                # Use the configured method and headers
                async with session.request(
                    method=method, url=url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = time.time() - start_time

                    # Read response content for validation
                    try:
                        response_text = await response.text()
                        response_size = len(response_text.encode("utf-8"))
                    except:
                        response_text = ""
                        response_size = 0

                    # Check if response matches expected status
                    success = response.status == expected_status

                    result = {
                        "timestamp": start_time,
                        "user_id": user_id,
                        "request_id": request_id,
                        "method": method,
                        "url": url,
                        "status_code": response.status,
                        "expected_status": expected_status,
                        "response_time": response_time,
                        "response_size": response_size,
                        "success": success,
                        "error": (
                            None
                            if success
                            else f"Expected {expected_status}, got {response.status}"
                        ),
                    }

                    results.append(result)

            except asyncio.TimeoutError:
                response_time = time.time() - start_time
                result = {
                    "timestamp": start_time,
                    "user_id": user_id,
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": None,
                    "expected_status": expected_status,
                    "response_time": response_time,
                    "response_size": 0,
                    "success": False,
                    "error": "Request timeout",
                }
                results.append(result)

            except Exception as e:
                response_time = time.time() - start_time
                result = {
                    "timestamp": start_time,
                    "user_id": user_id,
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": None,
                    "expected_status": expected_status,
                    "response_time": response_time,
                    "response_size": 0,
                    "success": False,
                    "error": str(e),
                }
                results.append(result)

            # Think time
            await asyncio.sleep(load_profile["think_time"])

        return results

    async def execute_database_test(
        self, target: Dict[str, Any], load_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute database load test"""
        # Validate required database configuration
        if not target.get("db_type"):
            raise ValueError("Database target must have a db_type")
        if not target.get("host"):
            raise ValueError("Database target must have a host")

        db_type = target["db_type"]
        host = target["host"]
        port = target.get("port", self._get_default_port(db_type))
        database = target.get("database", "test")
        query = target.get("query", "SELECT 1")

        self.logger.info(f"Starting database test for {db_type} at {host}:{port}")
        self.logger.info(f"Database: {database}, Query: {query}")

        # Get thread configuration
        threads = load_profile.get("threads", 4)  # Default to 4 threads if not specified
        users = load_profile.get("users", 10)

        self.logger.info(f"Using {threads} threads for {users} users")

        # This is a placeholder - actual database testing would require
        # specific database drivers and connection pooling
        results = []

        # Create tasks for concurrent database operations
        tasks = []

        # Distribute users across threads
        users_per_thread = max(1, users // threads)
        remaining_users = users % threads

        user_id = 0
        for thread_id in range(threads):
            # Calculate users for this thread
            thread_users = users_per_thread + (1 if thread_id < remaining_users else 0)

            if thread_users > 0:
                # Create tasks for users in this thread
                for i in range(thread_users):
                    task = self._database_user_task(target, user_id, load_profile)
                    tasks.append(task)
                    user_id += 1

        # Execute all tasks with controlled concurrency
        user_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        for user_result in user_results:
            if isinstance(user_result, list):
                results.extend(user_result)
            elif isinstance(user_result, Exception):
                self.logger.error(f"Database user task failed: {user_result}")

        self.logger.info(f"Database test completed using {threads} threads")
        return results

    async def _database_user_task(
        self, target: Dict[str, Any], user_id: int, load_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute database operations for a single user"""
        results = []

        # Get configuration parameters
        db_type = target["db_type"]
        host = target["host"]
        port = target.get("port", self._get_default_port(db_type))
        database = target.get("database", "test")
        query = target.get("query", "SELECT 1")

        # Calculate request timing
        total_requests = load_profile["duration"] // load_profile["think_time"]
        ramp_up_requests = load_profile["ramp_up"] // load_profile["think_time"]

        for request_id in range(total_requests):
            if not self.running:
                break

            # Ramp-up delay
            if request_id < ramp_up_requests:
                delay = (request_id + 1) * (load_profile["ramp_up"] / ramp_up_requests)
                await asyncio.sleep(delay)

            # Execute database operation
            start_time = time.time()
            try:
                # Simulate database query based on type
                query_time = self._simulate_database_query(db_type, query)
                await asyncio.sleep(query_time)

                response_time = time.time() - start_time

                result = {
                    "timestamp": start_time,
                    "user_id": user_id,
                    "request_id": request_id,
                    "db_type": db_type,
                    "host": host,
                    "port": port,
                    "database": database,
                    "query": query,
                    "response_time": response_time,
                    "success": True,
                    "error": None,
                }

                results.append(result)

            except Exception as e:
                response_time = time.time() - start_time
                result = {
                    "timestamp": start_time,
                    "user_id": user_id,
                    "request_id": request_id,
                    "db_type": db_type,
                    "host": host,
                    "port": port,
                    "database": database,
                    "query": query,
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                }
                results.append(result)

            # Think time
            await asyncio.sleep(load_profile["think_time"])

        return results

    async def execute_message_queue_test(
        self, target: Dict[str, Any], load_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute message queue load test"""
        # Validate required message queue configuration
        if not target.get("mq_type"):
            raise ValueError("Message queue target must have a mq_type")
        if not target.get("host"):
            raise ValueError("Message queue target must have a host")

        mq_type = target["mq_type"]
        host = target["host"]
        port = target.get("port", self._get_mq_default_port(mq_type))
        queue = target.get("queue", "test_queue")

        self.logger.info(f"Starting message queue test for {mq_type} at {host}:{port}")
        self.logger.info(f"Queue: {queue}")

        # Get thread configuration
        threads = load_profile.get("threads", 4)  # Default to 4 threads if not specified
        users = load_profile.get("users", 10)

        self.logger.info(f"Using {threads} threads for {users} users")

        # This is a placeholder - actual MQ testing would require
        # specific MQ drivers and connection management
        results = []

        # Create tasks for concurrent MQ operations
        tasks = []

        # Distribute users across threads
        users_per_thread = max(1, users // threads)
        remaining_users = users % threads

        user_id = 0
        for thread_id in range(threads):
            # Calculate users for this thread
            thread_users = users_per_thread + (1 if thread_id < remaining_users else 0)

            if thread_users > 0:
                # Create tasks for users in this thread
                for i in range(thread_users):
                    task = self._mq_user_task(target, user_id, load_profile)
                    tasks.append(task)
                    user_id += 1

        # Execute all tasks with controlled concurrency
        user_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        for user_result in user_results:
            if isinstance(user_result, list):
                results.extend(user_result)
            elif isinstance(user_result, Exception):
                self.logger.error(f"MQ user task failed: {user_result}")

        self.logger.info(f"Message queue test completed using {threads} threads")
        return results

    async def _mq_user_task(
        self, target: Dict[str, Any], user_id: int, load_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute message queue operations for a single user"""
        results = []

        # Get configuration parameters
        mq_type = target["mq_type"]
        host = target["host"]
        port = target.get("port", self._get_mq_default_port(mq_type))
        queue = target.get("queue", "test_queue")

        # Calculate request timing
        total_requests = load_profile["duration"] // load_profile["think_time"]
        ramp_up_requests = load_profile["ramp_up"] // load_profile["think_time"]

        for request_id in range(total_requests):
            if not self.running:
                break

            # Ramp-up delay
            if request_id < ramp_up_requests:
                delay = (request_id + 1) * (load_profile["ramp_up"] / ramp_up_requests)
                await asyncio.sleep(delay)

            # Execute message queue operation
            start_time = time.time()
            try:
                # Simulate message queue operation
                operation_time = self._simulate_mq_operation(mq_type)
                await asyncio.sleep(operation_time)

                response_time = time.time() - start_time

                result = {
                    "timestamp": start_time,
                    "user_id": user_id,
                    "request_id": request_id,
                    "mq_type": mq_type,
                    "host": host,
                    "port": port,
                    "queue": queue,
                    "operation": "send",  # Simulate send operation
                    "response_time": response_time,
                    "success": True,
                    "error": None,
                }

                results.append(result)

            except Exception as e:
                response_time = time.time() - start_time
                result = {
                    "timestamp": start_time,
                    "user_id": user_id,
                    "request_id": request_id,
                    "mq_type": mq_type,
                    "host": host,
                    "port": port,
                    "queue": queue,
                    "operation": "send",
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                }
                results.append(result)

            # Think time
            await asyncio.sleep(load_profile["think_time"])

        return results

    def stop(self):
        """Stop all running tests"""
        self.running = False
        self.logger.info("Test engine stopped")

    def get_results_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive summary statistics from test results"""
        if not results:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "throughput": 0.0,
                "errors": [],
                "percentiles": {},
                "response_time_distribution": {},
                "error_analysis": {},
                "performance_insights": {},
                "target_breakdown": {},
                "user_breakdown": {},
                "time_series_analysis": {},
            }

        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]

        response_times = [r.get("response_time", 0) for r in results if r.get("response_time")]

        # Calculate duration and timing
        timestamps = [r.get("timestamp", 0) for r in results if r.get("timestamp")]
        duration = max(timestamps) - min(timestamps) if timestamps else 0

        # Collect errors
        errors = list(set([r.get("error") for r in failed if r.get("error")]))

        # Calculate success rate
        success_rate = len(successful) / len(results) if results else 0.0

        # Calculate percentiles
        percentiles = self._calculate_percentiles(response_times)
        percentiles = {k: round(v, 4) for k, v in percentiles.items()}

        # Response time distribution
        response_time_distribution = self._analyze_response_time_distribution(response_times)

        # Error analysis
        error_analysis = self._analyze_errors(failed, len(results))

        # Performance insights
        performance_insights = self._generate_performance_insights(
            response_times, success_rate, duration, len(results)
        )

        # Target breakdown
        target_breakdown = self._analyze_target_performance(results)

        # User breakdown
        user_breakdown = self._analyze_user_performance(results)

        # Time series analysis
        time_series_analysis = self._analyze_time_series(results)

        return {
            "total_requests": len(results),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": round(success_rate, 4),
            "avg_response_time": (
                round(sum(response_times) / len(response_times), 4) if response_times else 0.0
            ),
            "min_response_time": round(min(response_times), 4) if response_times else 0.0,
            "max_response_time": round(max(response_times), 4) if response_times else 0.0,
            "throughput": round(len(results) / duration, 4) if duration > 0 else 0.0,
            "errors": errors,
            "percentiles": percentiles,
            "response_time_distribution": response_time_distribution,
            "error_analysis": error_analysis,
            "performance_insights": performance_insights,
            "target_breakdown": target_breakdown,
            "user_breakdown": user_breakdown,
            "time_series_analysis": time_series_analysis,
            "test_duration": duration,
            "requests_per_second": round(len(results) / duration, 4) if duration > 0 else 0.0,
        }

    def _calculate_percentiles(self, response_times: List[float]) -> Dict[str, float]:
        """Calculate response time percentiles"""
        if not response_times:
            return {}

        sorted_times = sorted(response_times)
        n = len(sorted_times)

        percentiles = {}
        for p in [50, 75, 90, 95, 99, 99.9]:
            index = int((p / 100) * (n - 1))
            percentiles[f"p{p}"] = sorted_times[index]

        return percentiles

    def _analyze_response_time_distribution(self, response_times: List[float]) -> Dict[str, Any]:
        """Analyze response time distribution"""
        if not response_times:
            return {}

        # Define buckets
        buckets = {
            "very_fast": 0,  # < 100ms
            "fast": 0,  # 100-500ms
            "moderate": 0,  # 500ms-1s
            "slow": 0,  # 1-3s
            "very_slow": 0,  # > 3s
        }

        for rt in response_times:
            if rt < 0.1:
                buckets["very_fast"] += 1
            elif rt < 0.5:
                buckets["fast"] += 1
            elif rt < 1.0:
                buckets["moderate"] += 1
            elif rt < 3.0:
                buckets["slow"] += 1
            else:
                buckets["very_slow"] += 1

        # Calculate percentages
        total = len(response_times)
        distribution = {k: (v / total * 100) for k, v in buckets.items()}

        return {
            "buckets": buckets,
            "distribution_percentages": distribution,
            "total_requests": total,
        }

    def _analyze_errors(
        self, failed_requests: List[Dict[str, Any]], total_requests: int
    ) -> Dict[str, Any]:
        """Analyze error patterns"""
        if not failed_requests:
            return {
                "error_count": 0,
                "error_types": {},
                "common_errors": [],
                "error_rate": 0.0,
                "status_codes": {},
            }

        error_types = {}
        status_codes = {}

        for req in failed_requests:
            # Count by error type
            error = req.get("error", "Unknown")
            error_types[error] = error_types.get(error, 0) + 1

            # Count by status code
            status_code = req.get("status_code", "Unknown")
            status_codes[str(status_code)] = status_codes.get(str(status_code), 0) + 1

        # Find most common errors
        common_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]

        error_rate = len(failed_requests) / total_requests if total_requests > 0 else 0.0

        return {
            "error_count": len(failed_requests),
            "error_types": error_types,
            "status_codes": status_codes,
            "common_errors": common_errors,
            "error_rate": error_rate,
        }

    def _generate_performance_insights(
        self, response_times: List[float], success_rate: float, duration: float, total_requests: int
    ) -> Dict[str, Any]:
        """Generate performance insights and recommendations"""
        insights = {
            "overall_assessment": "",
            "strengths": [],
            "concerns": [],
            "recommendations": [],
        }

        if not response_times:
            return insights

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        throughput = total_requests / duration if duration > 0 else 0

        # Overall assessment
        if success_rate >= 0.99 and avg_response_time < 0.5 and throughput > 10:
            insights["overall_assessment"] = "Excellent"
        elif success_rate >= 0.95 and avg_response_time < 1.0 and throughput > 5:
            insights["overall_assessment"] = "Good"
        elif success_rate >= 0.90 and avg_response_time < 2.0:
            insights["overall_assessment"] = "Acceptable"
        else:
            insights["overall_assessment"] = "Poor"

        # Strengths
        if success_rate >= 0.95:
            insights["strengths"].append(f"High reliability ({success_rate:.1%} success rate)")
        if avg_response_time < 0.5:
            insights["strengths"].append(f"Fast response times ({avg_response_time:.3f}s average)")
        if throughput > 10:
            insights["strengths"].append(f"High throughput ({throughput:.1f} req/s)")

        # Concerns
        if success_rate < 0.95:
            insights["concerns"].append(f"Low reliability ({success_rate:.1%} success rate)")
        if avg_response_time > 1.0:
            insights["concerns"].append(f"Slow response times ({avg_response_time:.3f}s average)")
        if max_response_time > 5.0:
            insights["concerns"].append(
                f"Very slow outliers detected ({max_response_time:.3f}s max)"
            )
        if throughput < 5:
            insights["concerns"].append(f"Low throughput ({throughput:.1f} req/s)")

        # Recommendations
        if success_rate < 0.95:
            insights["recommendations"].append("Investigate and fix error patterns")
        if avg_response_time > 1.0:
            insights["recommendations"].append(
                "Optimize response times through caching or database tuning"
            )
        if max_response_time > 5.0:
            insights["recommendations"].append("Investigate slow response outliers")
        if throughput < 5:
            insights["recommendations"].append(
                "Consider horizontal scaling or performance optimization"
            )

        return insights

    def _analyze_target_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by target/endpoint"""
        target_stats = {}

        for result in results:
            target_key = f"{result.get('method', 'UNKNOWN')} {result.get('url', 'unknown')}"

            if target_key not in target_stats:
                target_stats[target_key] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "response_times": [],
                    "errors": [],
                }

            target_stats[target_key]["total_requests"] += 1

            if result.get("success", False):
                target_stats[target_key]["successful_requests"] += 1
            else:
                target_stats[target_key]["failed_requests"] += 1
                if result.get("error"):
                    target_stats[target_key]["errors"].append(result["error"])

            if result.get("response_time"):
                target_stats[target_key]["response_times"].append(result["response_time"])

        # Calculate metrics for each target
        for target, stats in target_stats.items():
            response_times = stats["response_times"]
            if response_times:
                stats["avg_response_time"] = sum(response_times) / len(response_times)
                stats["min_response_time"] = min(response_times)
                stats["max_response_time"] = max(response_times)
                stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            else:
                stats["avg_response_time"] = 0
                stats["min_response_time"] = 0
                stats["max_response_time"] = 0
                stats["success_rate"] = 0

        return target_stats

    def _analyze_user_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by user"""
        user_stats = {}

        for result in results:
            user_id = result.get("user_id", "unknown")

            if user_id not in user_stats:
                user_stats[user_id] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "response_times": [],
                    "errors": [],
                }

            user_stats[user_id]["total_requests"] += 1

            if result.get("success", False):
                user_stats[user_id]["successful_requests"] += 1
            else:
                user_stats[user_id]["failed_requests"] += 1
                if result.get("error"):
                    user_stats[user_id]["errors"].append(result["error"])

            if result.get("response_time"):
                user_stats[user_id]["response_times"].append(result["response_time"])

        # Calculate metrics for each user
        for user_id, stats in user_stats.items():
            response_times = stats["response_times"]
            if response_times:
                stats["avg_response_time"] = sum(response_times) / len(response_times)
                stats["min_response_time"] = min(response_times)
                stats["max_response_time"] = max(response_times)
                stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            else:
                stats["avg_response_time"] = 0
                stats["min_response_time"] = 0
                stats["max_response_time"] = 0
                stats["success_rate"] = 0

        return user_stats

    def _analyze_time_series(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance over time"""
        if not results:
            return {}

        # Sort by timestamp
        sorted_results = sorted(results, key=lambda x: x.get("timestamp", 0))

        # Group by minute
        time_buckets = {}
        for result in sorted_results:
            timestamp = result.get("timestamp", 0)
            minute = int(timestamp / 60) * 60  # Round to minute

            if minute not in time_buckets:
                time_buckets[minute] = {
                    "requests": 0,
                    "successful": 0,
                    "failed": 0,
                    "response_times": [],
                }

            time_buckets[minute]["requests"] += 1

            if result.get("success", False):
                time_buckets[minute]["successful"] += 1
            else:
                time_buckets[minute]["failed"] += 1

            if result.get("response_time"):
                time_buckets[minute]["response_times"].append(result["response_time"])

        # Calculate metrics for each time bucket
        time_series = []
        for minute, stats in sorted(time_buckets.items()):
            response_times = stats["response_times"]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            success_rate = stats["successful"] / stats["requests"] if stats["requests"] > 0 else 0

            time_series.append(
                {
                    "timestamp": minute,
                    "requests": stats["requests"],
                    "success_rate": success_rate,
                    "avg_response_time": avg_response_time,
                }
            )

        return {"time_buckets": time_series, "trend_analysis": self._analyze_trends(time_series)}

    def _analyze_trends(self, time_series: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in time series data"""
        if len(time_series) < 2:
            return {}

        # Calculate trends
        response_times = [point["avg_response_time"] for point in time_series]
        success_rates = [point["success_rate"] for point in time_series]

        # Simple linear trend calculation
        def calculate_trend(values):
            if len(values) < 2:
                return "stable"

            first_half = values[: len(values) // 2]
            second_half = values[len(values) // 2 :]

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            change = (second_avg - first_avg) / first_avg if first_avg > 0 else 0

            if change > 0.1:
                return "increasing"
            elif change < -0.1:
                return "decreasing"
            else:
                return "stable"

        return {
            "response_time_trend": calculate_trend(response_times),
            "success_rate_trend": calculate_trend(success_rates),
            "performance_degradation": any(rt > 2.0 for rt in response_times),
            "stability_score": (
                1.0 - (max(response_times) - min(response_times)) / max(response_times)
                if max(response_times) > 0
                else 1.0
            ),
        }
