#!/usr/bin/env python3
"""
Enhanced search script to find more specific content for Antakya heritage.
"""
import subprocess
import time
from datetime import datetime

# Define targeted searches for specific monuments and collections
searches = [
    # St. Pierre Church variations
    "https://commons.wikimedia.org/wiki/Category:Saint_Pierre_Church,_Antakya",
    "https://www.loc.gov/pictures/search/?q=st+pierre+church+antioch",
    "https://www.loc.gov/pictures/search/?q=saint+peter+cave+church",
    
    # Pre-earthquake documentation
    "https://commons.wikimedia.org/wiki/Category:Churches_in_Hatay_Province",
    "https://commons.wikimedia.org/wiki/Category:Mosques_in_Hatay_Province",
    "https://commons.wikimedia.org/wiki/Category:Historic_buildings_in_Hatay_Province",
    
    # Hatay Archaeological Museum
    "https://commons.wikimedia.org/wiki/Category:Hatay_Archaeology_Museum",
    "https://www.loc.gov/pictures/search/?q=hatay+museum",
    
    # Historical photographs from Library of Congress
    "https://www.loc.gov/pictures/search/?q=antioch+photographs+1900",
    "https://www.loc.gov/pictures/search/?q=antioch+photographs+1920",
    "https://www.loc.gov/pictures/search/?q=antioch+photographs+1930",
    "https://www.loc.gov/pictures/search/?q=hatay+photographs",
    
    # More Wikimedia categories
    "https://commons.wikimedia.org/wiki/Category:Ancient_Roman_sites_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Byzantine_sites_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Seljuk_architecture_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Armenian_churches_in_Turkey",
    
    # Specific monuments
    "https://commons.wikimedia.org/wiki/Category:Habib-i_Neccar_Mosque",
    "https://commons.wikimedia.org/wiki/Category:Greek_Orthodox_Church_of_Antioch",
    "https://www.loc.gov/pictures/search/?q=habib+neccar+mosque",
    
    # Earthquake documentation
    "https://commons.wikimedia.org/wiki/Category:2023_Turkey%E2%80%93Syria_earthquakes",
    "https://commons.wikimedia.org/wiki/Category:Earthquake_damage_in_Turkey",
    
    # Turkish heritage sites
    "https://commons.wikimedia.org/wiki/Category:World_Heritage_Sites_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:National_parks_of_Turkey",
    
    # Ancient cities
    "https://commons.wikimedia.org/wiki/Category:Ancient_cities_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Archaeological_sites_in_Hatay_Province",
    
    # Historical maps and plans
    "https://www.loc.gov/pictures/search/?q=antioch+map",
    "https://www.loc.gov/pictures/search/?q=syria+map+ancient",
    
    # French mandate period
    "https://www.loc.gov/pictures/search/?q=french+mandate+syria",
    "https://commons.wikimedia.org/wiki/Category:French_Mandate_for_Syria_and_the_Lebanon",
]

print(f"Enhanced Heritage Search - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)
print(f"Searching {len(searches)} specific collections for Antakya heritage...")
print("="*60 + "\n")

total = 0
successful = 0

for i, url in enumerate(searches, 1):
    print(f"\n[{i}/{len(searches)}] Searching: {url}")
    
    cmd = ['python3', '-m', 'data_collection.cli', 'scrape', url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        
        # Extract number of records from output
        if "Successfully scraped" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "Successfully scraped" in line:
                    num = int(line.split()[2])
                    total += num
                    successful += 1
                    print(f"✓ Found {num} records (Total so far: {total})")
                    break
        else:
            print("✗ No data found")
            if result.stderr:
                print(f"  Error: {result.stderr[:100]}")
            
    except subprocess.TimeoutExpired:
        print("✗ Timeout - skipping")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Small delay between requests
    time.sleep(2)

print(f"\n{'='*60}")
print(f"ENHANCED SEARCH COMPLETE!")
print(f"{'='*60}")
print(f"✅ Successful searches: {successful}/{len(searches)}")
print(f"📊 Total new records collected: {total}")
print(f"{'='*60}")

# Suggest next steps
print("\nNext steps:")
print("1. Run combine_excel_files.py again to create new master collection")
print("2. Run download_images.py to download new images")
print("3. Check SALT Research and NIT Istanbul archives manually")