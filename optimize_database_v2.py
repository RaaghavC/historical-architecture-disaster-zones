#!/usr/bin/env python3
"""
Enhanced database optimization that extracts proper image names from URLs
and fetches actual metadata from Wikimedia
"""

import pandas as pd
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse
import os
import requests
from bs4 import BeautifulSoup
import time

print("Advanced Heritage Database Optimization...\n")

# Step 1: Load existing database
print("Step 1: Loading database...")
excel_file = sorted(Path('.').glob('USABLE_DATABASE_*.xlsx'))[-1]
df = pd.read_excel(excel_file, sheet_name='All_Records')
print(f"Loaded {len(df)} records")

def extract_image_name_from_url(url):
    """Extract the actual image filename from Wikimedia URL"""
    if 'File:' in url:
        # Extract filename after File:
        match = re.search(r'File:([^/]+?)(?:\?|$)', url)
        if match:
            filename = unquote(match.group(1))
            # Clean up the filename
            filename = filename.replace('_', ' ')
            filename = re.sub(r'\.(jpg|jpeg|png|gif|tif|tiff)$', '', filename, flags=re.I)
            return filename
    return None

def is_peripheral_image(url, title):
    """Detect and filter out logos, icons, etc."""
    peripheral_patterns = [
        r'logo', r'icon', r'button', r'arrow', r'powered.?by',
        r'mediawiki', r'wikimedia.?foundation', r'commons.?logo',
        r'previous.?page', r'next.?page', r'navigation',
        r'20px', r'16px', r'32px', r'\.svg', r'favicon',
        r'wiki\.png', r'wiki\.svg', r'wikivoyage', r'wikidata'
    ]
    
    url_lower = url.lower() if url else ''
    title_lower = title.lower() if title else ''
    
    for pattern in peripheral_patterns:
        if re.search(pattern, url_lower) or re.search(pattern, title_lower):
            return True
    
    # Skip very small images (likely icons)
    if re.search(r'\b(16|20|24|32|48)px\b', url):
        return True
        
    return False

def create_meaningful_description(title, category, location=None):
    """Create a meaningful description based on available data"""
    category_descriptions = {
        'Antakya_Heritage': 'Historical heritage site from Antakya (ancient Antioch)',
        'Ottoman_Architecture': 'Ottoman architectural heritage',
        'Byzantine_Architecture': 'Byzantine architectural heritage',
        'Archaeological_Sites': 'Archaeological site and ancient remains',
        'Earthquake_Damage': 'Documentation of earthquake damage to heritage sites',
        'Mosques': 'Islamic religious architecture',
        'Churches': 'Christian religious architecture'
    }
    
    base_desc = category_descriptions.get(category, 'Historical heritage documentation')
    
    # Parse location from title if possible
    location_keywords = ['church', 'mosque', 'temple', 'palace', 'fortress', 'castle', 
                        'basilica', 'monastery', 'cathedral', 'synagogue', 'bath', 'hamam']
    
    building_type = None
    for keyword in location_keywords:
        if keyword in title.lower():
            building_type = keyword.capitalize()
            break
    
    # Extract location from title patterns
    location_match = re.search(r'in (\w+)(?: village| city| town)?', title, re.I)
    if location_match:
        location = location_match.group(1)
    
    # Build description
    parts = [base_desc]
    if building_type:
        parts.append(f"Type: {building_type}")
    if location:
        parts.append(f"Location: {location}")
    
    # Add date if found in title
    year_match = re.search(r'(1[0-9]{3}|20[0-2][0-9])', title)
    if year_match:
        parts.append(f"Date: {year_match.group(1)}")
    
    return '. '.join(parts)

