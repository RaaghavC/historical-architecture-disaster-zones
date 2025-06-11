# Antakya Digital Preservation Toolkit

End-to-end pipeline for **Historical Architecture in Disaster Zones**:
from raw image harvesting → IIIF compliant archive → AI-assisted 3D
reconstruction → public API + viewer.

## Quick Start (macOS / Linux)

```bash
git clone https://github.com/your-org/historical-architecture-disaster-zones.git
cd historical-architecture-disaster-zones
cp .env.example .env                # add API keys
docker compose up -d postgres       # optional helper script
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
