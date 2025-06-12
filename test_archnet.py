#!/usr/bin/env python3
"""
Test what's actually on the ArchNet page.
"""
import requests
from bs4 import BeautifulSoup
import json

url = "https://www.archnet.org/sites/1644"

# Fetch the page
response = requests.get(url, verify=False)
soup = BeautifulSoup(response.text, 'html.parser')

print(f"Page title: {soup.title.text if soup.title else 'No title'}\n")

# Find all images
images = soup.find_all('img')
print(f"Found {len(images)} images:")
for i, img in enumerate(images[:10]):
    print(f"{i+1}. src: {img.get('src', 'N/A')}")
    print(f"   alt: {img.get('alt', 'N/A')}")
    print()

# Look for specific ArchNet patterns
print("\nLooking for ArchNet-specific elements:")

# Check for different selectors
selectors = [
    '.field-name-field-images',
    '.image-gallery',
    '.node-type-site',
    'article',
    '.content',
    '.field-item',
    'figure',
    '.views-field-field-images'
]

for selector in selectors:
    elements = soup.select(selector)
    if elements:
        print(f"\nFound {len(elements)} elements with selector '{selector}'")
        
# Look for metadata fields
print("\nLooking for metadata fields:")
field_selectors = [
    '.field-label',
    '.field-name-field-location',
    '.field-name-field-date',
    '.field-name-field-architect',
    'dl dt',
    'table.views-table td'
]

for selector in field_selectors:
    elements = soup.select(selector)
    if elements:
        print(f"\nFound {len(elements)} elements with selector '{selector}':")
        for elem in elements[:5]:
            print(f"  - {elem.get_text(strip=True)}")

# Save the HTML for inspection
with open('archnet_page.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("\nSaved HTML to archnet_page.html for inspection")