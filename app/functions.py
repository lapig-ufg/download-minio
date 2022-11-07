from minio import Minio

from app.config import settings


def client_minio():
    return Minio(
        settings.MINIO_HOST,
        settings.MINIO_USER,
        settings.MINIO_PASSWORD,
        secure=True,
    )
