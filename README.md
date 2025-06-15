# Antakya Digital Preservation Toolkit

End-to-end pipeline for **Historical Architecture in Disaster Zones**:
from raw image harvesting → IIIF compliant archive → AI-assisted 3D
reconstruction → public API + viewer.

## About This Project

This is an international collaborative research project funded by a **Stanford Public Humanities Seed Grant** to digitally document and preserve the architectural heritage of Antakya (ancient Antioch) following the devastating February 2023 earthquakes in Turkey. The project addresses the urgent need to preserve irreplaceable cultural heritage before further deterioration occurs.

**For the complete project vision, background, and detailed implementation plan, see [PROJECT_VISION.md](PROJECT_VISION.md).**

### Key Facts
- **3,752 of 8,444** historical structures in Hatay Province were damaged
- Monuments from Roman period to Ottoman Empire (300 BCE - 19th century) affected
- Three-year project timeline with four implementation phases
- Combines cutting-edge technology (AI, photogrammetry, LiDAR) with traditional research

## Quick Start (macOS / Linux)

```bash
git clone https://github.com/RaaghavC/historical-architecture-disaster-zones.git
cd historical-architecture-disaster-zones
cp .env.example .env                # add API keys
# spin up the bundled PostGIS instance
docker compose up -d postgres
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1 Collect data
python -m data_collection.cli harvest archnet --limit 500

# 2 Launch API (http://127.0.0.1:8000/docs)
uvicorn web.api:app --reload

# 3 Reconstruct a monument
python -m processing.photogrammetry reconstruct archnet:803387
```

All modules are heavily commented; read them in the order presented in
the main proposal (Phase 1 → Phase 4).
