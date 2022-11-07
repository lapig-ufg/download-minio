import geopandas as gpd
import pandas as pd

from app.db import geodb


class CreatGeoFile:
    def __init__(
        self, fileType, file, regiao, value, sql_layer, valueFilter
    ) -> None:
        self.fileType = fileType
        self.file = file
        self.regiao = regiao
        self.value = value
        self.sql_layer = sql_layer
        self.valueFilter = valueFilter

    def where(self, msfilter):
        return ' AND '.join(msfilter)

    def get_column_name(self):
        if self.fileType == 'csv':
            dbConnection = geodb()
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
            return ', '.join(
                [
                    name
                    for name in dataFrame.column_name
                    if not name in ['geom', 'geometry']
                ]
            )
        return ' * '

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
    SELECT {self.get_column_name()} 
    FROM {self.sql_layer} WHERE {self.where(list_filter)}"""

    def gpd(self):
        con = geodb()
        if self.fileType in ['shp', 'gpkg']:
            try:
                df = gpd.GeoDataFrame.from_postgis(
                    self.querey(), con, index_col='gid'
                )
            except KeyError:
                df = gpd.GeoDataFrame.from_postgis(self.querey(), con)
        elif self.fileType == 'csv':
            try:
                df = pd.read_sql(self.querey(), con, index_col='gid')
            except KeyError:
                df = pd.read_sql(self.querey(), con)
        con.close()
        return df
