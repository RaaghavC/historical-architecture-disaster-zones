"""
FastAPI back-end serving:

    • /items              – JSON list + bbox filtering
    • /items/{identifier} – full record + IIIF thumbnails
    • /geojson            – FeatureCollection for Leaflet
    • /meshes/{id}.ply    – static download of 3D mesh
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from shapely.geometry import mapping
import os

if os.getenv("TESTING") == "1":
    class _DummyQuery:
        def filter(self, *a, **kw):
            return self

        def filter_by(self, *a, **kw):
            return self

        def all(self):
            return []

        def one_or_none(self):
            return None

    class _DummySession:
        def query(self, *a, **kw):
            return _DummyQuery()

    DBSession = lambda: _DummySession()
    from database.models import Item  # only for type hints
else:
    from database.ingest import Session as DBSession
    from database.models import Item
from utils.iiif import make_iiif_url
from utils.metadata import DCRecord
from config import settings

app = FastAPI(title="Antakya Digital Archive")


@app.get("/items", response_model=list[DCRecord])
def list_items(bbox: str | None = None):
    sess: Session = DBSession()
    q = sess.query(Item)
    if bbox:
        minx, miny, maxx, maxy = map(float, bbox.split(","))
        wkt = (
            f"POLYGON(({minx} {miny}, {maxx} {miny}, {maxx} {maxy}, {minx} {maxy}, {minx} {miny}))"
        )
        q = q.filter(Item.geom.ST_Within(wkt))
    return [DCRecord.from_orm(o) for o in q.all()]


@app.get("/items/{identifier}", response_model=DCRecord)
def detail(identifier: str):
    sess = DBSession()
    item = sess.query(Item).filter_by(identifier=identifier).one_or_none()
    if not item:
        raise HTTPException(404, "Not found")
    rec = DCRecord.from_orm(item)
    if item.source_url and item.source_url.endswith(("jpg", "png")):
        rec.extra["iiif_thumbnail"] = make_iiif_url(item.source_url, w=256)
    return rec


@app.get("/geojson")
def as_geojson():
    sess = DBSession()
    feats = []
    for o in sess.query(Item).filter(Item.geom.isnot(None)).all():
        geom = o.geom
        feats.append(
            {
                "type": "Feature",
                "id": o.identifier,
                "properties": {"title": o.title},
                "geometry": mapping(geom),
            }
        )
    return {"type": "FeatureCollection", "features": feats}


@app.get("/meshes/{identifier}.ply")
def download_mesh(identifier: str):
    mesh_path = settings.DATA_DIR / "meshes" / f"{identifier}.ply"
    if not mesh_path.exists():
        raise HTTPException(404, "mesh not found")
    return FileResponse(mesh_path)
