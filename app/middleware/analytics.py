import threading
from datetime import datetime
from time import time

import requests
from starlette.middleware.base import (BaseHTTPMiddleware,
                                       RequestResponseEndpoint)
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from pymongo import MongoClient

from app.config import settings, logger



def get_location(ip_address):
    response = requests.get(
        f'https://ipapi.co/{ip_address}/json/', timeout=15
    ).json()
    location_data = {
        'city': response.get('city'),
        'region': response.get('region'),
        'country': response.get('country_name'),
    }
    return location_data


def _post_requests(requests_data: list[dict], framework: str):
    logger.debug(f'Get data user {requests_data}')
    requests_data['location'] = get_location(requests_data['ip_address'])
    with MongoClient(settings.MONGODB_URL) as client:
        db = client.analytics
        db[framework].insert_one(requests_data)


def log_request(request_data: dict, framework: str):
    threading.Thread(
        target=_post_requests, args=(request_data, framework)
        ).start()
        


class Analytics(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, api_name: str = 'AnalyticsFastAPI'):
        super().__init__(app)
        self.api_name = api_name

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time()
        response = await call_next(request)

        request_data = {
            'hostname': request.url.hostname,
            'ip_address': request.client.host,
            'path': request.url.path,
            'user_agent': request.headers['user-agent'],
            'method': request.method,
            'status': response.status_code,
            'response_time': int((time() - start) * 1000),
            'created_at': datetime.now().isoformat(),
        }

        log_request(request_data, self.api_name)
        return response
