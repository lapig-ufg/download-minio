from hashlib import shake_256

from app.db import ObjectId


def get_id(string: str) -> ObjectId:
    return ObjectId(shake_256(string.encode()).hexdigest(12))


def get_id_by_lon_lat(lon, lat, epsg):
    return get_id(f'{lon:.5f}{lat:.5f}{epsg}')
