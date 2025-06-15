"""
Data organization and export system for harvested archive data.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

from .universal_scraper import UniversalDataRecord, DataType
from .deduplication import DeduplicationEngine

logger = logging.getLogger(__name__)


class UniversalDataOrganizer:
    """Organize and export harvested data in multiple formats."""
    
    def __init__(self, records: List[UniversalDataRecord], deduplicate: bool = True):
        # Deduplicate records if requested
        if deduplicate and records:
            logger.info(f"Deduplicating {len(records)} records...")
            dedup_engine = DeduplicationEngine()
            self.records = dedup_engine.deduplicate(records)
            logger.info(f"After deduplication: {len(self.records)} unique records")
        else:
            self.records = records
        
        self.df = self._create_dataframe()
        
    def _create_dataframe(self) -> pd.DataFrame:
        """Convert records to pandas DataFrame."""
        data = []
        
        for record in self.records:
            row = {
                'ID': record.id,
                'Archive': record.source_archive,
                'URL': record.source_url,
                'Title': record.title,
                'Description': record.description[:200] + '...' if len(record.description) > 200 else record.description,
                'Date': record.date_created.isoformat() if record.date_created else '',
                'Date_Range': f"{record.date_range_start} - {record.date_range_end}" if record.date_range_start else '',
                'Date_Uncertainty': record.date_uncertainty or '',
                'Data_Type': record.data_type.value,
                'Is_Handwritten': record.data_type == DataType.HANDWRITTEN,
                'Language': ', '.join(record.language) if record.language else '',
                'Script': record.script or '',
                'Location': record.location.get('place_name', '') if record.location else '',
                'Creator': ', '.join(record.creator) if record.creator else '',
                'Keywords': ', '.join(record.keywords) if record.keywords else '',
                'Download_URL': record.download_url or '',
                'Thumbnail_URL': record.thumbnail_url or '',
                'Rights': record.rights or '',
                'License': record.license or '',
                'Harvested_Date': record.harvested_date.isoformat()
            }
            
            # Add geographic coordinates if available
            if record.location and 'lat' in record.location:
                row['Latitude'] = record.location['lat']
                row['Longitude'] = record.location['lon']
                
            data.append(row)
            
        return pd.DataFrame(data)
    
    def export_excel(self, filepath: str):
        """Export to Excel with multiple sheets."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Main data sheet
            self.df.to_excel(writer, sheet_name='All_Records', index=False)
            
            # Summary by archive
            if not self.df.empty:
                summary = self.df.groupby('Archive').agg({
                    'ID': 'count',
                    'Data_Type': lambda x: ', '.join(x.value_counts().index[:3])
                }).rename(columns={'ID': 'Total_Records', 'Data_Type': 'Top_Types'})
                summary.to_excel(writer, sheet_name='Summary_by_Archive')
                
                # By data type
                for data_type in DataType:
                    filtered = self.df[self.df['Data_Type'] == data_type.value]
                    if not filtered.empty:
                        sheet_name = f'{data_type.value}_Records'[:31]  # Excel sheet name limit
                        filtered.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                # Date analysis
                dated_records = self.df[self.df['Date'] != '']
                if not dated_records.empty:
                    dated_records['Year'] = pd.to_datetime(dated_records['Date']).dt.year
                    date_summary = dated_records.groupby('Year')['ID'].count()
                    date_summary.to_excel(writer, sheet_name='Records_by_Year')
                    
        logger.info(f"Exported {len(self.records)} records to Excel: {filepath}")
    
    def export_json(self, filepath: str):
        """Export as JSON with full metadata."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert records to dictionaries
        data = []
        for record in self.records:
            record_dict = {
                'id': record.id,
                'source_archive': record.source_archive,
                'source_url': record.source_url,
                'title': record.title,
                'description': record.description,
                'date_created': record.date_created.isoformat() if record.date_created else None,
                'date_range_start': record.date_range_start.isoformat() if record.date_range_start else None,
                'date_range_end': record.date_range_end.isoformat() if record.date_range_end else None,
                'date_uncertainty': record.date_uncertainty,
                'subject': record.subject,
                'keywords': record.keywords,
                'data_type': record.data_type.value,
                'mime_type': record.mime_type,
                'file_format': record.file_format,
                'dimensions': record.dimensions,
                'file_size': record.file_size,
                'resolution': record.resolution,
                'location': record.location,
                'coverage_spatial': record.coverage_spatial,
                'creator': record.creator,
                'contributor': record.contributor,
                'publisher': record.publisher,
                'rights': record.rights,
                'license': record.license,
                'access_restrictions': record.access_restrictions,
                'language': record.language,
                'script': record.script,
                'is_part_of': record.is_part_of,
                'related_items': record.related_items,
                'download_url': record.download_url,
                'thumbnail_url': record.thumbnail_url,
                'iiif_manifest': record.iiif_manifest,
                'harvested_date': record.harvested_date.isoformat(),
                'processing_notes': record.processing_notes,
                'confidence_score': record.confidence_score,
                'raw_metadata': record.raw_metadata
            }
            data.append(record_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Exported {len(self.records)} records to JSON: {filepath}")
    
    def export_database(self, db_path: str):
        """Export to SQLite database with normalized tables."""
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        
        try:
            # Create main records table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY,
                    source_archive TEXT,
                    source_url TEXT,
                    title TEXT,
                    description TEXT,
                    date_created TEXT,
                    date_range_start TEXT,
                    date_range_end TEXT,
                    date_uncertainty TEXT,
                    data_type TEXT,
                    mime_type TEXT,
                    file_format TEXT,
                    file_size INTEGER,
                    resolution TEXT,
                    location_name TEXT,
                    location_lat REAL,
                    location_lon REAL,
                    publisher TEXT,
                    rights TEXT,
                    license TEXT,
                    access_restrictions TEXT,
                    script TEXT,
                    is_part_of TEXT,
                    download_url TEXT,
                    thumbnail_url TEXT,
                    iiif_manifest TEXT,
                    harvested_date TEXT,
                    confidence_score REAL
                )
            ''')
            
            # Create related tables
            conn.execute('''
                CREATE TABLE IF NOT EXISTS record_keywords (
                    record_id TEXT,
                    keyword TEXT,
                    FOREIGN KEY (record_id) REFERENCES records(id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS record_subjects (
                    record_id TEXT,
                    subject TEXT,
                    FOREIGN KEY (record_id) REFERENCES records(id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS record_creators (
                    record_id TEXT,
                    creator TEXT,
                    FOREIGN KEY (record_id) REFERENCES records(id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS record_languages (
                    record_id TEXT,
                    language TEXT,
                    FOREIGN KEY (record_id) REFERENCES records(id)
                )
            ''')
            
            # Insert main records
            for record in self.records:
                conn.execute('''
                    INSERT OR REPLACE INTO records VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                ''', (
                    record.id,
                    record.source_archive,
                    record.source_url,
                    record.title,
                    record.description,
                    record.date_created.isoformat() if record.date_created else None,
                    record.date_range_start.isoformat() if record.date_range_start else None,
                    record.date_range_end.isoformat() if record.date_range_end else None,
                    record.date_uncertainty,
                    record.data_type.value,
                    record.mime_type,
                    record.file_format,
                    record.file_size,
                    record.resolution,
                    record.location.get('place_name') if record.location else None,
                    record.location.get('lat') if record.location else None,
                    record.location.get('lon') if record.location else None,
                    record.publisher,
                    record.rights,
                    record.license,
                    record.access_restrictions,
                    record.script,
                    record.is_part_of,
                    record.download_url,
                    record.thumbnail_url,
                    record.iiif_manifest,
                    record.harvested_date.isoformat(),
                    record.confidence_score
                ))
                
                # Insert related data
                for keyword in record.keywords:
                    conn.execute('INSERT INTO record_keywords VALUES (?, ?)', (record.id, keyword))
                    
                for subject in record.subject:
                    conn.execute('INSERT INTO record_subjects VALUES (?, ?)', (record.id, subject))
                    
                for creator in record.creator:
                    conn.execute('INSERT INTO record_creators VALUES (?, ?)', (record.id, creator))
                    
                for language in record.language:
                    conn.execute('INSERT INTO record_languages VALUES (?, ?)', (record.id, language))
            
            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_archive ON records(source_archive)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_data_type ON records(data_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_date ON records(date_created)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_location ON records(location_name)')
            
            conn.commit()
            logger.info(f"Exported {len(self.records)} records to database: {db_path}")
            
        finally:
            conn.close()
    
    def generate_summary_report(self) -> str:
        """Generate a text summary of the harvested data."""
        report = []
        report.append("=== HARVEST SUMMARY REPORT ===\n")
        report.append(f"Total Records: {len(self.records)}")
        report.append(f"Harvest Date: {datetime.now().isoformat()}\n")
        
        # By archive
        report.append("Records by Archive:")
        archive_counts = self.df['Archive'].value_counts()
        for archive, count in archive_counts.items():
            report.append(f"  - {archive}: {count}")
        
        # By data type
        report.append("\nRecords by Data Type:")
        type_counts = self.df['Data_Type'].value_counts()
        for dtype, count in type_counts.items():
            report.append(f"  - {dtype}: {count}")
        
        # Geographic coverage
        locations = self.df['Location'].dropna()
        if not locations.empty:
            report.append("\nGeographic Coverage:")
            location_counts = locations.value_counts().head(10)
            for location, count in location_counts.items():
                report.append(f"  - {location}: {count}")
        
        # Date range
        dated = self.df[self.df['Date'] != '']
        if not dated.empty:
            dates = pd.to_datetime(dated['Date'])
            report.append(f"\nDate Range: {dates.min()} to {dates.max()}")
        
        return '\n'.join(report)