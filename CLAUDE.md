# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Historical Architecture Disaster Zones is a digital preservation pipeline for architectural heritage. It harvests imagery from cultural heritage APIs, stores them with geospatial data in PostGIS, reconstructs 3D models using photogrammetry/AI, and serves them via FastAPI/IIIF.

## Common Development Commands

```bash
# Start PostGIS database
docker compose up -d postgres

# Install Python dependencies
pip install -r requirements.txt

# Harvest data from sources
python -m data_collection.cli harvest archnet --limit 500
python -m data_collection.cli harvest europeana --limit 100

# Start API server
uvicorn web.api:app --reload

# Run tests
pytest tests/

# 3D reconstruction
python -m processing.photogrammetry reconstruct archnet:803387
```

## Architecture Overview

1. **Data Collection** (`data_collection/`): Harvesters inherit from `BaseHarvester` implementing `query_remote_source()` and `transform()` methods. Each returns standardized `DCRecord` objects.

2. **Database** (`database/`): PostgreSQL with PostGIS extension. SQLAlchemy models in `models.py` handle spatial data via GeoAlchemy2. Schema auto-creates on first use.

3. **Processing** (`processing/`): 
   - `photogrammetry.py`: COLMAP → OpenMVS pipeline for 3D reconstruction
   - `ai_reconstruction.py`: Stable Diffusion with ControlNet for texture synthesis

4. **Web API** (`web/`): FastAPI endpoints serve items, geojson, and 3D meshes. Frontend uses Leaflet for mapping.

## Key Technical Details

- **Config Management**: Settings loaded from `.env` file via `config.py`
- **Spatial Queries**: Use `ST_Intersects` for bbox filtering in PostgreSQL
- **IIIF Compliance**: Thumbnails served with IIIF URL patterns
- **Error Handling**: Custom exceptions in harvesters, proper logging throughout
- **API Authentication**: Bearer tokens for write operations (when enabled)

## External Dependencies

- COLMAP and OpenMVS must be installed separately for 3D reconstruction
- PostgreSQL with PostGIS extension (provided via Docker)
- Stable Diffusion models downloaded automatically on first use