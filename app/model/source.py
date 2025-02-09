from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, HttpUrl


class TypeSource(str, Enum):
    PASTURE = 'pasture'
    CERRADO = 'cerrado'
    AMPLO = 'cerrado-2025-02-amplo'
    RESTRITO = 'cerrado-2025-02-restrito'


    ALL = 'all'

    def where(self):
        match self.value:
            case 'pasture':
                return "type_plataforma = 'pastagem'"
            case 'cerrado':
                return "type_plataforma = 'cerrado'"
            case 'cerrado-2025-02-amplo':
                return "type_plataforma = 'cerrado-2025-02-amplo'"
            case 'cerrado-2025-02-restrito':
                return "type_plataforma = 'cerrado-2025-02-restrito'"
        return None


class BaseSource(BaseModel):
    type_plataforma: str
    id: str
    doi: Optional[str]
    title: Optional[str]
    keywords: str|None
    cluster: int
    cited_by_count: int
    publication_date: date
    referenced_works_count: int
    relevance_score: float
    image: Optional[HttpUrl]


class Source(BaseModel):
    type_plataforma: str
    id: str
    doi: Optional[str]
    title: Optional[str]
    language: Optional[str]
    type_crossref: str
    id_sourcer: Optional[str]
    abstract: Optional[str]
    keywords: str|None
    image: Optional[HttpUrl]
    cluster: int
    cited_by_count: int
    publication_date: date
    referenced_works_count: int
    relevance_score: float
