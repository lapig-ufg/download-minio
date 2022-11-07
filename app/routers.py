from .api import download


def created_routes(app):

    app.include_router(
        download.router, prefix='/api/download', tags=['Download']
    )

    return app
