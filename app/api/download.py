import tempfile
from glob import glob
from zipfile import ZipFile, ZIP_BZIP2
import subprocess
from fastapi import APIRouter, HTTPException, Body, Path
from pydantic import BaseModel, HttpUrl

from app.config import logger, settings
from app.functions import client_minio
from app.model.creat_geofile import CreatGeoFile
from app.model.models import GeoFile
from app.model.payload import Download, FileTypes, Filter, Layer, Payload, Region, RegionType
from app.util.mapfile import get_layer
from app.util.exceptions import FilterException
from pymongo import MongoClient

router = APIRouter()


class DowloadUrl(BaseModel):
    object_name: str
    size: int
    host: str = settings.DOWNLOAD_URL
    buckt: str = settings.BUCKET
    url: HttpUrl = ''

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.url = f'https://{self.host}/{self.buckt}/{self.object_name}'


@router.post('/', response_description='Dowload', response_model=DowloadUrl)
async def atalas_payload(payload: Payload):
    return start_dowload(payload)


qbaixa = ''

@router.get('/{regionType}/{regionValue}/{fileType}/{valueType}/{valueFilter}', response_description='Dowload', response_model=DowloadUrl)
async def url_payload(
    regionType:RegionType  = Path(
        default=None, description="Qual o tipo de região  você quer baixar? "
    ),
    regionValue:str = Path(
        default=None, description="Qual o nome da região  você quer baixar? No caso de cidade(city) use o codigo de municipio do [IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)"
    ),
    fileType:FileTypes = Path(
        default=None, description="Tipo de arquivo que  você quer baixar? [csv, shp, gpkg, raster]"
    ),
    valueType:str = Path(
        default=None, description="Nome da camada que  você quer baixar?"
    ),
    valueFilter:str = Path(
        default=None, description="Filtro que sera usa para baixar camada?"
    ),
    update:str = Body(None)
    ):
    """
    Baixa uma camada do mapserver conforme os parametos a seguir:

    - **regionType**: Qual o tipo de região  você quer baixar? [biome, city, country, rater, region]
    - **regionValue**: Qual o nome da região  você quer baixar? No caso de cidade(city) use o codigo de municipio do [IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)
    - **fileType**: Tipo de arquivo que  você quer baixar? [csv, shp, gpkg, raster]
    - **valueType**: Nome da camada que  você quer baixar?
    - **valueFilter**: Filtro que sera usa para baixar camada
    """
    layerTypeName = None
    with MongoClient(settings.MONGODB_URL) as client:
        db = client.ows
        tmp = db.layers.find_one({"layertypes.valueType":valueType})
        try:
            layerTypeName = [x['download']['layerTypeName'] 
                for x in tmp["layertypes"] 
                if x["valueType"] == valueType][0]
        except Exception as e:
            layerTypeName = None
       

    payload = Payload(
            region = Region(
                type=regionType,
                value=regionValue.upper()
            ),
            layer= Layer(
                valueType = valueType,
                download = Download(layerTypeName=layerTypeName)
            ),
            typeDownload=fileType,
            filter = Filter(
                valueFilter=valueFilter
            ),
            update=update
        )
    logger.debug(payload)
    return start_dowload(payload)






def start_dowload(payload: Payload):

    valueFilter = ''
    try:
        valueFilter = payload.filter.valueFilter
        fileParam = f'{payload.layer.valueType}_{payload.filter.valueFilter}'
    except AttributeError:
        fileParam = payload.layer.valueType
    except Exception as e:
        logger.exception('erro')
        return HTTPException(500, f'e')

    region = payload.region
    try:
        client = client_minio()
    except Exception as e:
        logger.exception('Login erro')
        raise HTTPException(500, f'{e}')

    if payload.typeDownload == 'raster':
        if not valueFilter == '':
            raster_file, map_type, map_conect, crs = get_layer(valueFilter)
        else:
            raster_file, map_type, map_conect, crs = get_layer(
                payload.layer.download.layerTypeName
            )

        raster_file = raster_file.replace('/STORAGE/catalog/', '')
        pathFile = f'rater/{raster_file}'
        objects = client.list_objects(
            settings.BUCKET,
            prefix=f'{pathFile}',
            recursive=True,
        )

    else:
        pathFile = f'{region.type}/{region.value}/{payload.typeDownload}/{payload.layer.valueType}/{fileParam}'
        objects = client.list_objects(
            settings.BUCKET,
            prefix=f'{pathFile}.zip',
            recursive=True,
        )

    logger.info(
        "file: {}.zip fileType: {} regiao: {} value: {} sql_layer: {} valueFilter: {}".format(
            pathFile,
            payload.typeDownload,
            region.type,
            region.value,
            payload.layer.download.layerTypeName,
            valueFilter
        )
    )
    
    objects_list = list(objects)
    logger.debug(f"{len(objects_list)} , {payload.update}, {settings.KEY_UPDATE}" )
    
    if len(objects_list) == 1 and not payload.update == settings.KEY_UPDATE:
        return DowloadUrl(
            object_name=objects_list[0].object_name, size=objects_list[0].size
        )

    elif len(objects_list) > 1:
        logger.exception('ERROR TEM MAIS DE UM OBJECT')
        raise HTTPException(500, 'Flaha ao carregar o dados')
    if payload.typeDownload == 'raster':
        client = client_minio()
        try:
            result = client.fput_object(
                settings.BUCKET,
                f'{pathFile}',
                f'/storage/catalog/{raster_file}',
                content_type='application/x-geotiff',
            )
            
        except FileNotFoundError:
            raise HTTPException(400,'file_not_found')
        except Exception as e:
            logger.exception(e)
            raise HTTPException(500, e)
        
        logger.info(
            'created {0} object; etag: {1}, version-id: {2}'.format(
                result.object_name,
                result.etag,
                result.version_id,
            ),
        )
        objects = client.list_objects(
            settings.BUCKET,
            prefix=f'{pathFile}',
            recursive=True,
        )
        objects_list = list(objects)
        if len(objects_list) == 1 :
            return DowloadUrl(
                object_name=objects_list[0].object_name,
                size=objects_list[0].size,
            )
        else:
            logger.exception('Erro ao salvar dados')
            raise HTTPException(500, 'Erro ao gerar arquivo')
    else:
        try:
            map_layer, map_type, map_conect, crs = get_layer(
                payload.layer.download.layerTypeName
            )
            sql_layer = map_layer
            if not 'sqlite' == map_conect:
                db = map_conect
            else:
                logger.debug('is sql')
        except:
            sql_layer = payload.layer.download.layerTypeName
            db = ''

        if isinstance(map_conect, dict):
            return creat_file_postgre(
                payload,
                pathFile,
                region,
                sql_layer,
                valueFilter,
                fileParam,
                db,
                crs,
            )
        else:
            return HTTPException(500,'PayLoad')


