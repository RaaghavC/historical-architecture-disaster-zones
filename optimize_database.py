#!/usr/bin/env python3
"""
Optimize the heritage database by:
1. Cleaning titles and descriptions
2. Filtering out peripheral images
3. Extracting proper metadata from source files
"""

import pandas as pd
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse
import os

print("Optimizing heritage database...\n")

# Step 1: Load existing database and JSON source files
print("Step 1: Loading data sources...")
excel_file = sorted(Path('.').glob('USABLE_DATABASE_*.xlsx'))[-1]
df_existing = pd.read_excel(excel_file, sheet_name='All_Records')
print(f"Loaded {len(df_existing)} existing records")

# Load all JSON files to get proper metadata
all_metadata = []
harvested_dir = Path("harvested_data")

for json_file in harvested_dir.glob("**/*.json"):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_metadata.extend(data)
            elif isinstance(data, dict) and 'records' in data:
                all_metadata.extend(data['records'])
    except:
        pass

print(f"Loaded {len(all_metadata)} metadata records")

# Step 2: Create mapping of URLs to proper metadata
url_to_metadata = {}
for record in all_metadata:
    urls = [
        record.get('download_url'),
        record.get('url'),
        record.get('image_url'),
        record.get('source_url')
    ]
    for url in urls:
        if url:
            url_to_metadata[url] = record

# Step 3: Clean and enhance records
print("\nStep 2: Cleaning and enhancing records...")

def clean_title(title, metadata=None):
    """Extract clean title from messy text"""
    if metadata and metadata.get('title'):
        return metadata['title']
    
    # Remove common website clutter
    title = re.sub(r'- Wikimedia Commons.*$', '', title)
    title = re.sub(r'Category:', '', title)
    title = re.sub(r'File:', '', title)
    title = re.sub(r'\.jpg|\.png|\.tif.*$', '', title, flags=re.I)
    title = re.sub(r'Library of Congress.*$', '', title)
    title = re.sub(r'Prints & Photographs.*$', '', title)
    title = re.sub(r'Search Results:.*$', '', title)
    title = re.sub(r'Powered by.*$', '', title)
    title = re.sub(r'^\d+_', '', title)  # Remove number prefixes
    
    # Clean up underscores and extra spaces
    title = title.replace('_', ' ')
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Extract filename if it looks like a proper title
    if '/' in title:
        filename = title.split('/')[-1]
        if len(filename) > 10:
            title = filename
    
    return title if title and len(title) > 5 else None

def extract_description(metadata):
    """Extract meaningful description from metadata"""
    desc_fields = ['description', 'content', 'subject', 'caption', 'notes']
    for field in desc_fields:
        if metadata.get(field):
            desc = str(metadata[field])
            if len(desc) > 20 and desc != "No description available":
                return desc[:500]
    
    # Try to build description from other fields
    parts = []
    if metadata.get('location'):
        parts.append(f"Location: {metadata['location']}")
    if metadata.get('date'):
        parts.append(f"Date: {metadata['date']}")
    if metadata.get('creator'):
        parts.append(f"Creator: {metadata['creator']}")
    
    return '. '.join(parts) if parts else "Historical heritage image from archive"

def is_peripheral_image(title, url):
    """Detect logos, icons, and other non-heritage images"""
    # Check URL patterns
    peripheral_patterns = [
        r'logo', r'icon', r'button', r'arrow', r'powered.?by',
        r'mediawiki', r'wikimedia.?foundation', r'commons.?logo',
        r'previous.?page', r'next.?page', r'navigation',
        r'20px', r'16px', r'32px', r'\.svg', r'favicon'
    ]
    
    url_lower = url.lower() if url else ''
    title_lower = title.lower() if title else ''
    
    for pattern in peripheral_patterns:
        if re.search(pattern, url_lower) or re.search(pattern, title_lower):
            return True
    
    # Check if it's too small (likely an icon)
    if re.search(r'\b(16|20|24|32|48)px\b', url):
        return True
        
    return False

# Process records
enhanced_records = []
skipped_count = 0

for idx, row in df_existing.iterrows():
    # Get metadata if available
    metadata = url_to_metadata.get(row['Image_URL'], {})
    
    # Clean title
    clean_title_text = clean_title(row['Title'], metadata)
    if not clean_title_text:
        clean_title_text = f"Heritage Image {idx + 1}"
    
    # Skip peripheral images
    if is_peripheral_image(clean_title_text, row['Image_URL']):
        skipped_count += 1
        continue
    
    # Extract proper description
    description = extract_description(metadata) if metadata else row['Description']
    if description == "No description available":
        description = f"{clean_title_text} - {row['Category'].replace('_', ' ')}"
    
    # Create enhanced record
    enhanced_record = {
        'Title': clean_title_text,
        'Description': description,
        'Image_URL': row['Image_URL'],
        'Thumbnail_URL': row.get('Thumbnail_URL', row['Image_URL']),
        'Category': row['Category'],
        'Archive': row.get('Archive', 'Heritage Archive'),
        'Location': metadata.get('location', '') if metadata else '',
        'Date': metadata.get('date', '') if metadata else '',
        'Creator': metadata.get('creator', '') if metadata else '',
        'Keywords': metadata.get('keywords', []) if metadata else [],
        'Original_Page': row.get('Original_Page', '')
    }
    
    enhanced_records.append(enhanced_record)

print(f"\nFiltered out {skipped_count} peripheral images")
print(f"Enhanced {len(enhanced_records)} heritage records")

# Step 4: Create optimized dataframe
df_optimized = pd.DataFrame(enhanced_records)

# Remove any remaining duplicates
df_optimized = df_optimized.drop_duplicates(subset=['Image_URL'], keep='first')

# Sort by category and title
df_optimized = df_optimized.sort_values(['Category', 'Title'])

print(f"\nFinal optimized database: {len(df_optimized)} records")

# Step 5: Save optimized database
timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
output_file = f"OPTIMIZED_DATABASE_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    # All records
    df_optimized.to_excel(writer, sheet_name='All_Records', index=False)
    
    # Category summary
    category_summary = df_optimized['Category'].value_counts().reset_index()
    category_summary.columns = ['Category', 'Count']
    category_summary.to_excel(writer, sheet_name='Categories', index=False)
    
    # Add formatting
    workbook = writer.book
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D7E4BD',
        'border': 1
    })
    
    for sheet_name in writer.sheets:
        worksheet = writer.sheets[sheet_name]
        worksheet.set_column('A:A', 50)  # Title
        worksheet.set_column('B:B', 80)  # Description
        worksheet.set_column('C:D', 30)  # URLs

print(f"\n✅ Optimized database saved to: {output_file}")

# Show sample of cleaned data
print("\nSample of cleaned records:")
print("="*80)
for i in range(min(3, len(df_optimized))):
    record = df_optimized.iloc[i]
    print(f"\nTitle: {record['Title']}")
    print(f"Description: {record['Description'][:150]}...")
    print(f"Category: {record['Category']}")
    print("-"*80)