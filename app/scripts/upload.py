from glob import glob
from os import environ

from minio import Minio
from minio.commonconfig import Tags

from app.config import logger, settings
from app.model.models import GeoFile


def upload():
    paths = glob(f'{settings.DOWNLOAD}/**/*.*', recursive=True)

    client = Minio(
        settings.MINIO_HOST,
        settings.MINIO_USER,
        settings.MINIO_PASSWORD,
        secure=True,
    )
    update = False
    for path in paths:
        file = GeoFile(path)
        objects = client.list_objects(
            'ows',
            prefix=file.object_name,
            recursive=True,
        )
        if len(list(objects)) == 0 or update:
            result = client.fput_object(
                'ows',
                file.object_name,
                file.file_path,
                content_type=file.content_type,
                tags=file.to_tags,
                metadata=dict(file.to_tags),
            )
            logger.info(
                'created {0} object; etag: {1}, version-id: {2}'.format(
                    result.object_name,
                    result.etag,
                    result.version_id,
                ),
            )
        else:
            logger.info('File ja existe')
