import logging
import os
import sys

from dynaconf import Dynaconf

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def start_logger():
    type_logger = 'development'
    if os.environ.get('LAPIG_ENV') == 'production':
        type_logger = 'production'
    logger.info(f'The system is operating in mode {type_logger}')



settings = Dynaconf(
    envvar_prefix='MINIO',
    settings_files=[
        'settings.toml',
        '.secrets.toml',
        '../settings.toml',
        '/data/settings.toml',
    ],
    environments=True,
    load_dotenv=True,
)
