#!/usr/bin/env python3
"""
Download images with proper names and organization based on the fixed database.
"""
import pandas as pd
import requests
import os
from pathlib import Path
import time
from urllib.parse import urlparse, unquote
import re

print("Real Image Downloader for Antakya Heritage Project\n")

# Read the image catalog
catalog_files = sorted(Path('.').glob('IMAGE_CATALOG_*.csv'))
if not catalog_files:
    print("Error: No image catalog found! Run fix_database.py first.")
    exit(1)

catalog_file = catalog_files[-1]  # Most recent
print(f"Reading: {catalog_file}")

# Read the catalog
df = pd.read_csv(catalog_file)
downloadable = df[df['Can_Download'] == 'Yes']
print(f"Found {len(downloadable)} downloadable images\n")

# Create organized directories
base_dir = Path("organized_images")
base_dir.mkdir(exist_ok=True)

# Create category directories
categories = downloadable['Category'].unique()
cat_dirs = {}
for category in categories:
    cat_dir = base_dir / category
    cat_dir.mkdir(exist_ok=True)
    cat_dirs[category] = cat_dir

print("Created directories:")
for cat in sorted(categories):
    count = len(downloadable[downloadable['Category'] == cat])
    print(f"  - {cat}: {count} images")

# Download function with better error handling
def download_image(url, filepath):
    """Download image with proper headers and error handling."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Handle Wikimedia Commons URLs
        if 'commons.wikimedia.org' in url and '/thumb/' in url:
            # Try to get the full resolution version
            url = url.split('/thumb/')[0] + url.split('/thumb/')[1].rsplit('/', 1)[0]
        
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith(('image/', 'application/octet-stream')):
            return False, f"Not an image: {content_type}"
        
        # Save the file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Check file size
        size = os.path.getsize(filepath)
        if size < 1000:  # Less than 1KB
            os.remove(filepath)
            return False, "File too small"
        
        return True, "Success"
        
    except Exception as e:
        return False, str(e)[:100]

# Download images
print(f"\nStarting downloads...\n")

downloaded = 0
failed = 0
skipped = 0

# Process each category
for category in sorted(categories):
    cat_df = downloadable[downloadable['Category'] == category]
    print(f"\n--- {category} ({len(cat_df)} images) ---")
    
    for idx, row in cat_df.iterrows():
        # Create proper filename
        safe_title = re.sub(r'[^\w\s-]', '', row['Title'])[:60].strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        
        # Add ID to ensure uniqueness
        filename = f"{row['ID']:04d}_{safe_title}.jpg"
        filepath = cat_dirs[category] / filename
        
        # Skip if already exists
        if filepath.exists():
            print(f"[{idx+1}/{len(df)}] Exists: {filename}")
            skipped += 1
            continue
        
        # Download
        print(f"[{idx+1}/{len(df)}] Downloading: {filename}")
        success, message = download_image(row['Image_URL'], filepath)
        
        if success:
            downloaded += 1
            # Create info file
            info_file = filepath.with_suffix('.txt')
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"Title: {row['Title']}\n")
                f.write(f"Description: {row['Description']}\n")
                f.write(f"Category: {row['Category']}\n")
                f.write(f"Location: {row['Location']}\n")
                f.write(f"Date: {row['Date']}\n")
                f.write(f"Source URL: {row['Image_URL']}\n")
        else:
            print(f"  ❌ Failed: {message}")
            failed += 1
        
        # Small delay
        time.sleep(0.5)
        
        # Progress update
        if downloaded % 10 == 0 and downloaded > 0:
            print(f"\nProgress: {downloaded} downloaded, {failed} failed, {skipped} skipped\n")

# Create index HTML
print("\nCreating visual index...")

index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Antakya Heritage Image Collection</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #2c3e50; }
        .category { margin-bottom: 40px; background: white; padding: 20px; border-radius: 8px; }
        .category h2 { color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .image-item { text-align: center; }
        .image-item img { width: 100%; height: 150px; object-fit: cover; border: 1px solid #ddd; }
        .image-item p { margin: 5px 0; font-size: 12px; }
        .stats { background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Antakya Heritage Image Collection</h1>
    <div class="stats">
        <p>Total Images: """ + str(downloaded) + """</p>
        <p>Categories: """ + str(len(categories)) + """</p>
    </div>
"""

for category in sorted(categories):
    cat_dir = cat_dirs[category]
    images = list(cat_dir.glob("*.jpg"))[:20]  # Show first 20
    
    if images:
        index_html += f'\n<div class="category">\n<h2>{category.replace("_", " ")}</h2>\n'
        index_html += '<div class="image-grid">\n'
        
        for img in images:
            rel_path = img.relative_to(base_dir)
            index_html += f'''
            <div class="image-item">
                <img src="{rel_path}" alt="{img.stem}">
                <p>{img.stem[:30]}...</p>
            </div>
            '''
        
        index_html += '\n</div>\n</div>\n'

index_html += """
</body>
</html>
"""

index_file = base_dir / "index.html"
with open(index_file, 'w') as f:
    f.write(index_html)

# Summary
print(f"\n{'='*60}")
print(f"DOWNLOAD COMPLETE!")
print(f"{'='*60}")
print(f"✅ Downloaded: {downloaded} images")
print(f"⏭️  Skipped: {skipped} (already existed)")
print(f"❌ Failed: {failed}")
print(f"\nImages saved in: {base_dir.absolute()}")
print(f"Visual index: {index_file}")
print(f"\nEach image has a companion .txt file with metadata")
print(f"\nCategories:")
for cat in sorted(categories):
    count = len(list(cat_dirs[cat].glob("*.jpg")))
    print(f"  - {cat}: {count} images")