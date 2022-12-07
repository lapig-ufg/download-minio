from .api import download
from .api import layers

def created_routes(app):

    app.include_router(
        download.router, prefix='/api/download', tags=['Download']
    )
    
    app.include_router(
        layers.router, prefix='/api/layers', tags=['Layers']
    )

    return app
