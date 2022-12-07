from typing import  List, Union

from fastapi import APIRouter, HTTPException
from app.config import settings
from pickle import load
from app.model.functions import get_format_valid

from app.model.mapfile import MapFileLayers, Metadata
from app.config import logger


with open(f'{settings.CACHE_MAP}{settings.FILE_MAP_CACH}', 'rb') as f:
    lpmap = load(f)
    
with open(f'{settings.CACHE_MAP}{settings.LISTL_LAYER_OWS}', 'rb') as f:
    dateset = load(f)

with open(f'{settings.CACHE_MAP}{settings.LAYER_METATA_OWS}', 'rb') as f:
    all_metada = load(f)
    

router = APIRouter()


@router.get(
    '/',
    response_description='Lista as layers',
    response_model=List[str],
)
async def get_all_layers():
    return  dateset

@router.get(
    '/{layer}/metadata',
    response_description='Lista as layers',
    response_model=Union[MapFileLayers,List[MapFileLayers]],
)
async def get_all_layers(layer):
    try:
        result = lpmap[layer]
        result['name'] = layer
        result['fileType'] = get_format_valid(result["type"])
        return result
    except Exception:
        raise HTTPException(404,'Layer invalid')