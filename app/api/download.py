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

    pathFile = f'{region.type}/{region.value}/{payload.typeDownload}/{payload.layer.valueType}/{fileParam}'

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
    client = client_minio()
    objiects = client.list_objects(
        settings.BUCKET,
        prefix=f'{pathFile}.zip',
        recursive=True,
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
        raise NotImplemented
    else:
        geofile = CreatGeoFile(
            fileType=payload.typeDownload,
            file=f'{pathFile}.zip',
            regiao=region.type,
            value=region.value,
            sql_layer=payload.layer.download.layerTypeName,
            valueFilter=valueFilter,
        )
        df = geofile.gpd()
        with tempfile.TemporaryDirectory() as tmpdirname:
            client = client_minio()
            logger.debug(f'tmpdirname : {tmpdirname}')
            try:
                if payload.typeDownload == 'csv':
                    df.to_csv(f'{tmpdirname}/{fileParam}.csv')
                elif payload.typeDownload == 'gpkg':
                    df.to_file(f'{tmpdirname}/{fileParam}.gpkg', driver='GPKG')
                elif payload.typeDownload == 'shp':
                    df.to_file(f'{tmpdirname}/{fileParam}.shp')
            except ValueError as e:
                raise HTTPException(400, f'{e}')
            except Exception as e:
                raise HTTPException(500, f'{e}')

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
                f'test/{geofile.object_name}',
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
                prefix=f'test/{pathFile}.zip',
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


