from app.config import settings

from minio import Minio

def client_minio():
    return Minio(settings.MINIO_HOST, settings.MINIO_USER, settings.MINIO_PASSWORD, secure=True)