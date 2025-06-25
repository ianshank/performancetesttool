"""
CSV export functionality for NLM tool
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from utils.logger import get_logger


class CSVExporter:
    """Export test results and metrics to CSV format"""

    def __init__(self):
        self.logger = get_logger("nlm.exporter")

    def export_test_results(self, results: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Export test results to CSV

        Args:
            results: List of test result dictionaries
            output_path: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            if not results:
                self.logger.warning("No results to export")
                return False

            # Convert to DataFrame
            df = pd.DataFrame(results)

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Export to CSV
            df.to_csv(output_path, index=False)

            self.logger.info(f"Test results exported to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export test results: {e}")
            return False

    def export_summary_report(self, summary: Dict[str, Any], output_path: str) -> bool:
        """
        Export test summary to CSV

        Args:
            summary: Test summary dictionary
            output_path: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Flatten summary data
            flat_data = self._flatten_summary(summary)

            # Create DataFrame
            df = pd.DataFrame([flat_data])

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Export to CSV
            df.to_csv(output_path, index=False)

            self.logger.info(f"Summary report exported to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export summary report: {e}")
            return False

    def export_metrics(self, metrics: Dict[str, Any], output_path: str) -> bool:
        """
        Export metrics to CSV

        Args:
            metrics: Metrics dictionary
            output_path: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert metrics to DataFrame format
            metrics_data = []

            for metric_name, metric_values in metrics.items():
                if isinstance(metric_values, list):
                    for value in metric_values:
                        if isinstance(value, dict):
                            value["metric_name"] = metric_name
                            metrics_data.append(value)
                        else:
                            metrics_data.append({"metric_name": metric_name, "value": value})
                else:
                    metrics_data.append({"metric_name": metric_name, "value": metric_values})

            if not metrics_data:
                self.logger.warning("No metrics to export")
                return False

            # Create DataFrame
            df = pd.DataFrame(metrics_data)

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Export to CSV
            df.to_csv(output_path, index=False)

            self.logger.info(f"Metrics exported to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return False

    def export_ai_analysis(self, analysis: Dict[str, Any], output_path: str) -> bool:
        """
        Export AI analysis results to CSV

        Args:
            analysis: AI analysis results
            output_path: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Flatten analysis data
            flat_data = self._flatten_analysis(analysis)

            # Create DataFrame
            df = pd.DataFrame([flat_data])

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Export to CSV
            df.to_csv(output_path, index=False)

            self.logger.info(f"AI analysis exported to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export AI analysis: {e}")
            return False

    def _flatten_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten summary dictionary for CSV export"""
        flat_data = {}

        for key, value in summary.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_data[f"{key}_{sub_key}"] = sub_value
            elif isinstance(value, list):
                flat_data[key] = "; ".join(str(item) for item in value)
            else:
                flat_data[key] = value

        return flat_data

    def _flatten_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten AI analysis dictionary for CSV export"""
        flat_data = {}

        # Extract key fields
        flat_data["summary"] = analysis.get("summary", "")
        flat_data["llm_provider"] = analysis.get("llm_provider", "")
        flat_data["timestamp"] = analysis.get("timestamp", "")

        # Performance analysis
        perf_analysis = analysis.get("performance_analysis", {})
        flat_data["response_time_assessment"] = perf_analysis.get("response_time_assessment", "")
        flat_data["throughput_assessment"] = perf_analysis.get("throughput_assessment", "")
        flat_data["error_analysis"] = perf_analysis.get("error_analysis", "")

        # Bottlenecks and recommendations
        bottlenecks = perf_analysis.get("bottlenecks", [])
        flat_data["bottlenecks"] = "; ".join(bottlenecks)

        recommendations = perf_analysis.get("recommendations", [])
        flat_data["recommendations"] = "; ".join(recommendations)

        # Key findings
        key_findings = analysis.get("key_findings", [])
        flat_data["key_findings"] = "; ".join(key_findings)

        # Risk assessment
        risk_assessment = analysis.get("risk_assessment", {})
        flat_data["risk_severity"] = risk_assessment.get("severity", "")
        flat_data["risk_description"] = risk_assessment.get("description", "")

        # Next steps
        next_steps = analysis.get("next_steps", [])
        flat_data["next_steps"] = "; ".join(next_steps)

        return flat_data

    def create_comprehensive_report(
        self,
        test_results: List[Dict[str, Any]],
        summary: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None,
        ai_analysis: Optional[Dict[str, Any]] = None,
        output_dir: str = "reports",
    ) -> str:
        """
        Create a comprehensive report with multiple CSV files

        Args:
            test_results: Raw test results
            summary: Test summary
            metrics: Optional metrics data
            ai_analysis: Optional AI analysis results
            output_dir: Output directory for reports

        Returns:
            Path to the main report file
        """
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate timestamp for file names
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_name = summary.get("test_name", "test").replace(" ", "_").lower()

            # Export test results
            results_file = output_path / f"{test_name}_results_{timestamp}.csv"
            self.export_test_results(test_results, str(results_file))

            # Export summary
            summary_file = output_path / f"{test_name}_summary_{timestamp}.csv"
            self.export_summary_report(summary, str(summary_file))

            # Export metrics if available
            if metrics:
                metrics_file = output_path / f"{test_name}_metrics_{timestamp}.csv"
                self.export_metrics(metrics, str(metrics_file))

            # Export AI analysis if available
            if ai_analysis:
                analysis_file = output_path / f"{test_name}_analysis_{timestamp}.csv"
                self.export_ai_analysis(ai_analysis, str(analysis_file))

            # Create a master report file
            master_file = output_path / f"{test_name}_comprehensive_report_{timestamp}.csv"
            self._create_master_report(summary, metrics, ai_analysis, str(master_file))

            self.logger.info(f"Comprehensive report created in {output_dir}")
            return str(master_file)

        except Exception as e:
            self.logger.error(f"Failed to create comprehensive report: {e}")
            return ""

    def _create_master_report(
        self,
        summary: Dict[str, Any],
        metrics: Optional[Dict[str, Any]],
        ai_analysis: Optional[Dict[str, Any]],
        output_path: str,
    ) -> bool:
        """Create a master report combining all data"""
        try:
            # Combine all data into a single record
            master_data = {}

            # Add summary data
            master_data.update(self._flatten_summary(summary))

            # Add metrics summary
            if metrics:
                for metric_name, metric_values in metrics.items():
                    if isinstance(metric_values, list) and metric_values:
                        # Calculate average for numeric metrics
                        try:
                            avg_value = sum(
                                float(v) for v in metric_values if isinstance(v, (int, float))
                            ) / len(metric_values)
                            master_data[f"avg_{metric_name}"] = avg_value
                        except:
                            master_data[f"metric_{metric_name}"] = str(
                                metric_values[:5]
                            )  # First 5 values

            # Add AI analysis summary
            if ai_analysis:
                master_data.update(self._flatten_analysis(ai_analysis))

            # Create DataFrame and export
            df = pd.DataFrame([master_data])
            df.to_csv(output_path, index=False)

            return True

        except Exception as e:
            self.logger.error(f"Failed to create master report: {e}")
            return False

    def export_results(
        self, results: List[Dict[str, Any]], summary: Dict[str, Any], filename: str = ""
    ) -> str:
        """Export test results to CSV with enhanced metrics"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.csv"

        # Use reports directory as default
        output_dir = "reports"
        filepath = os.path.join(output_dir, filename)

        # Create export directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "timestamp",
                "user_id",
                "method",
                "url",
                "status_code",
                "response_time",
                "success",
                "error",
                "request_size",
                "response_size",
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow(
                    {
                        "timestamp": result.get("timestamp", ""),
                        "user_id": result.get("user_id", ""),
                        "method": result.get("method", ""),
                        "url": result.get("url", ""),
                        "status_code": result.get("status_code", ""),
                        "response_time": result.get("response_time", ""),
                        "success": result.get("success", False),
                        "error": result.get("error", ""),
                        "request_size": result.get("request_size", ""),
                        "response_size": result.get("response_size", ""),
                    }
                )

        # Create a summary CSV with detailed metrics
        summary_filename = filename.replace(".csv", "_summary.csv")
        summary_filepath = os.path.join(output_dir, summary_filename)

        with open(summary_filepath, "w", newline="", encoding="utf-8") as csvfile:
            # Write overall summary
            writer = csv.writer(csvfile)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Requests", summary.get("total_requests", 0)])
            writer.writerow(["Successful Requests", summary.get("successful_requests", 0)])
            writer.writerow(["Failed Requests", summary.get("failed_requests", 0)])
            writer.writerow(["Success Rate", f"{summary.get('success_rate', 0):.2%}"])
            writer.writerow(
                ["Average Response Time", f"{summary.get('avg_response_time', 0):.3f}s"]
            )
            writer.writerow(["Min Response Time", f"{summary.get('min_response_time', 0):.3f}s"])
            writer.writerow(["Max Response Time", f"{summary.get('max_response_time', 0):.3f}s"])
            writer.writerow(["Throughput", f"{summary.get('throughput', 0):.2f} req/s"])
            writer.writerow(["Test Duration", f"{summary.get('test_duration', 0):.2f}s"])
            writer.writerow(["Requests/Second", f"{summary.get('requests_per_second', 0):.2f}"])

            # Write percentiles
            percentiles = summary.get("percentiles", {})
            if percentiles:
                writer.writerow([])
                writer.writerow(["Percentiles"])
                writer.writerow(["Percentile", "Response Time (s)"])
                for p, value in percentiles.items():
                    writer.writerow([p, f"{value:.3f}"])

            # Write response time distribution
            response_time_distribution = summary.get("response_time_distribution", {})
            if response_time_distribution:
                writer.writerow([])
                writer.writerow(["Response Time Distribution"])
                writer.writerow(["Category", "Count", "Percentage"])
                dist = response_time_distribution.get("distribution_percentages", {})
                buckets = response_time_distribution.get("buckets", {})
                for category in ["very_fast", "fast", "moderate", "slow", "very_slow"]:
                    count = buckets.get(category, 0)
                    percentage = dist.get(category, 0)
                    writer.writerow([category, count, f"{percentage:.1f}%"])

            # Write error analysis
            error_analysis = summary.get("error_analysis", {})
            if error_analysis:
                writer.writerow([])
                writer.writerow(["Error Analysis"])
                writer.writerow(["Error Count", error_analysis.get("error_count", 0)])
                writer.writerow(["Error Rate", f"{error_analysis.get('error_rate', 0):.2%}"])

                # Write status codes
                status_codes = error_analysis.get("status_codes", {})
                if status_codes:
                    writer.writerow([])
                    writer.writerow(["Status Code Distribution"])
                    writer.writerow(["Status Code", "Count"])
                    for status, count in status_codes.items():
                        writer.writerow([status, count])

                # Write common errors
                common_errors = error_analysis.get("common_errors", [])
                if common_errors:
                    writer.writerow([])
                    writer.writerow(["Most Common Errors"])
                    writer.writerow(["Error", "Count"])
                    for error, count in common_errors:
                        writer.writerow([error, count])

            # Write performance insights
            performance_insights = summary.get("performance_insights", {})
            if performance_insights:
                writer.writerow([])
                writer.writerow(["Performance Insights"])
                writer.writerow(
                    ["Overall Assessment", performance_insights.get("overall_assessment", "N/A")]
                )

                strengths = performance_insights.get("strengths", [])
                if strengths:
                    writer.writerow([])
                    writer.writerow(["Strengths"])
                    for strength in strengths:
                        writer.writerow([strength])

                concerns = performance_insights.get("concerns", [])
                if concerns:
                    writer.writerow([])
                    writer.writerow(["Concerns"])
                    for concern in concerns:
                        writer.writerow([concern])

                recommendations = performance_insights.get("recommendations", [])
                if recommendations:
                    writer.writerow([])
                    writer.writerow(["Recommendations"])
                    for rec in recommendations:
                        writer.writerow([rec])

            # Write target breakdown
            target_breakdown = summary.get("target_breakdown", {})
            if target_breakdown:
                writer.writerow([])
                writer.writerow(["Target Performance Breakdown"])
                writer.writerow(
                    [
                        "Target",
                        "Total Requests",
                        "Success Rate",
                        "Avg Response Time (s)",
                        "Min Response Time (s)",
                        "Max Response Time (s)",
                    ]
                )
                for target, stats in target_breakdown.items():
                    writer.writerow(
                        [
                            target,
                            stats.get("total_requests", 0),
                            f"{stats.get('success_rate', 0):.2%}",
                            f"{stats.get('avg_response_time', 0):.3f}",
                            f"{stats.get('min_response_time', 0):.3f}",
                            f"{stats.get('max_response_time', 0):.3f}",
                        ]
                    )

            # Write user breakdown
            user_breakdown = summary.get("user_breakdown", {})
            if user_breakdown:
                writer.writerow([])
                writer.writerow(["User Performance Breakdown"])
                writer.writerow(
                    [
                        "User ID",
                        "Total Requests",
                        "Success Rate",
                        "Avg Response Time (s)",
                        "Min Response Time (s)",
                        "Max Response Time (s)",
                    ]
                )
                for user_id, stats in user_breakdown.items():
                    writer.writerow(
                        [
                            user_id,
                            stats.get("total_requests", 0),
                            f"{stats.get('success_rate', 0):.2%}",
                            f"{stats.get('avg_response_time', 0):.3f}",
                            f"{stats.get('min_response_time', 0):.3f}",
                            f"{stats.get('max_response_time', 0):.3f}",
                        ]
                    )

            # Write time series analysis
            time_series_analysis = summary.get("time_series_analysis", {})
            if time_series_analysis:
                time_buckets = time_series_analysis.get("time_buckets", [])
                if time_buckets:
                    writer.writerow([])
                    writer.writerow(["Time Series Analysis"])
                    writer.writerow(
                        ["Timestamp", "Requests", "Success Rate", "Avg Response Time (s)"]
                    )
                    for bucket in time_buckets:
                        writer.writerow(
                            [
                                bucket.get("timestamp", ""),
                                bucket.get("requests", 0),
                                f"{bucket.get('success_rate', 0):.2%}",
                                f"{bucket.get('avg_response_time', 0):.3f}",
                            ]
                        )

                trend_analysis = time_series_analysis.get("trend_analysis", {})
                if trend_analysis:
                    writer.writerow([])
                    writer.writerow(["Trend Analysis"])
                    writer.writerow(["Metric", "Value"])
                    writer.writerow(
                        ["Response Time Trend", trend_analysis.get("response_time_trend", "N/A")]
                    )
                    writer.writerow(
                        ["Success Rate Trend", trend_analysis.get("success_rate_trend", "N/A")]
                    )
                    writer.writerow(
                        [
                            "Performance Degradation",
                            "Yes" if trend_analysis.get("performance_degradation") else "No",
                        ]
                    )
                    writer.writerow(
                        ["Stability Score", f"{trend_analysis.get('stability_score', 0):.2f}"]
                    )

        self.logger.info(f"Exported detailed results to {filepath}")
        self.logger.info(f"Exported summary to {summary_filepath}")

        return filepath
