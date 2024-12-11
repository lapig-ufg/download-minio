from enum import Enum
from pickle import load
from typing import List, Optional, Union

from pydantic import BaseModel, HttpUrl

from app.config import settings
from app.model.models import make_enum

with open(f'{settings.CACHE_MAP}{settings.LISTL_LAYER_OWS}', 'rb') as f:
    listl_layer_ows = load(f)

EnumValueType = make_enum(
    'EnumValueType', {name: name for name in listl_layer_ows}
)


class DowloadUrl(BaseModel):
    object_name: str
    size: int
    host: str = settings.DOWNLOAD_URL
    buckt: str = settings.BUCKET
    file_name: str = ''
    content_type: str = ''
    url: HttpUrl = ''

    def __init__(self, **data) -> None:
        extensions = {
            'csv': 'text/csv',
            'gpkg': 'application/geopackage+sqlite3',
            'shp': 'application/octet-stream',
            'tif': 'application/x-geotiff',
            'tiff': 'application/x-geotiff',
            'zip': 'application/zip',
        }
        super().__init__(**data)
        self.url = f'https://{self.host}/{self.buckt}/{self.object_name}'
        self.file_name = self.object_name.split('/')[-1]
        try:
            self.content_type = extensions[
                self.object_name.split('/')[-1].split('.')[-1]
            ]
        except:
            self.content_type = 'application/octet-stream'


class EnumCountry(str, Enum):
    BRASIL = 'BRASIL'

    @property
    def enum_name(self):
        return 'country'


class EnumRegions(str, Enum):
    NORTE = 'NORTE'
    CENTRO_OESTE = 'CENTRO-OESTE'
    NORDESTE = 'NORDESTE'
    SUDESTE = 'SUDESTE'
    SUL = 'SUL'

    @property
    def enum_name(self):
        return 'region'


class EnumFronteiras(str, Enum):
    AMZ_LEGAL = 'AMZ_LEGAL'
    MATOPIBA = 'MATOPIBA'

    @property
    def enum_name(self):
        return 'fronteira'


class EnumBiomes(str, Enum):
    AMAZONIA = 'AMAZONIA'
    CAATINGA = 'CAATINGA'
    CERRADO = 'CERRADO'
    MATA_ATLANTICA = 'MATA_ATLANTICA'
    PAMPA = 'PAMPA'
    PANTANAL = 'PANTANAL'

    @property
    def enum_name(self):
        return 'biome'


class EnumCity(BaseModel):
    code: int

    def __repr__(self):
        return str(self.code)

    def upper(self):
        return str(self.code)

    @property
    def enum_name(self):
        return 'city'


class EnumStates(str, Enum):
    AC = 'AC'
    AL = 'AL'
    AM = 'AM'
    AP = 'AP'
    BA = 'BA'
    CE = 'CE'
    DF = 'DF'
    ES = 'ES'
    GO = 'GO'
    MA = 'MA'
    MG = 'MG'
    MS = 'MS'
    MT = 'MT'
    PA = 'PA'
    PB = 'PB'
    PE = 'PE'
    PI = 'PI'
    PR = 'PR'
    RJ = 'RJ'
    RN = 'RN'
    RO = 'RO'
    RR = 'RR'
    RS = 'RS'
    SC = 'SC'
    SE = 'SE'
    SP = 'SP'
    TO = 'TO'

    @property
    def enum_name(self):
        return 'state'


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
    attributes: Optional[List[Optional[Attribute]]]


class Download(BaseModel):
    csv: Optional[bool]
    shp: Optional[bool]
    gpkg: Optional[bool]
    raster: Optional[bool | str]
    layerTypeName: str
    loading: Optional[bool]


class RegionType(str, Enum):
    biome = 'biome'
    city = 'city'
    country = 'country'
    fronteira = 'fronteira'
    region = 'region'
    state = 'state'


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
    valueType: EnumValueType
    type: Optional[str] = None
    origin: Optional[Origin] = None
    typeLayer: Optional[str]
    viewValueType: Optional[str]
    typeLabel: Optional[str] = None
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
    value: Union[
        EnumCountry,
        EnumRegions,
        EnumStates,
        EnumFronteiras,
        EnumBiomes,
        EnumCity,
        str,
    ]

    def get(self):
        return str(self.value).split('.')[1]


class Payload(BaseModel):
    layer: Layer
    region: Region
    filter: Optional[Filter] = None
    typeDownload: FileTypes
