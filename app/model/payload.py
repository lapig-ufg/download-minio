from typing import List, Union, Optional

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
    csv: bool
    shp: bool
    gpkg: bool
    raster: bool
    layerTypeName: str
    loading: bool


class Filter(BaseModel):
    valueFilter: str
    viewValueFilter: Union[str,int]


class Metadatum(BaseModel):
    title: str
    description: Optional[str] = None


class Layer(BaseModel):
    valueType: str
    type: str
    origin: Origin
    typeLayer: str
    viewValueType: str
    typeLabel: str
    gallery: Optional[Gallery] = None
    wfsMapCard: WfsMapCard
    download: Download
    regionFilter: bool
    filters: List[Filter]
    filterLabel: str
    filterSelected: str
    filterHandler: str
    visible: bool
    opacity: int
    metadata: List[Metadatum]


class Region(BaseModel):
    type: str
    text: str
    value: str



class Payload(BaseModel):
    layer: Layer
    region: Region
    filter: Filter
    typeDownload: str