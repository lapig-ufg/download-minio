from typing import Dict, List

from fastapi import APIRouter, HTTPException
from app.model.source import BaseSource, TypeSource, Source
from app.config import settings, logger

import pandas as pd

from sqlalchemy import create_engine

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
async def getl_list_works(id:str):

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
    response_model=List[BaseSource],
)
async def getl_list_works(
    type_source:TypeSource, 
    page:int = 1,
    serch: str = None,
    cluseter: int = None,
    limit: int = 100
    ):

    if limit > 500:
        limit = 500
        
    offset = (page-1)*limit
    
    where = []
    
    where.append(type_source.where())
    
    if serch is not None:
        where.append(f"to_tsquery('english', '{serch}') @@ works.search ")
        
    if cluseter is not None:
        where.append(f'cluster = {cluseter}')

    _where = ' AND '.join(list(filter(lambda x: True if x is not None else False, where)))
    if not '' == _where:
        _where = f' WHERE {_where}'
    _range = f'offset {offset} limit {limit}'    
    sql = f"select id,doi,title,keywords,ismed_first,cluster from works {_where} {_range}"
    # logger.debug(sql)
    df = pd.read_sql(sql,engine)
    df['image'] = df.apply(get_img, axis=1)
    return df.to_dict('records')