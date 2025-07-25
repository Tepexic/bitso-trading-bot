#!/usr/bin/env python3
"""
Test script to compare trading signal frequency across different cryptocurrencies
"""
import sys
import os
sys.path.append('src')

from trading_bot import TradingBot
from strategies import MovingAverageStrategy, RSIStrategy

def test_currency_signals(currency_pair: str):
    """Test trading signals for a specific currency pair"""
    print(f"\n=== TESTING {currency_pair.upper()} ===")
    
    # Temporarily set the trading pair
    original_pair = os.environ.get('TRADING_PAIR', 'eth_mxn')
    os.environ['TRADING_PAIR'] = currency_pair
    
    try:
        bot = TradingBot()
        
        # Get current market data
        ticker = bot.api.get_ticker(currency_pair)
        if 'payload' in ticker:
            price = float(ticker['payload']['last'])
            high = float(ticker['payload']['high'])
            low = float(ticker['payload']['low'])
            volatility = ((high - low) / price) * 100
            
            print(f"Current Price: {price:,.2f} MXN")
            print(f"24h Volatility: {volatility:.2f}%")
            
            # Test strategies individually
            ma_strategy = MovingAverageStrategy(short_window=5, long_window=15)  # More sensitive
            rsi_strategy = RSIStrategy()
            
            # Get price history
            bot.run_trading_cycle()
            
            if hasattr(bot, 'price_history') and len(bot.price_history) >= 30:
                import pandas as pd
                df = pd.DataFrame(bot.price_history)
                
                # Test MA signals
                ma_buy = ma_strategy.should_buy(df)
                ma_sell = ma_strategy.should_sell(df)
                
                # Test RSI signals  
                rsi_buy = rsi_strategy.should_buy(df)
                rsi_sell = rsi_strategy.should_sell(df)
                
                print(f"MA Strategy  - Buy: {ma_buy}, Sell: {ma_sell}")
                print(f"RSI Strategy - Buy: {rsi_buy}, Sell: {rsi_sell}")
                
                # Calculate signal strength
                signal_count = sum([ma_buy, ma_sell, rsi_buy, rsi_sell])
                print(f"Total Signals: {signal_count}/4")
                
                if signal_count > 0:
                    print("🚨 ACTIVE SIGNALS DETECTED!")
                else:
                    print("😴 No signals detected")
                    
            return volatility
            
    except Exception as e:
        print(f"Error testing {currency_pair}: {e}")
        return 0
    finally:
        # Restore original trading pair
        os.environ['TRADING_PAIR'] = original_pair

if __name__ == "__main__":
    print("🔍 CRYPTOCURRENCY TRADING SIGNAL COMPARISON")
    print("=" * 50)
    
    # Test different currencies
    currencies_to_test = [
        'eth_mxn',      # Current (stable)
        'avax_mxn',     # High volatility
        'sol_mxn',      # High volatility  
        'ltc_mxn',      # Very high volatility
        'mana_mxn',     # High volatility
    ]
    
    results = []
    
    for currency in currencies_to_test:
        volatility = test_currency_signals(currency)
        results.append((currency, volatility))
    
    print("\n" + "=" * 50)
    print("📊 VOLATILITY RANKING (Higher = More Trading Opportunities)")
    print("=" * 50)
    
    # Sort by volatility
    results.sort(key=lambda x: x[1], reverse=True)
    
    for i, (currency, volatility) in enumerate(results, 1):
        emoji = "🚀" if volatility > 5 else "🛡️" if volatility > 3 else "😴"
        print(f"{i}. {emoji} {currency.upper():<12} {volatility:>6.2f}% volatility")
    
    print("\n💡 To switch currency, update your .env file:")
    print(f"   TRADING_PAIR={results[0][0]}  # Most volatile")
