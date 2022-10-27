from glob import glob
from minio.commonconfig import Tags
from minio import Minio
from os import environ
from app.config import settings, logger

class GeoFile():
    def __init__(self,path_name):
        
        split_path = path_name.split('/')[-5:]
        if not 5 == len(split_path):
            raise Exception(f'Path is not a valid {split_path}')
        self.limit_type = split_path[0]
        self.limit_name = split_path[1]
        self.file_type = split_path[2]
        self.layer = split_path[4].split('_year=')[0]
        self.year = int(split_path[4].split('_year=')[1].split('.')[0])
        self.extension = split_path[4].split('.')[1]
        self.file_path = path_name

    @property
    def object_name(self):
        return f'{self.limit_type}/{self.limit_name}/{self.file_type}/{self.layer}/{self.layer}_year={self.year}.{self.extension}'
    
    @property
    def to_tags(self):
        tags = Tags(for_object=True)
        tags['limit_type'] = self.limit_type
        tags['limit_name'] = self.limit_name
        tags['file_type'] = self.file_type
        tags['layer'] = self.layer
        tags['year'] = str(self.year)
        return tags
    @property
    def content_type(self):
        extensions = {
            'csv':'text/csv',
            'gpkg':'application/geopackage+sqlite3',
            'shp':'application/octet-stream',
            'tif':'application/x-geotiff',
            'tiff':'application/x-geotiff',
            'zip':'application/zip',

        }
        try:
            return extensions[self.extension]
        except:
            return 'application/octet-stream'
        
paths = glob(f'{settings.DOWNLOAD}/**/*.*', recursive=True)

client = Minio(settings.MINIO_HOST, settings.MINIO_USER, settings.MINIO_PASSWORD, secure=True)
update = False
for path in paths:
    file = GeoFile(path)
    objects = client.list_objects(
        "ows", prefix=file.object_name, recursive=True,
    )
    if len(list(objects)) == 0 or update:
        result = client.fput_object(
            "ows", file.object_name, file.file_path,
            content_type=file.content_type,
            tags=file.to_tags,
            metadata=dict(file.to_tags)
        )
        logger.info(
            "created {0} object; etag: {1}, version-id: {2}".format(
                result.object_name, result.etag, result.version_id,
            ),
        )
    else:
        logger.info('File ja existe')
