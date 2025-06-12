"""
Command-line interface for data collection.

Usage examples:
$ python -m data_collection.cli harvest archnet --limit 250
$ python -m data_collection.cli scrape https://archnet.org/sites/1644
$ python -m data_collection.cli search "Antakya" "Antioch" --archives archnet manar
$ python -m data_collection.cli antakya
"""
import typer
import importlib
from typing import Optional, List
from pathlib import Path

from utils.logging_config import get_logger

log = get_logger(__name__)
app = typer.Typer(add_completion=False)


@app.command()
def harvest(source: str, limit: int = 0):
    """Harvest data from API-based sources (legacy command)."""
    try:
        # Import database functionality only when needed
        from database.ingest import ingest_records
        
        module_name = f"data_collection.{source.lower()}_harvester"
        cls_name = f"{source.capitalize()}Harvester"
        cls = getattr(importlib.import_module(module_name), cls_name)
        harvester = cls()
        records = harvester.harvest()
        if limit:
            records = records[:limit]
        ingest_records(records)
        log.info("Finished ingesting %s records into PostGIS", len(records))
    except (ImportError, AttributeError) as e:
        typer.echo(f"Error: Unknown source '{source}'")
        typer.echo("Use 'python -m data_collection.cli list-sources' to see available sources")
        raise typer.Exit(1)


@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL to scrape"),
    output_dir: str = typer.Option("harvested_data", help="Output directory for results"),
):
    """Scrape data from any archive URL."""
    from data_collection.universal_harvester import UniversalHarvester
    harvester = UniversalHarvester(output_dir=output_dir)
    
    typer.echo(f"Scraping URL: {url}")
    df = harvester.harvest_url(url)
    
    if df.empty:
        typer.echo("No data found at the specified URL")
    else:
        typer.echo(f"Successfully scraped {len(df)} records")
        typer.echo(f"Results saved to: {output_dir}/")


@app.command()
def search(
    terms: List[str] = typer.Argument(..., help="Search terms"),
    archives: Optional[List[str]] = typer.Option(None, help="Specific archives to search"),
    output_dir: str = typer.Option("harvested_data", help="Output directory for results"),
):
    """Search multiple archives for specific terms."""
    from data_collection.universal_harvester import UniversalHarvester
    harvester = UniversalHarvester(output_dir=output_dir)
    
    if archives:
        typer.echo(f"Searching archives {', '.join(archives)} for: {', '.join(terms)}")
        df = harvester.harvest_search(terms, archives=archives)
    else:
        available = harvester.list_archives()
        typer.echo(f"Searching all archives ({', '.join(available)}) for: {', '.join(terms)}")
        df = harvester.harvest_all_archives(terms)
    
    if df.empty:
        typer.echo("No results found")
    else:
        typer.echo(f"\nTotal records found: {len(df)}")


@app.command()
def list_sources():
    """List available data sources."""
    typer.echo("Available API-based sources:")
    api_sources = ["archnet", "europeana", "dpla", "wikimedia", "manaralathar"]
    for source in api_sources:
        typer.echo(f"  - {source}")
    
    typer.echo("\nAvailable scraping archives:")
    from data_collection.universal_harvester import UniversalHarvester
    harvester = UniversalHarvester()
    for archive in harvester.list_archives():
        typer.echo(f"  - {archive}")
    
    typer.echo("\nNote: Any URL can be scraped using the 'scrape' command")


@app.command()
def antakya():
    """Harvest Antakya/Antioch heritage data from all sources."""
    typer.echo("Starting comprehensive Antakya heritage data collection...")
    
    search_terms = [
        "Antakya", "Antioch", "Hatay",
        "Habib-i Neccar", "Habib Neccar", "Habibi Najjar",
        "Greek Orthodox Church Antioch", "Rum Orthodox",
        "Antakya Castle", "Antioch Citadel", "Antakya Kalesi",
        "St. Pierre Church", "Sen Piyer"
    ]
    
    from data_collection.universal_harvester import UniversalHarvester
    harvester = UniversalHarvester(output_dir="antakya_heritage")
    df = harvester.harvest_all_archives(search_terms)
    
    if not df.empty:
        typer.echo(f"\nSuccessfully collected {len(df)} records related to Antakya heritage")
        typer.echo("\nData types collected:")
        type_counts = df['Data_Type'].value_counts()
        for dtype, count in type_counts.items():
            typer.echo(f"  - {dtype}: {count}")
        
        typer.echo("\nRecords by archive:")
        archive_counts = df['Archive'].value_counts()
        for archive, count in archive_counts.items():
            typer.echo(f"  - {archive}: {count}")
    else:
        typer.echo("No Antakya-related records found")


if __name__ == "__main__":
    app()