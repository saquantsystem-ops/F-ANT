from jesse.exchanges.exchange import Exchange
from jesse.models import Order
from jesse.enums import order_types
import jesse.helpers as jh
from jesse.store import store
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import pyotp
import jesse

class AngelOne(Exchange):
    def __init__(self, name='Angel One'):
        super().__init__()
        self.name = name
        self.smart_api = None
        self.session = None
        self.initialize_connection()

    def initialize_connection(self):
        # Fetch credentials from Jesse's configuration
        # Note: You need to ensure these are set in your config or .env
        api_key = jesse.config['env']['exchanges'][self.name]['api_key'] 
        client_code = jesse.config['env']['exchanges'][self.name]['username'] 
        password = jesse.config['env']['exchanges'][self.name]['password']
        totp_key = jesse.config['env']['exchanges'][self.name]['api_secret'] # Mapping API Secret to TOTP Key

        if not api_key or not client_code or not password:
             jh.error(f"Missing configuration for {self.name}. Please check your API keys.")
             return

        try:
            self.smart_api = SmartConnect(api_key=api_key)
            # Generate TOTP
            totp = pyotp.TOTP(totp_key).now()
            data = self.smart_api.generateSession(client_code, password, totp)
            
            if data['status']:
                self.session = data['data']
                print(f"Successfully connected to {self.name}")
                
                # Initialize WebSocket for Live Data
                self.init_websocket(client_code, data['data']['feedToken'], data['data']['jwtToken'])
            else:
                 jh.error(f"Connection failed to {self.name}: {data['message']}")

        except Exception as e:
            jh.error(f"Error connecting to {self.name}: {str(e)}")

    def init_websocket(self, client_code, feed_token, jwt_token):
        self.sws = SmartWebSocketV2(jwt_token, self.smart_api.api_key, client_code, feed_token)
        
        def on_data(wsapp, msg):
            # Handle tick data
            # print("Ticks: {}".format(msg))
            pass
            
        def on_open(wsapp):
            print("on open")
            
        def on_close(wsapp):
            print("on close")
            
        self.sws.on_data = on_data
        self.sws.on_open = on_open
        self.sws.on_close = on_close
        self.sws.connect()

    def market_order(self, symbol: str, qty: float, current_price: float, side: str, reduce_only: bool) -> Order:
        try:
             orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": symbol, # Needs mapping to Angel Symbol
                "symboltoken": "3045", # FIXME: dynamic token lookup needed
                "transactiontype": "BUY" if side == 'buy' else "SELL",
                "exchange": "NSE",
                "ordertype": "MARKET",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": "0",
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(qty)
                }
             order_id = self.smart_api.placeOrder(orderparams)
             
             order = Order({
                'id': order_id, # Use Angel One Order ID
                'symbol': symbol,
                'exchange': self.name,
                'side': side,
                'type': order_types.MARKET,
                'reduce_only': reduce_only,
                'qty': jh.prepare_qty(qty, side),
                'price': current_price,
                'status': 'ACTIVE' 
            })
             store.orders.add_order(order)
             store.orders.to_execute.append(order)
             return order
        except Exception as e:
            jh.error(f"Failed to place order: {e}")
            return None 

