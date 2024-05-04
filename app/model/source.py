from enum import Enum
from typing import Optional

from pydantic import BaseModel, HttpUrl

class TypeSource(str, Enum):
    PASTURE = 'pasture'
    MEDICINE = 'medecine'
    ALL = 'all'
    
    def where(self):
        if self.value == 'pasture':
            return 'ismed_first = FALSE'
        if self.value == 'pasture':
            return 'ismed_first = TRUE'
        return None        
    
    
class BaseSource(BaseModel):
    id: str
    doi: Optional[str]
    title: Optional[str]
    keywords:str
    ismed_first:bool
    cluster:int
    image: Optional[HttpUrl]

class Source(BaseModel):
    id: str
    doi: Optional[str]
    title: Optional[str]
    language: Optional[str]
    type_crossref: str
    ismed: Optional[str]
    id_sourcer: Optional[str]
    abstract: Optional[str]
    keywords: str
    ismed_first: bool
    image: Optional[HttpUrl]
    cluster: int