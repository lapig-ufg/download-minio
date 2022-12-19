from .api import download, layers, timesires


def created_routes(app):

    app.include_router(
        download.router, prefix='/api/download', tags=['Download']
    )

    app.include_router(layers.router, prefix='/api/layers', tags=['Layers'])

    app.include_router(
        timesires.router, prefix='/api/timesires', tags=['Timesires']
    )
    return app
