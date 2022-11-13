import geopandas as gpd
import pandas as pd

from app.config import logger
from app.db import geodb



class CreatGeoFile:
    def __init__(
        self, fileType, file, regiao, value, sql_layer, valueFilter, db =''
    ) -> None:
        self.fileType = fileType
        self.file = file
        self.regiao = regiao
        self.value = value
        self.valueFilter = valueFilter
        self.sql_layer = sql_layer
        self.db = db
        dbConnection = geodb(self.db)
        dataFrame = pd.read_sql(
                f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name   = '{self.sql_layer}'
            """,
                dbConnection,
            )
        dbConnection.close()
        cols = list(dataFrame.column_name)
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
        elif self.fileType == 'csv':
            df = pd.read_sql(query, con, index_col=self.index)
        con.close()
        return df