def fetch_wikimedia_metadata(url, limit_requests=True):
    """Fetch actual metadata from Wikimedia page"""
    if limit_requests:
        time.sleep(0.5)  # Be respectful
    
    try:
        # Convert File: URL to actual page URL
        if 'File:' in url:
            page_url = url.replace('/wiki/File:', '/wiki/File:')
            response = requests.get(page_url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract description from page
            desc_elem = soup.find('div', class_='description')
            if desc_elem:
                return desc_elem.get_text(strip=True)
            
            # Try other common description locations
            for class_name in ['fileinfotpl-desc', 'summary', 'information']:
                elem = soup.find('td', class_=class_name)
                if elem:
                    return elem.get_text(strip=True)[:300]
    except:
        pass
    
    return None

# Process records
print("\nStep 2: Cleaning and enhancing records...")
enhanced_records = []
skipped_count = 0
processed_count = 0

for idx, row in df.iterrows():
    processed_count += 1
    if processed_count % 100 == 0:
        print(f"  Processed {processed_count}/{len(df)} records...")
    
    # Extract proper image name from URL
    image_name = extract_image_name_from_url(row['Image_URL'])
    
    # Use extracted name or clean the title
    if image_name:
        clean_title = image_name
    else:
        # Fallback to cleaning the existing title
        clean_title = row['Title']
        clean_title = re.sub(r'Category:', '', clean_title)
        clean_title = re.sub(r'- Wikimedia Commons.*$', '', clean_title)
        clean_title = clean_title.strip()
    
    # Skip peripheral images
    if is_peripheral_image(row['Image_URL'], clean_title):
        skipped_count += 1
        continue
    
    # Create meaningful description
    description = create_meaningful_description(clean_title, row['Category'])
    
    # For important items, try to fetch real metadata (limit to avoid overwhelming)
    if idx < 20 and 'File:' in row['Image_URL']:
        fetched_desc = fetch_wikimedia_metadata(row['Image_URL'])
        if fetched_desc:
            description = fetched_desc[:300] + "..."
    
    # Extract location from title
    location = ''
    location_patterns = [
        r'in (\w+)(?: village| city| town)?',
        r'(\w+) (?:church|mosque|temple|cathedral)',
        r'(?:church|mosque|temple|cathedral) of (\w+)'
    ]
    for pattern in location_patterns:
        match = re.search(pattern, clean_title, re.I)
        if match:
            location = match.group(1).capitalize()
            break
    
    enhanced_record = {
        'Title': clean_title,
        'Description': description,
        'Image_URL': row['Image_URL'],
        'Thumbnail_URL': row.get('Thumbnail_URL', row['Image_URL']),
        'Category': row['Category'],
        'Archive': 'Wikimedia Commons',
        'Location': location,
        'Date': '',
        'Creator': '',
        'Keywords': [],
        'Source_Page': row.get('Original_Page', '')
    }
    
    enhanced_records.append(enhanced_record)

print(f"\nFiltered out {skipped_count} peripheral images")
print(f"Enhanced {len(enhanced_records)} heritage records")

# Create optimized dataframe
df_optimized = pd.DataFrame(enhanced_records)

# Remove duplicates based on title similarity
df_optimized = df_optimized.drop_duplicates(subset=['Title'], keep='first')

# Sort by category and title
df_optimized = df_optimized.sort_values(['Category', 'Title'])

print(f"\nFinal optimized database: {len(df_optimized)} records")

# Save optimized database
timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
output_file = f"OPTIMIZED_DATABASE_{timestamp}.xlsx"

with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    df_optimized.to_excel(writer, sheet_name='All_Records', index=False)
    
    # Category summary
    category_summary = df_optimized['Category'].value_counts().reset_index()
    category_summary.columns = ['Category', 'Count']
    category_summary.to_excel(writer, sheet_name='Categories', index=False)
    
    # Location summary
    location_summary = df_optimized[df_optimized['Location'] != '']['Location'].value_counts().head(20).reset_index()
    location_summary.columns = ['Location', 'Count']
    location_summary.to_excel(writer, sheet_name='Top_Locations', index=False)

print(f"\n✅ Optimized database saved to: {output_file}")

# Show sample of cleaned data
print("\nSample of optimized records:")
print("="*80)
samples = df_optimized[df_optimized['Category'] == 'Antakya_Heritage'].head(5)
for idx, record in samples.iterrows():
    print(f"\nTitle: {record['Title']}")
    print(f"Description: {record['Description']}")
    print(f"Location: {record['Location'] if record['Location'] else 'Not specified'}")
    print("-"*40)