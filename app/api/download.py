import subprocess
import tempfile
from glob import glob
from typing import Union
from zipfile import ZIP_BZIP2, ZipFile

from fastapi import APIRouter, HTTPException, Path, Query


from fastapi.responses import RedirectResponse, JSONResponse
from pymongo import MongoClient

from app.config import logger, settings
from app.exceptions import OGR2OGRisRun
from app.functions import client_minio, process_is_run_by_fileName
from app.model.creat_geofile import CreatGeoFile
from app.model.functions import get_format_valid, is_valid_query
from app.model.models import GeoFile
from app.model.payload import (
    DowloadUrl,
    Download,
    EnumBiomes,
    EnumCity,
    EnumCountry,
    EnumFronteiras,
    EnumRegions,
    EnumStates,
    FileTypes,
    Filter,
    Layer,
    Payload,
    Region,
)
from app.util.exceptions import FilterException
from app.util.mapfile import get_layer

router = APIRouter()


@router.post(
    '/',
    response_description='Retorna um objeto json com a url do download',
    response_model=DowloadUrl,
)
async def geofile(
    payload: Payload,
    update: str = Query('Lapig', include_in_schema=False),
    direct: bool = Query(False, include_in_schema=False),
):
    return start_dowload(payload, update, direct)


@router.get(
    '/{region}/{fileType}/{layer}',
    name='Get Geofile',
    response_description='Retorna um objeto json com a url para download',
    response_model=DowloadUrl,
)
async def get_geofile(
    region: Union[
        EnumCountry, EnumRegions, EnumStates, EnumFronteiras, EnumBiomes, int
    ] = Path(
        default=None,
        description='Qual o nome da região  você quer baixar? No caso de cidade(city) use o codigo de municipio do [IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)',
    ),
    fileType: FileTypes = Path(
        default=None,
        description='Tipo de arquivo que  você quer baixar? [csv, shp, gpkg, raster]',
    ),
    layer: str = Path(
        default=None, description='Nome da camada que  você quer baixar?'
    ),
    update: str = Query('Lapig', include_in_schema=False),
    direct: bool = Query(False, include_in_schema=False)
):
    """
    Baixa uma camada do mapserver conforme os parametos a seguir:

    - **region**: Qual o nome da região  você quer baixar? No caso de cidade(city) use o codigo de municipio do [IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)
    - **fileType**: Tipo de arquivo que  você quer baixar? [csv, shp, gpkg, raster]
    - **layer**: Nome da camada que  você quer baixar?
    """
    return url_geofile(region, fileType, layer, None, update, direct)


@router.get(
    '/{region}/{fileType}/{layer}/{filter}',
    name='Get Geofile by Filter',
    response_description='Retorna um objeto json com a url para download',
    response_model=DowloadUrl,
)
async def get_geofile_filter(
    region: Union[
        EnumCountry, EnumRegions, EnumStates, EnumFronteiras, EnumBiomes, int
    ] = Path(
        default=None,
        description='Qual o nome da região  você quer baixar? No caso de cidade(city) use o codigo de municipio do [IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)',
    ),
    fileType: FileTypes = Path(
        default=None,
        description='Tipo de arquivo que  você quer baixar? [csv, shp, gpkg, raster]',
    ),
    layer: str = Path(
        default=None, description='Nome da camada que  você quer baixar?'
    ),
    filter: str = Path(
        default=None, description='Filtro que sera usa para baixar camada?'
    ),
    update: str = Query('Lapig', include_in_schema=False),
    direct: bool = Query(False, include_in_schema=False),
):
    """
    Baixa uma camada do mapserver conforme os parametos a seguir:

    - **region**: Qual o nome da região  você quer baixar? No caso de cidade(city) use o codigo de municipio do [IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)
    - **fileType**: Tipo de arquivo que  você quer baixar? [csv, shp, gpkg, raster]
    - **layer**: Nome da camada que  você quer baixar?
    - **filter**: Filtro que sera usa para baixar camada
    """
    return url_geofile(region, fileType, layer, filter, update, direct)


