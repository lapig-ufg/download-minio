import threading
from datetime import datetime
from time import time

import requests
from pymongo import MongoClient
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.config import logger, settings


def get_location(ip_address):
    try:
        response = requests.get(
            f'https://ipapi.co/{ip_address}/json/', timeout=15
        ).json()
        location_data = {
            'city': response.get('city'),
            'region': response.get('region'),
            'country': response.get('country_name'),
            'org': response.get('org'),
        }
        return location_data
    except:
        raise Exception('not info')


def _post_requests(requests_data: list[dict], framework: str):
    try:
        requests_data['location'] = get_location(requests_data['ip_address'])
    except:
        pass
    with MongoClient(settings.MONGODB_URL) as client:
        db = client.analytics
        db[framework].insert_one(requests_data)


def log_request(request_data: dict, framework: str):
    threading.Thread(
        target=_post_requests, args=(request_data, framework)
    ).start()


class Analytics(BaseHTTPMiddleware):
    def __init__(
        self, app: ASGIApp, api_name: str = 'AnalyticsFastAPI', routes=[]
    ):
        super().__init__(app)
        self.api_name = api_name
        self.routes = routes

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time()
        response = await call_next(request)

        try:
            is_teste = request.headers['x-download-test']
        except:
            is_teste = False
        if not is_teste:
            user_interaction = {
                key.lower().replace('x-download-', '').replace('-', '_'): value
                for key, value in dict(response.headers).items()
                if 'x-download' in key.lower()
            }

            try:
                ip_address = request.headers['x-forwarded-for']
            except:
                ip_address = request.client.host

            if request.url.path.split('/')[1] in ['api', *self.routes]:
                logger.debug(dict(request.headers))
                headers = dict(request.headers)
                try:
                    headers.pop('cookie')
                except:
                    pass
                request_data = {
                    'headers': headers,
                    'hostname': request.url.hostname,
                    'ip_address': ip_address,
                    'path': request.url.path,
                    'method': request.method,
                    'status': response.status_code,
                    'response_time': int((time() - start) * 1000),
                    'created_at': datetime.now(),
                }
                if len(user_interaction) > 0:
                    request_data['user_interaction'] = user_interaction

                log_request(request_data, self.api_name)
            return response
        else:
            logger.debug('API TA SENDO TESTADA')
            return response
