-- PostGIS enabled database
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS item (
    id              SERIAL PRIMARY KEY,
    identifier      TEXT UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    creator         TEXT,
    description     TEXT,
    type            TEXT DEFAULT 'Image',
    format          TEXT,
    source_url      TEXT,
    rights          TEXT,
    coverage_time   TEXT,
    date_iso        TIMESTAMP,
    geom            geometry(Point, 4326),
    extra           JSONB
);
CREATE INDEX IF NOT EXISTS idx_item_gix ON item USING GIST (geom);
