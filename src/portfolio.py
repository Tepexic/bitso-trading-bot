import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Portfolio:
    """
    Portfolio management class to track positions and P&L
    """
    
    def __init__(self):
        self.positions = []
        self.total_profit_loss = 0.0
        self.trade_history = []
    
    def add_position(self, asset: str, amount: float, entry_price: float):
        """Add a new position to the portfolio"""
        position = {
            'asset': asset,
            'amount': amount,
            'entry_price': entry_price,
            'entry_time': datetime.now(),
            'unrealized_pnl': 0.0
        }
        self.positions.append(position)
        
        # Record trade
        self.trade_history.append({
            'action': 'BUY',
            'asset': asset,
            'amount': amount,
            'price': entry_price,
            'timestamp': datetime.now()
        })
        
        logger.info(f"Added position: {amount:.6f} {asset} at {entry_price:.2f}")
    
    def close_position(self, asset: str, amount: float, exit_price: float):
        """Close a position (full or partial)"""
        remaining_amount = amount
        total_pnl = 0.0
        
        # Find and close positions (FIFO)
        positions_to_remove = []
        for i, position in enumerate(self.positions):
            if position['asset'] == asset and remaining_amount > 0:
                if position['amount'] <= remaining_amount:
                    # Close entire position
                    pnl = (exit_price - position['entry_price']) * position['amount']
                    total_pnl += pnl
                    remaining_amount -= position['amount']
                    positions_to_remove.append(i)
                    
                    logger.info(f"Closed position: {position['amount']:.6f} {asset}, P&L: {pnl:.2f}")
                else:
                    # Partial close
                    pnl = (exit_price - position['entry_price']) * remaining_amount
                    total_pnl += pnl
                    position['amount'] -= remaining_amount
                    remaining_amount = 0
                    
                    logger.info(f"Partially closed position: {remaining_amount:.6f} {asset}, P&L: {pnl:.2f}")
        
        # Remove closed positions
        for i in reversed(positions_to_remove):
            del self.positions[i]
        
        # Update total P&L
        self.total_profit_loss += total_pnl
        
        # Record trade
        self.trade_history.append({
            'action': 'SELL',
            'asset': asset,
            'amount': amount - remaining_amount,
            'price': exit_price,
            'pnl': total_pnl,
            'timestamp': datetime.now()
        })
        
        return total_pnl
    
    def get_asset_amount(self, asset: str) -> float:
        """Get total amount of a specific asset in portfolio"""
        total = sum(pos['amount'] for pos in self.positions if pos['asset'] == asset)
        return total
    
    def update_unrealized_pnl(self, asset: str, current_price: float):
        """Update unrealized P&L for all positions of an asset"""
        for position in self.positions:
            if position['asset'] == asset:
                position['unrealized_pnl'] = (current_price - position['entry_price']) * position['amount']
    
    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L across all positions"""
        return sum(pos['unrealized_pnl'] for pos in self.positions)
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value in MXN"""
        total_value = 0.0
        
        for position in self.positions:
            asset = position['asset']
            amount = position['amount']
            
            if asset in current_prices:
                value = amount * current_prices[asset]
                total_value += value
        
        return total_value
    
    def log_status(self):
        """Log current portfolio status"""
        logger.info("=== Portfolio Status ===")
        logger.info(f"Total Realized P&L: {self.total_profit_loss:.2f} MXN")
        logger.info(f"Total Unrealized P&L: {self.get_total_unrealized_pnl():.2f} MXN")
        logger.info(f"Open Positions: {len(self.positions)}")
        
        for position in self.positions:
            logger.info(f"  {position['asset']}: {position['amount']:.6f} @ {position['entry_price']:.2f} "
                       f"(Unrealized P&L: {position['unrealized_pnl']:.2f})")
        
        logger.info(f"Total Trades: {len(self.trade_history)}")
        logger.info("========================")
    
    def get_performance_stats(self) -> Dict:
        """Get portfolio performance statistics"""
        if not self.trade_history:
            return {}
        
        buy_trades = [t for t in self.trade_history if t['action'] == 'BUY']
        sell_trades = [t for t in self.trade_history if t['action'] == 'SELL']
        
        profitable_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) < 0]
        
        stats = {
            'total_trades': len(buy_trades),
            'completed_trades': len(sell_trades),
            'profitable_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(profitable_trades) / len(sell_trades) if sell_trades else 0,
            'total_realized_pnl': self.total_profit_loss,
            'average_profit': sum(t.get('pnl', 0) for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0,
            'average_loss': sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0,
        }
        
        return stats
