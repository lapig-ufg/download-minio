from .api import feature
from .api import timeserie
from .api import upload
from .api import dataset
from .api import collections

def created_routes(app):
    
    app.include_router(
        collections.router, 
        prefix='/api/collections', 
        tags=['Collections']
        )
    
    return app