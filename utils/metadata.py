"""
Helpers for building *Dublin Core* + CIDOC-CRM compliant metadata records.

The same data structures are re-used across harvesters, the ingest
pipeline and the FastAPI serialisers, guaranteeing a single-source
of-truth.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, constr


class DCRecord(BaseModel):
    identifier: constr(min_length=8)
    title: str
    creator: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    type: str = "Image"
    format: str = "image/jpeg"
    source: Optional[HttpUrl] = None
    language: str = "und"
    rights: Optional[str] = None
    spatial_lat: Optional[float] = None
    spatial_lon: Optional[float] = None
    coverage_temporal: Optional[str] = None
    extra: Dict[str, Any] = {}

    class Config:
        orm_mode = True
