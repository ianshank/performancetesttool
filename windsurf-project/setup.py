#!/usr/bin/env python3
"""
Setup script for NLM Performance Testing Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="nlm-performance-tool",
    version="1.0.0",
    author="NLM Team",
    author_email="team@nlm-tool.com",
    description="Enterprise-grade load testing tool with AI analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/nlm-tool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "gui": [
            "PyQt6>=6.4.0",
        ],
        "dashboard": [
            "streamlit>=1.25.0",
            "plotly>=5.15.0",
        ],
        "ai": [
            "openai>=1.0.0",
            "anthropic>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nlm=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="load testing, performance testing, monitoring, aws, datadog, splunk, ai",
    project_urls={
        "Bug Reports": "https://github.com/your-org/nlm-tool/issues",
        "Source": "https://github.com/your-org/nlm-tool",
        "Documentation": "https://nlm-tool.readthedocs.io/",
    },
) 