import unicodedata
from hashlib import shake_256

from app.db import ObjectId


def get_id(string: str) -> ObjectId:
    return ObjectId(shake_256(string.encode()).hexdigest(12))


def get_id_by_lon_lat(lon, lat, epsg):
    return get_id(f'{lon:.5f}{lat:.5f}{epsg}')


def remove_accents(input_str: str):
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('utf-8')


def is_valid_query(ptype, ftype):
    geom = ['LINE', 'POINT', 'POLYGON', 'CSV', 'SHP', 'GPKG']
    raster = ['RASTER', 'TIFF', 'TIF']
    if ptype.upper() in geom and ftype.upper() in geom:
        return True
    if ptype.upper() in raster and ftype.upper() in raster:
        return True
    return False


def get_format_valid(ftype):
    fgeom = ['LINE', 'POINT', 'POLYGON']
    fraster = ['RASTER']
    if ftype.upper() in fgeom:
        return ['csv', 'shp', 'gpkg']
    if ftype.upper() in fraster:
        return ['raster']
