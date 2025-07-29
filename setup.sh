#!/bin/bash

# Pi Trader Setup Script
# This script helps set up the trading bot environment

echo "🚀 Setting up Pi Trader - Bitso Crypto Trading Bot"
echo "=================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created successfully"
    else
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Python packages..."

# Check if we're on Raspberry Pi and install system packages first
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null || grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    echo "🥧 Raspberry Pi detected - installing system dependencies..."
    
    # Install required system packages for pandas/numpy on Pi
    sudo apt update
    sudo apt install -y python3-dev python3-numpy python3-pandas python3-matplotlib python3-scipy libatlas-base-dev
    
    # Use Pi-specific requirements with pre-built wheels
    echo "📦 Installing Pi-optimized packages..."
    if pip install --only-binary=all -r requirements-pi.txt --extra-index-url https://www.piwheels.org/simple; then
        echo "✅ Pi-optimized packages installed successfully"
    else
        echo "⚠️  Falling back to system packages and essential pip packages..."
        # Install only essential packages that usually work on Pi
        pip install requests python-dotenv schedule --extra-index-url https://www.piwheels.org/simple
    fi
    
    # Install remaining packages that might not be in Pi requirements
    pip install --only-binary=all requests python-dotenv schedule --extra-index-url https://www.piwheels.org/simple
else
    # Regular installation for other systems
    pip install -r requirements.txt
fi

if [ $? -eq 0 ]; then
    echo "✅ All packages installed successfully"
else
    echo "❌ Failed to install some packages"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs reports data

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "✅ Environment file created from template"
    echo "⚠️  Please edit .env with your Bitso API credentials"
else
    echo "✅ Environment file already exists"
fi

# Test if the installation works
echo "🧪 Testing installation..."
.venv/bin/python -c "import requests, pandas, schedule; print('✅ All required packages installed successfully')" || {
    echo "❌ Package installation test failed"
    exit 1
}

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Bitso API credentials"
echo "2. Test the API connection: .venv/bin/python test_api.py"
echo "3. Run the trading bot: .venv/bin/python src/trading_bot.py"
echo ""
echo "📊 Available trading strategies:"
echo "   - MA (Moving Average): Set STRATEGY=ma"
echo "   - RSI (Relative Strength Index): Set STRATEGY=rsi"  
echo "   - Combined (MA + RSI): Set STRATEGY=combined"
echo ""
echo "🛡️ Safety recommendations:"
echo "   - Start with DRY_RUN=True for testing"
echo "   - Use BITSO_USE_STAGING=True for initial testing"
echo "   - Begin with small TRADE_AMOUNT values"
echo ""
echo "For more information, check the README.md file"
echo "=================================================="
