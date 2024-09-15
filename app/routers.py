from .api import download, layers, timeseries, status, biblio


def created_routes(app):

    app.include_router(
        download.router, prefix='/api/download', tags=['Download']
    )

    app.include_router(layers.router, prefix='/api/layers', tags=['Layers'])

    app.include_router(
        timeseries.router, prefix='/api/timeseries', tags=['Time Series']
    )
    app.include_router(
        biblio.router, prefix='/api/biblio', tags=['Bibliografia da Pastagem']
    )

    app.include_router(
        status.router, prefix='/status', tags=['Lapig Status'], include_in_schema=False
    )
    return app
