from datetime import datetime

import motor.motor_asyncio
import pytz
from bson import ObjectId
from pydantic import BaseConfig, BaseModel
from sqlalchemy import create_engine

from app.config import logger

from .config import settings

# client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
# db = client.pgrass


def geodb(database = ''):
    user = settings.DB_USER
    password = settings.DB_PASSWORD
    host = settings.DB_HOST
    port = settings.DB_PORT
    db = settings.DB_DATABASE
    if isinstance(database,dict):
        user = database['user']
        password = database['password']
        db = database['dbname']
       

    pgdb = 'postgresql+psycopg2'
    logger.debug(
        f'{pgdb}://{user}:{password}@{host}:{port}/{db}'.replace("'",""),
    )
    alchemyEngine = create_engine(
        f'{pgdb}://{user}:{password}@{host}:{port}/{db}'.replace("'",""), pool_recycle=3600
    )

    return alchemyEngine.connect()


def get_datetime_to_mongo():
    return datetime.now().astimezone(pytz.utc).isoformat()


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')


class MongoModel(BaseModel):
    class Config(BaseConfig):
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }

    @classmethod
    def from_mongo(cls, data: dict):
        """We must convert _id into "id"."""
        if not data:
            return data
        id = data.pop('_id', None)
        return cls(**dict(data, id=id))

    def mongo(self, **kwargs):
        exclude_unset = kwargs.pop('exclude_unset', True)
        by_alias = kwargs.pop('by_alias', True)

        parsed = self.dict(
            exclude_unset=exclude_unset,
            by_alias=by_alias,
            **kwargs,
        )

        # Mongo uses `_id` as default key. We should stick to that as well.
        if '_id' not in parsed and 'id' in parsed:
            parsed['_id'] = parsed.pop('id')

        return parsed
