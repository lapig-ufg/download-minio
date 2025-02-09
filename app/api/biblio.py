from math import ceil
from typing import List, Union

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine

from app.config import settings
from app.model.source import BaseSource, Source, TypeSource

from loguru import logger


class Status(BaseModel):
    pages: int
    total: int


engine = create_engine(
    f'postgresql://{settings.PGUSER}:{settings.PGPASSWORD}@{settings.PGHOST}:{settings.DB_PORT}/{settings.DB_DATABASE}'
)

router = APIRouter()


def get_img(row):
    if '-' in row["type_plataforma"]:
        local, year, _, modo = row['type_plataforma'].split('-')
        # public/literatura/cerrado/2025/amplo/000_keywords.png
        return f'https://{settings.DOWNLOAD_URL}/public/literatura/{local}/{year}/{modo}/{row["cluster"]:03}_keywords.png'
    return f'https://{settings.DOWNLOAD_URL}/public/literatura/{row["type_plataforma"]}/cluster/{row["cluster"]:03}_keywords.png'


@router.get(
    '/works/{type_source}/id/{_id}',
    response_description='List collections id ',
    response_model=Source,
)
async def getl_works(type_source: TypeSource, _id: str):
    df = pd.read_sql(
        f"select * from works where {type_source.where()} AND id = '{_id}'",
        engine,
    )
    df['image'] = df.apply(get_img, axis=1)
    if len(df) > 0:
        # logger.debug(df.to_dict('records')[0])
        return df.to_dict('records')[0]
    raise HTTPException(404, 'not existe work')


@router.get(
    '/works/list/{type_source}',
    response_description='List collections _id ',
    response_model=Union[List[BaseSource], Status],
)
async def getl_list_works(
    type_source: TypeSource,
    page: int = 1,
    search: str = None,
    cluster: int = None,
    sort_active: str = None,
    sort_direction: str = None,
    limit: int = 100,
):
    logger.info(
        (
            type_source,
            page,
            search,
            cluster,
            sort_active,
            sort_direction,
            limit,
        )
    )
    logger.info('getl_list_works')
    if limit > 500:
        limit = 500

    offset = (page - 1) * limit

    where = []

    where.append(type_source.where())

    _sort = ''
    if search is not None:
        where.append(f"to_tsquery('english', '{search}') @@ works.search ")

    if cluster is not None:
        where.append(f'cluster = {cluster}')

    if sort_active is not None and sort_direction in ['asc', 'desc']:
        _sort = f' ORDER BY {sort_active} {sort_direction}'

    _where = ' AND '.join(
        list(filter(lambda x: True if x is not None else False, where))
    )
    if '' != _where:
        _where = f' WHERE {_where}'
    logger.info(_where)
    logger.info(where)
    _range = f'offset {offset} limit {limit}'
    if page == 0:
        sql = sql = f'select count(*) from works {_where}'
        logger.debug(sql)
        df = pd.read_sql(sql, engine)
        if len(df) > 0:
            total = int(df['count'].iloc[0])
            return {'pages': int(ceil((total / limit))), 'total': int(total)}

    sql = f"""--sql
    select type_plataforma, id,
        doi,
        title,
        keywords,
        cluster, 
        cited_by_count, 
        publication_date, 
        referenced_works_count, 
        relevance_score 
        from works 
        {_where} {_sort} {_range}"""
    logger.info(sql)
    try:
        df = pd.read_sql(sql, engine)
        df['image'] = df.apply(get_img, axis=1)
        return df.to_dict('records')
    except Exception as e:
        logger.exception('Error: %s', e)
        raise HTTPException(status_code=500, detail='Error processing request')
