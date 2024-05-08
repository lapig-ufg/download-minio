from typing import Dict, List, Union
from math import ceil

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.model.source import BaseSource, TypeSource, Source
from app.config import settings, logger
from fastapi_cache.decorator import cache

import pandas as pd
import numpy as np

from sqlalchemy import create_engine

class Status(BaseModel):
    pages: int
    total: int

engine = create_engine(
    f'postgresql://{settings.PGUSER}:{settings.PGPASSWORD}@{settings.PGHOST}:{settings.PGPORT}/{settings.PGDATABASE}'
    )

router = APIRouter()

def get_img(row):
    _type = 'pasture'
    if row['ismed_first']:
        _type = 'med'
    return f'https://{settings.DOWNLOAD_URL}/public/bibiografia/{_type}/{row["cluster"]:03}_keywords.png'



@router.get(
    '/works/id/{id}',
    response_description='List collections _id ',
    response_model=Source,
)
@cache(expire=86400)
async def getl_works(id:str):

    df = pd.read_sql(f"select * from works where id = '{id}'",engine)
    df['image'] = df.apply(get_img, axis=1)
    if len(df) >0:
        # logger.debug(df.to_dict('records')[0])
        return df.to_dict('records')[0]
    raise HTTPException(
        404, 'not existe work'
                )
    
        

@router.get(
    '/works/list/{type_source}',
    response_description='List collections _id ',
    response_model=Union[List[BaseSource],Status],
)
@cache(expire=86400)
async def getl_list_works(
    type_source:TypeSource, 
    page:int = 1,
    search: str = None,
    cluster: int = None,
    sort_active:str = None,
    sort_direction:str = None,
    limit: int = 100
    
    ):

    if limit > 500:
        limit = 500
        
    offset = (page-1)*limit
    
    where = []
    
    where.append(type_source.where())
    
    _sort = ''
    if search is not None:
        where.append(f"to_tsquery('english', '{search}') @@ works.search ")
        
    if cluster is not None:
        where.append(f'cluster = {cluster}')
        
        
    if sort_active is not None and sort_direction in ['asc','desc']:
        _sort = f' ORDER BY {sort_active} {sort_direction}'
        

    _where = ' AND '.join(list(filter(lambda x: True if x is not None else False, where)))
    if not '' == _where:
        _where = f' WHERE {_where}'
    _range = f'offset {offset} limit {limit}'    
    if page == 0:
        sql = sql = f"select count(*) from works {_where}"
        logger.debug(sql)
        df = pd.read_sql(sql,engine)
        if len(df) > 0:
            total = int(df['count'].iloc[0])
            return {
                
                'pages': int(ceil((total/limit))),
                'total': int(total)
            }
    
    sql = f"select id,doi,title,keywords,ismed_first,cluster from works {_where} {_sort} {_range}"
    logger.debug(sql)
    df = pd.read_sql(sql,engine)
    df['image'] = df.apply(get_img, axis=1)
    return df.to_dict('records')