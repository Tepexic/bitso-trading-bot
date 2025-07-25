import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class TradingStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    def should_buy(self, data: pd.DataFrame) -> bool:
        """Determine if we should buy based on market data"""
        raise NotImplementedError
    
    def should_sell(self, data: pd.DataFrame) -> bool:
        """Determine if we should sell based on market data"""
        raise NotImplementedError

class MovingAverageStrategy(TradingStrategy):
    """
    Simple Moving Average strategy
    Buy when short MA crosses above long MA
    Sell when short MA crosses below long MA
    """
    
    def __init__(self, short_window: int = 10, long_window: int = 30):
        super().__init__("Moving Average Strategy")
        self.short_window = short_window
        self.long_window = long_window
    
    def calculate_signals(self, prices: pd.Series) -> pd.DataFrame:
        """Calculate trading signals based on moving averages"""
        df = pd.DataFrame({'price': prices})
        
        # Calculate moving averages
        df['short_ma'] = df['price'].rolling(window=self.short_window).mean()
        df['long_ma'] = df['price'].rolling(window=self.long_window).mean()
        
        # Generate signals using proper pandas indexing
        df['signal'] = 0
        df.loc[self.short_window:, 'signal'] = np.where(
            df.loc[self.short_window:, 'short_ma'] > df.loc[self.short_window:, 'long_ma'], 1, 0
        )
        df['position'] = df['signal'].diff()
        
        return df
    
    def should_buy(self, data: pd.DataFrame) -> bool:
        """Check if we should buy (short MA crosses above long MA)"""
        if len(data) < self.long_window:
            return False
        
        signals = self.calculate_signals(data['price'])
        return signals['position'].iloc[-1] == 1
    
    def should_sell(self, data: pd.DataFrame) -> bool:
        """Check if we should sell (short MA crosses below long MA)"""
        if len(data) < self.long_window:
            return False
        
        signals = self.calculate_signals(data['price'])
        return signals['position'].iloc[-1] == -1

class RSIStrategy(TradingStrategy):
    """
    RSI (Relative Strength Index) strategy
    Buy when RSI < 30 (oversold)
    Sell when RSI > 70 (overbought)
    """
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI Strategy")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def should_buy(self, data: pd.DataFrame) -> bool:
        """Check if we should buy (RSI indicates oversold)"""
        if len(data) < self.period + 1:
            return False
        
        rsi = self.calculate_rsi(data['price'])
        current_rsi = rsi.iloc[-1]
        
        logger.info(f"Current RSI: {current_rsi:.2f}")
        return current_rsi < self.oversold
    
    def should_sell(self, data: pd.DataFrame) -> bool:
        """Check if we should sell (RSI indicates overbought)"""
        if len(data) < self.period + 1:
            return False
        
        rsi = self.calculate_rsi(data['price'])
        current_rsi = rsi.iloc[-1]
        
        logger.info(f"Current RSI: {current_rsi:.2f}")
        return current_rsi > self.overbought

class CombinedStrategy(TradingStrategy):
    """
    Combined strategy using multiple indicators
    """
    
    def __init__(self):
        super().__init__("Combined Strategy")
        self.ma_strategy = MovingAverageStrategy()
        self.rsi_strategy = RSIStrategy()
    
    def should_buy(self, data: pd.DataFrame) -> bool:
        """Buy when both strategies agree"""
        ma_buy = self.ma_strategy.should_buy(data)
        rsi_buy = self.rsi_strategy.should_buy(data)
        
        logger.info(f"MA Strategy Buy Signal: {ma_buy}, RSI Strategy Buy Signal: {rsi_buy}")
        return ma_buy and rsi_buy
    
    def should_sell(self, data: pd.DataFrame) -> bool:
        """Sell when either strategy suggests selling"""
        ma_sell = self.ma_strategy.should_sell(data)
        rsi_sell = self.rsi_strategy.should_sell(data)
        
        logger.info(f"MA Strategy Sell Signal: {ma_sell}, RSI Strategy Sell Signal: {rsi_sell}")
        return ma_sell or rsi_sell
