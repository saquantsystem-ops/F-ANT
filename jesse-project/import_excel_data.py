import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Add jesse-ai to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jesse-ai')))

import jesse.helpers as jh
from jesse.models.Candle import store_candles

def import_from_excel(file_path, exchange='Excel', symbol='MY_SYMBOL'):
    print(f"Loading data from {file_path}...")
    
    try:
        # Load Excel file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        print(f"Columns found: {df.columns.tolist()}")
        
        # Standardize column names (case insensitive)
        df.columns = [c.lower() for c in df.columns]
        
        # Map columns
        col_map = {
            'timestamp': ['timestamp', 'time', 'date', 'datetime'],
            'open': ['open'],
            'high': ['high'],
            'low': ['low'],
            'close': ['close'],
            'volume': ['volume', 'vol']
        }
        
        final_cols = {}
        for target, aliases in col_map.items():
            for alias in aliases:
                if alias in df.columns:
                    final_cols[target] = alias
                    break
        
        # Check required columns
        required = ['timestamp', 'open', 'high', 'low', 'close']
        missing = [r for r in required if r not in final_cols]
        if missing:
            print(f"Error: Missing required columns: {missing}")
            print(f"Available columns: {df.columns.tolist()}")
            return

        # Prepare candle data
        candles = []
        for _, row in df.iterrows():
            # Convert timestamp to ms
            raw_ts = row[final_cols['timestamp']]
            if isinstance(raw_ts, str):
                try:
                    ts = int(datetime.strptime(raw_ts, '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
                except:
                    ts = int(datetime.strptime(raw_ts, '%Y-%m-%d').timestamp() * 1000)
            elif isinstance(raw_ts, pd.Timestamp):
                ts = int(raw_ts.timestamp() * 1000)
            else:
                ts = int(raw_ts)

            # Volume column is optional
            vol = row[final_cols['volume']] if 'volume' in final_cols else 0
            
            candle = [
                ts,
                float(row[final_cols['open']]),
                float(row[final_cols['close']]),
                float(row[final_cols['high']]),
                float(row[final_cols['low']]),
                float(vol)
            ]
            candles.append(candle)

        print(f"Prepared {len(candles)} candles.")
        
        # Determine timeframe (1D if only one per day, else infer)
        # For simplicity, we assume the user provides 1D data or 1m data.
        # Jesse needs a timeframe for storage.
        timeframe = '1D' 
        
        # Store in DB
        print(f"Storing candles in database (Exchange={exchange}, Symbol={symbol}, TF={timeframe})...")
        store_candles(np.array(candles), exchange, symbol, timeframe)
        print("Done! Data imported successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import candles from Excel/CSV')
    parser.add_argument('file', help='Path to Excel or CSV file')
    parser.add_argument('--symbol', default='MY_SYMBOL', help='Symbol name (e.g. RELIANCE.NS)')
    parser.add_argument('--exchange', default='Excel', help='Exchange name')
    
    args = parser.parse_args()
    
    import_from_excel(args.file, args.exchange, args.symbol)
