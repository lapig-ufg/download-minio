from minio import Minio

from app.config import logger, settings
import psutil

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



def process_is_run_ogr2ogr_by_fileName(fileName):

    for proc in psutil.process_iter([
        'cmdline', 
        'create_time', 
        'name', 
        'pid',  
        'status', 
        'username'
        ]):
        details = proc.info
        if details['name'] == 'ogr2ogr':
            for detail in details['cmdline']:
                if fileName in detail:
                    print(fileName)
                    return True
    return False