#!/usr/bin/env python3
"""
Combine all Excel files from harvested_data into one master file.
"""
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

print("Combining all Excel files into master spreadsheet...\n")

# Find all Excel files
harvested_dir = Path("harvested_data")
excel_files = list(harvested_dir.glob("**/*.xlsx"))

print(f"Found {len(excel_files)} Excel files to combine\n")

# Read and combine all files
all_dataframes = []
file_sources = []

for i, excel_file in enumerate(excel_files, 1):
    print(f"Reading {i}/{len(excel_files)}: {excel_file.name}")
    try:
        df = pd.read_excel(excel_file)
        # Add source file column
        df['Source_File'] = excel_file.parent.name
        all_dataframes.append(df)
        file_sources.append({
            'File': excel_file.name,
            'Records': len(df),
            'Folder': excel_file.parent.name
        })
    except Exception as e:
        print(f"  Error reading {excel_file}: {e}")

# Combine all dataframes
print("\nCombining all data...")
master_df = pd.concat(all_dataframes, ignore_index=True)

# Remove duplicates based on URL
print(f"\nTotal records before removing duplicates: {len(master_df)}")
master_df = master_df.drop_duplicates(subset=['Download_URL'], keep='first')
print(f"Total records after removing duplicates: {len(master_df)}")

# Sort by Archive and Title
master_df = master_df.sort_values(['Archive', 'Title'])

# Create master Excel file with multiple sheets
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"MASTER_COLLECTION_{timestamp}.xlsx"

print(f"\nCreating master file: {output_file}")

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Main sheet with all data
    master_df.to_excel(writer, sheet_name='All_Records', index=False)
    
    # Summary by archive
    summary = master_df['Archive'].value_counts().reset_index()
    summary.columns = ['Archive', 'Count']
    summary.to_excel(writer, sheet_name='Summary_by_Archive', index=False)
    
    # Summary by data type
    type_summary = master_df['Data_Type'].value_counts().reset_index()
    type_summary.columns = ['Data_Type', 'Count']
    type_summary.to_excel(writer, sheet_name='Summary_by_Type', index=False)
    
    # Antakya specific records
    antakya_keywords = ['antakya', 'antioch', 'hatay', 'habib', 'neccar', 'syrian gates']
    antakya_df = master_df[master_df['Title'].str.lower().str.contains('|'.join(antakya_keywords), na=False) |
                           master_df['Description'].str.lower().str.contains('|'.join(antakya_keywords), na=False)]
    antakya_df.to_excel(writer, sheet_name='Antakya_Related', index=False)
    
    # File sources
    sources_df = pd.DataFrame(file_sources)
    sources_df.to_excel(writer, sheet_name='File_Sources', index=False)

print(f"\n✅ Master file created: {output_file}")
print(f"\nContents:")
print(f"- All Records: {len(master_df)} unique records")
print(f"- Antakya Related: {len(antakya_df)} records")
print(f"- Archives: {len(master_df['Archive'].unique())} different sources")
print(f"- Data Types: {master_df['Data_Type'].value_counts().to_dict()}")

# Also create a simplified CSV for easy viewing
csv_file = f"MASTER_COLLECTION_{timestamp}.csv"
master_df[['Title', 'Description', 'Date', 'Archive', 'Download_URL']].to_csv(csv_file, index=False)
print(f"\n✅ Also created simplified CSV: {csv_file}")