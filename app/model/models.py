from datetime import datetime
from enum import Enum
from typing import Dict, List, Union

from pydantic import Field, HttpUrl
from pymongo import MongoClient
from app.config import settings, logger
from app.db import MongoModel, PyObjectId

from pydantic import BaseModel

class Region(BaseModel):
    text: str
    value: str
    type: str
    
class Filter(BaseModel):
    valueFilter: str
    viewValueFilter: str

class Download(BaseModel):
    csv: bool
    shp: bool
    gpkg: bool
    raster: bool
    layerTypeName: str
    loading: bool
    
class Layer(BaseModel):
    valueType: str
    type: str
    origin: Dict
    typeLayer: str
    viewValueType: str
    typeLabel: str
    wfsMapCard: Dict
    download: Download
    regionFilter: bool
    filters: List[Filter]
    filterLabel: str
    filterSelected: str
    filterHandler: str
    visible: bool
    opacity: float
    metadata: List[Dict]
    
class Payload(BaseModel):
    layer: Layer
    region: str
    filter: str
    typeDownload: str