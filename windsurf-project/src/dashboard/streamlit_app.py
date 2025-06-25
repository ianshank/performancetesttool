"""
Streamlit dashboard for NLM tool
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import ConfigManager
from integrations.aws_cloudwatch import CloudWatchIntegration
from integrations.datadog_integration import DatadogIntegration
from integrations.splunk_integration import SplunkIntegration


def main():
    """Main Streamlit dashboard application"""
    st.set_page_config(
        page_title="NLM Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📊 NLM Performance Testing Dashboard")
    st.markdown("Real-time monitoring and analysis of load test results")
    
    # Initialize session state
    if 'test_results' not in st.session_state:
        st.session_state.test_results = []
    if 'metrics_data' not in st.session_state:
        st.session_state.metrics_data = {}
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Environment selection
        env = st.selectbox(
            "Environment",
            ["dev", "qa", "stage", "prod"],
            index=0
        )
        
        # Monitoring services
        st.subheader("Monitoring Services")
        aws_enabled = st.checkbox("AWS CloudWatch", value=True)
        datadog_enabled = st.checkbox("Datadog", value=True)
        splunk_enabled = st.checkbox("Splunk", value=True)
        
        # Refresh interval
        refresh_interval = st.slider(
            "Refresh Interval (seconds)",
            min_value=5,
            max_value=60,
            value=10
        )
        
        # Manual refresh button
        if st.button("🔄 Refresh Data"):
            refresh_data(env, aws_enabled, datadog_enabled, splunk_enabled)
    
    # Main dashboard content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Real-time Metrics")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "Response Times", 
            "Throughput", 
            "Error Rates", 
            "System Metrics"
        ])
        
        with tab1:
            display_response_time_chart()
        
        with tab2:
            display_throughput_chart()
        
        with tab3:
            display_error_rate_chart()
        
        with tab4:
            display_system_metrics(env, aws_enabled, datadog_enabled, splunk_enabled)
    
    with col2:
        st.subheader("📋 Test Summary")
        display_test_summary()
        
        st.subheader("🚨 Alerts")
        display_alerts()

        st.subheader("🤖 AI Analysis & Suggestions")
        display_ai_analysis()
    
    # Auto-refresh
    if st.session_state.get('auto_refresh', True):
        time.sleep(refresh_interval)
        st.rerun()


def refresh_data(env, aws_enabled, datadog_enabled, splunk_enabled):
    """Refresh monitoring data from various sources"""
    try:
        config_manager = ConfigManager()
        config_manager.set_environment(env)
        
        # Load test results from file (simulated)
        load_test_results()
        
        # Load monitoring data
        if aws_enabled:
            load_aws_metrics(config_manager)
        
        if datadog_enabled:
            load_datadog_metrics(config_manager)
        
        if splunk_enabled:
            load_splunk_metrics(config_manager)
        
        st.success("Data refreshed successfully!")
        
    except Exception as e:
        st.error(f"Error refreshing data: {e}")


def load_test_results():
    """Load test results from file"""
    # This would load actual test results
    # For now, create sample data
    if not st.session_state.test_results:
        st.session_state.test_results = generate_sample_test_data()


def load_aws_metrics(config_manager):
    """Load AWS CloudWatch metrics"""
    try:
        cloudwatch = CloudWatchIntegration(config_manager)
        metrics = cloudwatch.get_metrics()
        st.session_state.metrics_data['aws'] = metrics
    except Exception as e:
        st.warning(f"Could not load AWS metrics: {e}")


def load_datadog_metrics(config_manager):
    """Load Datadog metrics"""
    try:
        datadog = DatadogIntegration(config_manager)
        metrics = datadog.get_metrics()
        st.session_state.metrics_data['datadog'] = metrics
    except Exception as e:
        st.warning(f"Could not load Datadog metrics: {e}")


def load_splunk_metrics(config_manager):
    """Load Splunk metrics"""
    try:
        splunk = SplunkIntegration(config_manager)
        metrics = splunk.get_metrics()
        st.session_state.metrics_data['splunk'] = metrics
    except Exception as e:
        st.warning(f"Could not load Splunk metrics: {e}")


def generate_sample_test_data():
    """Generate sample test data for demonstration"""
    import numpy as np
    
    # Generate sample data for the last hour
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    timestamps = pd.date_range(start=start_time, end=end_time, freq='10S')
    
    data = []
    for i, timestamp in enumerate(timestamps):
        # Simulate realistic response times with some variation
        base_response_time = 0.2 + 0.1 * np.sin(i / 10)  # Varying baseline
        noise = np.random.normal(0, 0.05)  # Random noise
        response_time = max(0.01, base_response_time + noise)
        
        # Simulate success/failure
        success = np.random.random() > 0.05  # 95% success rate
        
        data.append({
            'timestamp': timestamp,
            'response_time': response_time,
            'success': success,
            'status_code': 200 if success else 500,
            'user_id': np.random.randint(1, 11),
            'request_id': i
        })
    
    return data


def display_response_time_chart():
    """Display response time chart"""
    if not st.session_state.test_results:
        st.info("No test data available. Run a test to see results.")
        return
    
    df = pd.DataFrame(st.session_state.test_results)
    
    # Create response time chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['response_time'],
        mode='lines+markers',
        name='Response Time',
        line=dict(color='blue', width=2),
        marker=dict(size=4)
    ))
    
    # Add moving average
    window_size = 10
    if len(df) > window_size:
        moving_avg = df['response_time'].rolling(window=window_size).mean()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=moving_avg,
            mode='lines',
            name=f'Moving Average ({window_size})',
            line=dict(color='red', width=2, dash='dash')
        ))
    
    fig.update_layout(
        title="Response Time Over Time",
        xaxis_title="Time",
        yaxis_title="Response Time (seconds)",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Response time statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Average", f"{df['response_time'].mean():.3f}s")
    
    with col2:
        st.metric("Median", f"{df['response_time'].median():.3f}s")
    
    with col3:
        st.metric("95th Percentile", f"{df['response_time'].quantile(0.95):.3f}s")
    
    with col4:
        st.metric("Max", f"{df['response_time'].max():.3f}s")


def display_throughput_chart():
    """Display throughput chart"""
    if not st.session_state.test_results:
        st.info("No test data available.")
        return
    
    df = pd.DataFrame(st.session_state.test_results)
    
    # Calculate throughput (requests per minute)
    df['minute'] = df['timestamp'].dt.floor('min')
    throughput = df.groupby('minute').size().reset_index(name='requests')
    throughput['rps'] = throughput['requests'] / 60  # requests per second
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=throughput['minute'],
        y=throughput['rps'],
        name='Throughput (RPS)',
        marker_color='green'
    ))
    
    fig.update_layout(
        title="Throughput Over Time",
        xaxis_title="Time",
        yaxis_title="Requests per Second",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Throughput statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Average RPS", f"{throughput['rps'].mean():.2f}")
    
    with col2:
        st.metric("Peak RPS", f"{throughput['rps'].max():.2f}")
    
    with col3:
        st.metric("Total Requests", f"{len(df)}")


def display_error_rate_chart():
    """Display error rate chart"""
    if not st.session_state.test_results:
        st.info("No test data available.")
        return
    
    df = pd.DataFrame(st.session_state.test_results)
    
    # Calculate error rate over time
    df['minute'] = df['timestamp'].dt.floor('min')
    error_rate = df.groupby('minute').agg({
        'success': lambda x: (x == False).sum() / len(x) * 100
    }).reset_index()
    error_rate.columns = ['minute', 'error_rate']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=error_rate['minute'],
        y=error_rate['error_rate'],
        mode='lines+markers',
        name='Error Rate',
        line=dict(color='red', width=2),
        marker=dict(size=6)
    ))
    
    # Add threshold line
    fig.add_hline(y=5, line_dash="dash", line_color="orange", 
                  annotation_text="5% Threshold")
    
    fig.update_layout(
        title="Error Rate Over Time",
        xaxis_title="Time",
        yaxis_title="Error Rate (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Error statistics
    total_requests = len(df)
    failed_requests = len(df[~df['success']])
    error_rate_pct = (failed_requests / total_requests) * 100 if total_requests > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Requests", total_requests)
    
    with col2:
        st.metric("Failed Requests", failed_requests)
    
    with col3:
        st.metric("Error Rate", f"{error_rate_pct:.2f}%")


def display_system_metrics(env, aws_enabled, datadog_enabled, splunk_enabled):
    """Display system metrics from monitoring services"""
    st.subheader("System Metrics")
    
    if not any([aws_enabled, datadog_enabled, splunk_enabled]):
        st.info("No monitoring services enabled.")
        return
    
    # Display metrics from each service
    if aws_enabled and 'aws' in st.session_state.metrics_data:
        st.write("**AWS CloudWatch Metrics**")
        aws_metrics = st.session_state.metrics_data['aws']
        if aws_metrics:
            st.json(aws_metrics)
        else:
            st.info("No AWS metrics available.")
    
    if datadog_enabled and 'datadog' in st.session_state.metrics_data:
        st.write("**Datadog Metrics**")
        datadog_metrics = st.session_state.metrics_data['datadog']
        if datadog_metrics:
            st.json(datadog_metrics)
        else:
            st.info("No Datadog metrics available.")
    
    if splunk_enabled and 'splunk' in st.session_state.metrics_data:
        st.write("**Splunk Metrics**")
        splunk_metrics = st.session_state.metrics_data['splunk']
        if splunk_metrics:
            st.json(splunk_metrics)
        else:
            st.info("No Splunk metrics available.")


def display_test_summary():
    """Display test summary information"""
    if not st.session_state.test_results:
        st.info("No test data available.")
        return
    
    df = pd.DataFrame(st.session_state.test_results)
    
    # Calculate summary statistics
    total_requests = len(df)
    successful_requests = len(df[df['success']])
    failed_requests = total_requests - successful_requests
    avg_response_time = df['response_time'].mean()
    
    # Display metrics
    st.metric("Total Requests", total_requests)
    st.metric("Success Rate", f"{(successful_requests/total_requests)*100:.1f}%")
    st.metric("Avg Response Time", f"{avg_response_time:.3f}s")
    
    # Test duration
    if len(df) > 1:
        duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
        st.metric("Test Duration", f"{duration:.1f}s")


def display_alerts():
    """Display system alerts"""
    # This would show real alerts from monitoring systems
    # For now, show sample alerts
    
    alerts = [
        {"level": "warning", "message": "Response time above threshold", "time": "2 min ago"},
        {"level": "info", "message": "Test completed successfully", "time": "5 min ago"}
    ]
    
    for alert in alerts:
        if alert["level"] == "warning":
            st.warning(f"⚠️ {alert['message']} ({alert['time']})")
        elif alert["level"] == "error":
            st.error(f"🚨 {alert['message']} ({alert['time']})")
        else:
            st.info(f"ℹ️ {alert['message']} ({alert['time']})")


def display_ai_analysis():
    """Display AI-powered human-readable analysis and suggestions"""
    from ai.analysis_engine import AIAnalysisEngine
    config_manager = ConfigManager()
    engine = AIAnalysisEngine(config_manager)

    # Prepare summary and raw data
    if not st.session_state.test_results:
        st.info("No test data available for AI analysis.")
        return
    df = pd.DataFrame(st.session_state.test_results)
    # Build a summary similar to display_test_summary
    total_requests = len(df)
    successful_requests = len(df[df['success']])
    failed_requests = total_requests - successful_requests
    avg_response_time = df['response_time'].mean()
    summary = {
        'test_name': 'NLM Test',
        'duration': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() if len(df) > 1 else 0,
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'failed_requests': failed_requests,
        'avg_response_time': avg_response_time,
        'throughput': total_requests / ((df['timestamp'].max() - df['timestamp'].min()).total_seconds() or 1),
        'min_response_time': df['response_time'].min(),
        'max_response_time': df['response_time'].max(),
        'errors': df[df['success'] == False]['status_code'].value_counts().to_dict() if failed_requests else None
    }
    # Convert timestamps to seconds for AI engine compatibility
    raw_data = df.copy()
    if pd.api.types.is_datetime64_any_dtype(raw_data['timestamp']):
        raw_data['timestamp'] = raw_data['timestamp'].astype(int) // 10**9
    analysis = engine.analyze_test_results(summary, raw_data.to_dict(orient='records'))

    # Display the AI analysis
    if not analysis:
        st.info("No AI analysis available.")
        return
    st.markdown(f"**Summary:** {analysis.get('summary', 'No summary available.')}")
    perf = analysis.get('performance_analysis', {})
    if perf:
        st.markdown("**Performance Analysis:**")
        st.write(perf.get('response_time_assessment', ''))
        st.write(perf.get('throughput_assessment', ''))
        st.write(perf.get('error_analysis', ''))
        if perf.get('bottlenecks'):
            st.markdown("**Potential Bottlenecks:**")
            for b in perf['bottlenecks']:
                st.write(f"- {b}")
        if perf.get('recommendations'):
            st.markdown("**Recommendations:**")
            for r in perf['recommendations']:
                st.write(f"- {r}")
    if analysis.get('key_findings'):
        st.markdown("**Key Findings:**")
        for k in analysis['key_findings']:
            st.write(f"- {k}")
    if analysis.get('risk_assessment'):
        st.markdown("**Risk Assessment:**")
        st.write(f"Severity: {analysis['risk_assessment'].get('severity', '')}")
        st.write(analysis['risk_assessment'].get('description', ''))
    if analysis.get('next_steps'):
        st.markdown("**Next Steps:**")
        for n in analysis['next_steps']:
            st.write(f"- {n}")


if __name__ == "__main__":
    main() 