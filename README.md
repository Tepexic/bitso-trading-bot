# Pi Trader - Bitso Crypto Trading Bot

A Python-based cryptocurrency trading bot designed to run on Raspberry Pi, specifically configured for trading Ethereum on the Bitso exchange.

## Features

- **Multiple Trading Strategies**:
  - Moving Average Crossover
  - RSI (Relative Strength Index)
  - Combined Strategy
- **Risk Management**:
  - Stop Loss protection
  - Take Profit targets
  - Position sizing controls
- **Portfolio Management**: Track positions, P&L, and trading history
- **Real-time Monitoring**: Continuous market data fetching and analysis
- **Dry Run Mode**: Test strategies without real money
- **Comprehensive Logging**: Detailed logs for debugging and analysis
- **Performance Analytics**: Generate reports and visualizations

## Requirements

- Python 3.8+
- Bitso account with API access
- Raspberry Pi (or any Linux/macOS system)

## Quick Start

1. **Clone and Setup**:

   ```bash
   cd /Users/tepexic/GitHub/pi-trader
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Credentials**:

   ```bash
   cp .env.example .env
   # Edit .env with your Bitso API credentials
   ```

3. **Test API Connection**:

   ```bash
   python test_api.py
   ```

4. **Run the Bot**:
   ```bash
   python src/trading_bot.py
   ```

## Configuration

Edit the `.env` file with your settings:

```env
# Bitso API Configuration
BITSO_API_KEY=your_api_key_here
BITSO_API_SECRET=your_api_secret_here
BITSO_USE_STAGING=True  # Set to False for production

# Trading Configuration
TRADING_PAIR=eth_mxn
TRADE_AMOUNT=100.0
STOP_LOSS_PERCENTAGE=5.0
TAKE_PROFIT_PERCENTAGE=10.0

# Bot Configuration
LOG_LEVEL=INFO
CHECK_INTERVAL_MINUTES=5
DRY_RUN=True  # Set to False for live trading
```

**Environment Settings:**

- `BITSO_USE_STAGING=True`: Use Bitso's staging environment for testing
- `BITSO_USE_STAGING=False`: Use Bitso's production environment for live trading

## Getting Bitso API Credentials

1. Log in to your Bitso account
2. Go to API section in your account settings
3. Create a new API key with trading permissions
4. Copy the API Key and Secret to your `.env` file

**Important**: Never share your API credentials or commit them to version control.

## Trading Strategies

### Moving Average Strategy

- **Buy Signal**: Short-term MA crosses above long-term MA
- **Sell Signal**: Short-term MA crosses below long-term MA
- **Default Settings**: 10-period and 30-period moving averages

### RSI Strategy

- **Buy Signal**: RSI < 30 (oversold condition)
- **Sell Signal**: RSI > 70 (overbought condition)
- **Default Settings**: 14-period RSI

### Combined Strategy

- **Buy Signal**: Both MA and RSI strategies agree
- **Sell Signal**: Either strategy suggests selling
- **More Conservative**: Reduces false signals

## Risk Management

- **Stop Loss**: Automatically sell if price drops by specified percentage
- **Take Profit**: Automatically sell if price rises by specified percentage
- **Position Sizing**: Fixed amount per trade (configurable)
- **Dry Run Mode**: Test without real money

## Project Structure

```
pi-trader/
├── src/
│   ├── bitso_api.py      # Bitso API client
│   ├── trading_bot.py    # Main bot logic
│   ├── strategies.py     # Trading strategies
│   ├── portfolio.py      # Portfolio management
│   └── analyzer.py       # Performance analysis
├── logs/                 # Bot logs (created automatically)
├── reports/              # Performance reports (created automatically)
├── test_api.py          # API testing script
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Monitoring and Analysis

### View Logs

```bash
tail -f logs/trading_bot.log
```

### Generate Performance Report

```python
from src.analyzer import TradingAnalyzer
from src.portfolio import Portfolio

portfolio = Portfolio()
analyzer = TradingAnalyzer(portfolio)
analyzer.save_report()
analyzer.plot_trade_history()
```

## Safety Recommendations

1. **Start with Dry Run**: Always test with `DRY_RUN=True` first
2. **Small Amounts**: Start with small trade amounts
3. **Monitor Closely**: Watch the bot's performance especially initially
4. **Regular Backups**: Keep backups of your configuration and logs
5. **API Permissions**: Only give necessary permissions to your API key

## Raspberry Pi Setup

For optimal performance on Raspberry Pi:

1. **Install Python 3.8+**:

   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. **Install System Dependencies**:

   ```bash
   sudo apt install python3-matplotlib python3-pandas
   ```

3. **Set Up Service** (optional):
   ```bash
   # Create systemd service for auto-start
   sudo nano /etc/systemd/system/pi-trader.service
   ```

## Troubleshooting

### Common Issues

1. **API Authentication Errors**:

   - Check API credentials in `.env`
   - Verify API key has trading permissions
   - Ensure account is verified and active

2. **Network Issues**:

   - Check internet connection
   - Verify firewall settings
   - Test with `python test_api.py`

3. **Insufficient Data**:
   - Bot needs time to collect price history
   - Wait for at least 50 data points before trading

### Getting Help

1. Check the logs in `logs/trading_bot.log`
2. Run `python test_api.py` to verify setup
3. Ensure all dependencies are installed
4. Check Bitso API documentation for any changes

## Disclaimer

**This bot is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. Never trade with money you cannot afford to lose. The authors are not responsible for any financial losses.**

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Happy Trading! 🚀**
