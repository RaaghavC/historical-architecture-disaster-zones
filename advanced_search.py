#!/usr/bin/env python3
"""
Advanced search tool for the heritage database.
"""
import pandas as pd
from pathlib import Path
import sys

def search_database(keywords, category=None, exclude=None):
    """Search the database with multiple criteria."""
    
    # Read the database
    excel_file = sorted(Path('.').glob('USABLE_DATABASE_*.xlsx'))[-1]
    df = pd.read_excel(excel_file, sheet_name='All_Records')
    
    # Convert keywords to list
    if isinstance(keywords, str):
        keywords = [keywords]
    
    # Search in title and description
    mask = df['Title'].str.contains('|'.join(keywords), case=False, na=False) | \
           df['Description'].str.contains('|'.join(keywords), case=False, na=False)
    
    results = df[mask]
    
    # Filter by category if specified
    if category:
        results = results[results['Category'] == category]
    
    # Exclude keywords if specified
    if exclude:
        if isinstance(exclude, str):
            exclude = [exclude]
        exclude_mask = ~(results['Title'].str.contains('|'.join(exclude), case=False, na=False) | \
                         results['Description'].str.contains('|'.join(exclude), case=False, na=False))
        results = results[exclude_mask]
    
    return results

# Example searches
print("ADVANCED HERITAGE DATABASE SEARCH\n")
print("=" * 60)

# 1. Find St. Pierre Church specifically
print("\n1. SEARCHING FOR: St. Pierre/Peter Church in Antakya")
st_pierre = search_database(['pierre', 'peter', 'petrus'], category='Antakya_Heritage')
print(f"Found {len(st_pierre)} results:")
for idx, row in st_pierre.iterrows():
    if 'pierre' in row['Title'].lower() or 'peter' in row['Title'].lower():
        print(f"  - {row['Title']}")

# 2. Find Habib-i Neccar Mosque
print("\n2. SEARCHING FOR: Habib-i Neccar Mosque")
habib = search_database(['habib', 'neccar', 'habibi'])
print(f"Found {len(habib)} results:")
for idx, row in habib.iterrows():
    print(f"  - {row['Title']}")

# 3. Find earthquake damage documentation
print("\n3. SEARCHING FOR: 2023 Earthquake damage")
earthquake = search_database(['earthquake', '2023', 'damage', 'destruction'], 
                           category='Earthquake_Documentation')
print(f"Found {len(earthquake)} results:")
for idx, row in earthquake.head(5).iterrows():
    print(f"  - {row['Title']}")

# 4. Find Ottoman mosques (not in Antakya)
print("\n4. SEARCHING FOR: Ottoman mosques outside Antakya")
ottoman_mosques = search_database(['mosque', 'cami', 'minaret'], 
                                category='Ottoman_Islamic',
                                exclude=['antakya', 'antioch'])
print(f"Found {len(ottoman_mosques)} results:")
for idx, row in ottoman_mosques.iterrows():
    print(f"  - {row['Title']}")

# 5. Find ancient Roman sites
print("\n5. SEARCHING FOR: Ancient Roman sites in Turkey")
roman = search_database(['roman', 'rome', 'imperial', 'augustus', 'trajan'],
                       category='Archaeological_Sites')
print(f"Found {len(roman)} results:")
for idx, row in roman.head(5).iterrows():
    print(f"  - {row['Title']}")

# Interactive search
print("\n" + "=" * 60)
print("INTERACTIVE SEARCH")
print("=" * 60)

if len(sys.argv) > 1:
    # Use command line arguments
    search_terms = sys.argv[1:]
    print(f"\nSearching for: {' '.join(search_terms)}")
    results = search_database(search_terms)
else:
    # Prompt for input
    search_input = input("\nEnter search terms (or press Enter to skip): ")
    if search_input:
        results = search_database(search_input.split())
    else:
        results = pd.DataFrame()

if len(results) > 0:
    print(f"\nFound {len(results)} results:")
    print("-" * 60)
    
    # Group by category
    for category in results['Category'].unique():
        cat_results = results[results['Category'] == category]
        print(f"\n{category} ({len(cat_results)} results):")
        for idx, row in cat_results.head(10).iterrows():
            print(f"\n  Title: {row['Title']}")
            if row['Description'] != 'No description available':
                print(f"  Desc: {row['Description'][:100]}...")
            print(f"  URL: {row['Image_URL']}")
    
    # Save results
    output_file = "search_results.csv"
    results.to_csv(output_file, index=False)
    print(f"\n✅ Saved {len(results)} results to: {output_file}")
else:
    print("\nNo results found.")

# Show available categories
print("\n" + "=" * 60)
print("AVAILABLE CATEGORIES:")
excel_file = sorted(Path('.').glob('USABLE_DATABASE_*.xlsx'))[-1]
df = pd.read_excel(excel_file, sheet_name='All_Records')
for cat, count in df['Category'].value_counts().items():
    print(f"  - {cat}: {count} records")