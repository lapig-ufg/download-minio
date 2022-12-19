from .api import download, layers, timeseries


def created_routes(app):

    app.include_router(
        download.router, prefix='/api/download', tags=['Download']
    )

    app.include_router(layers.router, prefix='/api/layers', tags=['Layers'])

    app.include_router(
        timeseries.router, prefix='/api/timeseries', tags=['Time Series']
    )
    return app
