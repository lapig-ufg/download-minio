from minio import Minio

from app.config import logger, settings


class MinioAuthError(Exception):
    pass


def client_minio():
    logger.debug(f'{settings.MINIO_HOST} {settings.MINIO_USER}')
    try:
        return Minio(
            settings.MINIO_HOST,
            settings.MINIO_USER,
            settings.MINIO_PASSWORD,
            secure=True,
        )
    except Exception as e:
        raise MinioAuthError
