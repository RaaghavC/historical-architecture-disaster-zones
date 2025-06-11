from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from config import settings
from utils.metadata import DCRecord
from utils.logging_config import get_logger
from .models import Base, Item

log = get_logger(__name__)

engine = create_engine(settings.POSTGRES_DSN, echo=False, future=True)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)


def ingest_records(records: List[DCRecord]):
    sess = Session()
    for rec in records:
        pt = (
            from_shape(Point(rec.spatial_lon, rec.spatial_lat), srid=4326)
            if rec.spatial_lat and rec.spatial_lon
            else None
        )
        obj = Item(
            identifier=rec.identifier,
            title=rec.title,
            creator=rec.creator,
            description=rec.description,
            type=rec.type,
            format=rec.format,
            source_url=str(rec.source) if rec.source else None,
            rights=rec.rights,
            coverage_time=rec.coverage_temporal,
            date_iso=rec.date,
            geom=pt,
            extra=rec.extra,
        )
        sess.merge(obj)
    sess.commit()
    sess.close()
