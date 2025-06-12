#!/usr/bin/env python3
"""
Download all images from the master collection.
"""
import pandas as pd
import requests
import os
from pathlib import Path
import time
from urllib.parse import urlparse, unquote
import hashlib

print("Image Downloader for Antakya Heritage Project\n")

# Read the master Excel file
excel_files = sorted(Path('.').glob('MASTER_COLLECTION_*.xlsx'))
if not excel_files:
    print("Error: No master collection file found!")
    exit(1)

master_file = excel_files[-1]  # Most recent
print(f"Reading: {master_file}")

# Read the data
df = pd.read_excel(master_file, sheet_name='All_Records')
print(f"Found {len(df)} total records\n")

# Create download directories
base_dir = Path("downloaded_images")
base_dir.mkdir(exist_ok=True)

# Create subdirectories
categories = {
    'antakya': base_dir / "01_Antakya_Specific",
    'ottoman': base_dir / "02_Ottoman_Architecture", 
    'byzantine': base_dir / "03_Byzantine_Architecture",
    'archaeological': base_dir / "04_Archaeological_Sites",
    'other': base_dir / "05_Other_Heritage"
}

for cat_dir in categories.values():
    cat_dir.mkdir(exist_ok=True)

print("Download folders created:")
for name, path in categories.items():
    print(f"  - {path}")

# Function to categorize images
def categorize_image(row):
    title = str(row.get('Title', '')).lower()
    desc = str(row.get('Description', '')).lower()
    combined = title + ' ' + desc
    
    if any(word in combined for word in ['antakya', 'antioch', 'hatay', 'habib', 'neccar']):
        return 'antakya'
    elif any(word in combined for word in ['ottoman', 'osmanli', 'türk', 'turkish']):
        return 'ottoman'
    elif any(word in combined for word in ['byzantine', 'byzantium', 'roman']):
        return 'byzantine'
    elif any(word in combined for word in ['archaeological', 'ancient', 'ruins']):
        return 'archaeological'
    else:
        return 'other'

# Function to get filename from URL
def get_filename(url, title, index):
    # Try to get filename from URL
    parsed = urlparse(url)
    filename = os.path.basename(unquote(parsed.path))
    
    # If no good filename, create one
    if not filename or len(filename) < 5:
        # Use title to create filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        ext = '.jpg'  # Default extension
        filename = f"{index:04d}_{safe_title}{ext}"
    else:
        # Prepend index to ensure uniqueness
        filename = f"{index:04d}_{filename}"
    
    return filename

# Download images
print(f"\nStarting downloads... (this may take a while)\n")

downloaded = 0
failed = 0
skipped = 0

# Only download images (not PDFs)
image_df = df[df['Data_Type'] == 'image'].copy()
print(f"Filtering to images only: {len(image_df)} images to download\n")

# Limit downloads for testing (remove this line to download all)
# image_df = image_df.head(50)  # Comment this out to download ALL images

for idx, row in image_df.iterrows():
    url = row.get('Download_URL', '') or row.get('Thumbnail_URL', '')
    if not url:
        skipped += 1
        continue
    
    # Determine category
    category = categorize_image(row)
    save_dir = categories[category]
    
    # Get filename
    title = str(row.get('Title', f'Image_{idx}'))
    filename = get_filename(url, title, idx)
    filepath = save_dir / filename
    
    # Skip if already downloaded
    if filepath.exists():
        print(f"[{idx+1}/{len(image_df)}] Already exists: {filename}")
        skipped += 1
        continue
    
    # Download
    try:
        print(f"[{idx+1}/{len(image_df)}] Downloading: {filename}")
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        downloaded += 1
        
        # Small delay to be nice to servers
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:50]}")
        failed += 1
        
    # Progress update every 10 downloads
    if (idx + 1) % 10 == 0:
        print(f"\nProgress: {downloaded} downloaded, {failed} failed, {skipped} skipped\n")

# Final summary
print(f"\n{'='*60}")
print(f"DOWNLOAD COMPLETE!")
print(f"{'='*60}")
print(f"✅ Downloaded: {downloaded} images")
print(f"⏭️  Skipped: {skipped} (already existed)")
print(f"❌ Failed: {failed}")
print(f"\nImages saved in: {base_dir.absolute()}")

# Create index file
index_file = base_dir / "index.txt"
with open(index_file, 'w') as f:
    f.write("Antakya Heritage Image Collection\n")
    f.write("="*50 + "\n\n")
    for category, path in categories.items():
        files = list(path.glob("*"))
        f.write(f"{category.upper()}: {len(files)} files\n")
        
print(f"\nIndex created: {index_file}")

# Note about downloading all
if len(image_df) > 50:
    print("\n⚠️  NOTE: This was a limited download. To download ALL images:")
    print("    Edit download_images.py and comment out the line that limits to 50 images")