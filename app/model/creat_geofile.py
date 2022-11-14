import geopandas as gpd
import pandas as pd

from app.config import logger
from app.db import geodb
from app.util.mapfile import get_schema



class CreatGeoFile:
    def __init__(
        self, fileType, file, regiao, value, sql_layer, valueFilter, db ='',crs="epsg:4326"
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
        
        self.schema = get_schema(dataFrame)
        
        logger.debug(f"Full column_name: {cols}")
        type_geom = ['geom', 'geometry']
        try:
            self.geom = [name for name in cols if name in type_geom][0]
        except:
            raise ValueError('Geometry has not been defined')
        try:
            self.index = [name for name in cols if name in ['gid', 'objectid', 'index']][0]
        except:
            self.index = None
            
        if self.fileType == 'csv':
            self.column_name = ', '.join(
                [
                    name
                    for name in cols
                    if not name in type_geom
                ]
            )
        else:
            self.column_name = ', '.join(
                    [
                        name
                        for name in cols
                    ]
                )
        

    def where(self, msfilter):
        return ' AND '.join(msfilter)


    def region_type(self):
        region = self.regiao.lower()
        value = self.value.lower()
        query = {
            'city': f" UPPER(unaccent(cd_geocmu)) = UPPER(unaccent('{value}'))",
            'state': f" UPPER(unaccent(uf)) = UPPER(unaccent('{value}'))",
            'bioma': f" UPPER(unaccent(bioma)) = UPPER(unaccent('{value}'))",
            'fronteira': {
                'amaz_legal': 'amaz_legal = 1',
                'matopiba': 'matopiba = 1',
            },
            'region': f" UPPER(unaccent(regiao)) = UPPER(unaccent('{value}'))",
        }
        try:
            if region == 'fronteira':
                return query[region][value]
            return query[region]
        except:
            ...

    def querey(self):
        list_filter = []
        if not self.valueFilter == '':
            list_filter.append(self.valueFilter)
        list_filter.append(self.region_type())

        return f"""
    SELECT {self.column_name} 
    FROM {self.sql_layer} WHERE {self.where(list_filter)}"""

    def gpd(self):
        con = geodb(self.db)
        query = self.querey()
        logger.debug(query)
        if self.fileType in ['shp', 'gpkg']:
            df = gpd.GeoDataFrame.from_postgis(
                    query, con, index_col=self.index, geom_col=self.geom
                )
            schema_df = gpd.io.file.infer_schema(df)
            for i in self.schema:
                if self.schema[i] in ['date']:
                    schema_df['properties'][i] = 'str'
                    df[i] = pd.to_datetime(df[i]).dt.strftime('%Y-%m-%d') 
                if self.schema[i] in ['datetime']:
                    schema_df['properties'][i] = 'str'
                    df[i] = pd.to_datetime(df[i]).dt.strftime('%Y-%m-%d %H:%M:%S') 
                if self.schema[i] in ['integer']:
                    schema_df['properties'][i] = 'int'
                if self.schema[i] in ['numeric']:
                    schema_df['properties'][i] = 'float'
                if self.schema[i] in ['character varying']:
                    schema_df['properties'][i] = 'str'
                logger.debug(schema_df)
            df.crs = self.crs 
        elif self.fileType == 'csv':
            df = pd.read_sql(query, con, index_col=self.index)
            schema_df = ''
        con.close()
        return (df, schema_df)
