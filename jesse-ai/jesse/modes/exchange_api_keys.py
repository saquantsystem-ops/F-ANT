import json
from typing import Optional
from starlette.responses import JSONResponse
from jesse.info import live_trading_exchanges
import jesse.helpers as jh
from jesse.services import transformers


def get_exchange_api_keys() -> JSONResponse:
    # Return mock API keys to allow UI to select an exchange
    return JSONResponse({
        'data': [
            {
                'id': 'mock-angel-one-id',
                'exchange': 'Angel One',
                'name': 'Angel One Mock Account',
                'api_key': 'mock_api_key',
                'api_secret': 'mock_api_secret',
                'additional_fields': 'null',
                'general_notifications_id': None,
                'error_notifications_id': None
            }
        ]
    }, status_code=200)


def store_exchange_api_keys(
        exchange: str,
        name: str,
        api_key: str,
        api_secret: str,
        additional_fields: Optional[dict] = None,
        general_notifications_id: Optional[str] = None,
        error_notifications_id: Optional[str] = None,
) -> JSONResponse:
    # validate the exchange
    if exchange not in live_trading_exchanges:
        return JSONResponse({
            'status': 'error',
            'message': f'Invalid exchange: {exchange}'
        }, status_code=400)

    # Bypass DB
    return JSONResponse({
        'status': 'success',
        'message': 'API key has been stored (mock).',
        'data': {
            'id': jh.generate_unique_id(),
            'exchange_name': exchange,
            'name': name,
            'api_key': api_key,
            'api_secret': api_secret,
            'additional_fields': additional_fields or {},
            'created_at': jh.now_to_datetime(),
            'general_notifications_id': general_notifications_id,
            'error_notifications_id': error_notifications_id
        }
    }, status_code=200)


def delete_exchange_api_keys(exchange_api_key_id: str) -> JSONResponse:
    # Bypass DB
    return JSONResponse({
        'status': 'success',
        'message': 'API key has been deleted (mock).'
    }, status_code=200)
