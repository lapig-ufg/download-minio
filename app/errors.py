from typing import Callable

from bson.errors import InvalidId
from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute


class ErrorsRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                response: Response = await original_route_handler(request)
            except InvalidId as e:
                raise HTTPException(
                    status_code=400,
                    detail='The id informed is not valid, please check the data before sending it to us',
                )
            return response

        return custom_route_handler
