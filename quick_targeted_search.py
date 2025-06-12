#!/usr/bin/env python3
"""
Quick targeted search for high-priority Antakya content.
"""
import subprocess
import time

# High priority searches
priority_searches = [
    # St. Pierre Church
    "https://commons.wikimedia.org/wiki/Category:Saint_Pierre_Church,_Antakya",
    
    # Habib-i Neccar Mosque  
    "https://commons.wikimedia.org/wiki/Category:Habib-i_Neccar_Mosque",
    
    # Churches in Hatay
    "https://commons.wikimedia.org/wiki/Category:Churches_in_Hatay_Province",
    
    # Mosques in Hatay
    "https://commons.wikimedia.org/wiki/Category:Mosques_in_Hatay_Province",
    
    # Hatay Archaeological Museum
    "https://commons.wikimedia.org/wiki/Category:Hatay_Archaeology_Museum",
    
    # 2023 earthquake damage
    "https://commons.wikimedia.org/wiki/Category:2023_Turkey%E2%80%93Syria_earthquakes",
    
    # Archaeological sites in Hatay
    "https://commons.wikimedia.org/wiki/Category:Archaeological_sites_in_Hatay_Province",
]

print("Quick Targeted Search for Antakya Heritage\n")

total = 0
for i, url in enumerate(priority_searches, 1):
    print(f"[{i}/{len(priority_searches)}] {url.split('/')[-1][:50]}...")
    
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

print(f"\nTotal new records: {total}")