from datetime import datetime
from enum import Enum
from typing import Dict, List, Union

from minio.commonconfig import Tags
from pydantic import BaseModel, Field, HttpUrl
from pymongo import MongoClient

from app.config import logger, settings
from app.db import MongoModel, PyObjectId


def make_enum(name, values):
    _k = _v = None
    class TheEnum(str, Enum):
        nonlocal _k, _v
        for _k, _v in values.items():
            try:
                locals()[_k] = _v
            except:
                logger.exception('Make enum')
    TheEnum.__name__ = name
    return TheEnum  


class GeoFile:
    def __init__(self, path_name):

        split_path = path_name.split('/')[-5:]
        if not 5 == len(split_path):
            raise Exception(f'Path is not a valid {split_path}')
        self.limit_type = split_path[0]
        self.limit_name = split_path[1]
        self.file_type = split_path[2]
        self.layer = split_path[3]
        self.file_name = split_path[4]
        try:
            self.year = (
                f"_year={split_path[4].split('_year=')[1].split('.')[0]}"
            )
        except:
            self.year = ''
        self.extension = split_path[4].split('.')[1]
        self.file_path = path_name
        try:
            if self.year == '':
                self.year = f"{int(self.file_name.split('.')[0][-4:])}"
        except:
            self.year = ''

    def __repr__(self):
        return f'object_name:{self.object_name}\ntags:{self.to_tags}'

    @property
    def object_name(self):
        return f'{self.limit_type}/{self.limit_name}/{self.file_type}/{self.layer}/{self.file_name}'

    @property
    def to_tags(self):
        tags = Tags(for_object=True)
        tags['limit_type'] = self.limit_type
        tags['limit_name'] = self.limit_name
        tags['file_type'] = self.file_type
        tags['layer'] = self.layer
        if self.year != '':
            tags['year'] = str(self.year).replace('_year=', '')
        return tags

    @property
    def content_type(self):
        extensions = {
            'csv': 'text/csv',
            'gpkg': 'application/geopackage+sqlite3',
            'shp': 'application/octet-stream',
            'tif': 'application/x-geotiff',
            'tiff': 'application/x-geotiff',
            'zip': 'application/zip',
        }
        try:
            return extensions[self.extension]
        except:
            return 'application/octet-stream'
