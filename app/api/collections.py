from typing import Dict, List
from fastapi import APIRouter, HTTPException


from app.db import db_collections

router = APIRouter()

@router.get('/', response_description="List collections _id ", response_model=List[Dict])
async def get_collections():
    if (collections := await db_collections.find({},{'_id':1}).to_list(1000)) is not None:
        return collections
    raise HTTPException(status_code=404, detail=f"Base error")


