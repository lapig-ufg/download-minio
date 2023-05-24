import geopandas as gpd
import pandas as pd

from app.config import logger, settings
from app.db import geodb
from app.util.exceptions import FilterException
from app.util.mapfile import get_schema


def normalize_col(col):
    SQL = ['group']
    if col in SQL or ' ' in col:
        return f"'{col}'"
    return col


from pymongo import MongoClient


class CreatGeoFile:
    def __init__(
        self,
        fileType,
        file,
        regiao,
        value,
        sql_layer,
        valueFilter,
        db='',
        crs='epsg:4326',
    ) -> None:
        self.fileType = fileType
        self.file = file
        self.regiao = regiao
        self.value = value
        self.valueFilter = valueFilter
        self.sql_layer = sql_layer
        self.db = db
        self.crs = crs
        dbConnection = geodb(self.db)
        logger.debug(self.sql_layer)
        dataFrame = pd.read_sql(
            f"""
            SELECT column_name,data_type 
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name   = '{self.sql_layer}'
            """,
            dbConnection,
        )
        dbConnection.close()
        cols = list(dataFrame.column_name)
        self.cols = cols
        self.rename = False
        self.schema = get_schema(dataFrame)
        self.query_personality = False
        type_geom = ['geom', 'geometry']
        try:
            self.geom = [name for name in cols if name in type_geom][0]
        except:
            logger.exception('Geometry has not been defined')
        remove_cols = ['gid', 'objectid', 'index']

        with MongoClient(settings.MONGODB_URL) as client:
            db = client.ows
            personalized_query = db.queries.find_one(
                {'sql_layer': self.sql_layer}
            )
            try:
                self.rename = [
                    f'{normalize_col(key)} as {normalize_col(value)}'
                    for key, value in zip(
                        personalized_query['columns'],
                        personalized_query['columns_rename'],
                    )
                ]
            except:
                logger.debug(f'personalized_query: {personalized_query}')

            try:
                self.query_personality = personalized_query[self.fileType]
            except:
                ...
            try:
                self.cols = personalized_query['search_column']
            except:
                ...
        if not self.rename is False:
            if self.fileType == 'csv':
                logger.debug(self.rename)
                self.column_name = ', '.join(self.rename)
            else:
                self.column_name = ', '.join([*self.rename, self.geom])

        else:
            logger.debug('nao personalizado')
            if self.fileType == 'csv':
                self.column_name = ', '.join(
                    [
                        normalize_col(name)
                        for name in cols
                        if not name.lower() in [*type_geom, *remove_cols]
                    ]
                )
            else:
                self.column_name = ', '.join(
                    [
                        normalize_col(name)
                        for name in cols
                        if not name.lower() in remove_cols
                    ]
                )

    def where(self, msfilter):
        return ' AND '.join(msfilter)

    def region_type(self):
        region = self.regiao.lower()
        value = self.value.lower()
        query = {
            'city': {
                'col': 'cd_geocmu',
                'query': f" UPPER(unaccent(cd_geocmu)) = UPPER(unaccent('{value}'))",
            },
            'state': {
                'col': 'uf',
                'query': f" UPPER(unaccent(uf)) = UPPER(unaccent('{value}'))",
            },
            'biome': {
                'col': 'bioma',
                'query': f" UPPER(unaccent(bioma)) = UPPER(unaccent('{value}'))",
            },
            'fronteira': {
                'amaz_legal': 'amaz_legal = 1',
                'matopiba': 'matopiba = 1',
            },
            'region': {
                'col': 'regiao',
                'query': f" UPPER(unaccent(regiao)) = UPPER(unaccent('{value}'))",
            },
        }
        try:

            if region == 'country':
                return ''
            if region == 'fronteira':
                if not value in self.cols:
                    raise FilterException('unable_filter_layer')
                return query[region][value]

            if not query[region]['col'] in self.cols:
                raise FilterException('unable_filter_layer')
            return query[region]['query']

        except FilterException as e:
            raise FilterException(e)
        except Exception as e:
            logger.exception('Error filter')
            raise Exception(e)

    def query(self):
        list_filter = []
        if not self.valueFilter == '':
            list_filter.append(self.valueFilter)
        tmp_region = self.region_type()
        if not tmp_region == '':
            list_filter.append(tmp_region)
        if not self.query_personality is False:
            return self.query_personality.replace(
                '{{WHERE}}', self.where(list_filter)
            )
        if len(list_filter) == 0:
            return f'SELECT {self.column_name} FROM {self.sql_layer}'
        return f'SELECT {self.column_name} FROM {self.sql_layer} WHERE {self.where(list_filter)}'

    def gpd(self):
        con = geodb(self.db)
        query = self.query()
        logger.info(query)
        if self.fileType in ['shp', 'gpkg']:
            df = gpd.GeoDataFrame.from_postgis(query, con, geom_col=self.geom)
            schema_df = gpd.io.file.infer_schema(df)
            for i in self.schema:
                if self.schema[i] in ['date']:
                    df[i] = pd.to_datetime(df[i]).dt.strftime('%Y-%m-%d')
                if self.schema[i] in ['datetime']:
                    df[i] = pd.to_datetime(df[i]).dt.strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )
            df.crs = self.crs
        elif self.fileType == 'csv':
            df = pd.read_sql(query, con)
            schema_df = ''
        con.close()
        return (df, None)
