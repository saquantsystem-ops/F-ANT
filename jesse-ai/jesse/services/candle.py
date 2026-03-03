from typing import Tuple
import numpy as np
import arrow
from jesse.exceptions import CandleNotFoundInDatabase, InvalidDateRange
import jesse.helpers as jh
from jesse.services import logger
from jesse.models import Candle
from typing import List, Dict


def generate_candle_from_one_minutes(
        timeframe: str,
        candles: np.ndarray,
        accept_forming_candles: bool = False
) -> np.ndarray:
    if len(candles) == 0:
        raise ValueError('No candles were passed')

    if not accept_forming_candles and len(candles) != jh.timeframe_to_one_minutes(timeframe):
        raise ValueError(
            f'Sent only {len(candles)} candles but {jh.timeframe_to_one_minutes(timeframe)} is required to create a "{timeframe}" candle.'
        )

    return np.array([
        candles[0][0],
        candles[0][1],
        candles[-1][2],
        candles[:, 3].max(),
        candles[:, 4].min(),
        candles[:, 5].sum(),
    ])


def candle_dict_to_np_array(candle: dict) -> np.ndarray:
    return np.array([
        candle['timestamp'],
        candle['open'],
        candle['close'],
        candle['high'],
        candle['low'],
        candle['volume']
    ])


def print_candle(candle: np.ndarray, is_partial: bool, symbol: str) -> None:
    """
    Ever since the new GUI dashboard, this function should log instead of actually printing

    :param candle: np.ndarray
    :param is_partial: bool
    :param symbol: str
    """
    if jh.should_execute_silently():
        return

    candle_form = '  ==' if is_partial else '===='
    candle_info = f' {symbol} | {str(arrow.get(candle[0] / 1000))[:-9]} | {candle[1]} | {candle[2]} | {candle[3]} | {candle[4]} | {round(candle[5], 2)}'
    msg = candle_form + candle_info

    # store it in the log file
    logger.info(msg)


def is_bullish(candle: np.ndarray) -> bool:
    return candle[2] >= candle[1]


def is_bearish(candle: np.ndarray) -> bool:
    return candle[2] < candle[1]


def candle_includes_price(candle: np.ndarray, price: float) -> bool:
    return (price >= candle[4]) and (price <= candle[3])


def split_candle(candle: np.ndarray, price: float) -> tuple:
    """
    splits a single candle into two candles: earlier + later

    :param candle: np.ndarray
    :param price: float

    :return: tuple
    """
    timestamp = candle[0]
    o = candle[1]
    c = candle[2]
    h = candle[3]
    l = candle[4]
    v = candle[5]

    if is_bullish(candle) and l < price < o:
        return np.array([
            timestamp, o, price, o, price, v
        ]), np.array([
            timestamp, price, c, h, l, v
        ])
    elif price == o:
        return candle, candle
    elif is_bearish(candle) and o < price < h:
        return np.array([
            timestamp, o, price, price, o, v
        ]), np.array([
            timestamp, price, c, h, l, v
        ])
    elif is_bearish(candle) and l < price < c:
        return np.array([
            timestamp, o, price, h, price, v
        ]), np.array([
            timestamp, price, c, c, l, v
        ])
    elif is_bullish(candle) and c < price < h:
        return np.array([
            timestamp, o, price, price, l, v
        ]), np.array([
            timestamp, price, c, h, c, v
        ]),
    elif is_bearish(candle) and price == c:
        return np.array([
            timestamp, o, c, h, c, v
        ]), np.array([
            timestamp, price, price, price, l, v
        ])
    elif is_bullish(candle) and price == c:
        return np.array([
            timestamp, o, c, c, l, v
        ]), np.array([
            timestamp, price, price, h, price, v
        ])
    elif is_bearish(candle) and price == h:
        return np.array([
            timestamp, o, h, h, o, v
        ]), np.array([
            timestamp, h, c, h, l, v
        ])
    elif is_bullish(candle) and price == l:
        return np.array([
            timestamp, o, l, o, l, v
        ]), np.array([
            timestamp, l, c, h, l, v
        ])
    elif is_bearish(candle) and price == l:
        return np.array([
            timestamp, o, l, h, l, v
        ]), np.array([
            timestamp, l, c, c, l, v
        ])
    elif is_bullish(candle) and price == h:
        return np.array([
            timestamp, o, h, h, l, v
        ]), np.array([
            timestamp, h, c, h, c, v
        ])
    elif is_bearish(candle) and c < price < o:
        return np.array([
            timestamp, o, price, h, price, v
        ]), np.array([
            timestamp, price, c, price, l, v
        ])
    elif is_bullish(candle) and o < price < c:
        return np.array([
            timestamp, o, price, price, l, v
        ]), np.array([
            timestamp, price, c, h, price, v
        ])


