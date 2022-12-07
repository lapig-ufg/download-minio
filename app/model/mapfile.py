from typing import List, Optional

from pydantic import BaseModel


class Metadata(BaseModel):
    ows_title: str
    ows_abstract: str
    gml_exclude_items: str
    gml_include_items: str
    gml_geometries: str


class MapFileLayers(BaseModel):
    name: Optional[str]
    fileType: Optional[List[str]]
    projection: List[str]
    type: str
    metadata: Metadata
