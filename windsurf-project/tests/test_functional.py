import subprocess
import sys
import os
import time
import pytest
from pathlib import Path
import glob
import shutil

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
REPORTS_DIR = PROJECT_ROOT / "reports"

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
        text=True
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
        text=True
    )
    # Wait a few seconds for dashboard to start
    time.sleep(10)
    # Check process is still running and output contains expected text
    try:
        stdout, stderr = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        # Still running, that's fine
        process.terminate()
        return
    assert "Streamlit app" in stdout or "You can now view your Streamlit app" in stdout
    process.terminate()

@pytest.mark.functional
def test_gui_launch():
    """Functional test: Launch PyQt GUI and check it starts"""
    gui_path = SRC_DIR / "main.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    # Use --gui to launch the GUI
    process = subprocess.Popen(
        [sys.executable, str(gui_path), "--gui"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )
    # Wait a few seconds for GUI to start
    time.sleep(8)
    # Check process is running (should not exit immediately)
    assert process.poll() is None
    process.terminate()
    process.wait(timeout=10)

@pytest.mark.functional
def test_end_to_end_cli_and_output():
    """End-to-end functional test: Run CLI test and verify output files"""
    cli_path = SRC_DIR / "main.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    # Clean up reports dir before test
    if REPORTS_DIR.exists():
        shutil.rmtree(REPORTS_DIR)
    REPORTS_DIR.mkdir(exist_ok=True)
    process = subprocess.Popen(
        [sys.executable, str(cli_path), "--cli"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )
    user_input = "1\nhttp://httpbin.org/get\n2\n5\n8\n"
    try:
        stdout, stderr = process.communicate(input=user_input, timeout=90)
    except subprocess.TimeoutExpired:
        process.kill()
        pytest.fail("End-to-end CLI test timed out")
    assert process.returncode == 0
    # Check for output files in reports dir
    csv_files = glob.glob(str(REPORTS_DIR / "test_results_*.csv"))
    summary_files = glob.glob(str(REPORTS_DIR / "test_results_*_summary.csv"))
    assert csv_files, "No CSV results file found"
    assert summary_files, "No summary CSV file found"
    
    # Check content of main results CSV file (should have timestamp, response_time columns)
    main_csv_files = [f for f in csv_files if not f.endswith('_summary.csv')]
    assert main_csv_files, "No main results CSV file found"
    with open(main_csv_files[0], "r") as f:
        content = f.read()
        assert "timestamp" in content and "response_time" in content
    
    # Check content of summary CSV file (should have metrics like Total Requests, Success Rate)
    with open(summary_files[0], "r") as f:
        content = f.read()
        assert "Total Requests" in content and "Success Rate" in content

# Additional functional tests (GUI, end-to-end) can be added similarly 