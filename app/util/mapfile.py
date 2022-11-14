from json import dumps
from pickle import load

from app.config import settings


def get_schema(dataFrame):

    schema = {
        key: value
        for key, value in zip(
            list(dataFrame.column_name), list(dataFrame.data_type)
        )
    }
    return schema


def get_layer(name):
    with open(f'{settings.CACHE_MAP}{settings.FILE_MAP_CACH}', 'rb') as f:
        lpmap = load(f)
    layer = lpmap[name]
    crs = layer['projection'][0].split('=')[1]
    try:
        return (layer['file'], layer['type'], 'file', crs)
    except:
        connectiontype = layer['connectiontype']
        try:
            connection = connectiontype['POSTGIS']
            return (layer['table'], layer['type'], connection, crs)
        except:
            return (connectiontype['OGR'], layer['type'], 'sqlite', crs)
