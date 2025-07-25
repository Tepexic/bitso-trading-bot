import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import os
from bitso_api import BitsoAPI
from portfolio import Portfolio

class TradingAnalyzer:
    """
    Class for analyzing trading performance and generating reports
    """
    
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
    
    def generate_performance_report(self) -> dict:
        """Generate a comprehensive performance report"""
        stats = self.portfolio.get_performance_stats()
        
        if not stats:
            return {"message": "No trading data available"}
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_trades": stats['total_trades'],
                "completed_trades": stats['completed_trades'],
                "win_rate": f"{stats['win_rate']:.2%}",
                "total_pnl": f"{stats['total_realized_pnl']:.2f} MXN"
            },
            "performance_metrics": {
                "profitable_trades": stats['profitable_trades'],
                "losing_trades": stats['losing_trades'],
                "average_profit": f"{stats['average_profit']:.2f} MXN",
                "average_loss": f"{stats['average_loss']:.2f} MXN"
            }
        }
        
        return report
    
    def plot_trade_history(self, save_path: str = "reports/trade_history.png"):
        """Plot trade history over time"""
        if not self.portfolio.trade_history:
            print("No trade data available for plotting")
            return
        
        # Create DataFrame from trade history
        df = pd.DataFrame(self.portfolio.trade_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create cumulative P&L series
        sell_trades = df[df['action'] == 'SELL'].copy()
        if len(sell_trades) == 0:
            print("No completed trades to plot")
            return
        
        sell_trades['cumulative_pnl'] = sell_trades['pnl'].cumsum()
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(sell_trades['timestamp'], sell_trades['cumulative_pnl'], marker='o')
        plt.title('Cumulative P&L Over Time')
        plt.ylabel('Cumulative P&L (MXN)')
        plt.grid(True)
        
        plt.subplot(2, 1, 2)
        plt.bar(range(len(sell_trades)), sell_trades['pnl'], 
                color=['green' if pnl > 0 else 'red' for pnl in sell_trades['pnl']])
        plt.title('Individual Trade P&L')
        plt.xlabel('Trade Number')
        plt.ylabel('P&L (MXN)')
        plt.grid(True)
        
        plt.tight_layout()
        os.makedirs('reports', exist_ok=True)
        plt.savefig(save_path)
        plt.close()
        print(f"Trade history plot saved to {save_path}")
    
    def save_report(self, filename: str = None):
        """Save performance report to JSON file"""
        if filename is None:
            filename = f"reports/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.generate_performance_report()
        
        os.makedirs('reports', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Performance report saved to {filename}")
        return filename

def analyze_market_data(api: BitsoAPI, book: str = 'eth_mxn', hours: int = 24):
    """Analyze recent market data and trends"""
    try:
        # Get current ticker
        ticker = api.get_ticker(book)
        if not ticker.get('success'):
            print("Failed to fetch ticker data")
            return
        
        current_price = float(ticker['payload']['last'])
        volume = float(ticker['payload']['volume'])
        high = float(ticker['payload']['high'])
        low = float(ticker['payload']['low'])
        
        print(f"\n=== Market Analysis for {book.upper()} ===")
        print(f"Current Price: {current_price:.2f} MXN")
        print(f"24h High: {high:.2f} MXN")
        print(f"24h Low: {low:.2f} MXN")
        print(f"24h Volume: {volume:.2f} ETH")
        print(f"Price Range: {((high - low) / low * 100):.2f}%")
        
        # Calculate some basic metrics
        if high != low:
            current_position = (current_price - low) / (high - low)
            print(f"Current position in range: {current_position:.2%}")
        
        print("="*40)
        
    except Exception as e:
        print(f"Error analyzing market data: {e}")

if __name__ == "__main__":
    # Example usage
    api = BitsoAPI()  # Will use staging environment based on .env configuration
    portfolio = Portfolio()
    analyzer = TradingAnalyzer(portfolio)
    
    # Analyze current market
    analyze_market_data(api)
