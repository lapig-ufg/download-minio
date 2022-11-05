from typing import Dict, List
from fastapi import APIRouter, HTTPException
from app.model.payload import Payload
from app.config import settings, logger
from minio import Minio

router = APIRouter()

@router.post('/', response_description="Dowload", response_model=Dict)
async def start_dowload(payload: Payload):
    
    query = {
        'city': 'cd_geocmu={region.value}',
        'state': 'uf={region.value}',
        'bioma':'bioma={region.value}'
    }
    
    if payload.layer.filterHandler == 'layername':
        layerName = payload.layer.filterSelected
    else:
        layerName = payload.layer.valueType
        
    if payload.filter is None: 
        fileParam = f"{payload.layer.valueType}_{payload.filter.valueFilter}"
    else:
        fileParam = payload.layer.valueType
    

    pathFile = f"{payload.region.type}/{payload.region.value}/{payload.typeDownload}/{payload.layer.valueType}/{fileParam}"
    logger.info(f'{pathFile}')
    client = Minio(settings.MINIO_HOST, settings.MINIO_USER, settings.MINIO_PASSWORD, secure=True)
    objects = client.list_objects(
            "ows", prefix=pathFile, recursive=True,
        )
    if len(list(objects)) == 1:
        return f"{settings.MINIO_HOST}/ows/{pathFile}"
        
    return dict(payload)


