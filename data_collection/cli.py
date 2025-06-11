"""
$ python -m data_collection.cli harvest archnet --limit 250
"""
import typer, importlib
from database.ingest import ingest_records
from utils.logging_config import get_logger

log = get_logger(__name__)
app = typer.Typer(add_completion=False)


@app.command()
def harvest(source: str, limit: int = 0):
    module_name = f"data_collection.{source.lower()}_harvester"
    cls_name = f"{source.capitalize()}Harvester"
    cls = getattr(importlib.import_module(module_name), cls_name)
    harvester = cls()
    records = harvester.harvest()
    if limit:
        records = records[:limit]
    ingest_records(records)
    log.info("Finished ingesting %s records into PostGIS", len(records))


if __name__ == "__main__":
    app()
