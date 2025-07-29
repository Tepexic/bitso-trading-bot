import os
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
from dotenv import load_dotenv

from bitso_api import BitsoAPI
from strategies import MovingAverageStrategy, RSIStrategy, CombinedStrategy
from portfolio import Portfolio

load_dotenv()

# Set up logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingBot:
    """
    Main trading bot class that orchestrates all components
    """
    
    def __init__(self):
        self.api = BitsoAPI()  # Will use staging environment based on .env configuration
        self.portfolio = Portfolio()
        
        # Configuration from environment
        # Support both single pair and multi-pair modes
        single_pair = os.getenv('TRADING_PAIR')
        multi_pairs = os.getenv('TRADING_PAIRS')
        
        if multi_pairs:
            self.trading_pairs = [pair.strip() for pair in multi_pairs.split(',')]
            logger.info(f"Multi-pair mode: {self.trading_pairs}")
        elif single_pair:
            self.trading_pairs = [single_pair]
            logger.info(f"Single-pair mode: {single_pair}")
        else:
            self.trading_pairs = ['eth_mxn']
            logger.info("Default mode: eth_mxn")
        
        self.trade_amount = float(os.getenv('TRADE_AMOUNT', '100.0'))
        self.stop_loss_pct = float(os.getenv('STOP_LOSS_PERCENTAGE', '5.0'))
        self.take_profit_pct = float(os.getenv('TAKE_PROFIT_PERCENTAGE', '10.0'))
        self.dry_run = os.getenv('DRY_RUN', 'True').lower() == 'true'
        
        # Select strategy from environment variable
        strategy_name = os.getenv('STRATEGY', 'combined').lower()
        if strategy_name == 'ma':
            self.strategy = MovingAverageStrategy()
            logger.info('Using Moving Average Strategy')
        elif strategy_name == 'rsi':
            self.strategy = RSIStrategy()
            logger.info('Using RSI Strategy')
        else:
            self.strategy = CombinedStrategy()
            logger.info('Using Combined Strategy')
        
        # Data storage - separate history for each trading pair
        self.price_histories = {}
        for pair in self.trading_pairs:
            self.price_histories[pair] = pd.DataFrame(columns=['timestamp', 'price'])
        
        self.max_history_length = 1000
        
        # Load existing price data from logs if available
        self._load_historical_data()
        
        logger.info(f"Trading Bot initialized for pairs: {self.trading_pairs}")
        logger.info(f"Dry run mode: {self.dry_run}")
        
        total_points = sum(len(self.price_histories[pair]) for pair in self.trading_pairs)
        logger.info(f"Loaded {total_points} total historical price points across all pairs")
    
    def _load_historical_data(self):
        """Load historical price data from CSV files first, then fall back to log files"""
        
        for pair in self.trading_pairs:
            # First, try to load from the most recent CSV file for this pair
            if self._load_from_most_recent_csv(pair):
                continue
            
            # If no CSV files found, try to load from logs
            logger.info(f"No CSV files found for {pair}, attempting to load from log file...")
            self._load_historical_data_from_logs(pair)
    
    def _load_from_most_recent_csv(self, trading_pair: str) -> bool:
        """Load data from the most recent CSV file in the data directory for a specific pair"""
        import glob
        
        data_dir = 'data'
        if not os.path.exists(data_dir):
            logger.info(f"No data directory found for {trading_pair}")
            return False
        
        # Look for CSV files with our naming patterns for this specific pair ONLY
        csv_patterns = [
            f'data/price_history_{trading_pair}_*.csv',
            f'data/historical_prices_{trading_pair}_*.csv'
        ]
        
        csv_files = []
        for pattern in csv_patterns:
            csv_files.extend(glob.glob(pattern))
        
        # Also check legacy files but verify they contain the correct trading pair data
        legacy_patterns = [
            'data/price_history_*.csv',
            'data/historical_prices_*.csv'
        ]
        
        for pattern in legacy_patterns:
            legacy_files = glob.glob(pattern)
            for file in legacy_files:
                # Skip if it's already a pair-specific file
                if trading_pair in os.path.basename(file):
                    continue
                    
                # Check if this legacy file contains data for our trading pair
                if self._file_contains_pair_data(file, trading_pair):
                    csv_files.append(file)
        
        if not csv_files:
            logger.info(f"No CSV files found for {trading_pair}")
            return False
        
        # Sort by modification time (most recent first)
        csv_files.sort(key=os.path.getmtime, reverse=True)
        most_recent_file = csv_files[0]
        
        logger.info(f"Found {len(csv_files)} CSV files for {trading_pair}, loading from: {most_recent_file}")
        
        # Load the most recent file
        if self.load_price_history_from_file(most_recent_file, trading_pair):
            logger.info(f"Successfully loaded {len(self.price_histories[trading_pair])} price points for {trading_pair}")
            return True
        else:
            logger.warning(f"Failed to load from {most_recent_file} for {trading_pair}")
            return False
    
    def _file_contains_pair_data(self, filename: str, trading_pair: str) -> bool:
        """Check if a CSV file contains data that was logged for a specific trading pair"""
        try:
            # Quick check by looking at log entries that might reference this file
            # For now, we'll be conservative and only use pair-specific files
            # This prevents loading wrong data for the wrong currency
            return False
        except Exception:
            return False
    
    def _load_historical_data_from_logs(self, trading_pair: str):
        """Load historical price data from log files for a specific trading pair"""
        import re
        from datetime import datetime
        
        log_file = 'logs/trading_bot.log'
        
        if not os.path.exists(log_file):
            logger.info(f"No existing log file found for {trading_pair}, starting with empty price history")
            return
        
        try:
            price_data = []
            
            # Regular expression to match price log entries for this specific pair
            price_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - trading_bot - INFO - Current ' + \
                          re.escape(trading_pair) + r' price: ([\d.]+)'
            
            with open(log_file, 'r') as f:
                for line in f:
                    match = re.search(price_pattern, line)
                    if match:
                        timestamp_str = match.group(1)
                        price = float(match.group(2))
                        
                        try:
                            timestamp = pd.to_datetime(timestamp_str, format='%Y-%m-%d %H:%M:%S')
                            price_data.append({
                                'timestamp': timestamp,
                                'price': price
                            })
                        except ValueError as e:
                            logger.debug(f"Could not parse timestamp {timestamp_str}: {e}")
                            continue
            
            if price_data:
                # Create DataFrame from extracted data
                historical_df = pd.DataFrame(price_data)
                
                # Remove duplicates and sort by timestamp
                historical_df = historical_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                
                # Keep only recent data (within max_history_length)
                if len(historical_df) > self.max_history_length:
                    historical_df = historical_df.tail(self.max_history_length)
                
                self.price_histories[trading_pair] = historical_df.reset_index(drop=True)
                logger.info(f"Loaded {len(self.price_histories[trading_pair])} price points for {trading_pair} from log file")
            else:
                logger.info(f"No price data found in log file for {trading_pair}")
                
        except Exception as e:
            logger.warning(f"Could not load historical data from logs for {trading_pair}: {e}")
            logger.info(f"Starting with empty price history for {trading_pair}")
    
    def save_price_history_to_file(self, filename: str = None):
        """Save current price history to CSV files for backup"""
        try:
            os.makedirs('data', exist_ok=True)
            
            for pair in self.trading_pairs:
                if self.price_histories[pair].empty:
                    continue
                    
                if filename is None:
                    pair_filename = f"data/price_history_{pair}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                else:
                    # Add pair to filename
                    base, ext = os.path.splitext(filename)
                    pair_filename = f"{base}_{pair}{ext}"
                
                self.price_histories[pair].to_csv(pair_filename, index=False)
                logger.info(f"Price history for {pair} saved to {pair_filename}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to save price history: {e}")
            return False
    
    def load_price_history_from_file(self, filename: str, trading_pair: str):
        """Load price history from a CSV file for a specific trading pair"""
        try:
            if not os.path.exists(filename):
                logger.warning(f"File {filename} does not exist")
                return False
            
            df = pd.read_csv(filename)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Validate data structure
            if 'timestamp' not in df.columns or 'price' not in df.columns:
                logger.error("CSV file must contain 'timestamp' and 'price' columns")
                return False
            
            # Additional validation: check if this looks like reasonable price data
            if len(df) == 0:
                logger.warning(f"CSV file {filename} is empty")
                return False
                
            # Basic sanity check on price data
            prices = df['price']
            if prices.min() <= 0:
                logger.warning(f"CSV file {filename} contains invalid price data (negative or zero prices)")
                return False
            
            # Sort by timestamp and remove duplicates
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            
            # Keep only recent data
            if len(df) > self.max_history_length:
                df = df.tail(self.max_history_length)
            
            self.price_histories[trading_pair] = df.reset_index(drop=True)
            logger.info(f"Loaded {len(self.price_histories[trading_pair])} price points for {trading_pair} from {filename}")
            
            # Log some basic stats about the loaded data
            price_range = f"{prices.min():.2f} - {prices.max():.2f}"
            logger.info(f"Price range for {trading_pair}: {price_range} MXN")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load price history from {filename} for {trading_pair}: {e}")
            return False
    
    def fetch_market_data(self, trading_pair: str) -> Optional[float]:
        """Fetch current market data for a specific trading pair"""
        try:
            ticker = self.api.get_ticker(trading_pair)
            if ticker.get('success'):
                price = float(ticker['payload']['last'])
                timestamp = datetime.now()
                
                # Add to price history for this pair
                new_row = pd.DataFrame({
                    'timestamp': [timestamp],
                    'price': [price]
                })
                
                if self.price_histories[trading_pair].empty:
                    self.price_histories[trading_pair] = new_row
                else:
                    self.price_histories[trading_pair] = pd.concat([self.price_histories[trading_pair], new_row], ignore_index=True)
                
                # Keep only recent history
                if len(self.price_histories[trading_pair]) > self.max_history_length:
                    self.price_histories[trading_pair] = self.price_histories[trading_pair].tail(self.max_history_length)
                
                logger.info(f"Current {trading_pair} price: {price}")
                return price
            else:
                logger.error(f"Failed to fetch ticker for {trading_pair}: {ticker}")
                return None
        except Exception as e:
            logger.error(f"Error fetching market data for {trading_pair}: {e}")
            return None
    
    def check_account_status(self) -> bool:
        """Check if account is ready for trading"""
        try:
            status = self.api.get_account_status()
            if status.get('success'):
                account_status = status['payload']['status']
                logger.info(f"Account status: {account_status}")
                return account_status == 'active'
            else:
                logger.error(f"Failed to get account status: {status}")
                return False
        except Exception as e:
            logger.error(f"Error checking account status: {e}")
            return False
    
    def get_available_balance(self) -> Dict[str, float]:
        """Get available balance for trading"""
        try:
            balance_response = self.api.get_balance()
            if balance_response.get('success'):
                balances = {}
                for balance in balance_response['payload']['balances']:
                    currency = balance['currency'].upper()
                    available = float(balance['available'])
                    balances[currency] = available
                
                logger.debug(f"Available balances: {balances}")
                return balances
            else:
                logger.error(f"Failed to get balance: {balance_response}")
                return {}
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {}
    
    def has_sufficient_funds(self, trading_pair: str, trade_amount: float) -> bool:
        """Check if we have sufficient funds for a trade"""
        try:
            # For buying, we need MXN funds
            balances = self.get_available_balance()
            available_mxn = balances.get('MXN', 0.0)
            
            if available_mxn >= trade_amount:
                return True
            else:
                logger.warning(f"Insufficient funds for {trading_pair}: need {trade_amount} MXN, have {available_mxn} MXN")
                return False
                
        except Exception as e:
            logger.error(f"Error checking funds for {trading_pair}: {e}")
            return False
    
    def execute_buy_order(self, price: float, trading_pair: str) -> bool:
        """Execute a buy order for a specific trading pair"""
        try:
            asset = trading_pair.split('_')[0].upper()
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would buy {self.trade_amount} MXN worth of {asset} at {price}")
                self.portfolio.add_position(asset, self.trade_amount / price, price)
                return True
            
            # Use minor (MXN amount) for buy orders
            response = self.api.place_order(
                book=trading_pair,
                side='buy',
                order_type='market',
                minor=self.trade_amount  # Use MXN amount directly
            )
            
            if response.get('success'):
                logger.info(f"Buy order placed successfully for {trading_pair}: {response}")
                # Calculate asset amount from response or estimate
                asset_amount = self.trade_amount / price
                self.portfolio.add_position(asset, asset_amount, price)
                return True
            else:
                logger.error(f"Failed to place buy order for {trading_pair}: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing buy order for {trading_pair}: {e}")
            return False
    
    def get_actual_asset_balance(self, asset: str) -> float:
        """Get the actual available balance for a specific asset from the exchange"""
        try:
            balances = self.get_available_balance()
            return balances.get(asset.upper(), 0.0)
        except Exception as e:
            logger.error(f"Error getting actual balance for {asset}: {e}")
            return 0.0
    
    def validate_sell_amount(self, trading_pair: str, requested_amount: float) -> float:
        """
        Validate and adjust sell amount based on actual available balance
        Returns the validated amount that can actually be sold
        """
        asset = trading_pair.split('_')[0].upper()
        
        # Get actual balance from exchange
        actual_balance = self.get_actual_asset_balance(asset)
        portfolio_balance = self.portfolio.get_asset_amount(asset)
        
        logger.info(f"Sell validation for {asset}:")
        logger.info(f"  Requested amount: {requested_amount}")
        logger.info(f"  Portfolio tracking: {portfolio_balance}")
        logger.info(f"  Actual exchange balance: {actual_balance}")
        
        # Use the minimum of requested amount and actual balance
        available_to_sell = min(requested_amount, actual_balance)
        
        # Check if we have a minimum trade amount (Bitso usually has minimums)
        min_trade_amount = self.get_minimum_trade_amount(trading_pair)
        
        if available_to_sell < min_trade_amount:
            logger.warning(f"Available amount {available_to_sell} {asset} is below minimum trade amount {min_trade_amount}")
            return 0.0  # Can't trade
        
        if available_to_sell != requested_amount:
            logger.warning(f"Adjusting sell amount from {requested_amount} to {available_to_sell} {asset}")
        
        return available_to_sell
    
    def get_minimum_trade_amount(self, trading_pair: str) -> float:
        """Get minimum trade amount for a trading pair"""
        # These are typical Bitso minimums - you might want to fetch this from API
        minimums = {
            'eth_mxn': 0.001,   # 0.001 ETH
            'ltc_mxn': 0.01,    # 0.01 LTC  
            'avax_mxn': 0.1,    # 0.1 AVAX
            'sol_mxn': 0.01,    # 0.01 SOL
        }
        return minimums.get(trading_pair, 0.001)  # Default to 0.001
    
    def execute_sell_order(self, amount: float, price: float, trading_pair: str) -> bool:
        """Execute a sell order for a specific trading pair with balance validation"""
        try:
            asset = trading_pair.split('_')[0].upper()
            
            # Validate the sell amount against actual balance
            validated_amount = self.validate_sell_amount(trading_pair, amount)
            
            if validated_amount <= 0:
                logger.warning(f"Cannot sell {asset}: insufficient balance or below minimum trade amount")
                return False
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would sell {validated_amount} {asset} at {price}")
                self.portfolio.close_position(asset, validated_amount, price)
                return True
            
            # Use the validated amount for the actual order
            response = self.api.place_order(
                book=trading_pair,
                side='sell',
                order_type='market',
                major=validated_amount  # Use validated crypto amount
            )
            
            if response.get('success'):
                logger.info(f"Sell order placed successfully for {trading_pair}: {response}")
                # Update portfolio with the actual amount sold
                self.portfolio.close_position(asset, validated_amount, price)
                return True
            else:
                error_msg = response.get('error', {}).get('message', 'Unknown error')
                logger.error(f"Failed to place sell order for {trading_pair}: {error_msg}")
                
                # Handle specific Bitso error cases
                if 'insufficient' in error_msg.lower() or 'balance' in error_msg.lower():
                    logger.error(f"Insufficient balance error - this should have been caught by validation!")
                    # Sync portfolio with actual balances
                    self.sync_portfolio_with_exchange()
                
                return False
                
        except Exception as e:
            logger.error(f"Error executing sell order for {trading_pair}: {e}")
            return False
    
    def sync_portfolio_with_exchange(self):
        """Sync portfolio tracking with actual exchange balances"""
        try:
            logger.info("Syncing portfolio with exchange balances...")
            
            # Get actual balances from exchange
            exchange_balances = self.get_available_balance()
            
            # Clear portfolio positions that don't match reality
            for pair in self.trading_pairs:
                asset = pair.split('_')[0].upper()
                portfolio_amount = self.portfolio.get_asset_amount(asset)
                exchange_amount = exchange_balances.get(asset, 0.0)
                
                if abs(portfolio_amount - exchange_amount) > 0.001:  # Allow small rounding differences
                    logger.warning(f"Portfolio mismatch for {asset}:")
                    logger.warning(f"  Portfolio: {portfolio_amount}")
                    logger.warning(f"  Exchange: {exchange_amount}")
                    
                    # Clear the position in portfolio tracking
                    self.portfolio.clear_asset_positions(asset)
                    
                    # If exchange has balance, add it to portfolio
                    if exchange_amount > 0:
                        # Estimate average price from recent data
                        if len(self.price_histories[pair]) > 0:
                            avg_price = self.price_histories[pair]['price'].tail(10).mean()
                            self.portfolio.add_position(asset, exchange_amount, avg_price)
                            logger.info(f"Restored {asset} position: {exchange_amount} at estimated price {avg_price}")
            
            logger.info("Portfolio sync completed")
            
        except Exception as e:
            logger.error(f"Error syncing portfolio with exchange: {e}")
    
    def check_stop_loss_take_profit(self, current_price: float, trading_pair: str):
        """Check if any positions should be closed due to stop loss or take profit"""
        asset = trading_pair.split('_')[0].upper()
        
        for position in self.portfolio.positions:
            if position['asset'] == asset:
                entry_price = position['entry_price']
                amount = position['amount']
                
                # Calculate percentage change
                pct_change = ((current_price - entry_price) / entry_price) * 100
                
                # Check stop loss
                if pct_change <= -self.stop_loss_pct:
                    logger.warning(f"Stop loss triggered for {trading_pair}! Price change: {pct_change:.2f}%")
                    self.execute_sell_order(amount, current_price, trading_pair)
                
                # Check take profit
                elif pct_change >= self.take_profit_pct:
                    logger.info(f"Take profit triggered for {trading_pair}! Price change: {pct_change:.2f}%")
                    self.execute_sell_order(amount, current_price, trading_pair)
    
    def run_trading_cycle(self):
        """Run one trading cycle for all trading pairs"""
        logger.info("Starting trading cycle...")
        
        # Check account status first
        if not self.check_account_status():
            logger.warning("Account not ready for trading")
            return
        
        # Get available balance once for the entire cycle
        balances = self.get_available_balance()
        available_mxn = balances.get('MXN', 0.0)
        logger.info(f"Available MXN balance: {available_mxn:.2f}")
        
        # Collect all buy signals first, then prioritize if needed
        buy_signals = []
        
        # Process each trading pair
        for trading_pair in self.trading_pairs:
            logger.info(f"Processing {trading_pair}...")
            
            # Fetch current market data for this pair
            current_price = self.fetch_market_data(trading_pair)
            if not current_price:
                logger.warning(f"Failed to fetch data for {trading_pair}")
                continue
            
            # Check stop loss and take profit for this pair
            self.check_stop_loss_take_profit(current_price, trading_pair)
            
            # Only proceed with new trades if we have enough data
            if len(self.price_histories[trading_pair]) < 50:
                logger.info(f"Not enough data for {trading_pair}. Current: {len(self.price_histories[trading_pair])}, Need: 50")
                continue
            
            # Check trading signals for this pair
            try:
                should_buy = self.strategy.should_buy(self.price_histories[trading_pair])
                should_sell = self.strategy.should_sell(self.price_histories[trading_pair])
                
                # Get asset name from trading pair (e.g., eth_mxn -> ETH)
                asset = trading_pair.split('_')[0].upper()
                current_asset_amount = self.portfolio.get_asset_amount(asset)
                
                if should_buy and current_asset_amount == 0:
                    logger.info(f"Buy signal detected for {trading_pair}!")
                    buy_signals.append({
                        'pair': trading_pair,
                        'price': current_price,
                        'asset': asset
                    })
                
                elif should_sell and current_asset_amount > 0:
                    logger.info(f"Sell signal detected for {trading_pair}!")
                    self.execute_sell_order(current_asset_amount, current_price, trading_pair)
                
                else:
                    logger.info(f"No trading signals detected for {trading_pair}")
            
            except Exception as e:
                logger.error(f"Error in trading cycle for {trading_pair}: {e}")
        
        # Handle buy signals with fund management
        if buy_signals:
            self._process_buy_signals(buy_signals, available_mxn)
        
        # Log portfolio status
        self.portfolio.log_status()
        
        # Periodically save price history (every 10 cycles)
        total_points = sum(len(self.price_histories[pair]) for pair in self.trading_pairs)
        if total_points % 10 == 0 and total_points > 0:
            self.save_price_history_to_file()
    
    def _process_buy_signals(self, buy_signals: List[Dict], available_mxn: float):
        """Process buy signals with intelligent fund allocation"""
        logger.info(f"Processing {len(buy_signals)} buy signals with {available_mxn:.2f} MXN available")
        
        # Calculate how many trades we can afford
        affordable_trades = int(available_mxn // self.trade_amount)
        
        if affordable_trades == 0:
            logger.warning("No funds available for any buy orders")
            for signal in buy_signals:
                logger.warning(f"Buy signal for {signal['pair']} ignored due to insufficient funds")
            return
        
        if len(buy_signals) <= affordable_trades:
            # We can afford all trades
            logger.info(f"Can afford all {len(buy_signals)} trades")
            for signal in buy_signals:
                self.execute_buy_order(signal['price'], signal['pair'])
        else:
            # Need to prioritize - use configured allocation strategy
            logger.warning(f"Can only afford {affordable_trades} out of {len(buy_signals)} trades")
            
            allocation_strategy = os.getenv('FUND_ALLOCATION_STRATEGY', 'first_come_first_served')
            selected_signals = self._select_trades_by_strategy(buy_signals, affordable_trades, allocation_strategy)
            
            logger.info(f"Selected trades using {allocation_strategy}: {[s['pair'] for s in selected_signals]}")
            for signal in selected_signals:
                self.execute_buy_order(signal['price'], signal['pair'])
            
            # Log the ignored signals
            ignored_signals = [s for s in buy_signals if s not in selected_signals]
            for signal in ignored_signals:
                logger.warning(f"Buy signal for {signal['pair']} ignored due to fund allocation limits")
    
    def _select_trades_by_strategy(self, buy_signals: List[Dict], max_trades: int, strategy: str) -> List[Dict]:
        """Select which trades to execute based on allocation strategy"""
        import random
        
        if strategy == 'first_come_first_served':
            return buy_signals[:max_trades]
        
        elif strategy == 'random':
            return random.sample(buy_signals, min(max_trades, len(buy_signals)))
        
        elif strategy == 'equal_split':
            # For equal split, we might adjust trade amounts instead of selecting trades
            # For now, just return first N trades but log the strategy
            logger.info("Equal split strategy selected - consider implementing variable trade amounts")
            return buy_signals[:max_trades]
        
        else:
            logger.warning(f"Unknown allocation strategy '{strategy}', using first_come_first_served")
            return buy_signals[:max_trades]
    
    def start(self):
        """Start the trading bot"""
        logger.info("Starting Bitso Ethereum Trading Bot...")
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Run initial check
        self.run_trading_cycle()
        
        # Schedule regular trading cycles
        check_interval = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))
        schedule.every(check_interval).minutes.do(self.run_trading_cycle)
        
        logger.info(f"Bot scheduled to run every {check_interval} minutes")
        
        # Keep the bot running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    bot = TradingBot()
    bot.start()
