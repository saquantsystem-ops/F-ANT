import json
from starlette.responses import JSONResponse
import jesse.helpers as jh
from jesse.services import transformers


def get_notification_api_keys() -> JSONResponse:
    # Bypass DB
    return JSONResponse({
        'data': []
    }, status_code=200)


def store_notification_api_keys(
        name: str,
        driver: str,
        fields: dict
) -> JSONResponse:
    # Bypass DB
    return JSONResponse({
        'status': 'success',
        'message': 'Notification API key has been stored (mock).',
        'data': {
            'id': jh.generate_unique_id(),
            'name': name,
            'driver': driver,
            'fields': fields,
            'created_at': jh.now_to_datetime()
        }
    }, status_code=200)


def delete_notification_api_keys(notification_api_key_id: str) -> JSONResponse:
    # Bypass DB
    return JSONResponse({
        'status': 'success',
        'message': 'Notification API key has been deleted (mock).'
    }, status_code=200)