def url_geofile(
    regionValue, fileType, valueType, valueFilter, update, direct=False
):
    headers = {
        "X-Download-Region-Type": '',
        "X-Download-Region-Value": regionValue,
        "X-Download-Type-File": fileType,
        'X-Download-Layer':valueType,
        'X-Download-Filter':valueFilter
        
    }
    layerTypeName = None
    filterLabel = None
    logger.debug(regionValue)
    with MongoClient(settings.MONGODB_URL) as client:
        db = client.ows
        if isinstance(regionValue, int):
            if regionValue > 10 and regionValue < 54:
                db_states = client.validations.states
                tmp_states = db_states.find_one({'_id': regionValue})
                logger.debug(f'states {tmp_states["sigla"]}')
                regionValue = EnumStates(tmp_states['sigla'])
                logger.debug(regionValue)
            elif regionValue > 1100010 and regionValue < 5300109:
                regionValue = EnumCity(code=regionValue)
            else:
                
                raise HTTPException(400, 'filter_number_invalid', headers=headers)

        tmp = db.layers.find_one({'layertypes.valueType': valueType})
        try:
            tmp_descriptor = [
                x for x in tmp['layertypes'] if x['valueType'] == valueType
            ][0]

            try:
                filterLabel = tmp_descriptor['filterLabel']
                filters = [
                    str(x['valueFilter']) for x in tmp_descriptor['filters']
                ]
            except:
                filterLabel = None

            try:
                layerTypeName = tmp_descriptor['download']['layerTypeName']
            except:
                layerTypeName = valueType
        except Exception as e:
            logger.exception('ERROR COM MONGO')
    if valueFilter == 'year=all' and fileType == 'csv':
        valueFilter = ''
    else:
        if filterLabel is not None and valueFilter is None:
            if fileType == 'csv':
                headers['X-Download-Filter']=''
                raise HTTPException(
                    400, f'É obrigatorio informa um filter, use um desses. {filters+["year=all"]}',
                    headers=headers
                )
            
            else:
                headers['X-Download-Filter']=''
                raise HTTPException(
                    400, f'É obrigatorio informa um filter, use um desses. {filters}',headers=headers
                )
        if filterLabel is not None and not valueFilter in filters:
            if fileType == 'csv':
                raise HTTPException(
                400, f'Filtro informado não é valido, use um desses. {filters+["year=all"]}',headers=headers
                )
            else:
                raise HTTPException(
                    400, f'Filtro informado não é valido, use um desses. {filters}',headers=headers
                )
    logger.debug(f"{regionValue.enum_name}|{valueFilter}|")
    if valueFilter is None:
        payload = Payload(
            region=Region(type=regionValue.enum_name, value=regionValue.upper()),
            layer=Layer(
                valueType=valueType, download=Download(layerTypeName=layerTypeName)
            ),
            typeDownload=fileType
        )

    else:
        payload = Payload(
            region=Region(type=regionValue.enum_name, value=regionValue.upper()),
            layer=Layer(
                valueType=valueType, download=Download(layerTypeName=layerTypeName)
            ),
            typeDownload=fileType,
            filter=Filter(valueFilter=valueFilter),
        )
    logger.debug(payload)
    return start_dowload(payload, update, direct)


