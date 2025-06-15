#!/usr/bin/env python3
"""
Unified Heritage System - Complete backend for heritage data collection and display
Combines all functionality into a single, efficient system
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import webbrowser
import argparse
from typing import List, Dict, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our existing modules
sys.path.append(str(Path(__file__).parent))
from data_collection.universal_harvester import UniversalHarvester
from data_collection.organizer import UniversalDataOrganizer

class UnifiedHeritageSystem:
    """Main system class that handles all heritage data operations"""
    
    def __init__(self):
        self.data_dir = Path("heritage_data")
        self.data_dir.mkdir(exist_ok=True)
        self.database_file = self.data_dir / "unified_heritage_database.xlsx"
        self.harvester = UniversalHarvester()
        self.organizer = UniversalDataOrganizer()
        
    def get_or_create_database(self) -> pd.DataFrame:
        """Get existing database or create a new one"""
        if self.database_file.exists():
            logger.info(f"Loading existing database from {self.database_file}")
            return pd.read_excel(self.database_file, sheet_name='All_Records')
        else:
            logger.info("No database found, creating new one")
            return pd.DataFrame()
    
    def clean_and_optimize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and optimize the database records"""
        logger.info("Cleaning and optimizing data...")
        
        # Import cleaning functions from our optimization script
        from optimize_database_v2 import (
            extract_image_name_from_url, 
            is_peripheral_image,
            create_meaningful_description
        )
        
        cleaned_records = []
        for idx, row in df.iterrows():
            # Skip peripheral images
            if is_peripheral_image(row.get('Image_URL', ''), row.get('Title', '')):
                continue
                
            # Extract proper title
            title = extract_image_name_from_url(row.get('Image_URL', ''))
            if not title:
                title = row.get('Title', 'Untitled')
                
            # Create meaningful description
            desc = create_meaningful_description(
                title, 
                row.get('Category', 'Heritage'),
                row.get('Location')
            )
            
            cleaned_records.append({
                'Title': title,
                'Description': desc,
                'Image_URL': row.get('Image_URL', ''),
                'Thumbnail_URL': row.get('Thumbnail_URL', row.get('Image_URL', '')),
                'Category': row.get('Category', 'Heritage'),
                'Archive': row.get('Archive', 'Unknown'),
                'Location': row.get('Location', ''),
                'Date': row.get('Date', ''),
                'Creator': row.get('Creator', ''),
                'Keywords': row.get('Keywords', []),
                'Source_Page': row.get('Source_Page', '')
            })
            
        df_cleaned = pd.DataFrame(cleaned_records)
        logger.info(f"Cleaned {len(df_cleaned)} records from {len(df)} original")
        return df_cleaned
    
    def harvest_archive(self, archive_url: str) -> pd.DataFrame:
        """Harvest data from a specific archive"""
        logger.info(f"Harvesting from: {archive_url}")
        
        # Harvest data
        records = self.harvester.harvest_url(archive_url)
        
        if not records:
            logger.warning("No records harvested")
            return pd.DataFrame()
            
        # Convert to dataframe
        df = pd.DataFrame([r.to_dict() for r in records])
        
        # Map fields to our standard format
        df_mapped = pd.DataFrame({
            'Title': df.get('title', 'Untitled'),
            'Description': df.get('description', ''),
            'Image_URL': df.get('download_url', df.get('url', '')),
            'Thumbnail_URL': df.get('thumbnail_url', df.get('download_url', '')),
            'Category': df.get('archive', 'Heritage').apply(lambda x: x.replace(' ', '_')),
            'Archive': df.get('source_archive', 'Unknown'),
            'Location': df.get('location', '').apply(lambda x: x.get('place_name', '') if isinstance(x, dict) else x),
            'Date': df.get('date_display', ''),
            'Creator': df.get('creator', []).apply(lambda x: ', '.join(x) if isinstance(x, list) else x),
            'Keywords': df.get('keywords', []),
            'Source_Page': df.get('source_url', '')
        })
        
        return df_mapped
    
    def search_archives(self, search_terms: List[str], archives: List[str] = None) -> pd.DataFrame:
        """Search across multiple archives"""
        logger.info(f"Searching for: {search_terms}")
        
        if archives:
            records = self.harvester.harvest_search(search_terms, archives)
        else:
            records = self.harvester.harvest_all_archives(search_terms)
            
        if not records:
            logger.warning("No records found")
            return pd.DataFrame()
            
        # Convert to dataframe using same mapping as above
        df = pd.DataFrame([r.to_dict() for r in records])
        
        df_mapped = pd.DataFrame({
            'Title': df.get('title', 'Untitled'),
            'Description': df.get('description', ''),
            'Image_URL': df.get('download_url', df.get('url', '')),
            'Thumbnail_URL': df.get('thumbnail_url', df.get('download_url', '')),
            'Category': df.get('archive', 'Heritage').apply(lambda x: x.replace(' ', '_')),
            'Archive': df.get('source_archive', 'Unknown'),
            'Location': df.get('location', '').apply(lambda x: x.get('place_name', '') if isinstance(x, dict) else x),
            'Date': df.get('date_display', ''),
            'Creator': df.get('creator', []).apply(lambda x: ', '.join(x) if isinstance(x, list) else x),
            'Keywords': df.get('keywords', []),
            'Source_Page': df.get('source_url', '')
        })
        
        return df_mapped
    
    def merge_with_existing(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """Merge new data with existing database"""
        existing_df = self.get_or_create_database()
        
        if existing_df.empty:
            return new_df
            
        # Combine dataframes
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Remove duplicates based on Image_URL
        combined_df = combined_df.drop_duplicates(subset=['Image_URL'], keep='first')
        
        logger.info(f"Merged to {len(combined_df)} total records")
        return combined_df
    
    def save_database(self, df: pd.DataFrame):
        """Save the database with multiple sheets"""
        logger.info(f"Saving database to {self.database_file}")
        
        with pd.ExcelWriter(self.database_file, engine='xlsxwriter') as writer:
            # All records
            df.to_excel(writer, sheet_name='All_Records', index=False)
            
            # Category summary
            category_summary = df['Category'].value_counts().reset_index()
            category_summary.columns = ['Category', 'Count']
            category_summary.to_excel(writer, sheet_name='Categories', index=False)
            
            # Archive summary
            archive_summary = df['Archive'].value_counts().reset_index()
            archive_summary.columns = ['Archive', 'Count']
            archive_summary.to_excel(writer, sheet_name='Archives', index=False)
            
            # Location summary
            locations = df[df['Location'] != '']['Location'].value_counts().head(50)
            if not locations.empty:
                location_summary = locations.reset_index()
                location_summary.columns = ['Location', 'Count']
                location_summary.to_excel(writer, sheet_name='Top_Locations', index=False)
                
        logger.info("Database saved successfully")
    
    def generate_web_interface(self, df: pd.DataFrame):
        """Generate the web interface for exploring data"""
        logger.info("Generating web interface...")
        
        # Read the template from enhanced_search.py
        with open('enhanced_search.py', 'r') as f:
            template_content = f.read()
            
        # Extract just the HTML generation part
        html_start = template_content.find('html = f"""')
        html_end = template_content.find('"""', html_start + 10)
        
        if html_start == -1 or html_end == -1:
            logger.error("Could not extract HTML template")
            return
            
        # Execute the HTML template with our dataframe
        exec_globals = {'df': df, 'len': len}
        exec(f"html = f{template_content[html_start+7:html_end+3]}", exec_globals)
        html = exec_globals['html']
        
        # Save and open
        output_file = self.data_dir / "heritage_explorer.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
            
        webbrowser.open(f"file://{output_file.absolute()}")
        logger.info(f"Web interface saved to {output_file}")
    
    def quick_search(self, search_terms: List[str]):
        """Quick search across all archives and display results"""
        logger.info(f"Quick search for: {search_terms}")
        
        # Search all archives
        new_df = self.search_archives(search_terms)
        
        if new_df.empty:
            logger.warning("No results found")
            return
            
        # Clean the data
        new_df = self.clean_and_optimize_data(new_df)
        
        # Merge with existing
        combined_df = self.merge_with_existing(new_df)
        
        # Save database
        self.save_database(combined_df)
        
        # Generate and open web interface
        self.generate_web_interface(combined_df)
        
        logger.info(f"Found {len(new_df)} new records, total database has {len(combined_df)} records")
    
    def add_archive(self, archive_url: str):
        """Add data from a specific archive URL"""
        logger.info(f"Adding archive: {archive_url}")
        
        # Harvest from archive
        new_df = self.harvest_archive(archive_url)
        
        if new_df.empty:
            logger.warning("No data harvested")
            return
            
        # Clean the data
        new_df = self.clean_and_optimize_data(new_df)
        
        # Merge with existing
        combined_df = self.merge_with_existing(new_df)
        
        # Save database
        self.save_database(combined_df)
        
        logger.info(f"Added {len(new_df)} records from archive")
    
    def view_database(self):
        """View the current database in web interface"""
        df = self.get_or_create_database()
        
        if df.empty:
            logger.warning("Database is empty")
            return
            
        self.generate_web_interface(df)
        logger.info(f"Viewing {len(df)} records")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Unified Heritage System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search archives for heritage data')
    search_parser.add_argument('terms', nargs='+', help='Search terms')
    search_parser.add_argument('--archives', nargs='*', help='Specific archives to search')
    
    # Add archive command
    add_parser = subparsers.add_parser('add', help='Add data from a specific archive URL')
    add_parser.add_argument('url', help='Archive URL to harvest')
    
    # View command
    view_parser = subparsers.add_parser('view', help='View current database')
    
    # Antakya special command
    antakya_parser = subparsers.add_parser('antakya', help='Comprehensive Antakya heritage search')
    
    args = parser.parse_args()
    
    # Initialize system
    system = UnifiedHeritageSystem()
    
    if args.command == 'search':
        system.quick_search(args.terms)
    elif args.command == 'add':
        system.add_archive(args.url)
    elif args.command == 'view':
        system.view_database()
    elif args.command == 'antakya':
        # Special comprehensive Antakya search
        system.quick_search(['Antakya', 'Antioch', 'Hatay', 'earthquake', 'heritage'])
    else:
        parser.print_help()


if __name__ == '__main__':
    main()