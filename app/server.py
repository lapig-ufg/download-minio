import os
from json import load as jload
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from opentelemetry.trace import get_tracer
from redis import asyncio as aioredis
from starlette.exceptions import HTTPException as StarletteHTTPException
from unidecode import unidecode

from app.config import logger, settings, start_logger
from app.middleware.analytics import Analytics
from app.middleware.TokenMiddleware import TokenMiddleware

from .routers import created_routes

tracer = get_tracer(f'download_minio_{os.environ.get("LAPIG_ENV")}')

start_logger()

app = FastAPI()
app.add_middleware(TokenMiddleware)
app.add_middleware(Analytics, api_name=settings.API_NAME)


origins = [
    '*',
    'http://127.0.0.1:8000',
    'http://localhost:4200',
    'http://localhost:8000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app = created_routes(app)


templates_path = Path('templates')
templates = Jinja2Templates(directory=templates_path)

app.mount('/static', StaticFiles(directory=templates_path.resolve()), 'static')


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    start_code = exc.status_code
    logger.info(exc)

    if request.url.path.split('/')[1] == 'api':
        try:
            return JSONResponse(
                content={'status_code': start_code, 'message': exc.detail},
                status_code=start_code,
                headers=exc.headers,
            )
        except:
            return JSONResponse(
                content={'status_code': start_code, 'message': exc.detail},
                status_code=start_code,
            )

    base_url = request.base_url
    if settings.HTTPS:
        base_url = f'{base_url}'.replace('http://', 'https://')
    return templates.TemplateResponse(
        'error.html',
        {
            'request': request,
            'base_url': base_url,
            'info': '',
            'status': start_code,
            'message': exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    try:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                {
                    'detail': unidecode(str(exc.errors())),
                    'body': unidecode(str(exc.body)),
                }
            ),
            headers={
                'X-Download-Detail': f'{unidecode(str(exc.errors()))}',
                'X-Download-Body': f'{unidecode(str(exc.body))}',
            },
        )
    except Exception as e:
        logger.exception(
            f'Validation exception: {e} {exc.errors()} {exc.body}'
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                {
                    'detail': unidecode(str(exc.errors())),
                    'body': unidecode(str(exc.body)),
                }
            ),
        )


@app.on_event('startup')
async def startup():
    logger.debug('startup')
    try:
        redis = aioredis.from_url(f'redis://{settings.REDIS_URL}')
        FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')
    except:
        logger.exception('REDIS FALL')


@app.on_event('shutdown')
async def shutdown():
    """Perform shutdown activities."""
    # If you have any shutdown activities that need to be defined,
    # define them here.
    pass


def custom_openapi():
    try:
        with open('/APP/version.json') as user_file:
            parsed_json = jload(user_file)
            version = parsed_json['commitId']
    except:
        version = 'not-informad'
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title='Lapig - Laboratório de Processamento de Imagens e Geoprocessamento',
        version=version,
        contact={'name': 'Lapig', 'url': 'https://lapig.iesa.ufg.br/'},
        description='API para baixar dados do mapserver',
        routes=app.routes,
    )
    openapi_schema['info']['x-logo'] = {
        'url': 'https://files.cercomp.ufg.br/weby/up/1313/o/Marca_Lapig_PNG_sem_descri%C3%A7%C3%A3o-removebg-preview.png?1626024108'
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
