from datetime import datetime
import time
from SmartApi import SmartConnect
import pyotp
import jesse.helpers as jh
import jesse.enums as exchanges
from jesse.modes.import_candles_mode.drivers.interface import CandleExchange
try:
    import jesse_project.jesse.config as config
except ImportError:
    try:
        import jesse.config as config
    except ImportError:
        config = None

class AngelOne(CandleExchange):
    def __init__(self):
        # Rate limit: Angel One has specific limits, setting conservative default
        super().__init__('Angel One', 1000, 1.0, None)
        self.smart_api = None
        self.initialize_connection()

    def initialize_connection(self):
        try:
            # We need to temporarily access the user's config to get credentials for importing candles
            # This is a bit tricky as 'jesse.config' might not be fully loaded or available in this context
            # depending on how 'import-candles' mode is run. 
            # Ideally, we should prompt or use environment variables, but sticking to the user's setup:
            
            # Accessing from global config if possible, or re-reading .env
            from jesse.services.env import ENV_VALUES
            
            # Assuming the user uses the same env structure for now, but we might need to rely on static lookup if config isn't populated
            # However, for CandleExchange, we usually don't need auth for public data, BUT Angel One requires Auth for historical data.
            
            # FIXME: Hardcoding or fetching logic needs to be robust. 
            # For now, we will attempt to connect using the same logic as the main driver, 
            # but we need to check if we can access the config store.
            
            import jesse.services.env as env_module
            # Re-read env if needed (though jesse usually loads it)
            
            # Attempt to find Angel One keys in probable locations if not in loaded config
            # Note: In standard Jesse, import-candles might run without full app boot.
            
            api_key = ENV_VALUES.get('ANGEL_ONE_API_KEY') 
            client_code = ENV_VALUES.get('ANGEL_ONE_CLIENT_CODE')
            password = ENV_VALUES.get('ANGEL_ONE_PASSWORD')
            totp_key = ENV_VALUES.get('ANGEL_ONE_TOTP_KEY')

            # Fallback for the user's specific request context where they might have set it in specific keys
            # or if we want to reuse the 'exchanges' config structure if available.
           
            if not api_key: 
                 # Try to look into the loaded config if available
                 pass

            if api_key and client_code and password and totp_key:
                self.smart_api = SmartConnect(api_key=api_key)
                totp = pyotp.TOTP(totp_key).now()
                data = self.smart_api.generateSession(client_code, password, totp)
                if data['status']:
                    print("Angel One Candle Driver Connected")
                else:
                    print(f"Angel One Candle Driver Connection Failed: {data['message']}")
            else:
                print("Angel One credentials missing for candle import. Please ensure ANGEL_ONE_API_KEY, ANGEL_ONE_CLIENT_CODE, ANGEL_ONE_PASSWORD, ANGEL_ONE_TOTP_KEY are in .env")

        except Exception as e:
            print(f"Error initializing Angel One Candle Driver: {str(e)}")


    def fetch(self, symbol: str, start_timestamp: int, timeframe: str) -> list:
        if not self.smart_api:
            return []
            
        # Convert timestamp to required format
        # start_timestamp is usually ms
        from_date = datetime.fromtimestamp(start_timestamp / 1000).strftime('%Y-%m-%d %H:%M')
        # We need to decide end_date, usually fetch a chunk. 
        # Jesse usually manages the loop, we just need to return a batch.
        # Angel One max limit per request needs respecting.
        
        # Let's fetch 30 days chunk or as requested
        # Note: 'symbol' here is typically 'BTC-USDT', we need to map to Angel One Token.
        # This requires a symbol mapping mechanism. 
        # For simplicity/demo, assuming symbol IS the token or we have a map.
        # REALITY: We need to search symbol token.
        
        try:
            token_info = self.smart_api.searchScrip("NSE", symbol) # Assuming NSE equity for now
            if token_info['status'] and len(token_info['data']) > 0:
                 symbol_token = token_info['data'][0]['symboltoken']
            else:
                 print(f"Symbol {symbol} not found")
                 return []
                 
            # Calculating end date (e.g. +30 days effectively or until now)
            # This is a simplified fetch
            to_date = datetime.now().strftime('%Y-%m-%d %H:%M') # Just fetch until now for this chunk implementation demo
            
            historicParam = {
                "exchange": "NSE",
                "symboltoken": symbol_token,
                "interval": self._map_timeframe(timeframe),
                "fromdate": from_date, 
                "todate": to_date
            }
            
            data = self.smart_api.getCandleData(historicParam)
            
            if data['status'] and data['data']:
                # Map back to Jesse format: [timestamp, open, close, high, low, volume]
                candles = []
                for c in data['data']:
                    # Angel format: timestamp(str), open, high, low, close, volume
                    # "2021-02-12T09:15:00+05:30"
                    ts_str = c[0]
                    # Parse TS string to timestamp ms
                    dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S%z")
                    ts = int(dt.timestamp() * 1000)
                    
                    candles.append([
                        ts,
                        float(c[1]),
                        float(c[4]), # Close
                        float(c[2]), # High
                        float(c[3]), # Low
                        float(c[5])
                    ])
                return candles
            else:
                 return []
                 
        except Exception as e:
            print(f"Error fetching candles: {e}")
            return []

    def get_starting_time(self, symbol: str) -> int:
        # Hardcoding or implementing logic to find list date
        # Returning a default for now
        return int(datetime(2020, 1, 1).timestamp() * 1000)

    def get_available_symbols(self) -> list:
        # Return a dummy list or dynamic fetch
        return ["SBIN-EQ", "RELIANCE-EQ"] # Examples

    def _map_timeframe(self, tf):
        # Map Jesse timeframe to Angel One interval
        mapping = {
            '1m': 'ONE_MINUTE',
            '3m': 'THREE_MINUTE',
            '5m': 'FIVE_MINUTE',
            '15m': 'FIFTEEN_MINUTE',
            '30m': 'THIRTY_MINUTE',
            '1h': 'ONE_HOUR',
            '1D': 'ONE_DAY'
        }
        return mapping.get(tf, 'ONE_DAY')
