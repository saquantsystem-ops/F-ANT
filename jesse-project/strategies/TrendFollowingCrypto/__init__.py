from jesse.strategies import Strategy
import jesse.indicators as ta
import jesse.helpers as jh

class TrendFollowingCrypto(Strategy):
    def __init__(self):
        super().__init__()
        self.fast_ema = 0
        self.slow_ema = 0

    @property
    def fast_ema_val(self):
        return ta.ema(self.candles, 12)

    @property
    def slow_ema_val(self):
        return ta.ema(self.candles, 26)

    def should_long(self) -> bool:
        # Long if fast EMA crosses above slow EMA
        return self.fast_ema_val > self.slow_ema_val and self.fast_ema_val > self.slow_ema_val * 1.001

    def should_short(self) -> bool:
        # Spot exchange support only (no shorting)
        return False

    def should_cancel_entry(self) -> bool:
        return True

    def go_long(self):
        # Use 98% of balance to avoid float precision issues
        qty = jh.size_to_qty(self.balance * 0.98, self.price, fee_rate=self.fee_rate)
        self.buy = qty, self.price

    def go_short(self):
        pass

    def on_open_position(self, order):
        pass

    def update_position(self):
        # Exit if fast EMA crosses below slow EMA
        if self.fast_ema_val < self.slow_ema_val:
            self.liquidate()

    def filters(self):
        return []

    def hyperparameters(self):
        return [
            {'name': 'fast_ema_period', 'type': int, 'min': 5, 'max': 50, 'default': 12},
            {'name': 'slow_ema_period', 'type': int, 'min': 20, 'max': 200, 'default': 26},
        ]
