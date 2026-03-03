"""
Simple Always Trade Strategy for Jesse Testing
This strategy generates trades to demonstrate the dashboard
"""
from jesse.strategies import Strategy
import jesse.indicators as ta


class SMACrossover(Strategy):
    """
    Modified SMA Crossover - More Aggressive Trading
    Generates more trades for testing purposes
    """
    
    def __init__(self):
        super().__init__()
        self.last_signal = None
    
    @property
    def fast_sma_period(self) -> int:
        return self.hp.get('fast_period', 10)
    
    @property
    def slow_sma_period(self) -> int:
        return self.hp.get('slow_period', 30)
    
    @property
    def fast_sma(self):
        return ta.sma(self.candles, self.fast_sma_period)
    
    @property
    def slow_sma(self):
        return ta.sma(self.candles, self.slow_sma_period)
    
    def should_long(self) -> bool:
        # Go long when fast SMA crosses above slow SMA
        # Simplified logic: just check if fast > slow and we're not already long
        if self.fast_sma > self.slow_sma and not self.is_long:
            return True
        return False
    
    def should_short(self) -> bool:
        # Shorting is disabled for spot exchanges (like YFinance)
        return False
    
    def should_cancel_entry(self) -> bool:
        return False
    
    def go_long(self):
        # Use 98% of balance to avoid float precision errors
        qty = (self.balance * 0.98) / self.price
        if qty > 0:
            self.buy = qty, self.price
    
    def go_short(self):
        # Use 98% of balance to avoid float precision errors
        qty = (self.balance * 0.98) / self.price
        if qty > 0:
            self.sell = qty, self.price
    
    def update_position(self):
        # Exit when fast SMA crosses below slow SMA
        if self.is_long and self.fast_sma < self.slow_sma:
            self.liquidate()
    
    def hyperparameters(self):
        return [
            {'name': 'fast_period', 'type': int, 'min': 2, 'max': 20, 'default': 2},
            {'name': 'slow_period', 'type': int, 'min': 5, 'max': 50, 'default': 5},
        ]
