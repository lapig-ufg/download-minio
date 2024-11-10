from typing import Dict, List

from fastapi import APIRouter

router = APIRouter()


@router.get(
    '/',
    response_description='List collections _id ',
    response_model=List[Dict],
)
async def get_collections():
    return {'status': 'oi'}
