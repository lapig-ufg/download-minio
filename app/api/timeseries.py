from json import dumps, loads
from typing import Union

from fastapi import APIRouter, HTTPException, Path, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient

from app.config import logger, settings
from app.model.payload import (
    EnumBiomes,
    EnumCity,
    EnumCountry,
    EnumFronteiras,
    EnumRegions,
    EnumStates,
    FileTypes,
)

router = APIRouter()


@router.get(
    '/{region}/{fileType}/{layer}',
    name='Get Time Series Geofile',
    response_description='Retorna um txt com os link para Download',
)
async def get_geofile(
    request: Request,
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
    type: str = Query('txt', include_in_schema=False),
):
    """
    Baixa uma camada do mapserver conforme os parametos a seguir:

    - **region**: Qual o nome da região  você quer baixar? No caso de cidade(city) use o codigo de municipio do [IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)
    - **fileType**: Tipo de arquivo que  você quer baixar? [csv, shp, gpkg, raster]
    - **layer**: Nome da camada que  você quer baixar?
    """
    base_url = request.base_url
    if settings.HTTPS:
        base_url = f'{base_url}'.replace('http://', 'https://')

    regionValue = region
    # fileType,
    valueType = layer
    with MongoClient(settings.MONGODB_URL) as client:
        db = client.ows
        if isinstance(regionValue, int):
            if regionValue > 10 and regionValue < 54:
                db_states = client.validations.states
                tmp_states = db_states.find_one({'_id': regionValue})
                try:
                    logger.debug(f'states {tmp_states["sigla"]}')
                    regionValue = EnumStates(tmp_states['sigla'])
                except:
                    raise HTTPException(400, 'invalid_region')
                logger.debug(regionValue)
            elif regionValue > 1100010 and regionValue < 5300109:
                regionValue = EnumCity(code=regionValue)
            else:
                raise HTTPException(400, 'filter_number_invalid')

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
        except TypeError:
            raise HTTPException(400, 'layer_not_exist')

        except Exception as e:
            logger.exception('ERROR COM MONGO')
        base_url = f'{base_url}api/download/{regionValue}/{fileType}/{layer}'
        extencao = 'zip'
        if fileType == 'raster':
            extencao = 'tif'

        if filterLabel is None:
            match type:
                case 'json':
                    return Response(
                        jsonable_encoder(dumps({'urls': [f'{base_url}']})),
                        200,
                        media_type='application/json',
                    )
                case _:
                    return Response(
                        f'{base_url}', 200, media_type='text/plain'
                    )

        else:
            rows = []
            for _filter in filters:
                rows.append(f'{base_url}/{_filter}?direct=true')
            match type:
                case 'json':
                    return Response(
                        jsonable_encoder(dumps({'urls': rows})),
                        200,
                        media_type='application/json',
                    )
                case 'wget':
                    comand = '#/bin/bash\n'
                    for _filter in filters:
                        comand += f'wget -O {layer}_{regionValue}_{_filter}.{extencao} {base_url}/{_filter}?direct=true  \n'
                    return Response(comand, 200, media_type='text/plain')
                case _:
                    return Response(
                        '\n'.join(rows), 200, media_type='text/plain'
                    )
