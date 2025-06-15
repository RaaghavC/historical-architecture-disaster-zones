"""
Test the new archive scrapers
"""

import logging
from data_collection.scrapers.salt_scraper import SALTResearchScraper, search_ottoman_antakya_salt
from data_collection.scrapers.akkasah_scraper import AkkasahScraper
from data_collection.scrapers.nit_scraper import NITKielScraper, search_all_ottoman_archives

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_salt_research():
    """Test SALT Research scraper"""
    print("\n" + "="*60)
    print("Testing SALT Research Archive")
    print("="*60)
    
    scraper = SALTResearchScraper()
    
    # Test search
    records = scraper.scrape(search_terms=["Antakya mosque"], max_pages=1)
    
    print(f"\nFound {len(records)} records")
    for i, record in enumerate(records[:3]):
        print(f"\n{i+1}. {record.title}")
        print(f"   Type: {record.data_type.value}")
        print(f"   Source: {record.source_url}")
        if record.description:
            print(f"   Description: {record.description[:100]}...")

def test_akkasah():
    """Test Akkasah scraper"""
    print("\n" + "="*60)
    print("Testing Akkasah Photography Archive")
    print("="*60)
    
    scraper = AkkasahScraper()
    
    # Test - will likely return offline message
    records = scraper.scrape(search_terms=["Syria architecture"], max_pages=1)
    
    print(f"\nFound {len(records)} records")
    for record in records:
        print(f"\n- {record.title}")
        print(f"  {record.description[:200]}..." if len(record.description) > 200 else f"  {record.description}")

def test_nit_kiel():
    """Test NIT Kiel Archive scraper"""
    print("\n" + "="*60)
    print("Testing NIT Machiel Kiel Archive")
    print("="*60)
    
    scraper = NITKielScraper()
    
    # Test
    records = scraper.scrape(search_terms=["Antakya Ottoman"])
    
    print(f"\nFound {len(records)} records")
    for record in records:
        print(f"\n- {record.title}")
        if record.description:
            print(f"  {record.description[:150]}...")

def test_combined_search():
    """Test searching across all Ottoman archives"""
    print("\n" + "="*60)
    print("Testing Combined Ottoman Archive Search for Antakya")
    print("="*60)
    
    records = search_all_ottoman_archives("Antakya")
    
    print(f"\nTotal unique records found: {len(records)}")
    
    # Group by archive
    by_archive = {}
    for record in records:
        archive = record.source_archive
        if archive not in by_archive:
            by_archive[archive] = []
        by_archive[archive].append(record)
    
    for archive, archive_records in by_archive.items():
        print(f"\n{archive}: {len(archive_records)} records")
        for record in archive_records[:2]:
            print(f"  - {record.title}")

if __name__ == "__main__":
    # Test each scraper
    test_salt_research()
    test_akkasah()
    test_nit_kiel()
    test_combined_search()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)