def inject_warmup_candles_to_store(candles: np.ndarray, exchange: str, symbol: str) -> None:
    if candles is None or candles.size == 0:
        raise ValueError(f'Could not inject warmup candles because the passed candles are empty. Have you imported enough warmup candles for {exchange}/{symbol}?')

    from jesse.config import config
    from jesse.store import store

    # batch add 1m candles:
    store.candles.batch_add_candle(candles, exchange, symbol, '1m', with_generation=False)

    # loop to generate, and add candles (without execution)
    for i in range(len(candles)):
        for timeframe in config['app']['considering_timeframes']:
            # skip 1m. already added
            if timeframe == '1m':
                continue

            num = jh.timeframe_to_one_minutes(timeframe)

            if (i + 1) % num == 0:
                generated_candle = generate_candle_from_one_minutes(
                    timeframe,
                    candles[(i - (num - 1)):(i + 1)],
                    True
                )

                store.candles.add_candle(
                    generated_candle,
                    exchange,
                    symbol,
                    timeframe,
                    with_execution=False,
                    with_generation=False
                )


def get_candles(
        exchange: str,
        symbol: str,
        timeframe: str,
        start_date_timestamp: int,
        finish_date_timestamp: int,
        warmup_candles_num: int = 0,
        caching: bool = False,
        is_for_jesse: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    symbol = symbol.upper()

    # convert start_date and finish_date to timestamps
    trading_start_date_timestamp = jh.timestamp_to_arrow(start_date_timestamp).floor(
        'day').int_timestamp * 1000
    trading_finish_date_timestamp = (jh.timestamp_to_arrow(finish_date_timestamp).floor(
        'day').int_timestamp * 1000) - 60_000

    # if warmup_candles is set, calculate the warmup start and finish timestamps
    if warmup_candles_num > 0:
        warmup_finish_timestamp = trading_start_date_timestamp
        warmup_start_timestamp = warmup_finish_timestamp - (
                warmup_candles_num * jh.timeframe_to_one_minutes(timeframe) * 60_000)
        warmup_finish_timestamp -= 60_000
        warmup_candles = _get_candles_from_db(exchange, symbol, warmup_start_timestamp, warmup_finish_timestamp,
                                              caching=caching)
    else:
        warmup_candles = None

    # fetch trading candles from database
    trading_candles = _get_candles_from_db(exchange, symbol, trading_start_date_timestamp,
                                           trading_finish_date_timestamp, caching=caching)

    # if timeframe is 1m or is_for_jesse is True, return the candles as is because they
    # are already 1m candles which is the accepted format for practicing with Jesse.
    if timeframe == '1m' or is_for_jesse or exchange == 'YFinance':
        if exchange == 'YFinance':
            # Check if source candles are Daily (1D) or Hourly (1h/1m)
            # 86,400,000 ms = 1 day
            # we check the gap between the first two candles
            def should_expand(c_arr):
                if c_arr is None or len(c_arr) < 2:
                    return False
                # If gap is exactly 24h, it's 1D data
                gap = c_arr[1][0] - c_arr[0][0]
                return gap == 86_400_000

            if should_expand(warmup_candles):
                warmup_candles = _expand_1d_to_1m(warmup_candles)
            if should_expand(trading_candles):
                trading_candles = _expand_1d_to_1m(trading_candles)
                
        return warmup_candles, trading_candles

    # if the timeframe is not 1m, generate the candles for the requested timeframe
    if warmup_candles_num > 0:
        warmup_candles = _get_generated_candles(timeframe, warmup_candles)
    else:
        warmup_candles = None
    trading_candles = _get_generated_candles(timeframe, trading_candles)

    return warmup_candles, trading_candles


def _expand_1d_to_1m(candles: np.ndarray) -> np.ndarray:
    if candles is None or len(candles) == 0:
        return candles

    # Each daily candle will be expanded into 1440 1-minute candles
    expanded = np.zeros((len(candles) * 1440, 6))

    for i, candle in enumerate(candles):
        start_ts = int(candle[0])
        o, c, h, l, v = candle[1], candle[2], candle[3], candle[4], candle[5]

        # distribute the volume across the 1440 minutes (mostly 0 except the last one)
        for j in range(1440):
            idx = i * 1440 + j
            expanded[idx][0] = start_ts + j * 60000
            expanded[idx][1] = o
            # For the first 1439 minutes, keep price at Open
            if j < 1439:
                expanded[idx][2] = o # Close
                expanded[idx][3] = o # High
                expanded[idx][4] = o # Low
                expanded[idx][5] = 0 # Volume
            else:
                # The last minute contains the actual High, Low, Close and Volume
                expanded[idx][2] = c
                expanded[idx][3] = h
                expanded[idx][4] = l
                expanded[idx][5] = v

    return expanded


def _get_candles_from_db(
        exchange, symbol, start_date_timestamp, finish_date_timestamp, caching: bool = False
) -> np.ndarray:
    from jesse.models.Candle import fetch_candles_from_db
    from jesse.services.cache import cache

    if caching:
        key = jh.key(exchange, symbol)
        cache_key = f"{start_date_timestamp}-{finish_date_timestamp}-{key}"
        cached_value = cache.get_value(cache_key)
        if cached_value:
            return np.array(cached_value)

    # validate the dates
    if start_date_timestamp == finish_date_timestamp:
        raise InvalidDateRange('start_date and finish_date cannot be the same.')
    if start_date_timestamp > finish_date_timestamp:
        raise InvalidDateRange(f'start_date ({jh.timestamp_to_date(start_date_timestamp)}) is greater than finish_date ({jh.timestamp_to_date(finish_date_timestamp)}).')

    # For YFinance, try to fetch 1h data first (more granular), then fallback to 1D
    if exchange == 'YFinance':
        # Symbol normalization for YFinance
        original_symbol = symbol
        if symbol.endswith('-EQ'):
            symbol = symbol.replace('-EQ', '.NS')
        elif symbol.endswith('-USDT'):
            symbol = symbol.replace('-USDT', '-USD')
            
        # Try 1h first
        candles_tuple = fetch_candles_from_db(exchange, symbol, '1h', start_date_timestamp, finish_date_timestamp)
        if len(candles_tuple) > 0:
            return np.array(candles_tuple)
        
        # Fallback to 1D
        timeframe = '1D'
    else:
        timeframe = '1m'

    print(f"DEBUG_DB_QUERY: Exch={exchange}, Sym={symbol}, TF={timeframe}, Start={start_date_timestamp}, End={finish_date_timestamp}")
    candles_tuple = fetch_candles_from_db(exchange, symbol, timeframe, start_date_timestamp, finish_date_timestamp)
    print(f"DEBUG_DB_RESULT: Found {len(candles_tuple)} candles")
    
    if len(candles_tuple) == 0:
        # Fallback: if YFinance has no 1D data in that range, it might be empty. 
        # But we shouldn't necessarily error unless strict.
        pass

    candles = np.array(candles_tuple)

    if caching:
        cache.set_value(cache_key, tuple(candles), expire_seconds=60 * 60 * 24 * 7)

    return candles


def _get_generated_candles(timeframe, trading_candles) -> np.ndarray:
    # generate candles for the requested timeframe
    generated_candles = []
    for i in range(len(trading_candles)):
        num = jh.timeframe_to_one_minutes(timeframe)

        if (i + 1) % num == 0:
            generated_candles.append(
                generate_candle_from_one_minutes(
                    timeframe,
                    trading_candles[(i - (num - 1)):(i + 1)],
                    True
                )
            )

    return np.array(generated_candles)


def get_existing_candles() -> List[Dict]:
    """
    Returns a list of all existing candles grouped by exchange and symbol
    """
    results = []
    
    # Get unique exchange-symbol combinations
    pairs = Candle.select(
        Candle.exchange, 
        Candle.symbol
    ).distinct().tuples()

    for exchange, symbol in pairs:
        # Get first and last candle for this pair
        first = Candle.select(
            Candle.timestamp
        ).where(
            Candle.exchange == exchange,
            Candle.symbol == symbol
        ).order_by(
            Candle.timestamp.asc()
        ).first()

        last = Candle.select(
            Candle.timestamp
        ).where(
            Candle.exchange == exchange,
            Candle.symbol == symbol
        ).order_by(
            Candle.timestamp.desc()
        ).first()

        if first and last:
            results.append({
                'exchange': exchange,
                'symbol': symbol,
                'start_date': arrow.get(first.timestamp / 1000).format('YYYY-MM-DD'),
                'end_date': arrow.get(last.timestamp / 1000).format('YYYY-MM-DD')
            })

    return results

def delete_candles(exchange: str, symbol: str) -> None:
    """
    Deletes all candles for the given exchange and symbol
    """
    Candle.delete().where(
        Candle.exchange == exchange,
        Candle.symbol == symbol
    ).execute()
