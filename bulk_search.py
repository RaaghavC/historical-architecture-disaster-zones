#!/usr/bin/env python3
"""
Bulk search script to collect hundreds of records.
"""
import subprocess
import time

# Define search URLs
searches = [
    # Wikimedia Commons - various categories
    "https://commons.wikimedia.org/wiki/Category:Ottoman_architecture",
    "https://commons.wikimedia.org/wiki/Category:Byzantine_architecture",
    "https://commons.wikimedia.org/wiki/Category:Archaeological_sites_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Ruins_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Earthquakes_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Historic_sites_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Cultural_heritage_of_Turkey",
    
    # Library of Congress - broader searches
    "https://www.loc.gov/pictures/search/?q=turkey+mosque",
    "https://www.loc.gov/pictures/search/?q=byzantine+church",
    "https://www.loc.gov/pictures/search/?q=ottoman+empire",
    "https://www.loc.gov/pictures/search/?q=archaeological+turkey",
    "https://www.loc.gov/pictures/search/?q=ruins+ancient",
    "https://www.loc.gov/pictures/search/?q=middle+east+architecture",
    "https://www.loc.gov/pictures/search/?q=syria+historic",
    
    # Specific monument searches
    "https://commons.wikimedia.org/wiki/Category:Antioch",
    "https://www.loc.gov/pictures/search/?q=antioch+ancient",
    "https://www.loc.gov/pictures/search/?q=orontes+river",
]

print("Starting bulk search for hundreds of records...\n")

total = 0
for i, url in enumerate(searches, 1):
    print(f"\n[{i}/{len(searches)}] Searching: {url}")
    
    cmd = ['python3', '-m', 'data_collection.cli', 'scrape', url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Extract number of records from output
        if "Successfully scraped" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "Successfully scraped" in line:
                    num = int(line.split()[2])
                    total += num
                    print(f"✓ Found {num} records (Total so far: {total})")
                    break
        else:
            print("✗ No data found")
            
    except subprocess.TimeoutExpired:
        print("✗ Timeout - skipping")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Small delay between requests
    time.sleep(2)

print(f"\n{'='*50}")
print(f"TOTAL RECORDS COLLECTED: {total}")
print(f"{'='*50}")