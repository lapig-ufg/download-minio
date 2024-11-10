from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.config import logger, settings

security = HTTPBearer()


class TokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, routes=[]):
        super().__init__(app)
        self.routes = routes

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path.split('/')[1] in ['status', *self.routes]:
            token = self.extract_token(request)

            if not token:
                return Response(
                    status_code=401, content='Token de acesso ausente'
                )

            # Faça a verificação do token de acesso aqui
            if token != settings.TOKEN:
                return Response(
                    status_code=401, content='Token de acesso inválido'
                )
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(f'Erro interno: {e}')
            return Response(
                status_code=500, content='Error interno do servidor'
            )

    def extract_token(self, request: Request) -> str:
        # Verifica o token no header 'Authorization'
        authorization: HTTPAuthorizationCredentials = request.headers.get(
            'Authorization'
        )
        if authorization:
            return authorization.credentials

        # Verifica o token na query da URL
        token = request.query_params.get('token')
        if token:
            return token

        return None
