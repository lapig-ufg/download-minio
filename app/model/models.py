from datetime import datetime
from enum import Enum
from typing import Dict, List, Union

from pydantic import Field, HttpUrl
from pymongo import MongoClient
from app.config import settings, logger
from app.db import MongoModel, PyObjectId

from pydantic import BaseModel
