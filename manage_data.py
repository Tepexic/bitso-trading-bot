#!/usr/bin/env python3
"""
Historical Data Manager for Pi Trader
This script helps you manage and import historical price data
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import argparse

# Add src directory to path
sys.path.append('src')

from trading_bot import TradingBot
from bitso_api import BitsoAPI

def extract_from_logs(log_file='logs/trading_bot.log', trading_pair='eth_mxn'):
    """Extract historical price data from log files"""
    import re
    
    if not os.path.exists(log_file):
        print(f"❌ Log file {log_file} not found")
        return None
    
    price_data = []
    
    # Regular expression to match price log entries
    price_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - trading_bot - INFO - Current ' + \
                  re.escape(trading_pair) + r' price: ([\d.]+)'
    
    print(f"📂 Reading log file: {log_file}")
    
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
                except ValueError:
                    continue
    
    if price_data:
        df = pd.DataFrame(price_data)
        df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
        print(f"✅ Extracted {len(df)} price points from logs")
        return df
    else:
        print("❌ No price data found in logs")
        return None

def fetch_recent_data(hours=24, interval_minutes=5):
    """Fetch recent price data from Bitso API to populate history"""
    try:
        api = BitsoAPI()
        current_price_data = []
        
        print(f"📡 Fetching current market data every {interval_minutes} minutes for {hours} hours...")
        print("This is a simulation - in reality you'd collect this data over time")
        
        # For demonstration, we'll just get current price multiple times
        # In practice, you'd run this script periodically or use the bot over time
        ticker = api.get_ticker('eth_mxn')
        if ticker.get('success'):
            current_price = float(ticker['payload']['last'])
            current_time = datetime.now()
            
            # Create some sample historical data points (for demo purposes)
            # In reality, you'd collect this data over time
            for i in range(min(50, hours * (60 // interval_minutes))):
                timestamp = current_time - timedelta(minutes=i * interval_minutes)
                # Add some realistic price variation (±0.5%)
                import random
                price_variation = random.uniform(-0.005, 0.005)
                simulated_price = current_price * (1 + price_variation)
                
                current_price_data.append({
                    'timestamp': timestamp,
                    'price': simulated_price
                })
            
            df = pd.DataFrame(current_price_data)
            df = df.sort_values('timestamp').reset_index(drop=True)
            print(f"✅ Generated {len(df)} sample data points")
            return df
        else:
            print("❌ Failed to fetch current price data")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def save_to_csv(df, filename=None):
    """Save DataFrame to CSV file"""
    if filename is None:
        filename = f"data/historical_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    os.makedirs('data', exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"💾 Data saved to: {filename}")
    return filename

def load_into_bot(filename):
    """Load historical data into trading bot"""
    try:
        bot = TradingBot()
        
        print(f"📊 Current price history length: {len(bot.price_history)}")
        
        if bot.load_price_history_from_file(filename):
            print(f"✅ Successfully loaded data into bot")
            print(f"📊 New price history length: {len(bot.price_history)}")
            
            if len(bot.price_history) >= 50:
                print("🎉 Bot now has enough data to start trading!")
            else:
                print(f"⏳ Need {50 - len(bot.price_history)} more data points to start trading")
        else:
            print("❌ Failed to load data into bot")
            
    except Exception as e:
        print(f"❌ Error loading data into bot: {e}")

def main():
    parser = argparse.ArgumentParser(description='Manage historical price data for Pi Trader')
    parser.add_argument('action', choices=['extract', 'fetch', 'load'], 
                       help='Action to perform: extract from logs, fetch from API, or load into bot')
    parser.add_argument('--file', '-f', help='File to save to or load from')
    parser.add_argument('--hours', type=int, default=24, help='Hours of data to fetch (default: 24)')
    parser.add_argument('--interval', type=int, default=5, help='Interval in minutes (default: 5)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Pi Trader - Historical Data Manager")
    print("=" * 60)
    
    if args.action == 'extract':
        print("Extracting price data from logs...")
        df = extract_from_logs()
        if df is not None:
            filename = save_to_csv(df, args.file)
            print(f"📈 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"💰 Price range: {df['price'].min():.2f} to {df['price'].max():.2f} MXN")
    
    elif args.action == 'fetch':
        print("Fetching sample price data...")
        df = fetch_recent_data(args.hours, args.interval)
        if df is not None:
            filename = save_to_csv(df, args.file)
            print(f"📈 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"💰 Price range: {df['price'].min():.2f} to {df['price'].max():.2f} MXN")
    
    elif args.action == 'load':
        if not args.file:
            print("❌ Please specify a file to load with --file option")
            return
        print(f"Loading data from {args.file}...")
        load_into_bot(args.file)
    
    print("=" * 60)
    print("Operation completed!")

if __name__ == "__main__":
    main()