def start_dowload(payload: Payload, update: str, direct: bool):
    
    file_type = '.zip'
    if payload.typeDownload == 'csv':
        file_type = '.csv'
    valueFilter = ''
    region = payload.region
    headers = {
        "X-Download-Region-Type": region.type,
        "X-Download-Region-Value": region.value,
        "X-Download-Type-File": payload.typeDownload,
        'X-Download-Layer':payload.layer.valueType,
        'X-Download-Filter':valueFilter
        
    }
    try:
        valueFilter = payload.filter.valueFilter
        if payload.filter.valueFilter == '':
            fileParam = f'{region.value.lower()}_{payload.layer.valueType}'
        else:
            fileParam = f'{region.value.lower()}_{payload.layer.valueType}_{payload.filter.valueFilter}'
        headers['X-Download-Filter'] = valueFilter
    except AttributeError:
        fileParam = f'{region.value.lower()}_{payload.layer.valueType}'
    except Exception as e:
        logger.exception('erro')
        return HTTPException(500, f'e', headers=headers)

    
    try:
        client = client_minio()
    except Exception as e:
        logger.exception('Login erro')
        raise HTTPException(500, f'{e}', headers=headers)

    try:
        name_layer, map_type, map_conect, crs = get_layer(valueFilter)
    except:
        try:
            name_layer, map_type, map_conect, crs = get_layer(
                payload.layer.download.layerTypeName
            )
        except:
            logger.warning('Nome passado nao foi achado no filemap')
            try:
                logger.debug(payload.layer.valueType)
                name_layer, map_type, map_conect, crs = get_layer(
                    payload.layer.valueType
                )
                name_layer = name_layer.replace('_s100', '')
                sql_layer = name_layer
                if not 'sqlite' == map_conect:
                    db = map_conect
                else:
                    logger.debug('is sql')
            except:
                sql_layer = payload.layer.download.layerTypeName
                db = ''
                logger.exception('eu acho que é sql')

    logger.debug(f'name_layer:{name_layer} map_type:{map_type}')
    if not is_valid_query(payload.typeDownload, map_type):
        raise HTTPException(
            415,
            f'Incongruity in the type of data entered, please enter valid data for this layer\n Valid formats {get_format_valid(map_type)}',
            headers=headers
        )

    if payload.typeDownload == 'raster':

        name_layer = name_layer.replace('/STORAGE/catalog/', '')
        pathFile = f'raster/{name_layer}'
        objects = client.list_objects(
            settings.BUCKET,
            prefix=f'{pathFile}',
            recursive=True,
        )

    else:
        #ows/city/1200401/gpkg/pasture_col6_s100
        
        pathFile = f'{region.type}/{region.value}/{payload.typeDownload}/{payload.layer.valueType}/{fileParam}'
        objects = client.list_objects(
            settings.BUCKET,
            prefix=f'{pathFile}{file_type}',
            recursive=True,
        )

    logger.info(
        'file: {}{} fileType: {} regiao: {} value: {} sql_layer: {} valueFilter: {}'.format(
            pathFile,
            file_type,
            payload.typeDownload,
            region.type,
            region.value,
            payload.layer.download.layerTypeName,
            valueFilter,
        )
    )
    
    
    objects_list = list(objects)
    logger.debug(f'{len(objects_list)} , {update}, {settings.KEY_UPDATE}')

    if len(objects_list) == 1 and not update == settings.KEY_UPDATE:
        return responce_dowload(objects_list, direct, headers)

    elif len(objects_list) > 1:
        logger.exception('ERROR TEM MAIS DE UM OBJECT')
        raise HTTPException(500, 'Flaha ao carregar o dados', headers=headers)
    if payload.typeDownload == 'raster':
        client = client_minio()
        try:
            result = client.fput_object(
                settings.BUCKET,
                f'{pathFile}',
                f'/storage/catalog/{name_layer}',
                content_type='application/x-geotiff',
            )

        except FileNotFoundError:
            raise HTTPException(400, 'file_not_found', headers=headers)
        except Exception as e:
            logger.exception(e)
            raise HTTPException(500, e, headers=headers)

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
        if len(objects_list) == 1:
            return responce_dowload(objects_list, direct, headers)
        else:
            logger.exception('Erro ao salvar dados')
            raise HTTPException(500, 'Erro ao gerar arquivo', headers=headers)
    else:
        logger.debug(payload.layer.download.layerTypeName)
        try:

            sql_layer = name_layer
            if not 'sqlite' == map_conect:
                db = map_conect
            else:
                logger.debug('is sql')
        except:
            sql_layer = payload.layer.download.layerTypeName
            db = ''
            logger.debug('eu acho que é sql')
        logger.info(f'Processando map_layer:{name_layer}')
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
                direct,
            )
        else:
            return HTTPException(500, 'PayLoad', headers=headers)


