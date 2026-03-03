
import os
import sys

# Add jesse-ai source to path
sys.path.insert(0, r"c:\Users\DELL\Desktop\jesse_backup\jesse-ai")

import jesse.helpers as jh
from jesse.services.db import database
from jesse.models.Candle import Candle

database.open_connection()

print("Checking DB content...")
count = Candle.select().count()
print(f"Total candles in DB: {count}")

if count > 0:
    first = Candle.select().first()
    print(f"First candle: Exchange={first.exchange}, Symbol={first.symbol}, TF={first.timeframe}, TS={first.timestamp}")
    
    # Check SBIN.NS specifically
    rel_count = Candle.select().where(Candle.symbol == 'SBIN.NS').count()
    print(f"SBIN.NS candles: {rel_count}")
    
    if rel_count > 0:
        rel_first = Candle.select().where(Candle.symbol == 'SBIN.NS').order_by(Candle.timestamp.asc()).first()
        rel_last = Candle.select().where(Candle.symbol == 'SBIN.NS').order_by(Candle.timestamp.desc()).first()
        print(f"SBIN.NS Range: {rel_first.timestamp} ({jh.timestamp_to_date(rel_first.timestamp)}) to {rel_last.timestamp} ({jh.timestamp_to_date(rel_last.timestamp)})")
        print(f"Timeframe stored: {rel_first.timeframe}")

database.close_connection()
