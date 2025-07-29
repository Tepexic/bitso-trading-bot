#!/bin/bash

echo "🥧 Raspberry Pi Setup - Bitso Trading Bot"
echo "========================================="

# Update system first
echo "📦 Updating system packages..."
sudo apt update

# Install system Python packages (pre-compiled for Pi)
echo "🔧 Installing system Python packages..."
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y python3-numpy python3-pandas python3-matplotlib python3-requests
sudo apt install -y libatlas-base-dev libblas-dev liblapack-dev gfortran

# Create virtual environment
echo "🏠 Creating virtual environment..."
python3 -m venv .venv --system-site-packages

# Activate virtual environment  
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install additional packages via pip with piwheels
echo "⚙️  Installing additional packages..."
pip install --upgrade pip
pip install --extra-index-url https://www.piwheels.org/simple python-dotenv schedule pytz python-dateutil seaborn

# Create directories
echo "📁 Creating directories..."
mkdir -p logs reports data

# Copy environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "✅ Environment file created from template"
    echo "⚠️  Please edit .env with your Bitso API credentials"
else
    echo "✅ Environment file already exists"
fi

# Test installation
echo "🧪 Testing installation..."
if .venv/bin/python -c "import pandas, numpy, requests, schedule; print('✅ All packages working')"; then
    echo "✅ Raspberry Pi setup completed successfully!"
else
    echo "❌ Some packages may not be working correctly"
fi

echo ""
echo "Next steps:"
echo "1. Edit .env file: nano .env"
echo "2. Test API: .venv/bin/python test_api.py"
echo "3. Deploy service: ./deploy_raspberry_pi.sh"
