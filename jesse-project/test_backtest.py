
import os
import sys

# Add jesse-ai source to path
sys.path.insert(0, r"c:\Users\DELL\Desktop\jesse_backup\jesse-ai")

import jesse.helpers as jh
from jesse.services.db import database
from jesse import research
from jesse.config import config
from jesse.routes import router

# Initialize DB connection
database.open_connection()

# Set up configuration for YFinance (Backtest mode)
config['app']['trading_mode'] = 'backtest'

print("Setting up routes...")
router.set_routes([
    ('YFinance', 'RELIANCE.NS', '1D', 'SMACrossover')
])

print("Fetching candles...")
# Fetch candles manually to verify they exist
start_ts = jh.date_to_timestamp('2018-01-01') 
end_ts = jh.date_to_timestamp('2024-01-01')
print(f"Fetching candles from {start_ts} to {end_ts}...")

# research.get_candles returns (warmup_candles, trading_candles)
candles_tuple = research.get_candles('YFinance', 'RELIANCE.NS', '1D', start_ts, end_ts)
warmup_from_fetch, trading_data_all = candles_tuple

# print info
if warmup_from_fetch is not None:
    print(f"Fetch returned Warmup set: {len(warmup_from_fetch)} candles")
else:
    print("Fetch returned NO Warmup set (None)")

if trading_data_all is not None:
    print(f"Fetch returned Trading set: {len(trading_data_all)} candles")
else:
    print("Fetch returned NO Trading set!")
    exit()

if len(trading_data_all) < 250:
    print("ERROR: Not enough candles found for backtest!")
    exit()

# Setup correct candles for backtest
# We simulate our own warmup split from the fetched 'trading_data_all'
# Taking first 210 as warmup
warmup_data = trading_data_all[:210]
trading_data_real = trading_data_all[210:]

print(f"Using {len(warmup_data)} candles for warmup.")
print(f"Using {len(trading_data_real)} candles for simulation.")

# Prepare candles dictionary for backtest inputs
candles_dict = {
    'YFinance-RELIANCE.NS': {
        'exchange': 'YFinance',
        'symbol': 'RELIANCE.NS',
        'candles': trading_data_real
    }
}

warmup_candles_dict = {
    'YFinance-RELIANCE.NS': {
        'exchange': 'YFinance',
        'symbol': 'RELIANCE.NS',
        'candles': warmup_data
    }
}

print("Running backtest logic...")

try:
    backtest_result = research.backtest(
        config={
            'starting_balance': 10000,
            'fee': 0,
            'type': 'spot',
            'futures_leverage': 1,
            'futures_leverage_mode': 'cross',
            'exchange': 'YFinance',
            'warm_up_candles': 210
        },
        routes=[{'exchange': 'YFinance', 'symbol': 'RELIANCE.NS', 'timeframe': '1D', 'strategy': 'SMACrossover'}],
        data_routes=[], 
        candles=candles_dict,
        warmup_candles=warmup_candles_dict
    )
    
    print("\nBacktest SUCCESSFUL!")
    metrics = backtest_result['metrics']
    if metrics:
        print(f"Total Trades: {metrics['total']}")
        print(f"Net Profit: {metrics['net_profit_percentage']}%")
        print(f"Win Rate: {metrics['win_rate']}%")
    else:
        print("No metrics returned (maybe no trades).")

except Exception as e:
    print(f"\nBacktest FAILED with error: {e}")
    import traceback
    traceback.print_exc()

database.close_connection()
