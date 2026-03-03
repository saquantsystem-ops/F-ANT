
import os
import sys

# Add jesse-ai source to path FIRST
sys.path.insert(0, r"c:\Users\DELL\Desktop\jesse_backup\jesse-ai")

import jesse.helpers as jh
from jesse.services.db import database

# Initialize DB connection
database.open_connection()

from jesse.models.Candle import Candle, store_candles_into_db
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

def import_data():
    symbols = [
        ('BTC-USD', '1h'),
        ('ETH-USD', '1h'),
        ('RELIANCE.NS', '1h'),
        ('SBIN.NS', '1h'),
        ('BTC-USD', '1D'),
        ('ETH-USD', '1D'),
        ('RELIANCE.NS', '1D'),
        ('SBIN.NS', '1D'),
    ]
    
    print("Creating Candle table if it doesn't exist...")
    if not database.db.table_exists('candle'):
        database.db.create_tables([Candle])
        print("Candle table created.")
    else:
        print("Candle table already exists.")

    print(f"Starting import for {len(symbols)} symbols...")
    
    for symbol, timeframe in symbols:
        print(f"\nProcessing {symbol} ({timeframe})...")
        
        try:
            # Mapping timeframe for yfinance
            yf_interval = '1d' if timeframe == '1D' else '60m'
            yf_period = '5y' if timeframe == '1D' else '730d'

            # Fetch data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=yf_period, interval=yf_interval)
            
            if hist.empty:
                print(f"No data found for {symbol}")
                continue
                
            print(f"Downloaded {len(hist)} candles for {symbol}")
            
            candles_np = []
            for index, row in hist.iterrows():
                # Timestamp in ms
                ts = int(index.timestamp() * 1000)
                
                # OHLCV
                open_val = row['Open']
                high_val = row['High']
                low_val = row['Low']
                close_val = row['Close']
                vol_val = row['Volume']
                
                candles_np.append([ts, open_val, close_val, high_val, low_val, vol_val])
                
            # Store in DB
            candles_np = np.array(candles_np)
            store_candles_into_db('YFinance', symbol, timeframe, candles_np, on_conflict='ignore')
            print(f"Successfully stored {len(candles_np)} candles in DB for {symbol}")
            
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")

    print("\nImport completed successfully!")
    database.close_connection()

if __name__ == "__main__":
    import_data()
