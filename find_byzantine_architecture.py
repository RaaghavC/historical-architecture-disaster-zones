#!/usr/bin/env python3
"""
Find and download all Byzantine architecture images.
"""
import pandas as pd
import requests
import os
from pathlib import Path
import time

print("Finding all Byzantine architecture...\n")

# Read the database
excel_file = sorted(Path('.').glob('USABLE_DATABASE_*.xlsx'))[-1]
print(f"Reading: {excel_file}")

# Read all records
df = pd.read_excel(excel_file, sheet_name='All_Records')

# Method 1: Byzantine category
byzantine_cat = df[df['Category'] == 'Byzantine_Roman']

# Method 2: Byzantine keywords in title/description
byzantine_keywords = ['byzantine', 'byzantium', 'constantinople', 'hagia', 'orthodox', 'basilica', 'justinian', 'theodora', 'roman empire', 'eastern roman']

mask = (
    df['Title'].str.contains('|'.join(byzantine_keywords), case=False, na=False) |
    df['Description'].str.contains('|'.join(byzantine_keywords), case=False, na=False)
)

byzantine_keyword = df[mask]

# Combine and remove duplicates
combined = pd.concat([byzantine_cat, byzantine_keyword]).drop_duplicates(subset=['Image_URL'])

print(f"Found {len(combined)} Byzantine architecture records:")
print("-" * 60)

# Group by subcategories
churches = combined[combined['Title'].str.contains('church|Church|cathedral|Cathedral|basilica|Basilica', case=False, na=False)]
fortifications = combined[combined['Title'].str.contains('wall|Wall|fort|Fort|castle|Castle|tower|Tower', case=False, na=False)]
mosaics = combined[combined['Title'].str.contains('mosaic|Mosaic|fresco|Fresco', case=False, na=False)]
other = combined[~combined.index.isin(churches.index) & ~combined.index.isin(fortifications.index) & ~combined.index.isin(mosaics.index)]

print(f"\nByCategories:")
print(f"- Churches/Basilicas: {len(churches)}")
print(f"- Fortifications: {len(fortifications)}")
print(f"- Mosaics/Frescoes: {len(mosaics)}")
print(f"- Other: {len(other)}")

# Create organized directories
base_dir = Path("byzantine_architecture")
base_dir.mkdir(exist_ok=True)

subdirs = {
    'churches': base_dir / "01_Churches_Basilicas",
    'fortifications': base_dir / "02_Fortifications",
    'mosaics': base_dir / "03_Mosaics_Frescoes",
    'other': base_dir / "04_Other"
}

for subdir in subdirs.values():
    subdir.mkdir(exist_ok=True)

# Save complete list
combined.to_csv(base_dir / "byzantine_complete_list.csv", index=False)
print(f"\n✅ Saved complete list to: byzantine_architecture/byzantine_complete_list.csv")

# Create HTML gallery
html = """<!DOCTYPE html>
<html>
<head>
    <title>Byzantine Architecture Collection</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #8B4513; text-align: center; }
        h2 { color: #D2691E; border-bottom: 2px solid #D2691E; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .item { background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .item img { width: 100%; height: 200px; object-fit: cover; }
        .item h3 { font-size: 14px; margin: 10px 0 5px 0; }
        .item p { font-size: 12px; color: #666; margin: 0; }
        .stats { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Byzantine Architecture Collection</h1>
    <div class="stats">
        <h2>Collection Statistics</h2>
        <p>Total Records: """ + str(len(combined)) + """</p>
        <p>Churches & Basilicas: """ + str(len(churches)) + """</p>
        <p>Fortifications: """ + str(len(fortifications)) + """</p>
        <p>Mosaics & Frescoes: """ + str(len(mosaics)) + """</p>
    </div>
"""

# Add galleries for each category
categories = [
    ("Churches & Basilicas", churches, subdirs['churches']),
    ("Fortifications", fortifications, subdirs['fortifications']),
    ("Mosaics & Frescoes", mosaics, subdirs['mosaics']),
    ("Other Byzantine", other, subdirs['other'])
]

print("\nDownloading images by category...")

for cat_name, cat_df, cat_dir in categories:
    if len(cat_df) == 0:
        continue
        
    print(f"\n--- {cat_name} ({len(cat_df)} items) ---")
    
    html += f'\n<h2>{cat_name}</h2>\n<div class="gallery">\n'
    
    downloaded = 0
    for idx, row in cat_df.head(30).iterrows():  # Limit to 30 per category for demo
        try:
            # Create filename
            safe_title = ''.join(c for c in row['Title'] if c.isalnum() or c in ' -_')[:50]
            filename = f"{downloaded:03d}_{safe_title.strip()}.jpg"
            filepath = cat_dir / filename
            
            if not filepath.exists():
                print(f"  Downloading: {filename}")
                response = requests.get(row['Image_URL'], timeout=30, verify=False)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Save metadata
                with open(filepath.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                    f.write(f"Title: {row['Title']}\n")
                    f.write(f"Description: {row['Description']}\n")
                    f.write(f"URL: {row['Image_URL']}\n")
                
                time.sleep(0.5)
            
            # Add to HTML
            rel_path = filepath.relative_to(base_dir)
            html += f'''
            <div class="item">
                <img src="{rel_path}" alt="{row['Title']}">
                <h3>{row['Title'][:50]}...</h3>
                <p>{row['Description'][:80]}...</p>
            </div>
            '''
            
            downloaded += 1
            
        except Exception as e:
            print(f"    Error: {e}")
    
    html += '\n</div>\n'
    print(f"  Downloaded: {downloaded}")

html += """
</body>
</html>
"""

# Save HTML
with open(base_dir / "byzantine_gallery.html", 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ Created visual gallery: byzantine_architecture/byzantine_gallery.html")
print(f"\nYou can now:")
print(f"1. Browse the visual gallery by opening byzantine_gallery.html")
print(f"2. View organized folders in byzantine_architecture/")
print(f"3. Check the complete list in byzantine_complete_list.csv")