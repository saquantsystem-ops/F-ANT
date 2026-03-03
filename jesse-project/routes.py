from jesse.utils import anchor_timeframe

# Format: (exchange, symbol, timeframe, strategy_name)
routes = [
    ('YFinance', 'SBIN.NS', '1D', 'SMACrossover'),
]

extra_candles = []