def creat_file_postgre(
    payload, pathFile, region, sql_layer, valueFilter, fileParam, db, crs
):
    try:
        geofile = CreatGeoFile(
            fileType=payload.typeDownload,
            file=f'{pathFile}.zip',
            regiao=region.type,
            value=region.value,
            sql_layer=sql_layer,
            valueFilter=valueFilter,
            db=db,
            crs=crs,
        )

        
    except ValueError as e:
        if str(e) == "Cannot write empty DataFrame to file.":
            logger.info(f"{e}")
            raise HTTPException(
                    400,
                'file_empty',
                )
        logger.exception('Valor Error not empty')
        raise HTTPException(
                    400,
                f'{e}',
                )
    except FilterException as e:
        raise HTTPException(
                400,
                f"{e}",
            )

    except Exception as e:
        raise HTTPException(
                400,
                f"{e}",
            )
        
        

    with tempfile.TemporaryDirectory() as tmpdirname:
        client = client_minio()
        logger.debug(f'tmpdirname : {tmpdirname}')
        try:
            if payload.typeDownload == 'csv':
                logger.debug(f'{tmpdirname}/{fileParam}.csv')
                df, schema = geofile.gpd()
                df.to_csv(f'{tmpdirname}/{fileParam}.csv')
            elif payload.typeDownload == 'gpkg':
                logger.debug(f'{tmpdirname}/{fileParam}.gpkg')
                DB_HOST= settings.DB_HOST
                if db == '':
                    DB_PORT=settings.DB_PORT
                    DB_USER=settings.DB_USER
                    DB_PASSWORD=settings.DB_PASSWORD
                    DB_NAME=settings.DB_DATABASE
                else:
                    DB_PORT=db['port']
                    DB_USER=db['user']
                    DB_PASSWORD=db['password'].replace("'",'')
                    DB_NAME=db['dbname']
                FILE_STR = f'{tmpdirname}/{fileParam}.gpkg'
                PG_STR = f"PG:\"dbname='{DB_NAME}' host='{DB_HOST}' port='{DB_PORT}' user='{DB_USER}' password='{DB_PASSWORD}'\" " 
                ogr2ogr = f'ogr2ogr -f GPKG {FILE_STR} {PG_STR} -sql "{geofile.query()}"'
                logger.info(ogr2ogr)
                return_value = subprocess.call(ogr2ogr, shell=True)
                logger.debug(return_value)
            elif payload.typeDownload == 'shp':
                logger.debug(f'{tmpdirname}/{fileParam}.shp')
                df, schema = geofile.gpd()
                df.to_file(f'{tmpdirname}/{fileParam}.shp')
        except ValueError as e:
            logger.exception(
                f'Erro ao Criar arquivo ValueError: {e}'
            )
            raise HTTPException(
                400,
                f'Erro ao Criar arquivo ValueError: {e}',
            )
        except Exception as e:
            logger.exception('Erro ao Criar arquivo ValueError: {e}')
            raise HTTPException(
                500, f'Erro ao Criar arquivo: {e}'
            )

        file_paths = glob(f'{tmpdirname}/*')
        with ZipFile(f'{tmpdirname}/{fileParam}.zip', 'w', ZIP_BZIP2) as zip:
            # writing each file one by one
            for file in file_paths:
                zip.write(file, file.split('/')[-1])

        logger.info(
            f'zip criado {tmpdirname}/{fileParam}.zip dos arquivos {file_paths}'
        )
        geofile = GeoFile(f'{pathFile}.zip')
        try:
            result = client.fput_object(
                settings.BUCKET,
                f'{geofile.object_name}',
                f'{tmpdirname}/{fileParam}.zip',
                content_type=geofile.content_type,
                tags=geofile.to_tags,
                metadata=dict(geofile.to_tags),
            )
        except FileNotFoundError:
            raise HTTPException(400,'file_not_found')
        except Exception as e:
            logger.exception(e)
            raise HTTPException(500, e)
            
        logger.info(
            'created {0} object; etag: {1}, version-id: {2}'.format(
                result.object_name,
                result.etag,
                result.version_id,
            ),
        )
        objects = client.list_objects(
            settings.BUCKET,
            prefix=f'{pathFile}.zip',
            recursive=True,
        )
        objects_list = list(objects)
        if len(objects_list) == 1:
            return DowloadUrl(
                object_name=objects_list[0].object_name,
                size=objects_list[0].size,
            )
        else:
            logger.exception('Erro ao salvar dados')
            raise HTTPException(500, 'Erro ao gerar arquivo')
