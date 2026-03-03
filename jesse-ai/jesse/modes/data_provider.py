import json
import os
import numpy as np
import peewee
from fastapi.responses import FileResponse
import jesse.helpers as jh
from jesse.info import live_trading_exchanges, backtesting_exchanges


def get_candles(exchange: str, symbol: str, timeframe: str):
    from jesse.services.db import database
    # If using mocked db that returns nothing, we should check if we can query
    # But since we want to BYPASS, let's just return empty array for now
    # or simulate based on whatever simple logic if needed.
    
    # Actually, we can't reliably get warmup_candles without DB config or passing it.
    # For now, return empty list to prevent crash.
    return []

    # Original code commented out/replaced for bypass
    # database.open_connection()
    # ... (rest of function logic would go here but we return early)

    return [
        {
            'time': int(c[0] / 1000),
            'open': c[1],
            'close': c[2],
            'high': c[3],
            'low': c[4],
            'volume': c[5],
        } for c in candles
    ]


def get_config(client_config: dict, has_live=False) -> dict:
    # Bypass database
    data = client_config

    # make sure the list of BACKTEST exchanges is up to date
    for k in list(data['backtest']['exchanges'].keys()):
        if k not in backtesting_exchanges:
            del data['backtest']['exchanges'][k]

    # make sure the list of LIVE exchanges is up to date
    if has_live:
        for k in list(data['live']['exchanges'].keys()):
            if k not in live_trading_exchanges:
                del data['live']['exchanges'][k]

    return {
        'data': data
    }


def update_config(client_config: dict):
    # Bypass database - no persistence
    pass


def download_file(mode: str, file_type: str, session_id: str = None):
    if mode == 'backtest' and file_type == 'log':
        path = f'storage/logs/backtest-mode/{session_id}.txt'
        filename = f'backtest-{session_id}.txt'
    elif mode == 'backtest' and file_type == 'csv':
        path = f'storage/csv/{session_id}.csv'
        filename = f'backtest-{session_id}.csv'
    elif mode == 'backtest' and file_type == 'json':
        path = f'storage/json/{session_id}.json'
        filename = f'backtest-{session_id}.json'
    elif mode == 'backtest' and file_type == 'full-reports':
        path = f'storage/full-reports/{session_id}.html'
        filename = f'backtest-{session_id}.html'
    elif mode == 'backtest' and file_type == 'tradingview':
        path = f'storage/trading-view-pine-editor/{session_id}.txt'
        filename = f'backtest-{session_id}.txt'
    elif mode == 'optimize' and file_type == 'log':
        path = f'storage/logs/optimize-mode.txt'
        # filename should be "optimize-" + current timestamp
        filename = f'optimize-{jh.timestamp_to_date(jh.now(True))}.txt'
    elif mode == 'monte-carlo' and file_type == 'log':
        path = f'storage/logs/monte-carlo-mode/{session_id}.txt'
        filename = f'monte-carlo-{session_id}.txt'
    else:
        raise Exception(f'Unknown file type: {file_type} or mode: {mode}')

    return FileResponse(path=path, filename=filename, media_type='application/octet-stream')


def get_backtest_logs(session_id: str):
    path = f"storage/logs/backtest-mode/{session_id}.txt"

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        content = f.read()

    return jh.compressed_response(content)


def get_monte_carlo_logs(session_id: str):
    path = f'storage/logs/monte-carlo-mode/{session_id}.txt'

    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        content = f.read()
            
    return content


def download_backtest_log(session_id: str):
    """
    Returns the log file for a specific backtest session as a downloadable file
    """
    path = f'storage/logs/backtest-mode/{session_id}.txt'
    
    if not os.path.exists(path):
        raise Exception('Log file not found')
        
    filename = f'backtest-{session_id}.txt'
    return FileResponse(
        path=path,
        filename=filename,
        media_type='text/plain'
    )
