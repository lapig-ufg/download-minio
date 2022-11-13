from pickle import load
from json import dumps
from config import settings

with open(file_ows = f'{settings.CACHE_MAP}{settings.FILE_MAP_CACH}', 'rb') as f:
    lpmap = load(f)
    
def get_layer(name):
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