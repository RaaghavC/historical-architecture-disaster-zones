#!/usr/bin/env python3
"""
Search Library of Congress for historical photographs of Antakya/Antioch.
"""
import subprocess
import time

# Library of Congress historical searches
loc_searches = [
    # Historical periods
    "https://www.loc.gov/pictures/search/?q=antioch+1900s",
    "https://www.loc.gov/pictures/search/?q=antioch+1920s", 
    "https://www.loc.gov/pictures/search/?q=antioch+1930s",
    "https://www.loc.gov/pictures/search/?q=antioch+1940s",
    
    # Alternative spellings and names
    "https://www.loc.gov/pictures/search/?q=antakya+turkey",
    "https://www.loc.gov/pictures/search/?q=hatay+turkey",
    "https://www.loc.gov/pictures/search/?q=alexandretta",
    
    # Specific subjects
    "https://www.loc.gov/pictures/search/?q=antioch+church",
    "https://www.loc.gov/pictures/search/?q=antioch+mosque",
    "https://www.loc.gov/pictures/search/?q=antioch+bazaar",
    "https://www.loc.gov/pictures/search/?q=antioch+walls",
    
    # Archaeological and ancient
    "https://www.loc.gov/pictures/search/?q=antioch+ancient",
    "https://www.loc.gov/pictures/search/?q=antioch+ruins",
    "https://www.loc.gov/pictures/search/?q=antioch+excavation",
]

print("Library of Congress Historical Search\n")

total = 0
for i, url in enumerate(loc_searches, 1):
    query = url.split('?q=')[1].replace('+', ' ')
    print(f"[{i}/{len(loc_searches)}] Searching: {query}")
    
    cmd = ['python3', '-m', 'data_collection.cli', 'scrape', url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if "Successfully scraped" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "Successfully scraped" in line:
                    num = int(line.split()[2])
                    total += num
                    print(f"  ✓ Found {num} records")
                    break
        else:
            print("  ✗ No results")
            
    except:
        print("  ✗ Error/timeout")
    
    time.sleep(2)

print(f"\nTotal Library of Congress records: {total}")