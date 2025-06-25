#!/bin/bash
# Installation script for NLM Performance Testing Tool

set -e

echo "🚀 Installing NLM Performance Testing Tool"
echo "=========================================="

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p reports
mkdir -p config

# Copy environment file
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your credentials"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x demo.py
chmod +x src/main.py

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run the demo: python demo.py"
echo "3. Launch GUI: python src/main.py --gui"
echo "4. Launch CLI: python src/main.py --cli"
echo "5. Launch dashboard: streamlit run src/dashboard/streamlit_app.py"
echo ""
echo "📖 For more information, see README.md" 