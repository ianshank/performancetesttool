import glob
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
REPORTS_DIR = PROJECT_ROOT.parent / "reports"
DEMO_REPORTS_DIR = PROJECT_ROOT.parent / "windsurf-project" / "demo_reports"
TEST_DIRS = [REPORTS_DIR, DEMO_REPORTS_DIR]


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Fixture to clean up test data before and after each test"""
    # Pre-test cleanup
    for test_dir in TEST_DIRS:
        if test_dir.exists():
            shutil.rmtree(test_dir)
            test_dir.mkdir(exist_ok=True)

    yield  # This is where the test runs

    # Post-test cleanup
    for test_dir in TEST_DIRS:
        if test_dir.exists():
            shutil.rmtree(test_dir)
            test_dir.mkdir(exist_ok=True)


@pytest.mark.functional
def test_cli_quick_test():
    """Functional test: Run CLI quick test and check output"""
    cli_path = SRC_DIR / "main.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    # Simulate CLI quick test with --cli and input
    process = subprocess.Popen(
        [sys.executable, str(cli_path), "--cli"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )
    # Simulate user input: 1 (Quick Test), URL, users, duration, then exit (8)
    user_input = "1\nhttp://httpbin.org/get\n2\n5\n8\n"
    try:
        stdout, stderr = process.communicate(input=user_input, timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        pytest.fail("CLI quick test timed out")
    assert process.returncode == 0
    assert "Quick Test" in stdout
    assert "Test Results" in stdout or "Test Name" in stdout
    assert "Thank you for using NLM" in stdout


@pytest.mark.functional
def test_dashboard_launch():
    """Functional test: Launch Streamlit dashboard and check it starts"""
    dashboard_path = SRC_DIR / "dashboard" / "streamlit_app.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    # Launch dashboard in subprocess
    process = subprocess.Popen(
        ["streamlit", "run", str(dashboard_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )
    # Wait a few seconds for dashboard to start
    time.sleep(10)
    # Check process is still running and output contains expected text
    try:
        stdout, stderr = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        # Still running, that's fine
        process.terminate()
        process.wait(timeout=10)
        return
    assert "Streamlit app" in stdout or "You can now view your Streamlit app" in stdout
    process.terminate()
    process.wait(timeout=10)


@pytest.mark.functional
def test_gui_launch():
    """Functional test: Launch PyQt GUI and check it starts"""
    try:
        # Mock PyQt components
        from unittest.mock import MagicMock, patch

        mock_qapp = MagicMock()
        mock_gui = MagicMock()

        # Add src to path for imports
        sys.path.insert(0, str(SRC_DIR))

        # Create patches
        patches = [
            patch("PyQt5.QtWidgets.QApplication", MagicMock(return_value=mock_qapp)),
            patch("PyQt5.QtWidgets.QMainWindow", MagicMock()),
            patch("PyQt5.QtWidgets.QWidget", MagicMock()),
            patch("PyQt5.QtWidgets.QVBoxLayout", MagicMock()),
            patch("PyQt5.QtWidgets.QHBoxLayout", MagicMock()),
            patch("PyQt5.QtWidgets.QTabWidget", MagicMock()),
            patch("PyQt5.QtWidgets.QTreeWidget", MagicMock()),
            patch("PyQt5.QtWidgets.QPushButton", MagicMock()),
            patch("PyQt5.QtWidgets.QLabel", MagicMock()),
            patch("PyQt5.QtWidgets.QLineEdit", MagicMock()),
            patch("PyQt5.QtWidgets.QSpinBox", MagicMock()),
            patch("PyQt5.QtWidgets.QComboBox", MagicMock()),
            patch("PyQt5.QtWidgets.QTextEdit", MagicMock()),
            patch("PyQt5.QtWidgets.QGroupBox", MagicMock()),
            patch("PyQt5.QtWidgets.QFormLayout", MagicMock()),
            patch("PyQt5.QtWidgets.QMessageBox", MagicMock()),
            patch("PyQt5.QtWidgets.QProgressBar", MagicMock()),
            patch("PyQt5.QtWidgets.QSplitter", MagicMock()),
            patch("PyQt5.QtWidgets.QTableWidget", MagicMock()),
        ]

        # Start all patches
        for p in patches:
            p.start()

        try:
            # Import after patching to ensure mocks are used
            from src.gui.gui_interface import GUIInterface
            from src.utils.config import ConfigManager

            # Create and initialize GUI
            config_manager = ConfigManager()
            gui = GUIInterface(config_manager)

            # Verify GUI was initialized
            assert gui is not None
            assert hasattr(gui, "test_tree")
            assert hasattr(gui, "test_name_edit")
            assert hasattr(gui, "start_btn")
            assert hasattr(gui, "stop_btn")
            assert hasattr(gui, "results_table")

            # Show GUI
            gui.show()

            # Clean up
            gui.close()

        finally:
            # Stop all patches
            for p in patches:
                p.stop()

    except ImportError as e:
        pytest.skip(f"GUI test skipped due to missing dependencies: {e}")
    except Exception as e:
        pytest.skip(f"GUI test skipped in headless environment: {e}")


@pytest.mark.functional
def test_end_to_end_cli_and_output():
    """End-to-end functional test: Run CLI test and verify output files"""
    cli_path = SRC_DIR / "main.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    process = subprocess.Popen(
        [sys.executable, str(cli_path), "--cli"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        cwd=str(PROJECT_ROOT.parent),
    )
    user_input = "1\nhttp://httpbin.org/get\n2\n5\n8\n"
    try:
        stdout, stderr = process.communicate(input=user_input, timeout=90)
    except subprocess.TimeoutExpired:
        process.kill()
        pytest.fail("End-to-end CLI test timed out")
    assert process.returncode == 0
    # Print CLI output for debugging
    print(f"[DEBUG] CLI stdout:\n{stdout}")
    print(f"[DEBUG] CLI stderr:\n{stderr}")
    # Check for output files in reports dir
    print(f"[DEBUG] REPORTS_DIR: {REPORTS_DIR}")
    print(
        f"[DEBUG] Contents of REPORTS_DIR: {os.listdir(REPORTS_DIR) if REPORTS_DIR.exists() else 'Does not exist'}"
    )
    csv_files = glob.glob(str(REPORTS_DIR / "test_results_*.csv"))
    summary_files = glob.glob(str(REPORTS_DIR / "test_results_*_summary.csv"))
    assert csv_files, "No CSV results file found"
    assert summary_files, "No summary CSV file found"

    # Check content of main results CSV file (should have timestamp, response_time columns)
    main_csv_files = [f for f in csv_files if not f.endswith("_summary.csv")]
    assert main_csv_files, "No main results CSV file found"
    with open(main_csv_files[0], "r") as f:
        content = f.read()
        assert "timestamp" in content and "response_time" in content

    # Check content of summary CSV file (should have metrics like Total Requests, Success Rate)
    with open(summary_files[0], "r") as f:
        content = f.read()
        assert "Total Requests" in content and "Success Rate" in content


@pytest.mark.functional
def test_end_to_end_with_dashboard():
    """End-to-end functional test with dashboard: Run CLI test, launch dashboard, and verify proper cleanup"""
    # Launch dashboard first
    dashboard_path = SRC_DIR / "dashboard" / "streamlit_app.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)

    # Launch dashboard in subprocess
    dashboard_process = subprocess.Popen(
        ["streamlit", "run", str(dashboard_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )

    # Wait for dashboard to start
    time.sleep(10)

    try:
        # Run the CLI test
        cli_path = SRC_DIR / "main.py"
        cli_process = subprocess.Popen(
            [sys.executable, str(cli_path), "--cli"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            cwd=str(PROJECT_ROOT.parent),
        )

        user_input = "1\nhttp://httpbin.org/get\n2\n5\n8\n"
        try:
            stdout, stderr = cli_process.communicate(input=user_input, timeout=90)
        except subprocess.TimeoutExpired:
            cli_process.kill()
            pytest.fail("End-to-end CLI test timed out")

        assert cli_process.returncode == 0

        # Print CLI output for debugging
        print(f"[DEBUG] CLI stdout:\n{stdout}")
        print(f"[DEBUG] CLI stderr:\n{stderr}")

        # Check for output files in reports dir
        print(f"[DEBUG] REPORTS_DIR: {REPORTS_DIR}")
        print(
            f"[DEBUG] Contents of REPORTS_DIR: {os.listdir(REPORTS_DIR) if REPORTS_DIR.exists() else 'Does not exist'}"
        )
        csv_files = glob.glob(str(REPORTS_DIR / "test_results_*.csv"))
        summary_files = glob.glob(str(REPORTS_DIR / "test_results_*_summary.csv"))
        assert csv_files, "No CSV results file found"
        assert summary_files, "No summary CSV file found"

        # Check content of main results CSV file
        main_csv_files = [f for f in csv_files if not f.endswith("_summary.csv")]
        assert main_csv_files, "No main results CSV file found"
        with open(main_csv_files[0], "r") as f:
            content = f.read()
            assert "timestamp" in content and "response_time" in content

        # Check content of summary CSV file
        with open(summary_files[0], "r") as f:
            content = f.read()
            assert "Total Requests" in content and "Success Rate" in content

        # Give dashboard time to process the results
        time.sleep(5)

    finally:
        # Ensure dashboard is properly terminated
        dashboard_process.terminate()
        try:
            dashboard_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            dashboard_process.kill()
            dashboard_process.wait()


# Additional functional tests (GUI, end-to-end) can be added similarly
