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
        self.total_profit_loss = 0.0  # Net after fees
        self.total_fees_paid = 0.0
        self.trade_history = []
    
    def add_position(self, asset: str, amount: float, entry_price: float, fee_rate: float = 0.0):
        """Add a new position to the portfolio.
        entry_price should already include fees: raw_price * (1 + fee_rate).
        fee_rate stored for reference.
        """
        position = {
            'asset': asset,
            'amount': amount,
            'entry_price': entry_price,
            'entry_time': datetime.now(),
            'unrealized_pnl': 0.0,
            'entry_fee_rate': fee_rate
        }
        self.positions.append(position)
        
        # Record trade
        self.trade_history.append({
            'action': 'BUY',
            'asset': asset,
            'amount': amount,
            'price': entry_price,
            'fee_rate': fee_rate,
            'timestamp': datetime.now()
        })
        
        logger.info(f"Added position: {amount:.6f} {asset} at {entry_price:.2f}")
    
    def close_position(self, asset: str, amount: float, exit_price: float, fee_rate: float = 0.0):
        """Close a position (full or partial).
        exit_price is raw; net proceeds = exit_price * (1 - fee_rate).
        PnL is computed using fee-inclusive entry_price vs net exit.
        """
        remaining_amount = amount
        total_pnl = 0.0
        total_fee_value = 0.0
        
        # Find and close positions (FIFO)
        positions_to_remove = []
        for i, position in enumerate(self.positions):
            if position['asset'] == asset and remaining_amount > 0:
                if position['amount'] <= remaining_amount:
                    net_exit_price = exit_price * (1 - fee_rate)
                    pnl = (net_exit_price - position['entry_price']) * position['amount']
                    total_pnl += pnl
                    total_fee_value += position['amount'] * exit_price * fee_rate
                    remaining_amount -= position['amount']
                    positions_to_remove.append(i)
                    logger.info(f"Closed position: {position['amount']:.6f} {asset}, Net P&L: {pnl:.2f}")
                else:
                    net_exit_price = exit_price * (1 - fee_rate)
                    pnl = (net_exit_price - position['entry_price']) * remaining_amount
                    total_pnl += pnl
                    total_fee_value += remaining_amount * exit_price * fee_rate
                    position['amount'] -= remaining_amount
                    logger.info(f"Partially closed position: {remaining_amount:.6f} {asset}, Net P&L: {pnl:.2f}")
                    remaining_amount = 0
        
        # Remove closed positions
        for i in reversed(positions_to_remove):
            del self.positions[i]
        
        # Update total P&L
        self.total_profit_loss += total_pnl
        self.total_fees_paid += total_fee_value
            
        # Record trade
        self.trade_history.append({
            'action': 'SELL',
            'asset': asset,
            'amount': amount - remaining_amount,
            'price': exit_price,
            'fee_rate': fee_rate,
            'fee_value': total_fee_value,
            'pnl': total_pnl,
            'timestamp': datetime.now()
        })
        
        return total_pnl
    
    def get_asset_amount(self, asset: str) -> float:
        """Get total amount of a specific asset in portfolio"""
        total = sum(pos['amount'] for pos in self.positions if pos['asset'] == asset)
        return total
    
    def clear_asset_positions(self, asset: str):
        """Clear all positions for a specific asset (used for sync corrections)"""
        original_count = len(self.positions)
        self.positions = [pos for pos in self.positions if pos['asset'] != asset]
        removed_count = original_count - len(self.positions)
        
        if removed_count > 0:
            logger.warning(f"Cleared {removed_count} positions for {asset} due to balance mismatch")
    
    def update_unrealized_pnl(self, asset: str, current_price: float):
        """Update unrealized P&L for all positions of an asset"""
        for position in self.positions:
            if position['asset'] == asset:
                # Conservative: assume taker exit fee ~0.65% (hard-coded; could be parameterized)
                estimated_exit_fee_rate = 0.0065
                net_exit_price = current_price * (1 - estimated_exit_fee_rate)
                position['unrealized_pnl'] = (net_exit_price - position['entry_price']) * position['amount']
    
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
            logger.info(f"Total Fees Paid (est): {self.total_fees_paid:.2f} MXN")
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
            'total_fees_paid': self.total_fees_paid,
            'average_profit': sum(t.get('pnl', 0) for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0,
            'average_loss': sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0,
        }
        
        return stats
