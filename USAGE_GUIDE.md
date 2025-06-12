# Universal Scraping System - Usage Guide

## Current Status

The universal scraping system is now functional with the following fixes:
1. ✅ Fixed database column mismatch error
2. ✅ Enhanced data extraction capabilities
3. ✅ Fixed SSL certificate issues
4. ✅ Created modular scraper architecture

## How to Use the System

### 1. Basic URL Scraping

```bash
# Scrape any website
python3 -m data_collection.cli scrape "https://example.com/page"

# Results are saved in harvested_data/ directory
```

### 2. Search Multiple Archives

```bash
# Search all configured archives
python3 -m data_collection.cli search "Antakya" "mosque" "Ottoman"

# Search specific archives only
python3 -m data_collection.cli search "Damascus" --archives manar
```

### 3. Comprehensive Antakya Harvest

```bash
# This searches for Antakya-related content across all archives
python3 -m data_collection.cli antakya
```

## Working Examples

### Example 1: Scraping Manar al-Athar

```bash
# Search for Syrian architecture
python3 -m data_collection.cli search "Syria" "Damascus" --archives manar

# Scrape a specific collection
python3 -m data_collection.cli scrape "https://www.manar-al-athar.ox.ac.uk/pages/browse.php?country=Turkey"
```

### Example 2: Using the Simple Scraper (for testing)

```bash
# If the main scraper has issues, use the simple scraper
python3 simple_scrape.py "https://www.archnet.org/sites/1644"
```

### Example 3: Programmatic Usage

```python
from data_collection.universal_harvester import UniversalHarvester

# Create harvester
harvester = UniversalHarvester(output_dir="my_results")

# Scrape a URL
df = harvester.harvest_url("https://example.com")

# Search archives
results = harvester.harvest_search(["mosque", "Ottoman"], archives=["manar"])

# Access the data
print(f"Found {len(df)} records")
print(df[['Title', 'Data_Type', 'Date', 'Location']].head())
```

## Output Files

Each harvest creates a timestamped directory with:

1. **Excel file** (`.xlsx`): 
   - Main sheet with all records
   - Separate sheets by data type
   - Summary statistics

2. **JSON file** (`.json`):
   - Complete metadata for each record
   - All fields preserved

3. **SQLite database** (`.db`):
   - Normalized tables
   - Queryable with SQL

4. **Summary report** (`_report.txt`):
   - Statistics about the harvest
   - Data type breakdown
   - Geographic coverage

## Data Fields Collected

- **Identification**: ID, source archive, URLs
- **Content**: Title, description, keywords, subjects
- **Temporal**: Dates (created, ranges, uncertainty)
- **Geographic**: Location, coordinates, spatial coverage
- **Type**: Data type, MIME type, format
- **Attribution**: Creator, contributor, publisher
- **Access**: Download URL, thumbnail, rights, license
- **Technical**: Dimensions, file size, language, script

## Known Issues & Solutions

### Issue: No images found on ArchNet
- **Cause**: ArchNet loads images dynamically with JavaScript
- **Solution**: Use their search or collection pages instead of individual site pages

### Issue: SSL Certificate errors
- **Solution**: The system now bypasses SSL verification for development

### Issue: Empty descriptions
- **Solution**: The enhanced scrapers now look in multiple locations for metadata

## Tips for Better Results

1. **Use search terms instead of direct URLs when possible**
   - Archives often have better data on search result pages

2. **Try multiple related terms**
   - "Antakya", "Antioch", "Hatay" may return different results

3. **Check collection/browse pages**
   - These often have more structured data than individual pages

4. **Combine archives**
   - Different archives have different strengths

## Adding New Archives

To add support for a new archive:

1. Create a scraper in `data_collection/scrapers/`
2. Inherit from `UniversalArchiveScraper`
3. Implement `_scrape_search()` and extraction methods
4. Register in `universal_harvester.py`

## Examples of Successful Harvests

### Manar al-Athar
- Good for: Islamic architecture, archaeological sites
- Best approach: Use search with location terms
- Example: `search "Turkey" "Syria" --archives manar`

### Generic Scraper
- Works with: Any website with images
- Best for: Unknown archives, gallery pages
- Example: `scrape "https://example.com/gallery"`

## Troubleshooting

1. **No data found**: Try a search instead of direct URL
2. **Timeout errors**: Reduce number of search terms
3. **Missing data**: Check the JSON file for raw data
4. **Database errors**: Fixed in latest version

## Next Steps

The system is designed to be extended. Future enhancements could include:
- Browser automation for JavaScript-heavy sites
- OCR for handwritten documents
- IIIF manifest parsing
- Additional archive implementations