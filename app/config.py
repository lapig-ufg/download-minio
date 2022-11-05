from dynaconf import Dynaconf
from loguru import logger
import os
import sys


def start_logger():
    type_logger = 'development'
    if os.environ.get("LAPIG_ENV") == 'production':
        type_logger = 'production'
    logger.info(f'The system is operating in mode {type_logger}')

confi_format='[ {time} | process: {process.id} | {level: <8}] {module}.{function}:{line} {message}'
rotation='500 MB'


if os.environ.get("LAPIG_ENV") == 'production':
    logger.remove()
    logger.add(sys.stderr,level='INFO', format=confi_format)
    

logger.add('../log/downloadmino/downloadmino.log', rotation=rotation, level="INFO")
logger.add('../log/downloadmino/downloadmino_WARNING.log', level="WARNING", rotation=rotation)

settings = Dynaconf(
    envvar_prefix='MINIO',
    settings_files=['settings.toml', '.secrets.toml','../settings.toml','/data/settings.toml'],
    environments=True,
    load_dotenv=True,
)


