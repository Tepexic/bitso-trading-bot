#!/bin/bash

# Uninstall Bitso Trading Bot systemd service
echo "🗑️  Uninstalling Bitso Trading Bot service..."

# Stop the service
echo "🛑 Stopping service..."
sudo systemctl stop pi-trader.service 2>/dev/null || true

# Disable the service
echo "❌ Disabling service..."
sudo systemctl disable pi-trader.service 2>/dev/null || true

# Remove the service file
echo "🗂️  Removing service file..."
sudo rm -f /etc/systemd/system/pi-trader.service

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Clean up control scripts
echo "🧹 Cleaning up control scripts..."
rm -f start_bot.sh stop_bot.sh status_bot.sh restart_bot.sh monitor_bot.sh

echo "✅ Service uninstalled successfully!"
echo "💡 The bot files and virtual environment are still available in this directory"
