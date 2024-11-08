from enum import Enum
from typing import Optional
from datetime import date

from pydantic import BaseModel, HttpUrl

class TypeSource(str, Enum):
    PASTURE = 'pasture'
    CERRADO = 'cerrado'
    ALL = 'all'
    
    def where(self):
        if self.value == 'pasture':
            return 'type_plataforma = pastagem'
        if self.value == 'medicine':
            return 'type_plataforma = cerrado'
        return None        
    
    
class BaseSource(BaseModel):
    id: str
    doi: Optional[str]
    title: Optional[str]
    keywords:str
    ismed_first:bool
    cluster:int
    cited_by_count: int
    publication_date:date
    referenced_works_count: int
    relevance_score: float
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
    cited_by_count: int
    publication_date:date
    referenced_works_count: int
    relevance_score: float