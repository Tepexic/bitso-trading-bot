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

## Trading Strategies 📊

The bot implements three sophisticated trading strategies that you can switch between using the `STRATEGY` environment variable:

### 1. Moving Average (MA) Strategy 📈

**What it does:**

- Uses two moving averages: a short-term (10 periods) and long-term (30 periods)
- A moving average smooths out price data by creating a constantly updated average price over a specific time period

**Signals:**

- **Buy Signal**: When the short MA (10-period) crosses **above** the long MA (30-period)
  - Indicates upward momentum - recent prices are higher than the longer-term average
  - Example: If ETH's 10-day average becomes higher than its 30-day average, it suggests a bullish trend
- **Sell Signal**: When the short MA crosses **below** the long MA
  - Indicates downward momentum - recent prices are falling below the longer-term trend

**Best for:** Trending markets, trend following
**Pros:** Simple and reliable, reduces noise from short-term fluctuations
**Cons:** Lag indicator (signals come after trend has started), false signals in choppy markets

### 2. RSI Strategy 🎯

**What it does:**

- RSI (Relative Strength Index) measures the speed and magnitude of price changes
- Ranges from 0 to 100, indicating if an asset is oversold or overbought
- Formula: `RSI = 100 - (100 / (1 + RS))` where `RS = Average Gain / Average Loss`

**Signals:**

- **Buy Signal**: When RSI < 30 (oversold condition)
  - Suggests the asset has been sold too aggressively and may bounce back
  - Example: If ETH's RSI drops to 25, it might be a good buying opportunity
- **Sell Signal**: When RSI > 70 (overbought condition)
  - Suggests the asset has been bought too aggressively and may correct downward

**Best for:** Range-bound markets, identifying reversal points
**Pros:** More responsive than moving averages, great for spotting extremes
**Cons:** Can stay overbought/oversold for extended periods in strong trends

### 3. Combined Strategy 🎯📈

**What happens when combined:**

**Buy Signal (Conservative Approach):**

- **BOTH** MA and RSI must agree (`ma_buy AND rsi_buy`)
- MA says "trend is up" AND RSI says "oversold, ready to bounce"
- Creates more conservative, higher-confidence buy signals
- Example: Short MA crosses above long MA AND RSI is below 30

**Sell Signal (Protective Approach):**

- **EITHER** MA or RSI suggests selling (`ma_sell OR rsi_sell`)
- If MA says "trend is down" OR RSI says "overbought", then sell
- Creates a more protective exit strategy

**Why this combination works:**

1. **Trend + Momentum**: MA identifies trend direction, RSI identifies momentum extremes
2. **Reduced False Signals**: Requiring both indicators to agree for buying reduces whipsaws
3. **Quick Exits**: Allowing either indicator to trigger a sell helps preserve profits

**Best for:** All market conditions, risk-averse traders
**Pros:** Higher quality signals, better risk management
**Cons:** Fewer trading opportunities, may miss some profitable trades

### Strategy Comparison

| Strategy     | Best For          | Signal Frequency      | Risk Level | Best Markets   |
| ------------ | ----------------- | --------------------- | ---------- | -------------- |
| **MA**       | Trend following   | Fewer, later          | Medium     | Trending       |
| **RSI**      | Mean reversion    | More frequent         | Higher     | Range-bound    |
| **Combined** | Balanced approach | Fewer, higher quality | Lower      | All conditions |

### Configuration

Choose your strategy in `.env`:

```bash
STRATEGY=ma          # Moving Average only
STRATEGY=rsi         # RSI only
STRATEGY=combined    # Both strategies combined (default)
```

### Tunable Parameters

Customize strategy behavior with these environment variables:

```bash
# Moving Average Settings
MA_SHORT_PERIOD=10      # Short moving average window
MA_LONG_PERIOD=30       # Long moving average window

# RSI Settings
RSI_PERIOD=14           # RSI calculation period
RSI_OVERSOLD=30         # RSI buy threshold
RSI_OVERBOUGHT=70       # RSI sell threshold
```

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
