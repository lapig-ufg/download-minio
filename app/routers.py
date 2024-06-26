from .api import download, layers, timeseries, status, bibio


def created_routes(app):

    app.include_router(
        download.router, prefix='/api/download', tags=['Download']
    )

    app.include_router(layers.router, prefix='/api/layers', tags=['Layers'])

    app.include_router(
        timeseries.router, prefix='/api/timeseries', tags=['Time Series']
    )
    app.include_router(
        bibio.router, prefix='/api/bibio', tags=['Bibiografia Patagem']
    )

    app.include_router(
        status.router, prefix='/status', tags=['Lapig Status'], include_in_schema=False
    )
    return app
