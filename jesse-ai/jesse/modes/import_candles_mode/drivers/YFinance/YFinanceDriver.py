"""
YFinance Driver for Jesse
Provides free historical data for stocks, crypto, and forex from Yahoo Finance.

Supported symbols:
- Indian Stocks: RELIANCE.NS, TCS.NS, INFY.NS, SBIN.NS (NSE)
- Indian Stocks: RELIANCE.BO, TCS.BO (BSE)
- US Stocks: AAPL, GOOGL, MSFT, AMZN
- Crypto: BTC-USD, ETH-USD, BNB-USD
- Forex: EURUSD=X, GBPUSD=X, USDINR=X
"""

from datetime import datetime, timedelta
import time
import jesse.helpers as jh
from jesse.enums import exchanges
from jesse.modes.import_candles_mode.drivers.interface import CandleExchange

try:
    import yfinance as yf
except ImportError:
    yf = None
    print("yfinance not installed. Please run: pip install yfinance")


class YFinanceDriver(CandleExchange):
    def __init__(self):
        # Rate limit: Yahoo Finance is lenient but we should be respectful
        # 2000 requests per hour / 3600 = ~0.55 per second, we use 0.5
        super().__init__(
            name=exchanges.YFINANCE,
            count=500,  # Number of candles per request
            rate_limit_per_second=0.5,
            backup_exchange_class=None
        )
        
        if yf is None:
            raise ImportError("yfinance package not installed. Run: pip install yfinance")
    
    def fetch(self, symbol: str, start_timestamp: int, timeframe: str) -> list:
        """
        Fetch candles from Yahoo Finance.
        
        Args:
            symbol: Yahoo Finance symbol (e.g., 'RELIANCE.NS', 'BTC-USD', 'AAPL')
            start_timestamp: Start time in milliseconds
            timeframe: Jesse timeframe (e.g., '1m', '5m', '1h', '1D')
            
        Returns:
            List of candles in format: [[timestamp, open, close, high, low, volume], ...]
        """
        try:
            # Normalize symbol for YFinance
            # Convert Angel One format (-EQ) to YFinance format (.NS)
            if symbol.endswith('-EQ'):
                symbol = symbol.replace('-EQ', '.NS')
            
            # Convert timestamp from ms to datetime
            start_date = datetime.fromtimestamp(start_timestamp / 1000)
            
            # For import, we ALWAYS use daily data since 1m/1h historical data
            # is very limited on YFinance (only 7-60 days back)
            interval = '1d'
            
            # Get data up to today
            end_date = datetime.now()
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            df = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval=interval,
                auto_adjust=True,  # Adjust for splits and dividends
                prepost=False  # Don't include pre/post market data
            )
            
            if df.empty:
                jh.debug(f"YFinance: No data returned for {symbol} from {start_date} to {end_date}")
                return []
            
            # Convert to Jesse candle format dict: {timestamp, open, close, high, low, volume}
            # Note: We return dicts, not lists, for the import mode
            candles = []
            for index, row in df.iterrows():
                # Convert index to timestamp in milliseconds
                ts = int(index.timestamp() * 1000)
                
                candles.append({
                    'id': jh.generate_unique_id(),
                    'exchange': self.name,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': ts,
                    'open': float(row['Open']),
                    'close': float(row['Close']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'volume': float(row['Volume'])
                })
            
            return candles
            
        except Exception as e:
            jh.debug(f"YFinance fetch error for {symbol}: {str(e)}")
            return []
    
    def get_starting_time(self, symbol: str) -> int:
        """
        Get the earliest available timestamp for a symbol.
        
        Yahoo Finance has different data availability:
        - 1m data: last 30 days only
        - 5m-30m data: last 60 days
        - 1h data: last 730 days
        - 1d+ data: many years of history
        
        We return a conservative estimate based on daily data availability.
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="max", interval="1d")
            
            if not hist.empty:
                first_date = hist.index[0]
                return int(first_date.timestamp() * 1000)
            
            # Default: return 5 years ago
            default_start = datetime.now() - timedelta(days=5*365)
            return int(default_start.timestamp() * 1000)
            
        except Exception as e:
            jh.debug(f"YFinance get_starting_time error for {symbol}: {str(e)}")
            # Default: return 5 years ago
            default_start = datetime.now() - timedelta(days=5*365)
            return int(default_start.timestamp() * 1000)
    
    def get_available_symbols(self) -> list:
        """
        Return a list of common/popular symbols.
        Yahoo Finance doesn't have a simple API to list all symbols,
        so we return some popular ones.
        """
        return [
            # Indian Stocks (NSE)
            'RELIANCE.NS',
            'TCS.NS',
            'INFY.NS',
            'HDFCBANK.NS',
            'ICICIBANK.NS',
            'SBIN.NS',
            'BHARTIARTL.NS',
            'ITC.NS',
            'KOTAKBANK.NS',
            'LT.NS',
            'AXISBANK.NS',
            'WIPRO.NS',
            'HINDUNILVR.NS',
            'MARUTI.NS',
            'TATAMOTORS.NS',
            'TATASTEEL.NS',
            'BAJFINANCE.NS',
            'NTPC.NS',
            'POWERGRID.NS',
            'ONGC.NS',
            
            # US Stocks
            'AAPL',
            'GOOGL',
            'MSFT',
            'AMZN',
            'META',
            'TSLA',
            'NVDA',
            'JPM',
            'V',
            'JNJ',
            
            # Crypto
            'BTC-USD',
            'ETH-USD',
            'BNB-USD',
            'XRP-USD',
            'SOL-USD',
            'ADA-USD',
            'DOGE-USD',
            
            # Forex
            'EURUSD=X',
            'GBPUSD=X',
            'USDJPY=X',
            'USDINR=X',
            'AUDUSD=X',
        ]
    
    def _map_timeframe(self, tf: str) -> str:
        """
        Map Jesse timeframe to Yahoo Finance interval.
        
        Yahoo Finance intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        """
        mapping = {
            '1m': '1m',
            '3m': '5m',      # 3m not available, use 5m
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '45m': '60m',    # 45m not available, use 60m
            '1h': '60m',
            '2h': '60m',     # 2h not available, use 60m (will aggregate)
            '3h': '60m',     # 3h not available
            '4h': '60m',     # 4h not available
            '6h': '60m',     # 6h not available
            '8h': '60m',     # 8h not available
            '12h': '60m',    # 12h not available
            '1D': '1d',
            '3D': '1d',      # 3D not available, use 1d
            '1W': '1wk',
            '1M': '1mo',
        }
        return mapping.get(tf, '1d')
