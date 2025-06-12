#!/usr/bin/env python3
"""
Find all churches in Antakya and download them.
"""
import pandas as pd
import requests
import os
from pathlib import Path
import time

print("Finding all churches in Antakya...\n")

# Read the database
excel_file = sorted(Path('.').glob('USABLE_DATABASE_*.xlsx'))[-1]
print(f"Reading: {excel_file}")

# Read all records
df = pd.read_excel(excel_file, sheet_name='All_Records')

# Find churches in Antakya
# Method 1: Churches in Antakya category
antakya_churches = df[
    (df['Category'] == 'Antakya_Heritage') & 
    (df['Title'].str.contains('church|Church|chapel|Chapel|St\.|Saint', case=False, na=False))
]

# Method 2: Any church with Antakya/Antioch in title or description
church_keywords = ['church', 'chapel', 'cathedral', 'basilica', 'st.', 'saint', 'pierre', 'peter']
antakya_keywords = ['antakya', 'antioch', 'hatay']

# Search in titles and descriptions
mask = (
    df['Title'].str.contains('|'.join(church_keywords), case=False, na=False) & 
    (df['Title'].str.contains('|'.join(antakya_keywords), case=False, na=False) |
     df['Description'].str.contains('|'.join(antakya_keywords), case=False, na=False))
)

all_antakya_churches = df[mask]

# Combine and remove duplicates
combined = pd.concat([antakya_churches, all_antakya_churches]).drop_duplicates(subset=['Image_URL'])

print(f"\nFound {len(combined)} churches related to Antakya:")
print("-" * 60)

# Display results
for idx, row in combined.iterrows():
    print(f"\n{idx+1}. {row['Title']}")
    if row['Description'] != 'No description available':
        print(f"   Description: {row['Description'][:100]}...")
    print(f"   Category: {row['Category']}")
    print(f"   URL: {row['Image_URL']}")

# Save results
output_dir = Path("antakya_churches")
output_dir.mkdir(exist_ok=True)

# Save list to CSV
combined.to_csv(output_dir / "antakya_churches_list.csv", index=False)
print(f"\n✅ Saved list to: antakya_churches/antakya_churches_list.csv")

# Download images
print(f"\nDownloading {len(combined)} church images...")

downloaded = 0
for idx, row in combined.iterrows():
    try:
        # Create filename
        safe_title = ''.join(c for c in row['Title'] if c.isalnum() or c in ' -_')[:60]
        filename = f"{idx:03d}_{safe_title.strip()}.jpg"
        filepath = output_dir / filename
        
        if filepath.exists():
            print(f"Skipping (exists): {filename}")
            continue
            
        print(f"Downloading: {filename}")
        
        # Download
        response = requests.get(row['Image_URL'], timeout=30, verify=False)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Save metadata
        with open(filepath.with_suffix('.txt'), 'w', encoding='utf-8') as f:
            f.write(f"Title: {row['Title']}\n")
            f.write(f"Description: {row['Description']}\n")
            f.write(f"Category: {row['Category']}\n")
            f.write(f"Source: {row.get('Archive', 'Unknown')}\n")
            f.write(f"URL: {row['Image_URL']}\n")
        
        downloaded += 1
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n✅ Downloaded {downloaded} church images to: antakya_churches/")