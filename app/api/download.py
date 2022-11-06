from typing import Dict, List
from fastapi import APIRouter, HTTPException
from app.model.payload import Payload
from app.config import settings, logger
from minio import Minio
import pandas as pd
import geopans as gpd

from pydantic import BaseModel, HttpUrl

router = APIRouter()

class DowloadUrl(BaseModel):
    object_name: str
    size: int
    host: str = settings.MINIO_HOST
    buckt:str = settings.BUCKET
    url: HttpUrl = ''
    def __init__(self,**data) -> None:
        super().__init__(**data)
        self.url = f"https://{self.host}/{self.buckt}/{self.object_name}"
        
        


@router.post('/', response_description="Dowload",  response_model=DowloadUrl)
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
    
    logger.debug(payload.filter)
    try:
        fileParam = f"{payload.layer.valueType}_{payload.filter.valueFilter}"
    except AttributeError:
        fileParam = payload.layer.valueType
    except Exception as e:
        logger.exception('erro')
        return HTTPException(500,f'e')
    

    pathFile = f"{payload.region.type}/{payload.region.value}/{payload.typeDownload}/{payload.layer.valueType}/{fileParam}"
    logger.info(f'{pathFile}')
    client = Minio(settings.MINIO_HOST, settings.MINIO_USER, settings.MINIO_PASSWORD, secure=True)
    objects = client.list_objects(
            settings.BUCKET, prefix=f"{pathFile}.zip", recursive=True,
        )
    objects_list = list(objects)
    if len(objects_list) == 1:
        return DowloadUrl(
            object_name = objects_list[0].object_name,
            size = objects_list[0].size
            )
        
    return dict(payload)


