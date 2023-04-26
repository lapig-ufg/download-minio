from pickle import load
from typing import Dict, List, Union

from fastapi import APIRouter, HTTPException

from app.config import logger, settings
from app.model.functions import get_format_valid
from app.model.mapfile import MapFileLayers, Metadata

with open(f'{settings.CACHE_MAP}{settings.FILE_MAP_CACH}', 'rb') as f:
    lpmap = load(f)

with open(f'{settings.CACHE_MAP}{settings.LISTL_LAYER_OWS}', 'rb') as f:
    dateset = load(f)

with open(f'{settings.CACHE_MAP}{settings.LAYER_METATA_OWS}', 'rb') as f:
    all_metada = load(f)

result = sorted(set(dateset) & set(lpmap))
router = APIRouter()


@router.get(
    '/',
    response_description='Lista as layers',
    response_model=List[str],
)
async def get_all_layers():
    return sorted(result)


@router.get(
    '/{layer}/metadata',
    response_description='Obetem metadata',
    response_model=Dict,
)
async def get_metadata(layer):
    try:
        return all_metada[layer]
    except Exception:
        raise HTTPException(404, 'Layer invalid')
