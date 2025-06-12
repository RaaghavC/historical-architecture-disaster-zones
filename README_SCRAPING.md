# Universal Archive Scraping System

## Overview

This system provides a modular, extensible framework for harvesting data from any digital archive, with special focus on Antakya/Antioch heritage documentation. It can handle multiple data types (images, text, PDFs, manuscripts) and export results in various formats.

## Features

- **Universal Data Model**: Handles any content type with comprehensive metadata
- **Automatic Detection**: Identifies data types (image/text/handwritten/PDF/etc.)
- **Flexible Scraping**: Works with any website structure
- **Smart Organization**: Exports to Excel, JSON, and SQLite database
- **Parallel Processing**: Harvest multiple archives simultaneously
- **Anti-Detection**: Built-in rate limiting and browser automation

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Chrome driver for Selenium (if not already installed)
python -m webdriver_manager.chrome
```

## Usage

### 1. Scrape a Single URL

```bash
python -m data_collection.cli scrape "https://archnet.org/sites/1644"
```

### 2. Search Multiple Archives

```bash
# Search all registered archives
python -m data_collection.cli search "Antakya" "Antioch" "Habib-i Neccar"

# Search specific archives only
python -m data_collection.cli search "Antakya" --archives archnet manar
```

### 3. Harvest Antakya Heritage Data

```bash
# Comprehensive Antakya data collection
python -m data_collection.cli antakya
```

### 4. List Available Sources

```bash
python -m data_collection.cli list-sources
```

## Output Formats

Results are saved in the `harvested_data/` directory (or custom directory) with:

1. **Excel File** (`*.xlsx`):
   - Main sheet with all records
   - Summary by archive
   - Separate sheets by data type
   - Date analysis

2. **JSON File** (`*.json`):
   - Complete metadata for each record
   - Preserves all fields and relationships

3. **SQLite Database** (`*.db`):
   - Normalized tables with indexes
   - Queryable for complex analysis

4. **Summary Report** (`*_report.txt`):
   - Statistics and overview of harvest

## Data Fields

Each record includes:

- **Identification**: ID, source archive, URL
- **Content**: Title, description, keywords, subjects
- **Temporal**: Date created, date ranges, uncertainty markers
- **Geographic**: Location, coordinates, spatial coverage
- **Type**: Data type (image/text/PDF/etc.), MIME type
- **Attribution**: Creator, contributor, publisher
- **Access**: Download URL, thumbnail, rights, license
- **Technical**: Dimensions, file size, language, script

## Adding New Archives

To add support for a new archive:

1. Create a new scraper in `data_collection/scrapers/`:

```python
from ..universal_scraper import UniversalArchiveScraper

class MyArchiveScraper(UniversalArchiveScraper):
    def __init__(self):
        super().__init__("My Archive", "https://myarchive.org")
    
    def _register_extractors(self):
        # Register data extractors
        pass
    
    def _scrape_search(self, search_terms):
        # Implement search logic
        pass
```

2. Register it in `universal_harvester.py`:

```python
self.scrapers['myarchive'] = MyArchiveScraper()
```

## Architecture

```
data_collection/
├── universal_scraper.py      # Base classes and data model
├── universal_harvester.py    # Master orchestrator
├── organizer.py             # Data organization and export
├── scrapers/
│   ├── extractors.py        # Content type extractors
│   ├── archnet_scraper.py   # ArchNet implementation
│   ├── manar_scraper.py     # Manar al-Athar implementation
│   └── generic_scraper.py   # Generic website scraper
└── cli.py                   # Command-line interface
```

## Examples

### Scraping ArchNet

```bash
# Scrape specific monument page
python -m data_collection.cli scrape "https://archnet.org/sites/1644"

# Search for Antakya content
python -m data_collection.cli search "Antakya" --archives archnet
```

### Scraping Any Website

```bash
# The generic scraper works with any URL
python -m data_collection.cli scrape "https://example.com/gallery"
```

### Programmatic Usage

```python
from data_collection.universal_harvester import UniversalHarvester

# Initialize harvester
harvester = UniversalHarvester()

# Harvest from URL
df = harvester.harvest_url("https://archnet.org/sites/1644")

# Search archives
results = harvester.harvest_search(["Antakya", "Antioch"])

# Access data
print(f"Found {len(df)} records")
print(df[['Title', 'Data_Type', 'Date']].head())
```

## Troubleshooting

1. **No data found**: Check if the website requires login or has anti-scraping measures
2. **Rate limiting**: Adjust `rate_limit_delay` in scraper settings
3. **JavaScript content**: Enable browser mode by setting `use_browser=True`
4. **Missing Chrome driver**: Run `python -m webdriver_manager.chrome`

## Notes

- Respect robots.txt and website terms of service
- Some archives may require authentication
- Large harvests can take significant time
- Results are automatically deduplicated based on URLs