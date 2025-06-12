#!/usr/bin/env python3
"""
Comprehensive test and example of the scraping system.
"""
import sys
from data_collection.universal_harvester import UniversalHarvester

def test_archnet():
    """Test ArchNet scraping."""
    print("=== Testing ArchNet ===")
    harvester = UniversalHarvester(output_dir="test_results")
    
    # Test direct URL scraping
    urls = [
        "https://www.archnet.org/collections/1013",  # Collection page
        "https://www.archnet.org/search?search_api_fulltext=mosque",  # Search results
    ]
    
    for url in urls:
        print(f"\nScraping: {url}")
        df = harvester.harvest_url(url)
        if not df.empty:
            print(f"Found {len(df)} records")
            print(df[['Title', 'Data_Type', 'Description']].head())
        else:
            print("No data found")

def test_manar():
    """Test Manar al-Athar."""
    print("\n=== Testing Manar al-Athar ===")
    harvester = UniversalHarvester(output_dir="test_results")
    
    # Test search
    search_terms = ["Syria", "Damascus", "mosque"]
    print(f"Searching for: {search_terms}")
    df = harvester.harvest_search(search_terms, archives=['manar'])
    
    if not df.empty:
        print(f"Found {len(df)} records")
        print("\nSample records:")
        print(df[['Title', 'Location', 'Date']].head(10))
    else:
        print("No data found")

def test_generic():
    """Test generic scraper on various sites."""
    print("\n=== Testing Generic Scraper ===")
    harvester = UniversalHarvester(output_dir="test_results")
    
    test_urls = [
        "https://www.loc.gov/pictures/search/?q=antioch",
        "https://www.metmuseum.org/art/collection/search/446063",
    ]
    
    for url in test_urls:
        print(f"\nScraping: {url}")
        df = harvester.harvest_url(url)
        if not df.empty:
            print(f"Found {len(df)} records")
            print(f"Types: {df['Data_Type'].value_counts().to_dict()}")

def main():
    """Run all tests."""
    print("Universal Scraping System - Comprehensive Test\n")
    
    # Run tests
    test_archnet()
    test_manar()
    test_generic()
    
    print("\n=== Test Complete ===")
    print("Check 'test_results/' directory for output files")

if __name__ == "__main__":
    main()