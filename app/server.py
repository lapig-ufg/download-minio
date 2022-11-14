from pathlib import Path

from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import logger, settings, start_logger

from .routers import created_routes

start_logger()

app = FastAPI()

origins = [
    "*",
    "http://127.0.0.1:8000",
    "http://localhost:4200",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





app = created_routes(app)


templates_path = Path('templates')
templates = Jinja2Templates(directory=templates_path)

app.mount('/static', StaticFiles(directory=templates_path.resolve()), 'static')


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    start_code = exc.status_code
    if request.url.path.split('/')[1] == 'api':
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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({'detail': exc.errors(), 'body': exc.body}),
    )


@app.on_event('startup')
async def startup():
    logger.debug('startup')
    """Perform startup activities."""
    # If you have any startup activities that need to be defined,
    # define them here.
    pass


@app.on_event('shutdown')
async def shutdown():
    """Perform shutdown activities."""
    # If you have any shutdown activities that need to be defined,
    # define them here.
    pass
