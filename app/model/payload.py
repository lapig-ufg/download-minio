from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel


class Origin(BaseModel):
    sourceService: str
    typeOfTMS: str


class DisplayMapCardAttributes(BaseModel):
    column: str
    label: str
    columnType: str


class Gallery(BaseModel):
    id_column: str
    tableName: str


class Attribute(BaseModel):
    column: str
    label: str
    columnType: str


class WfsMapCard(BaseModel):
    show: Optional[bool]
    displayMapCardAttributes: Optional[DisplayMapCardAttributes]
    attributes: Optional[List[Attribute]]


class Download(BaseModel):
    csv: Optional[bool]
    shp: Optional[bool]
    gpkg: Optional[bool]
    raster: Optional[bool]
    layerTypeName: str
    loading: Optional[bool]


class RegionType(str, Enum):
    biome = "biome"
    city = "city"
    country = "country"
    fronteira = "fronteira"
    region = "region"
    state = "state"


class FileTypes(str, Enum):
    csv = 'csv'
    shp = 'shp'
    gpkg = 'gpkg'
    raster = 'raster'

class Filter(BaseModel):
    valueFilter: str
    viewValueFilter: Optional[Union[str, int]]


class Metadatum(BaseModel):
    title: str
    description: Optional[str] = None


class Layer(BaseModel):
    valueType: str
    type: Optional[str]= None
    origin: Optional[Origin]= None
    typeLayer: Optional[str]
    viewValueType: Optional[str]
    typeLabel: Optional[str]= None
    gallery: Optional[Gallery] = None
    wfsMapCard: Optional[WfsMapCard] = None
    download: Optional[Download] = None
    regionFilter: Optional[bool] = None
    filters: Optional[List[Filter]] = None
    filterLabel: Optional[str] = None
    filterSelected: Optional[str] = None
    filterHandler: Optional[str] = None
    visible: Optional[bool] = None
    opacity: Optional[int] = None
    metadata: Optional[List[Metadatum]] = None


class Region(BaseModel):
    type: RegionType
    text: Optional[str]
    value: str


class Payload(BaseModel):
    layer: Layer
    region: Region
    filter: Optional[Filter] = None
    typeDownload: FileTypes
