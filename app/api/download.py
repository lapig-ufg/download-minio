from typing import Dict, List
from fastapi import APIRouter, HTTPException
from app.model.payload import Payload

router = APIRouter()

@router.post('/', response_description="Dowload", response_model=Dict)
async def start_dowload(payload: Payload):
    return dict(payload)


