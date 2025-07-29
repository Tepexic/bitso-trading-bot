# Raspberry Pi Deployment Guide

This guide explains how to deploy the Bitso Trading Bot on a Raspberry Pi 3B running Raspbian Lite for 24/7 autonomous operation.

## 📋 Prerequisites

- Raspberry Pi 3B with Raspbian Lite OS
- Internet connection (WiFi or Ethernet)
- SSH access to the Pi
- Basic command line knowledge

## 🚀 Quick Deployment

### 1. Prepare Your Raspberry Pi

```bash
# Update the system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y git python3 python3-pip python3-venv

# Install Python development headers (needed for some packages)
sudo apt install -y python3-dev build-essential
```

### 2. Clone and Setup the Bot

```bash
# Clone the repository
cd ~
git clone https://github.com/Tepexic/bitso-trading-bot.git
cd bitso-trading-bot

# Use the Pi-specific setup script (recommended for Raspberry Pi)
chmod +x setup_pi.sh
./setup_pi.sh

# Alternative: Use the general setup script
# chmod +x setup.sh
# ./setup.sh
```

**Note:** The `setup_pi.sh` script is optimized for Raspberry Pi and installs system packages to avoid compilation issues with NumPy/Pandas.

### 3. Configure Your API Credentials

```bash
# Edit the environment file
nano .env

# Set your real Bitso API credentials:
# BITSO_API_KEY=your_real_api_key
# BITSO_API_SECRET=your_real_api_secret
# BITSO_USE_STAGING=False  # For production trading
# DRY_RUN=False           # For live trading
```

### 4. Deploy as System Service

```bash
# Run the Raspberry Pi deployment script
chmod +x deploy_raspberry_pi.sh
./deploy_raspberry_pi.sh
```

That's it! Your bot is now running as a system service and will automatically start when the Pi boots up.

## 🎮 Managing the Bot

After deployment, you'll have these control scripts:

```bash
./start_bot.sh      # Start the trading bot
./stop_bot.sh       # Stop the trading bot
./restart_bot.sh    # Restart the trading bot
./status_bot.sh     # Check status and recent logs
./monitor_bot.sh    # Monitor live logs (Ctrl+C to exit)
```

## 📊 Monitoring

### View Live Logs

```bash
./monitor_bot.sh
# or
sudo journalctl -u pi-trader.service -f
```

### Check Service Status

```bash
./status_bot.sh
# or
sudo systemctl status pi-trader.service
```

### View Historical Logs

```bash
sudo journalctl -u pi-trader.service -n 100  # Last 100 lines
sudo journalctl -u pi-trader.service --since "1 hour ago"
```

## 🔧 Advanced Configuration

### Modify Service Settings

```bash
sudo systemctl edit pi-trader.service
```

### Change Log Level

```bash
# Edit .env file
nano .env

# Set LOG_LEVEL to DEBUG for more detailed logs
LOG_LEVEL=DEBUG
```

### Auto-restart Service

```bash
sudo systemctl restart pi-trader.service
```

### Disable Auto-start

```bash
sudo systemctl disable pi-trader.service
```

## 🛡️ Security Recommendations

1. **Change Default Pi Password**

   ```bash
   passwd
   ```

2. **Enable SSH Key Authentication**

   ```bash
   ssh-keygen -t rsa -b 4096
   # Copy public key to ~/.ssh/authorized_keys
   ```

3. **Enable UFW Firewall**

   ```bash
   sudo apt install ufw
   sudo ufw enable
   sudo ufw allow ssh
   ```

4. **Regular Updates**
   ```bash
   # Create update script
   cat > update_system.sh << 'EOF'
   #!/bin/bash
   sudo apt update && sudo apt upgrade -y
   cd ~/bitso-trading-bot
   git pull origin main
   ./restart_bot.sh
   EOF
   chmod +x update_system.sh
   ```

## 🔄 Troubleshooting

### Bot Won't Start

```bash
# Check service status
sudo systemctl status pi-trader.service

# Check logs for errors
sudo journalctl -u pi-trader.service -n 50

# Test manual start
cd ~/bitso-trading-bot
.venv/bin/python src/trading_bot.py
```

### Network Issues

```bash
# Test internet connectivity
ping -c 4 google.com

# Test Bitso API
.venv/bin/python test_api.py
```

### High CPU/Memory Usage

```bash
# Monitor resources
htop

# Check if multiple instances are running
ps aux | grep trading_bot
```

### Logs Taking Too Much Space

```bash
# Limit journal size
sudo nano /etc/systemd/journald.conf
# Set: SystemMaxUse=100M

# Restart journald
sudo systemctl restart systemd-journald
```

## ⚡ Performance Optimization for Pi 3B

### 1. Reduce Memory Usage

```bash
# Edit .env to reduce check frequency
nano .env
# Set: CHECK_INTERVAL_MINUTES=10  # Check less frequently
```

### 2. Limit Trading Pairs

```bash
# Edit .env to trade fewer pairs
nano .env
# Set: TRADING_PAIRS=eth_mxn  # Trade only ETH instead of multiple currencies
```

### 3. GPU Memory Split

```bash
sudo raspi-config
# Advanced Options > Memory Split > Set to 16
```

## 📈 Remote Monitoring Setup

### 1. SSH Tunnel for Secure Access

```bash
# From your computer:
ssh -L 8080:localhost:8080 pi@your-pi-ip

# Then access Pi locally at localhost:8080
```

### 2. Email Notifications (Optional)

```bash
# Install sendmail
sudo apt install sendmail

# Add to crontab for daily reports
crontab -e
# Add: 0 9 * * * /home/pi/bitso-trading-bot/status_bot.sh | mail -s "Daily Bot Report" your@email.com
```

## 🔋 Power Management

### UPS Setup (Recommended)

- Consider a UPS hat for your Pi to handle power outages
- Popular options: PiJuice, UPS PIco

### Graceful Shutdown

```bash
# The bot handles SIGTERM gracefully and will:
# - Complete current trading cycle
# - Save all data
# - Close positions safely (if configured)
```

---

Your Raspberry Pi is now running a professional-grade cryptocurrency trading bot! 🚀
