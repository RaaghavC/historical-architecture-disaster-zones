#!/usr/bin/env python3
"""
Simple test script for scraping without database dependencies.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data_collection.universal_harvester import UniversalHarvester

def main():
    # Get URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://archnet.org/sites/1644"
    
    print(f"Scraping: {url}")
    
    # Create harvester
    harvester = UniversalHarvester(output_dir="test_harvest")
    
    # Harvest the URL
    df = harvester.harvest_url(url)
    
    if df.empty:
        print("No data found")
    else:
        print(f"\nSuccess! Found {len(df)} records")
        print("\nFirst few records:")
        print(df[['Title', 'Data_Type', 'Archive']].head())
        print(f"\nResults saved to: test_harvest/")

if __name__ == "__main__":
    main()