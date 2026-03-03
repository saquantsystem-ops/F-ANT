from jesse.enums import exchanges as exchanges_enums, timeframes
from jesse.services.env import ENV_VALUES

def is_dev_env() -> bool:
    return ENV_VALUES.get('IS_DEV_ENV', '').upper() == 'TRUE'

if is_dev_env():
    JESSE_API_URL = ENV_VALUES.get('JESSE_API_URL', 'http://localhost:8040/api')
    JESSE_API2_URL = ENV_VALUES.get('JESSE_API2_URL', 'http://localhost:8080')
    JESSE_WEBSITE_URL = ENV_VALUES.get('JESSE_WEBSITE_URL', 'http://localhost:8040')
else:
    JESSE_API_URL = 'https://jesse.trade/api'
    JESSE_API2_URL = 'https://api.jesse.trade'
    JESSE_WEBSITE_URL = 'https://jesse.trade'

BYBIT_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_3, timeframes.MINUTE_5, timeframes.MINUTE_15, timeframes.MINUTE_30,
                    timeframes.HOUR_1, timeframes.HOUR_2, timeframes.HOUR_4, timeframes.HOUR_6, timeframes.HOUR_12, timeframes.DAY_1]
BINANCE_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_3, timeframes.MINUTE_5, timeframes.MINUTE_15, timeframes.MINUTE_30,
                      timeframes.HOUR_1, timeframes.HOUR_2, timeframes.HOUR_4, timeframes.HOUR_6, timeframes.HOUR_8, timeframes.HOUR_12, timeframes.DAY_1]
COINBASE_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_5,
                       timeframes.MINUTE_15, timeframes.HOUR_1, timeframes.HOUR_6, timeframes.DAY_1]
APEX_PRO_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_5, timeframes.MINUTE_15,
                       timeframes.MINUTE_30, timeframes.HOUR_1, timeframes.HOUR_2, timeframes.HOUR_4, timeframes.HOUR_6, timeframes.HOUR_12, timeframes.DAY_1]
GATE_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_5, timeframes.MINUTE_15,
                   timeframes.MINUTE_30, timeframes.HOUR_1, timeframes.HOUR_2, timeframes.HOUR_4, timeframes.HOUR_6, timeframes.HOUR_8, timeframes.HOUR_12, timeframes.DAY_1, timeframes.WEEK_1]
FTX_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_3, timeframes.MINUTE_5, timeframes.MINUTE_15, timeframes.MINUTE_30,
                  timeframes.HOUR_1, timeframes.HOUR_2, timeframes.HOUR_4, timeframes.HOUR_6, timeframes.HOUR_12, timeframes.DAY_1]
BITGET_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_5, timeframes.MINUTE_15,
                     timeframes.MINUTE_30, timeframes.HOUR_1, timeframes.HOUR_4, timeframes.HOUR_12, timeframes.DAY_1]
DYDX_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_5, timeframes.MINUTE_15,
                   timeframes.MINUTE_30, timeframes.HOUR_1, timeframes.HOUR_4, timeframes.DAY_1]
HYPERLIQUID_TIMEFRAMES = [timeframes.MINUTE_1, timeframes.MINUTE_3, timeframes.MINUTE_5, timeframes.MINUTE_15,
                         timeframes.MINUTE_30, timeframes.HOUR_1, timeframes.HOUR_2, timeframes.HOUR_4, timeframes.HOUR_8, timeframes.HOUR_12, timeframes.DAY_1]

exchange_info = {
    # Angel One
    exchanges_enums.ANGEL_ONE: {
        "name": exchanges_enums.ANGEL_ONE,
        "url": "https://www.angelone.in",
        "fee": 0.000,
        "type": "spot",
        "supported_leverage_modes": ["cross"],
        "supported_timeframes": [timeframes.MINUTE_1, timeframes.MINUTE_5, timeframes.MINUTE_15, timeframes.HOUR_1, timeframes.DAY_1],
        "modes": {
            "backtesting": True,
            "live_trading": True,
        },
        "required_live_plan": "free",
    },
    # YFinance
    exchanges_enums.YFINANCE: {
        "name": exchanges_enums.YFINANCE,
        "url": "https://finance.yahoo.com",
        "fee": 0.000,
        "type": "spot",
        "supported_leverage_modes": ["cross"],
        "supported_timeframes": [timeframes.MINUTE_1, timeframes.MINUTE_5, timeframes.MINUTE_15, timeframes.MINUTE_30, timeframes.HOUR_1, timeframes.DAY_1, timeframes.WEEK_1, timeframes.MONTH_1],
        "modes": {
            "backtesting": True,
            "live_trading": False,
        },
        "required_live_plan": "free",
    },
}

# list of supported exchanges for backtesting
backtesting_exchanges = [k for k, v in exchange_info.items() if v['modes']['backtesting'] is True]
backtesting_exchanges = list(sorted(backtesting_exchanges))

# list of supported exchanges for live trading
live_trading_exchanges = [k for k, v in exchange_info.items() if v['modes']['live_trading'] is True]
live_trading_exchanges = list(sorted(live_trading_exchanges))

# used for backtesting, and live trading when local candle generation is enabled:
jesse_supported_timeframes = [
    timeframes.MINUTE_1,
    timeframes.MINUTE_3,
    timeframes.MINUTE_5,
    timeframes.MINUTE_15,
    timeframes.MINUTE_30,
    timeframes.MINUTE_45,
    timeframes.HOUR_1,
    timeframes.HOUR_2,
    timeframes.HOUR_3,
    timeframes.HOUR_4,
    timeframes.HOUR_6,
    timeframes.HOUR_8,
    timeframes.HOUR_12,
    timeframes.DAY_1,
]
