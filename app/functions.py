from minio import Minio

from app.config import logger, settings


class MinioAuthError(Exception):
    pass


def client_minio():
    logger.debug(f'{settings.MINIO_HOST} {settings.MINIO_USER}')
    try:
        logger.debug(f"host:{settings.MINIO_HOST} user:{settings.MINIO_USER} password:{settings.MINIO_PASSWORD}")
        return Minio(
            settings.MINIO_HOST,
            settings.MINIO_USER,
            settings.MINIO_PASSWORD,
            secure=True,
        )
    except Exception as e:
        raise MinioAuthError
