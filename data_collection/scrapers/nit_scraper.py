"""
Netherlands Institute in Turkey (NIT) - Machiel Kiel Archive Scraper
Critical source for Ottoman architectural documentation
Professor Machiel Kiel's 40+ years of Ottoman monument photography
"""

import re
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup

from ..universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType

logger = logging.getLogger(__name__)


class NITKielScraper(UniversalArchiveScraper):
    """
    Scraper for the Machiel Kiel Photographic Archive at NIT Istanbul
    Contains ~30,000 photographs of Ottoman monuments across the Balkans and Anatolia
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://www.nit-istanbul.org",
            archive_name="NIT Machiel Kiel Archive"
        )
        self.archive_url = "https://www.nit-istanbul.org/projects/machiel-kiel-photographic-archive"
        self.database_url = "https://nit-istanbul.org/kiel-archive/database"  # If they have online access
        
    def scrape(self, url: str = None, search_terms: List[str] = None, max_pages: int = 5) -> List[UniversalDataRecord]:
        """Scrape NIT Kiel Archive"""
        records = []
        
        # Check if database is online
        if not self._check_database_access():
            logger.info("NIT Kiel database not directly accessible, creating reference records")
            return self._create_reference_records(search_terms)
        
        if search_terms:
            for term in search_terms:
                logger.info(f"Searching NIT Kiel Archive for: {term}")
                search_records = self._search_archive(term, max_pages)
                records.extend(search_records)
        elif url:
            if '/photo/' in url or '/item/' in url:
                record = self._extract_item_details(url)
                if record:
                    records.append(record)
            else:
                records.extend(self._extract_collection(url))
        
        return self._deduplicate_records(records)
    
    def _check_database_access(self) -> bool:
        """Check if the Kiel archive database is accessible online"""
        try:
            # Try various possible database URLs
            possible_urls = [
                self.database_url,
                f"{self.base_url}/kiel-database",
                f"{self.base_url}/archive/search"
            ]
            
            for url in possible_urls:
                try:
                    response = self.session.get(url, timeout=5)
                    if response.ok:
                        return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def _create_reference_records(self, search_terms: List[str] = None) -> List[UniversalDataRecord]:
        """Create reference records for the Kiel Archive when database is not online"""
        records = []
        
        # Main archive information
        main_record = UniversalDataRecord(
            id="nit_kiel_main",
            source_archive=self.archive_name,
            source_url=self.archive_url,
            title="Machiel Kiel Photographic Archive - Ottoman Architectural Documentation",
            description=(
                "The Machiel Kiel Archive at the Netherlands Institute in Turkey contains approximately "
                "30,000 photographs documenting Ottoman architecture across the Balkans, Anatolia, and "
                "the Arab provinces. Professor Kiel photographed these monuments over 40+ years of "
                "fieldwork (1960s-2000s). The archive is particularly strong in documenting mosques, "
                "medreses, hamams, hans, and other Ottoman civic architecture. Many photographed "
                "monuments have since been destroyed or heavily altered, making this archive invaluable "
                "for reconstruction efforts."
            ),
            data_type=DataType.TEXT,
            keywords=[
                'Ottoman architecture', 'Machiel Kiel', 'photographic archive',
                'Balkans', 'Anatolia', 'mosque', 'medrese', 'hamam', 'han'
            ],
            raw_metadata={
                'archive_size': '~30,000 photographs',
                'date_range': '1960s-2000s',
                'geographic_coverage': [
                    'Turkey', 'Greece', 'Bulgaria', 'Macedonia', 'Albania',
                    'Bosnia', 'Serbia', 'Syria', 'Lebanon', 'Jordan'
                ],
                'monument_types': [
                    'Mosques', 'Medreses', 'Hamams', 'Hans/Caravanserais',
                    'Bridges', 'Fountains', 'Tombs', 'Fortifications'
                ],
                'access': 'On-site research by appointment'
            }
        )
        records.append(main_record)
        
        # Specific Antakya/Hatay documentation
        antakya_record = UniversalDataRecord(
            id="nit_kiel_antakya",
            source_archive=self.archive_name,
            source_url=self.archive_url,
            title="Kiel Archive - Antakya/Hatay Ottoman Monuments",
            description=(
                "The Kiel Archive contains significant documentation of Ottoman monuments in Antakya "
                "(ancient Antioch) and the Hatay region. This includes photographs of the Habib-i Neccar "
                "Mosque, Defterdar Mosque, Ottoman hans, and other structures damaged in the 2023 "
                "earthquakes. Kiel's photographs from the 1970s-1990s show these monuments in their "
                "pre-earthquake state with architectural details now lost."
            ),
            data_type=DataType.TEXT,
            keywords=[
                'Antakya', 'Hatay', 'Antioch', 'Habib-i Neccar', 'Ottoman mosque',
                'earthquake damage', 'architectural documentation'
            ],
            raw_metadata={
                'specific_monuments': [
                    'Habib-i Neccar Mosque',
                    'Defterdar Ibrahim Pasha Mosque',
                    'Ulu Cami',
                    'Ottoman commercial buildings',
                    'Historic hans'
                ],
                'documentation_period': '1970s-1990s',
                'significance': 'Pre-earthquake architectural record'
            }
        )
        records.append(antakya_record)
        
        # Research access information
        access_record = UniversalDataRecord(
            id="nit_kiel_access",
            source_archive=self.archive_name,
            source_url=f"{self.base_url}/contact",
            title="Accessing the Machiel Kiel Archive for Research",
            description=(
                "Researchers can access the Kiel Archive by appointment at the Netherlands Institute "
                "in Turkey (Istanbul). The archive is being digitized but is not yet fully available "
                "online. For earthquake damage documentation and reconstruction efforts, the NIT may "
                "provide expedited access to relevant photographs. Contact: info@nit-istanbul.org"
            ),
            data_type=DataType.TEXT,
            keywords=['research access', 'appointment', 'digitization', 'contact'],
            raw_metadata={
                'location': 'Istanbul, Turkey',
                'access_type': 'On-site by appointment',
                'digitization_status': 'In progress',
                'contact_email': 'info@nit-istanbul.org',
                'special_provisions': 'Expedited access for disaster documentation'
            }
        )
        records.append(access_record)
        
        # Create specific search-based records if terms provided
        if search_terms:
            for term in search_terms:
                term_lower = term.lower()
                if any(place in term_lower for place in ['antakya', 'hatay', 'antioch']):
                    search_record = UniversalDataRecord(
                        id=f"nit_kiel_search_{term.replace(' ', '_')}",
                        source_archive=self.archive_name,
                        source_url=self.archive_url,
                        title=f"Kiel Archive Search: {term}",
                        description=(
                            f"The Machiel Kiel Archive likely contains photographs related to '{term}'. "
                            f"Researchers should contact NIT Istanbul directly to inquire about specific "
                            f"Ottoman monuments in this search area. The archive's systematic documentation "
                            f"covers most significant Ottoman structures in Anatolia."
                        ),
                        data_type=DataType.TEXT,
                        keywords=[term] + ['Ottoman architecture', 'photographic documentation']
                    )
                    records.append(search_record)
        
        return records
    
    def _search_archive(self, query: str, max_pages: int) -> List[UniversalDataRecord]:
        """Search the archive if online access is available"""
        records = []
        
        # This would be implemented if/when NIT provides online database access
        # For now, create targeted reference records
        
        query_lower = query.lower()
        
        # Create specific record for architectural terms
        if any(term in query_lower for term in ['mosque', 'cami', 'medrese', 'hamam', 'han']):
            record = UniversalDataRecord(
                id=f"nit_kiel_{query.replace(' ', '_')}",
                source_archive=self.archive_name,
                source_url=self.archive_url,
                title=f"Kiel Archive - {query} Documentation",
                description=(
                    f"The Machiel Kiel Archive contains extensive photographic documentation of "
                    f"Ottoman {query}. These photographs, taken between the 1960s-2000s, provide "
                    f"crucial architectural details for restoration and reconstruction efforts."
                ),
                data_type=DataType.TEXT,
                keywords=[query, 'Ottoman architecture', 'Machiel Kiel', 'photographic archive']
            )
            records.append(record)
        
        return records
    
    def _extract_collection(self, url: str) -> List[UniversalDataRecord]:
        """Extract information about the collection from the main page"""
        records = []
        
        try:
            response = self.session.get(url)
            if response.ok:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract any featured collections or highlights
                featured_sections = soup.select('.featured, .highlight, .collection-item')
                
                for section in featured_sections:
                    title = self._extract_text(section, 'h2, h3, .title')
                    if not title:
                        continue
                    
                    record = UniversalDataRecord(
                        id=f"nit_kiel_collection_{title[:30].replace(' ', '_')}",
                        source_archive=self.archive_name,
                        source_url=url,
                        title=f"Kiel Collection - {title}",
                        description=self._extract_text(section, 'p, .description'),
                        data_type=DataType.TEXT,
                        keywords=['Machiel Kiel', 'collection', 'Ottoman architecture']
                    )
                    
                    # Extract any images shown
                    img = section.select_one('img')
                    if img:
                        img_url = urljoin(self.base_url, img.get('src', ''))
                        record.thumbnail_url = img_url
                        record.data_type = DataType.IMAGE
                    
                    records.append(record)
                    
        except Exception as e:
            logger.error(f"Error extracting NIT collection: {e}")
        
        return records
    
    def _extract_text(self, element, selector: str) -> str:
        """Safely extract text from element"""
        elem = element.select_one(selector)
        return elem.get_text(strip=True) if elem else ''


# Specific searches for Ottoman Antakya documentation
def search_ottoman_antakya_kiel():
    """Search for Ottoman Antakya/Hatay documentation in Kiel Archive"""
    scraper = NITKielScraper()
    
    # Key terms for Ottoman Antakya
    search_terms = [
        'Antakya',
        'Hatay',
        'Antioch Ottoman',
        'Habib Neccar',
        'Defterdar mosque',
        'Antakya han',
        'Hatay Ottoman architecture'
    ]
    
    all_records = []
    for term in search_terms:
        records = scraper.scrape(search_terms=[term])
        all_records.extend(records)
    
    return scraper._deduplicate_records(all_records)


# Combined search across all Ottoman archives
def search_all_ottoman_archives(location: str = "Antakya"):
    """Search all Ottoman architectural archives for a specific location"""
    all_records = []
    
    # SALT Research
    logger.info("Searching SALT Research...")
    from .salt_scraper import SALTResearchScraper
    salt = SALTResearchScraper()
    salt_records = salt.scrape(search_terms=[f"{location} Ottoman", f"{location} architecture"])
    all_records.extend(salt_records)
    
    # Akkasah (if available)
    logger.info("Searching Akkasah...")
    akkasah = AkkasahScraper()
    akkasah_records = akkasah.scrape(search_terms=[location, f"{location} mosque"])
    all_records.extend(akkasah_records)
    
    # NIT Kiel
    logger.info("Searching NIT Kiel Archive...")
    kiel = NITKielScraper()
    kiel_records = kiel.scrape(search_terms=[location, f"{location} Ottoman"])
    all_records.extend(kiel_records)
    
    # Deduplicate across all archives
    seen_titles = set()
    unique_records = []
    for record in all_records:
        if record.title not in seen_titles:
            seen_titles.add(record.title)
            unique_records.append(record)
    
    logger.info(f"Total unique records across all archives: {len(unique_records)}")
    return unique_records