from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from starlette.exceptions import HTTPException
from app.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

class TokenMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app: ASGIApp, routes=[]
    ):
        super().__init__(app)
        self.routes = routes
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint)-> Response:
        if request.url.path.split('/')[1] in ['status', *self.routes]:
            token = self.extract_token(request)
            
            if not token:
                return Response(status_code=401, content="Token de acesso ausente")
            
            # Faça a verificação do token de acesso aqui
            if token != settings.TOKEN:
                return Response(status_code=401, content="Token de acesso inválido")
        
        response = await call_next(request)
        return response
    
    def extract_token(self, request: Request) -> str:
        # Verifica o token no header 'Authorization'
        authorization: HTTPAuthorizationCredentials = request.headers.get("Authorization")
        if authorization:
            return authorization.credentials
        
        # Verifica o token na query da URL
        token = request.query_params.get("token")
        if token:
            return token
        
        return None