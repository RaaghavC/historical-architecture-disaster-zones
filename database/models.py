from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from geoalchemy2 import Geometry
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    creator = Column(Text)
    description = Column(Text)
    type = Column(String)
    format = Column(String)
    source_url = Column(String)
    rights = Column(Text)
    coverage_time = Column(String)
    date_iso = Column(DateTime)
    geom = Column(Geometry("POINT", srid=4326))
    extra = Column(JSON)