def creat_file_postgre(
    payload,
    pathFile,
    region,
    sql_layer,
    valueFilter,
    fileParam,
    db,
    crs,
    direct,
):
    headers = {
        "X-Download-Region-Type": region.type,
        "X-Download-Region-Value": region.value,
        "X-Download-Type-File": payload.typeDownload,
        'X-Download-Layer':payload.layer.valueType,
        'X-Download-Filter':valueFilter
        
    }
    file_type = '.zip'
    if payload.typeDownload == 'csv':
        file_type = '.csv'
    try:
        geofile = CreatGeoFile(
            fileType=payload.typeDownload,
            file=f'{pathFile}{file_type}',
            regiao=region.type,
            value=region.value,
            sql_layer=sql_layer,
            valueFilter=valueFilter,
            db=db,
            crs=crs,
        )

    except ValueError as e:
        if str(e) == 'Cannot write empty DataFrame to file.':
            logger.info(f'{e}')
            raise HTTPException(
                400,
                'file_empty', headers=headers
            )
        logger.exception('Valor Error not empty')
        raise HTTPException(
            400,
            f'{e}', headers=headers
        )
    except FilterException as e:
        raise HTTPException(
            400,
            f'{e}', headers=headers
        )

    except Exception as e:
        raise HTTPException(
            400,
            f'{e}', headers=headers
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
                DB_HOST = settings.DB_HOST
                if db == '':
                    DB_PORT = settings.DB_PORT
                    DB_USER = settings.DB_USER
                    DB_PASSWORD = settings.DB_PASSWORD
                    DB_NAME = settings.DB_DATABASE
                else:
                    DB_PORT = db['port']
                    DB_USER = db['user']
                    DB_PASSWORD = db['password'].replace("'", '')
                    DB_NAME = db['dbname']
                FILE_STR = f'{tmpdirname}/{fileParam}.gpkg'
                PG_STR = f"PG:\"dbname='{DB_NAME}' host='{DB_HOST}' port='{DB_PORT}' user='{DB_USER}' password='{DB_PASSWORD}'\" "
                logger.info(f'OGR2OGR {FILE_STR}')
                if not process_is_run_by_fileName(
                    'ogr2ogr', FILE_STR.split('/')[-1]
                ):
                    ogr2ogr = f'ogr2ogr -f GPKG {FILE_STR} {PG_STR} -sql "{geofile.query()}"'
                    logger.info(ogr2ogr)
                    return_value = subprocess.call(ogr2ogr, shell=True)
                    logger.debug(return_value)
                else:
                    raise OGR2OGRisRun()
            elif payload.typeDownload == 'shp':
                logger.debug(f'{tmpdirname}/{fileParam}.shp')
                df, schema = geofile.gpd()
                df.to_file(f'{tmpdirname}/{fileParam}.shp')
        except OGR2OGRisRun:
            raise HTTPException(
                400,
                f'ogr2ogr_run', headers=headers
            )
        except ValueError as e:
            if str(e) == 'Cannot write empty DataFrame to file.':
                logger.info(f'{e}')
                raise HTTPException(
                    400,
                    'file_empty', headers=headers
                )
            logger.exception('Valor Error not empty')
            raise HTTPException(
                400,
                f'{e}', headers=headers
            )
        except FilterException as e:
            raise HTTPException(400, f'{e}', headers=headers)
        except Exception as e:
            logger.exception('Erro ao Criar arquivo ValueError: {e}')
            raise HTTPException(500, f'Erro ao Criar arquivo: {e}', headers=headers)

        file_paths = glob(f'{tmpdirname}/*')
        if file_type == '.zip':
            with ZipFile(f'{tmpdirname}/{fileParam}.zip', 'w', ZIP_BZIP2) as zip:
                # writing each file one by one
                for file in file_paths:
                    zip.write(file, file.split('/')[-1])

            logger.info(
                f'zip criado {tmpdirname}/{fileParam}.zip dos arquivos {file_paths}'
            )
        geofile = GeoFile(f'{pathFile}{file_type}')
        try:
            result = client.fput_object(
                settings.BUCKET,
                f'{geofile.object_name}',
                f'{tmpdirname}/{fileParam}{file_type}',
                content_type=geofile.content_type,
                tags=geofile.to_tags,
                metadata=dict(geofile.to_tags),
            )
        except FileNotFoundError:
            raise HTTPException(400, 'file_not_found', headers=headers)
        except Exception as e:
            logger.exception(e)
            raise HTTPException(500, e, headers=headers)

        logger.info(
            'created {0} object; etag: {1}, version-id: {2}'.format(
                result.object_name,
                result.etag,
                result.version_id,
            ),
        )
        objects = client.list_objects(
            settings.BUCKET,
            prefix=f'{pathFile}{file_type}',
            recursive=True,
        )
        objects_list = list(objects)
        if len(objects_list) == 1:
            return responce_dowload(objects_list, direct, headers)
        else:
            logger.exception('Erro ao salvar dados')
            raise HTTPException(500, 'Erro ao gerar arquivo', headers=headers)


def responce_dowload(obj, direct,headers):
    tmp_dowloadUrl = DowloadUrl(
        object_name=obj[0].object_name, size=obj[0].size
    )
    if direct:
        return RedirectResponse(tmp_dowloadUrl.url, 307)

    else:
        return JSONResponse(content=dict(tmp_dowloadUrl), headers=headers )
