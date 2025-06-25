"""
PyQt5 GUI interface for NLM tool
"""

import json
import sys
import threading
from typing import Any, Dict, Optional

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.test_runner import TestRunner
from utils.logger import get_logger


class TestWorkerThread(QThread):
    """Worker thread for running tests without blocking the GUI"""

    test_completed = pyqtSignal(dict)
    test_error = pyqtSignal(str)

    def __init__(self, test_runner: TestRunner, test_config: Dict[str, Any]):
        super().__init__()
        self.test_runner = test_runner
        self.test_config = test_config

    def run(self):
        """Run the test in the background"""
        try:
            results = self.test_runner.run_test(self.test_config)
            self.test_completed.emit(results)
        except Exception as e:
            self.test_error.emit(str(e))


class HTTPConfigDialog(QDialog):
    """Dialog for configuring HTTP request parameters"""

    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.initial_data = initial_data or {
            "url": "http://localhost:8080/health",
            "method": "GET",
            "headers": {},
            "expected_status": 200,
        }
        self.result_data = None
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Configure HTTP Request")
        self.setGeometry(200, 200, 500, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_edit = QLineEdit(self.initial_data["url"])
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        # Method
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH"])
        self.method_combo.setCurrentText(self.initial_data["method"])
        method_layout.addWidget(self.method_combo)
        layout.addLayout(method_layout)

        # Expected Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Expected Status:"))
        self.status_spin = QSpinBox()
        self.status_spin.setRange(100, 599)
        self.status_spin.setValue(self.initial_data["expected_status"])
        status_layout.addWidget(self.status_spin)
        layout.addLayout(status_layout)

        # Headers
        layout.addWidget(QLabel("Headers (JSON format):"))
        self.headers_edit = QTextEdit()
        self.headers_edit.setMaximumHeight(100)
        self.headers_edit.setPlainText("{}")
        layout.addWidget(self.headers_edit)

        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def accept(self):
        """Handle OK button click"""
        try:
            headers_text = self.headers_edit.toPlainText().strip()
            headers = json.loads(headers_text) if headers_text else {}

            self.result_data = {
                "url": self.url_edit.text(),
                "method": self.method_combo.currentText(),
                "headers": headers,
                "expected_status": self.status_spin.value(),
            }
            super().accept()
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Invalid JSON", "Please enter valid JSON for headers.")

    def reject(self):
        """Handle Cancel button click"""
        self.result_data = None
        super().reject()


class DatabaseConfigDialog(QDialog):
    """Dialog for configuring database request parameters"""

    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.initial_data = initial_data or {
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "query": "SELECT 1",
        }
        self.result_data = None
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Configure Database Query")
        self.setGeometry(200, 200, 500, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Database Type
        db_type_layout = QHBoxLayout()
        db_type_layout.addWidget(QLabel("Database Type:"))
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["postgresql", "mysql", "mongodb", "sqlite"])
        self.db_type_combo.setCurrentText(self.initial_data["db_type"])
        db_type_layout.addWidget(self.db_type_combo)
        layout.addLayout(db_type_layout)

        # Host
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Host:"))
        self.host_edit = QLineEdit(self.initial_data["host"])
        host_layout.addWidget(self.host_edit)
        layout.addLayout(host_layout)

        # Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(self.initial_data["port"])
        port_layout.addWidget(self.port_spin)
        layout.addLayout(port_layout)

        # Database Name
        db_name_layout = QHBoxLayout()
        db_name_layout.addWidget(QLabel("Database:"))
        self.db_name_edit = QLineEdit(self.initial_data["database"])
        db_name_layout.addWidget(self.db_name_edit)
        layout.addLayout(db_name_layout)

        # Query
        layout.addWidget(QLabel("Query:"))
        self.query_edit = QTextEdit()
        self.query_edit.setMaximumHeight(100)
        self.query_edit.setPlainText(self.initial_data["query"])
        layout.addWidget(self.query_edit)

        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def accept(self):
        """Handle OK button click"""
        self.result_data = {
            "db_type": self.db_type_combo.currentText(),
            "host": self.host_edit.text(),
            "port": self.port_spin.value(),
            "database": self.db_name_edit.text(),
            "query": self.query_edit.toPlainText(),
        }
        super().accept()

    def reject(self):
        """Handle Cancel button click"""
        self.result_data = None
        super().reject()


class GUIInterface(QMainWindow):
    """Main GUI window for the NLM tool"""

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger("nlm.gui")
        self.test_runner = TestRunner(config_manager)
        self.test_worker = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("NLM Performance Testing Tool v1.0.0")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Test Plan
        self.create_test_plan_panel(splitter)

        # Right panel - Results and Controls
        self.create_results_panel(splitter)

        # Set splitter proportions
        splitter.setSizes([400, 800])

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.statusBar().showMessage("Ready")

    def create_test_plan_panel(self, parent):
        """Create the test plan configuration panel"""
        test_plan_widget = QWidget()
        layout = QVBoxLayout(test_plan_widget)

        # Test Plan Tree
        test_plan_group = QGroupBox("Test Plan")
        test_plan_layout = QVBoxLayout(test_plan_group)

        self.test_tree = QTreeWidget()
        self.test_tree.setHeaderLabel("Test Elements")
        self.test_tree.setMinimumHeight(300)
        self.test_tree.itemDoubleClicked.connect(self.edit_test_element)
        test_plan_layout.addWidget(self.test_tree)

        # Add test elements buttons
        buttons_layout = QHBoxLayout()

        add_http_btn = QPushButton("Add HTTP Request")
        add_http_btn.clicked.connect(self.add_http_request)
        buttons_layout.addWidget(add_http_btn)

        add_db_btn = QPushButton("Add Database")
        add_db_btn.clicked.connect(self.add_database_request)
        buttons_layout.addWidget(add_db_btn)

        add_mq_btn = QPushButton("Add Message Queue")
        add_mq_btn.clicked.connect(self.add_message_queue)
        buttons_layout.addWidget(add_mq_btn)

        # Add remove button
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_test_element)
        remove_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        buttons_layout.addWidget(remove_btn)

        test_plan_layout.addLayout(buttons_layout)
        layout.addWidget(test_plan_group)

        # Test Configuration
        config_group = QGroupBox("Test Configuration")
        config_layout = QFormLayout(config_group)

        # Test name
        self.test_name_edit = QLineEdit("New Test")
        config_layout.addRow("Test Name:", self.test_name_edit)

        # Environment selection
        self.env_combo = QComboBox()
        self.env_combo.addItems(["dev", "qa", "stage", "prod"])
        self.env_combo.setCurrentText(self.config_manager.environment)
        self.env_combo.currentTextChanged.connect(self.on_environment_changed)
        config_layout.addRow("Environment:", self.env_combo)

        # Load profile
        self.users_spin = QSpinBox()
        self.users_spin.setRange(1, 1000)
        self.users_spin.setValue(10)
        config_layout.addRow("Users:", self.users_spin)

        # Threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 100)
        self.threads_spin.setValue(4)
        config_layout.addRow("Threads:", self.threads_spin)

        self.ramp_up_spin = QSpinBox()
        self.ramp_up_spin.setRange(1, 3600)
        self.ramp_up_spin.setValue(30)
        config_layout.addRow("Ramp-up (s):", self.ramp_up_spin)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(60)
        config_layout.addRow("Duration (s):", self.duration_spin)

        self.think_time_spin = QSpinBox()
        self.think_time_spin.setRange(0, 60)
        self.think_time_spin.setValue(1)
        config_layout.addRow("Think Time (s):", self.think_time_spin)

        layout.addWidget(config_group)

        # Control buttons
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Test")
        self.start_btn.clicked.connect(self.start_test)
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Test")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        control_layout.addWidget(self.stop_btn)

        layout.addLayout(control_layout)

        parent.addWidget(test_plan_widget)

    def create_results_panel(self, parent):
        """Create the results and monitoring panel"""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)

        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Results tab
        self.create_results_tab(tabs)

        # Monitoring tab
        self.create_monitoring_tab(tabs)

        # Logs tab
        self.create_logs_tab(tabs)

        parent.addWidget(results_widget)

    def create_results_tab(self, tabs):
        """Create the results display tab"""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)

        # Summary section
        summary_group = QGroupBox("Test Summary")
        summary_layout = QFormLayout(summary_group)

        self.summary_labels = {}
        for field in [
            "Test Name",
            "Duration",
            "Total Requests",
            "Successful",
            "Failed",
            "Avg Response Time",
            "Throughput",
        ]:
            label = QLabel("--")
            self.summary_labels[field] = label
            summary_layout.addRow(f"{field}:", label)

        layout.addWidget(summary_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(
            ["Timestamp", "User ID", "Request ID", "Status", "Response Time", "Error"]
        )
        layout.addWidget(self.results_table)

        tabs.addTab(results_widget, "Results")

    def create_monitoring_tab(self, tabs):
        """Create the monitoring tab"""
        monitoring_widget = QWidget()
        layout = QVBoxLayout(monitoring_widget)

        # Monitoring status
        status_group = QGroupBox("Monitoring Status")
        status_layout = QFormLayout(status_group)

        self.monitoring_labels = {}
        for service in ["AWS CloudWatch", "Datadog", "Splunk"]:
            label = QLabel("Not Connected")
            label.setStyleSheet("color: red;")
            self.monitoring_labels[service] = label
            status_layout.addRow(f"{service}:", label)

        layout.addWidget(status_group)

        # Metrics display area
        metrics_group = QGroupBox("Real-time Metrics")
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        metrics_group.setLayout(QVBoxLayout())
        metrics_group.layout().addWidget(self.metrics_text)
        layout.addWidget(metrics_group)

        tabs.addTab(monitoring_widget, "Monitoring")

    def create_logs_tab(self, tabs):
        """Create the logs display tab"""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)

        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)

        tabs.addTab(logs_widget, "Logs")

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = file_menu.addAction("New Test")
        new_action.triggered.connect(self.new_test)

        open_action = file_menu.addAction("Open Test")
        open_action.triggered.connect(self.open_test)

        save_action = file_menu.addAction("Save Test")
        save_action.triggered.connect(self.save_test)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        dashboard_action = tools_menu.addAction("Open Dashboard")
        dashboard_action.triggered.connect(self.open_dashboard)

        export_action = tools_menu.addAction("Export Results")
        export_action.triggered.connect(self.export_results)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def add_http_request(self):
        """Add HTTP request to test plan"""
        # Show configuration dialog first
        dialog = HTTPConfigDialog(self)
        dialog.show()

        # Wait for dialog to close
        dialog.exec_()

        if dialog.result_data:
            item = QTreeWidgetItem(self.test_tree)
            data = dialog.result_data
            data["type"] = "http"
            item.setData(0, Qt.ItemDataRole.UserRole, data)
            item.setText(0, f"HTTP Request - {data['method']} {data['url']}")
            self.logger.info(f"Added HTTP request: {data['method']} {data['url']}")

    def add_database_request(self):
        """Add database request to test plan"""
        # Show configuration dialog first
        dialog = DatabaseConfigDialog(self)
        dialog.show()

        # Wait for dialog to close
        dialog.exec_()

        if dialog.result_data:
            item = QTreeWidgetItem(self.test_tree)
            data = dialog.result_data
            data["type"] = "database"
            item.setData(0, Qt.ItemDataRole.UserRole, data)
            item.setText(0, f"Database Query - {data['db_type']} {data['host']}:{data['port']}")
            self.logger.info(
                f"Added database query: {data['db_type']} {data['host']}:{data['port']}"
            )

    def add_message_queue(self):
        """Add message queue to test plan"""
        item = QTreeWidgetItem(self.test_tree)
        item.setText(0, "Message Queue")
        item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            {
                "type": "message_queue",
                "mq_type": "rabbitmq",
                "host": "localhost",
                "port": 5672,
                "queue": "test_queue",
            },
        )

    def remove_selected_test_element(self):
        """Remove selected test element from the tree"""
        current_item = self.test_tree.currentItem()
        if current_item:
            # Get the parent of the current item
            parent = current_item.parent()
            if parent:
                # Remove from parent
                parent.removeChild(current_item)
            else:
                # Remove from root level
                index = self.test_tree.indexOfTopLevelItem(current_item)
                if index >= 0:
                    self.test_tree.takeTopLevelItem(index)
            self.logger.info("Removed test element from test plan")
        else:
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.information(self, "No Selection", "Please select a test element to remove.")

    def configure_http_request(self, item):
        """Configure HTTP request parameters"""
        # Show configuration dialog first
        dialog = HTTPConfigDialog(self)
        dialog.show()

        # Wait for dialog to close
        dialog.exec_()

        if dialog.result_data:
            data = dialog.result_data
            item.setData(0, Qt.ItemDataRole.UserRole, data)
            item.setText(0, f"HTTP Request - {data['method']} {data['url']}")

    def on_environment_changed(self, environment):
        """Handle environment change"""
        self.config_manager.set_environment(environment)
        self.logger.info(f"Environment changed to: {environment}")

    def start_test(self):
        """Start the test execution"""
        try:
            # Build test configuration from UI
            test_config = self.build_test_config()

            if not test_config:
                QMessageBox.warning(
                    self, "Configuration Error", "Please configure at least one test target."
                )
                return

            # Update UI state
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Start test in background thread
            self.test_worker = TestWorkerThread(self.test_runner, test_config)
            self.test_worker.test_completed.connect(self.on_test_completed)
            self.test_worker.test_error.connect(self.on_test_error)
            self.test_worker.start()

            self.statusBar().showMessage("Test running...")

        except Exception as e:
            self.logger.error(f"Failed to start test: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start test: {e}")

    def stop_test(self):
        """Stop the current test"""
        if self.test_worker and self.test_worker.isRunning():
            self.test_worker.terminate()
            self.test_worker.wait()

        self.test_runner.stop_current_test()

        # Update UI state
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.statusBar().showMessage("Test stopped")

    def build_test_config(self) -> Optional[Dict[str, Any]]:
        """Build test configuration from UI elements"""
        targets = []

        # Extract targets from tree
        for i in range(self.test_tree.topLevelItemCount()):
            item = self.test_tree.topLevelItem(i)
            target_data = item.data(0, Qt.ItemDataRole.UserRole)
            if target_data:
                targets.append(target_data)

        if not targets:
            return None

        return {
            "test_name": self.test_name_edit.text(),
            "environment": self.env_combo.currentText(),
            "targets": targets,
            "load_profile": {
                "users": self.users_spin.value(),
                "threads": self.threads_spin.value(),
                "ramp_up": self.ramp_up_spin.value(),
                "duration": self.duration_spin.value(),
                "think_time": self.think_time_spin.value(),
            },
        }

    def on_test_completed(self, results: Dict[str, Any]):
        """Handle test completion"""
        # Update UI state
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # Update summary
        self.update_summary(results)

        # Update results table
        self.update_results_table(results)

        self.statusBar().showMessage("Test completed")

        # Show completion message
        QMessageBox.information(
            self,
            "Test Complete",
            f"Test '{results.get('test_name', 'Unknown')}' completed successfully!",
        )

    def on_test_error(self, error: str):
        """Handle test error"""
        # Update UI state
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.statusBar().showMessage("Test failed")

        # Show error message
        QMessageBox.critical(self, "Test Error", f"Test failed: {error}")

    def update_summary(self, results: Dict[str, Any]):
        """Update the summary display"""
        self.summary_labels["Test Name"].setText(results.get("test_name", "--"))
        self.summary_labels["Duration"].setText(f"{results.get('duration', 0):.2f}s")
        self.summary_labels["Total Requests"].setText(str(results.get("total_requests", 0)))
        self.summary_labels["Successful"].setText(str(results.get("successful_requests", 0)))
        self.summary_labels["Failed"].setText(str(results.get("failed_requests", 0)))
        self.summary_labels["Avg Response Time"].setText(
            f"{results.get('avg_response_time', 0):.3f}s"
        )
        self.summary_labels["Throughput"].setText(f"{results.get('throughput', 0):.2f} req/s")

    def update_results_table(self, results: Dict[str, Any]):
        """Update the results table"""
        # This would populate the table with detailed results
        # For now, just clear it
        self.results_table.setRowCount(0)

    def new_test(self):
        """Create a new test"""
        self.test_tree.clear()
        self.test_name_edit.setText("New Test")
        self.users_spin.setValue(10)
        self.threads_spin.setValue(4)
        self.ramp_up_spin.setValue(30)
        self.duration_spin.setValue(60)
        self.think_time_spin.setValue(1)

    def open_test(self):
        """Open a test configuration"""
        # TODO: Implement file open dialog
        QMessageBox.information(self, "Info", "Open test feature not implemented yet.")

    def save_test(self):
        """Save the current test configuration"""
        # TODO: Implement file save dialog
        QMessageBox.information(self, "Info", "Save test feature not implemented yet.")

    def open_dashboard(self):
        """Open the Streamlit dashboard"""
        # TODO: Launch Streamlit dashboard
        QMessageBox.information(self, "Info", "Dashboard feature not implemented yet.")

    def export_results(self):
        """Export test results"""
        # TODO: Implement CSV export
        QMessageBox.information(self, "Info", "Export feature not implemented yet.")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About NLM",
            "NLM Performance Testing Tool v1.0.0\n\n"
            "A comprehensive load testing tool with AI analysis.",
        )

    def edit_test_element(self, item, column):
        """Handle double-click on test element"""
        if column == 0:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data:
                return

            if data.get("type") == "http":
                # Show HTTP configuration dialog
                dialog = HTTPConfigDialog(self, data)
                dialog.show()
                dialog.exec_()

                if dialog.result_data:
                    updated_data = dialog.result_data
                    updated_data["type"] = "http"
                    item.setData(0, Qt.ItemDataRole.UserRole, updated_data)
                    item.setText(
                        0, f"HTTP Request - {updated_data['method']} {updated_data['url']}"
                    )
                    self.logger.info(
                        f"Updated HTTP request: {updated_data['method']} {updated_data['url']}"
                    )

            elif data.get("type") == "database":
                # Show database configuration dialog
                dialog = DatabaseConfigDialog(self, data)
                dialog.show()
                dialog.exec_()

                if dialog.result_data:
                    updated_data = dialog.result_data
                    updated_data["type"] = "database"
                    item.setData(0, Qt.ItemDataRole.UserRole, updated_data)
                    item.setText(
                        0,
                        f"Database Query - {updated_data['db_type']} {updated_data['host']}:{updated_data['port']}",
                    )
                    self.logger.info(
                        f"Updated database query: {updated_data['db_type']} {updated_data['host']}:{updated_data['port']}"
                    )

    def run(self):
        """Run the GUI application"""
        self.show()
        return QApplication.instance().exec()
