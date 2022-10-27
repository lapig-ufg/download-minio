from .api import collections

def created_routes(app):
    
    app.include_router(
        collections.router, 
        prefix='/api/collections', 
        tags=['Collections']
        )
    
    return app