#!/bin/bash

# Raspberry Pi Deployment Script for Bitso Trading Bot
# This script sets up the bot as a systemd service for auto-start

echo "🥧 Setting up Bitso Trading Bot on Raspberry Pi"
echo "=============================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  This script is designed for Raspberry Pi. Proceeding anyway..."
fi

# Check if we're in the right directory
if [ ! -f "src/trading_bot.py" ]; then
    echo "❌ Please run this script from the bitso-trading-bot directory"
    echo "Expected structure: ./src/trading_bot.py should exist"
    exit 1
fi

# Get the current directory (should be the project root)
PROJECT_DIR=$(pwd)
CURRENT_USER=$(whoami)
CURRENT_GROUP=$(id -gn)
SERVICE_FILE="pi-trader.service"

echo "📍 Project directory: $PROJECT_DIR"
echo "👤 Current user: $CURRENT_USER"
echo "👥 Current group: $CURRENT_GROUP"

# Update the service file with the correct path and user
echo "🔧 Updating service file paths and user..."
cp $SERVICE_FILE "${SERVICE_FILE}.backup"
sed -e "s|REPLACE_PROJECT_DIR|$PROJECT_DIR|g" \
    -e "s|REPLACE_USER|$CURRENT_USER|g" \
    -e "s|REPLACE_GROUP|$CURRENT_GROUP|g" \
    "${SERVICE_FILE}.backup" > $SERVICE_FILE

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create and configure your .env file first:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Check if API credentials are configured
if grep -q "your_api_key_here\|your_api_secret_here" .env; then
    echo "⚠️  WARNING: .env file contains default API credentials!"
    echo "Please edit .env with your real Bitso API credentials before continuing."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first to set up the environment"
    exit 1
fi

# Test the bot can start
echo "🧪 Testing bot startup..."
timeout 10s .venv/bin/python src/trading_bot.py &
TEST_PID=$!
sleep 5

if kill -0 $TEST_PID 2>/dev/null; then
    kill $TEST_PID
    echo "✅ Bot startup test successful"
else
    echo "❌ Bot failed to start. Please check your configuration."
    exit 1
fi

# Install the systemd service
echo "📋 Installing systemd service..."
sudo cp $SERVICE_FILE /etc/systemd/system/

# Stop any existing service first
if sudo systemctl is-active --quiet pi-trader.service; then
    echo "🛑 Stopping existing service..."
    sudo systemctl stop pi-trader.service
fi

# Reload systemd and enable the service
echo "🔄 Enabling service for auto-start..."
sudo systemctl daemon-reload
sudo systemctl enable pi-trader.service

# Create log monitoring script
echo "📜 Creating log monitoring script..."
cat > monitor_bot.sh << 'EOF'
#!/bin/bash
# Monitor the trading bot logs

echo "Bitso Trading Bot - Live Logs"
echo "============================="
echo "Press Ctrl+C to exit"
echo ""

sudo journalctl -u pi-trader.service -f --no-pager
EOF

chmod +x monitor_bot.sh

# Create control scripts
echo "🎮 Creating control scripts..."

# Start script
cat > start_bot.sh << 'EOF'
#!/bin/bash
echo "Starting Bitso Trading Bot..."
sudo systemctl start pi-trader.service
sudo systemctl status pi-trader.service --no-pager -l
EOF

# Stop script
cat > stop_bot.sh << 'EOF'
#!/bin/bash
echo "Stopping Bitso Trading Bot..."
sudo systemctl stop pi-trader.service
sudo systemctl status pi-trader.service --no-pager -l
EOF

# Status script
cat > status_bot.sh << 'EOF'
#!/bin/bash
echo "Bitso Trading Bot Status:"
echo "========================"
sudo systemctl status pi-trader.service --no-pager -l
echo ""
echo "Recent logs:"
echo "============"
sudo journalctl -u pi-trader.service -n 20 --no-pager
EOF

# Restart script
cat > restart_bot.sh << 'EOF'
#!/bin/bash
echo "Restarting Bitso Trading Bot..."
sudo systemctl restart pi-trader.service
sudo systemctl status pi-trader.service --no-pager -l
EOF

chmod +x start_bot.sh stop_bot.sh status_bot.sh restart_bot.sh

echo ""
echo "🎉 Raspberry Pi deployment completed successfully!"
echo ""
echo "📋 Available commands:"
echo "   ./start_bot.sh     - Start the trading bot"
echo "   ./stop_bot.sh      - Stop the trading bot"  
echo "   ./restart_bot.sh   - Restart the trading bot"
echo "   ./status_bot.sh    - Check bot status and recent logs"
echo "   ./monitor_bot.sh   - Monitor live logs (Ctrl+C to exit)"
echo ""
echo "🔄 The bot will now start automatically when the Pi boots up!"
echo ""
echo "💡 Tips:"
echo "   - Check logs with: sudo journalctl -u pi-trader.service"
echo "   - Disable auto-start with: sudo systemctl disable pi-trader.service"
echo "   - Edit service with: sudo systemctl edit pi-trader.service"
echo ""
echo "🚀 Starting the bot now..."
sudo systemctl start pi-trader.service

echo ""
echo "📊 Initial status:"
sudo systemctl status pi-trader.service --no-pager -l
echo "=============================================="
