from pickle import load
from json import dumps
from app.config import settings


    
def get_layer(name):
    with open(f'{settings.CACHE_MAP}{settings.FILE_MAP_CACH}', 'rb') as f:
        lpmap = load(f)
    layer = lpmap[name]
    try:
        return (layer['file'],layer['type'], 'file')
    except:
        connectiontype = layer['connectiontype']
        try:
            connection = connectiontype['POSTGIS']
            return (layer['table'],layer['type'], connection)
        except:
            return (connectiontype['OGR'],layer['type'], 'sqlite')