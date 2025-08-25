"""Self-check script for Bitso trading bot after recent fee & freshness changes.
Runs a single dry-run trading cycle with a stub API to ensure no exceptions and basic logic works.
"""
import os
import sys
import random
import logging
from datetime import datetime

# Ensure src is on path for both package and direct module imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from src.trading_bot import TradingBot  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("self_check")


class StubAPI:
    """Stub Bitso API to avoid real network calls during integrity check."""
    def __init__(self):
        self.counter = 0

    def get_ticker(self, book: str = 'eth_mxn'):
        # Simulate mild price drift
        base = 50000 + (self.counter * 10)
        self.counter += 1
        return {"success": True, "payload": {"last": f"{base + random.randint(-50,50):.2f}"}}

    def get_account_status(self):
        return {"success": True, "payload": {"status": "active"}}

    def get_balance(self):
        # Provide plenty of MXN balance
        return {"success": True, "payload": {"balances": [
            {"currency": "mxn", "available": "100000", "locked": "0"}
        ]}}

    def place_order(self, **kwargs):
        return {"success": True, "payload": {"oid": "stub-order", "original_amount": kwargs.get('major') or kwargs.get('minor')}}


def run_self_check():
    # Ensure DRY_RUN
    os.environ['DRY_RUN'] = 'True'
    os.environ.setdefault('FEE_MAKER', '0.005')
    os.environ.setdefault('FEE_TAKER', '0.0065')
    os.makedirs('logs', exist_ok=True)

    bot = TradingBot()
    # Replace real API with stub
    bot.api = StubAPI()

    # Force a single trading pair & seed history to reach indicator threshold quicker
    bot.trading_pairs = ['eth_mxn']
    import pandas as pd
    now = datetime.now()
    prices = [50000 + i*5 for i in range(55)]  # 55 points for strategy readiness
    bot.price_histories['eth_mxn'] = pd.DataFrame({
        'timestamp': [now for _ in prices],  # all fresh points
        'price': prices
    })

    try:
        bot.run_trading_cycle()
        logger.info("Self-check cycle completed without exceptions.")
        # Summarize portfolio
        if bot.portfolio.positions:
            logger.info(f"Open positions after cycle: {len(bot.portfolio.positions)}")
        logger.info(f"Total realized P&L: {bot.portfolio.total_profit_loss:.2f} MXN")
        logger.info(f"Total fees tracked: {bot.portfolio.total_fees_paid:.2f} MXN")
        return 0
    except Exception as e:
        logger.exception("Self-check failed: %s", e)
        return 1


if __name__ == '__main__':
    exit(run_self_check())
