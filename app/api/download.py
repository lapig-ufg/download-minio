import tempfile
from glob import glob
from zipfile import ZipFile

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.config import logger, settings
from app.functions import client_minio
from app.model.creat_geofile import CreatGeoFile
from app.model.models import GeoFile
from app.model.payload import Payload
from app.util.mapfile import get_layer

router = APIRouter()


class DowloadUrl(BaseModel):
    object_name: str
    size: int
    host: str = settings.MINIO_HOST
    buckt: str = settings.BUCKET
    url: HttpUrl = ''

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.url = f'https://{self.host}/{self.buckt}/{self.object_name}'


@router.post('/', response_description='Dowload', response_model=DowloadUrl)
async def start_dowload(payload: Payload):

    if payload.layer.filterHandler == 'layername':
        layerName = payload.layer.filterSelected
    else:
        layerName = payload.layer.valueType

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

    logger.debug(
        f"""
                 file: {pathFile}.zip
                 fileType: {payload.typeDownload}
                 regiao: {region.type}
                 value: {region.value}
                 sql_layer: {payload.layer.download.layerTypeName}
                 valueFilter: {valueFilter}
                 """
    )

    objects_list = list(objects)
    if len(objects_list) == 1:
        return DowloadUrl(
            object_name=objects_list[0].object_name, size=objects_list[0].size
        )

    elif len(objects_list) > 1:
        logger.exception('ERROR TEM MAIS DE UM OBJECT')
        raise HTTPException(500, 'Flaha ao carregar o dados')
    if payload.typeDownload == 'raster':
        client = client_minio()
        result = client.fput_object(
            'ows',
            f'{pathFile}',
            f'/storage/catalog/{raster_file}',
            content_type='application/x-geotiff',
        )
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
                ...
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
    try:
        df, schema = geofile.gpd()
    except ValueError as e:
        if str(e) == "Cannot write empty DataFrame to file.":
            logger.info(f"{e}")
            raise HTTPException(
                    400,
                'file_empty',
                )
        raise HTTPException(
                    400,
                f'{e}',
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
                df.to_csv(f'{tmpdirname}/{fileParam}.csv')
            elif payload.typeDownload == 'gpkg':
                logger.debug(f'{tmpdirname}/{fileParam}.gpkg')
                df.to_file(
                    f'{tmpdirname}/{fileParam}.gpkg',
                    driver='GPKG',
                    schema=schema,
                )
            elif payload.typeDownload == 'shp':
                logger.debug(f'{tmpdirname}/{fileParam}.shp')
                df.to_file(f'{tmpdirname}/{fileParam}.shp', schema=schema)
        except ValueError as e:
            logger.exception(
                f'Erro ao Criar arquivo ValueError: {e}\n{df.columns}\n{df.dtypes}'
            )
            raise HTTPException(
                400,
                f'Erro ao Criar arquivo ValueError: {e}',
            )
        except Exception as e:
            logger.exception('Erro ao Criar arquivo ValueError: {e}')
            raise HTTPException(
                500, f'Erro ao Criar arquivo: {e}\n{df.columns}\n{df.dtypes}'
            )

        file_paths = glob(f'{tmpdirname}/*')
        with ZipFile(f'{tmpdirname}/{fileParam}.zip', 'w') as zip:
            # writing each file one by one
            for file in file_paths:
                zip.write(file, file.split('/')[-1])

        logger.info(
            f'zip criado {tmpdirname}/{fileParam}.zip dos arquivos {file_paths}'
        )
        geofile = GeoFile(f'{pathFile}.zip')

        result = client.fput_object(
            'ows',
            f'{geofile.object_name}',
            f'{tmpdirname}/{fileParam}.zip',
            content_type=geofile.content_type,
            tags=geofile.to_tags,
            metadata=dict(geofile.to_tags),
        )
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
