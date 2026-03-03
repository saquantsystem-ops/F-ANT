import jesse.helpers as jh
from jesse.enums import exchanges
from jesse.modes.import_candles_mode.drivers.interface import CandleExchange

class ExcelDriver(CandleExchange):
    def __init__(self):
        super().__init__(
            name=exchanges.EXCEL,
            count=1000,
            rate_limit_per_second=10,
            backup_exchange_class=None
        )
    
    def fetch(self, symbol: str, start_timestamp: int, timeframe: str) -> list:
        # Excel data is local and already imported into DB
        # This fetch is just a stub for the interface
        return []
    
    def get_starting_time(self, symbol: str) -> int:
        return 0
    
    def get_available_symbols(self) -> list:
        # We can dynamically get this from DB if needed
        return ['MY_SYMBOL']
