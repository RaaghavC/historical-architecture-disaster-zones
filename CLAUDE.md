# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Historical Architecture Disaster Zones is a digital preservation pipeline for architectural heritage, with special focus on Antakya/Antioch documentation following the February 2023 earthquakes. The system provides:
1. Universal web scraping from cultural heritage archives
2. Geospatial data storage in PostGIS
3. 3D reconstruction using photogrammetry/AI
4. Public API and viewer with IIIF compliance

## Common Development Commands

### Database & Environment Setup
```bash
# Copy environment template and add API keys
cp .env.example .env

# Start PostGIS database
docker compose up -d postgres

# Install Python dependencies
pip install -r requirements.txt
```

### Data Collection Commands
```bash
# Original harvesting commands (database-based)
python -m data_collection.cli harvest archnet --limit 500
python -m data_collection.cli harvest europeana --limit 100

# Universal scraping commands (no database required)
python -m data_collection.cli scrape "https://example.com/page"
python -m data_collection.cli search "Antakya" "mosque" "Ottoman"
python -m data_collection.cli antakya  # Comprehensive Antakya harvest
python -m data_collection.cli list-sources  # Show available archives

# Combine harvested Excel files
python combine_excel_files.py

# Download images from master collection
python download_images.py
```

### Testing & Development
```bash
# Run tests
pytest tests/

# Start API server
uvicorn web.api:app --reload

# 3D reconstruction
python -m processing.photogrammetry reconstruct archnet:803387
```

## Architecture Overview

### 1. Data Collection (`data_collection/`)
Two parallel systems:
- **Original Harvesters**: Database-integrated, inherit from `BaseHarvester`
- **Universal Scrapers**: Standalone web scraping, inherit from `UniversalArchiveScraper`

Universal scraping architecture:
```
universal_scraper.py      # Base classes, UniversalDataRecord model (30+ fields)
universal_harvester.py    # Master orchestrator for all scrapers
organizer.py             # Multi-format export (Excel, JSON, SQLite)
scrapers/
├── extractors.py        # Content type detection (image/text/manuscript/PDF)
├── generic_scraper.py   # Works with any website
├── archnet_scraper.py   # ArchNet-specific implementation
└── manar_scraper.py     # Manar al-Athar implementation
```

### 2. Database (`database/`)
- PostgreSQL with PostGIS extension
- SQLAlchemy models in `models.py` handle spatial data via GeoAlchemy2
- Schema auto-creates on first use
- Note: Universal scrapers work without database dependency

### 3. Processing (`processing/`)
- `photogrammetry.py`: COLMAP → OpenMVS pipeline for 3D reconstruction
- `ai_reconstruction.py`: Stable Diffusion with ControlNet for texture synthesis
- `lidar_processing.py`: Point cloud processing
- `validation.py`: Quality checks for reconstructions

### 4. Web API (`web/`)
- FastAPI endpoints serve items, geojson, and 3D meshes
- Frontend uses Leaflet for mapping
- IIIF compliance for image serving

## Key Technical Details

### Universal Scraping System
- **Data Model**: `UniversalDataRecord` with comprehensive metadata fields
- **Rate Limiting**: Built-in delays and anti-detection measures
- **SSL Handling**: Bypasses verification for development (verify=False)
- **Parallel Processing**: ThreadPoolExecutor for multiple archives
- **Output Formats**: Excel (with multiple sheets), JSON, SQLite, text reports
- **Deduplication**: Automatic based on download URLs

### Database Operations
- **Config Management**: Settings from `.env` via `config.py`
- **Spatial Queries**: Use `ST_Intersects` for bbox filtering
- **Connection**: PostgreSQL DSN format in POSTGRES_DSN env var

### API Features
- **IIIF Compliance**: Thumbnails with IIIF URL patterns
- **Authentication**: Bearer tokens for write operations (when enabled)
- **Error Handling**: Custom exceptions, comprehensive logging

## External Dependencies

Required installations:
- PostgreSQL with PostGIS extension (or use Docker)
- COLMAP and OpenMVS for 3D reconstruction
- Chrome/Chromium for Selenium (if using browser mode)

Python packages:
- Web scraping: beautifulsoup4, selenium, pandas, openpyxl
- Database: sqlalchemy, geoalchemy2, psycopg2
- API: fastapi, uvicorn
- Processing: numpy, opencv-python, trimesh

## Troubleshooting Common Issues

1. **PostgreSQL connection refused**: Ensure Docker container is running
2. **SSL certificate errors**: Fixed with verify=False in scrapers
3. **No data found**: Some sites load content dynamically - try search instead of direct URLs
4. **Database column mismatch**: Fixed in organizer.py (27 vs 28 values)
5. **Missing Chrome driver**: Run `python -m webdriver_manager.chrome`

## Data Organization

Harvested data structure:
```
harvested_data/
├── harvest_url_[domain]_[timestamp]/
│   ├── *.xlsx          # Excel with multiple analysis sheets
│   ├── *.json          # Complete metadata
│   ├── *.db            # SQLite database
│   └── *_report.txt    # Summary statistics

downloaded_images/
├── 01_Antakya_Specific/
├── 02_Ottoman_Architecture/
├── 03_Byzantine_Architecture/
├── 04_Archaeological_Sites/
└── 05_Other_Heritage/
```