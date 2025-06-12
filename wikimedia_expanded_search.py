#!/usr/bin/env python3
"""
Expanded Wikimedia Commons search for Turkish heritage.
"""
import subprocess
import time

# Expanded Wikimedia searches
wikimedia_searches = [
    # Turkish heritage categories
    "https://commons.wikimedia.org/wiki/Category:Caravanserais_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Madrasas_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Hammams_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Bridges_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Castles_in_Turkey",
    
    # Religious architecture
    "https://commons.wikimedia.org/wiki/Category:Orthodox_churches_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Catholic_churches_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Synagogues_in_Turkey",
    
    # Historical periods
    "https://commons.wikimedia.org/wiki/Category:Roman_sites_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Crusader_castles",
    "https://commons.wikimedia.org/wiki/Category:Mamluk_architecture",
    
    # Museums and collections
    "https://commons.wikimedia.org/wiki/Category:Museums_in_Turkey",
    "https://commons.wikimedia.org/wiki/Category:Archaeological_museums_in_Turkey",
    
    # Specific regions near Antakya
    "https://commons.wikimedia.org/wiki/Category:Buildings_in_Adana_Province",
    "https://commons.wikimedia.org/wiki/Category:Buildings_in_Gaziantep_Province",
    "https://commons.wikimedia.org/wiki/Category:Buildings_in_Kilis_Province",
]

print("Expanded Wikimedia Commons Search\n")

total = 0
for i, url in enumerate(wikimedia_searches, 1):
    category = url.split('Category:')[1]
    print(f"[{i}/{len(wikimedia_searches)}] {category[:40]}...")
    
    cmd = ['python3', '-m', 'data_collection.cli', 'scrape', url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if "Successfully scraped" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "Successfully scraped" in line:
                    num = int(line.split()[2])
                    total += num
                    print(f"  ✓ {num} records")
                    break
        else:
            print("  ✗ No data")
            
    except:
        print("  ✗ Error")
    
    time.sleep(1)

print(f"\nTotal Wikimedia records: {total}")