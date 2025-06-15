"""
Akkasah Photography Archive Scraper (NYU Abu Dhabi)
Specializes in Middle Eastern and Arab world photography
Important for regional architectural documentation
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


class AkkasahScraper(UniversalArchiveScraper):
    """
    Scraper for Akkasah Center for Photography at NYU Abu Dhabi
    Contains important Middle Eastern architectural photography
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://akkasah.org",
            archive_name="Akkasah"
        )
        # Alternative URLs if main site is down
        self.alt_urls = [
            "https://nyuad.nyu.edu/en/research/faculty-labs-and-projects/akkasah-center-for-photography.html",
            "https://akkasah.net"
        ]
        self.api_base = "https://akkasah.org/api/v1"
        
    def scrape(self, url: str = None, search_terms: List[str] = None, max_pages: int = 5) -> List[UniversalDataRecord]:
        """Scrape Akkasah archive for photography"""
        records = []
        
        # Check if main site is accessible
        if not self._check_site_availability():
            logger.warning("Akkasah main site is down, trying alternatives...")
            return self._scrape_alternatives(search_terms)
        
        if search_terms:
            for term in search_terms:
                logger.info(f"Searching Akkasah for: {term}")
                search_records = self._search_archive(term, max_pages)
                records.extend(search_records)
        elif url:
            if '/photo/' in url or '/collection/' in url:
                record = self._extract_photo_details(url)
                if record:
                    records.append(record)
            else:
                records.extend(self._extract_collection(url))
        
        return self._deduplicate_records(records)
    
    def _check_site_availability(self) -> bool:
        """Check if Akkasah site is available"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.ok
        except:
            return False
    
    def _scrape_alternatives(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Scrape alternative sources when main site is down"""
        records = []
        
        # Create informational record about the archive
        info_record = UniversalDataRecord(
            id="akkasah_info",
            source_archive=self.archive_name,
            source_url=self.alt_urls[0],
            title="Akkasah Center for Photography - Archive Currently Offline",
            description=(
                "The Akkasah Center for Photography at NYU Abu Dhabi houses one of the most "
                "comprehensive collections of photographs from the Middle East, North Africa, "
                "and South Asia. The archive contains historical photographs documenting "
                "architectural heritage, urban development, and cultural practices. "
                "The database appears to be temporarily offline."
            ),
            data_type=DataType.TEXT,
            keywords=['photography', 'Middle East', 'architecture', 'Arab world', 'heritage'],
            raw_metadata={
                'institution': 'NYU Abu Dhabi',
                'focus': 'Middle Eastern photography',
                'status': 'temporarily offline',
                'collections': [
                    'Historical architecture',
                    'Urban documentation',
                    'Cultural heritage',
                    'Archaeological sites'
                ]
            }
        )
        records.append(info_record)
        
        # Add contact information for researchers
        contact_record = UniversalDataRecord(
            id="akkasah_contact",
            source_archive=self.archive_name,
            source_url="https://nyuad.nyu.edu/en/research/faculty-labs-and-projects/akkasah-center-for-photography/contact.html",
            title="Akkasah Center - Research Access Information",
            description=(
                "For research access to the Akkasah photographic collections, "
                "researchers should contact the center directly through NYU Abu Dhabi. "
                "The collection includes significant documentation of Ottoman and "
                "modern architecture across the Arab world."
            ),
            data_type=DataType.TEXT,
            keywords=['research access', 'contact', 'photography archive']
        )
        records.append(contact_record)
        
        return records
    
    def _search_archive(self, query: str, max_pages: int) -> List[UniversalDataRecord]:
        """Search Akkasah archive via API or web interface"""
        records = []
        
        # Try API first
        api_url = f"{self.api_base}/search"
        
        for page in range(max_pages):
            params = {
                'q': query,
                'page': page + 1,
                'per_page': 50,
                'fields': 'all'
            }
            
            try:
                response = self.session.get(api_url, params=params)
                if response.ok:
                    data = response.json()
                    
                    for item in data.get('results', []):
                        record = self._parse_api_result(item)
                        if record:
                            records.append(record)
                    
                    # Check if more pages exist
                    if data.get('total_pages', 0) <= page + 1:
                        break
                    
                    time.sleep(self.delay)
                else:
                    # Fallback to web scraping
                    return self._search_web_interface(query, max_pages)
                    
            except Exception as e:
                logger.error(f"Error searching Akkasah API: {e}")
                return self._search_web_interface(query, max_pages)
        
        return records
    
    def _search_web_interface(self, query: str, max_pages: int) -> List[UniversalDataRecord]:
        """Fallback web interface search"""
        records = []
        
        search_url = f"{self.base_url}/search"
        
        for page in range(max_pages):
            params = {
                'q': query,
                'page': page + 1
            }
            
            try:
                response = self.session.get(search_url, params=params)
                if response.ok:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find photo results
                    results = soup.select('.photo-item, .search-result, .grid-item')
                    
                    for item in results:
                        record = self._parse_web_result(item)
                        if record:
                            records.append(record)
                    
                    # Check for next page
                    if not soup.select_one('.next-page, .pagination .next'):
                        break
                    
                    time.sleep(self.delay)
                    
            except Exception as e:
                logger.error(f"Error searching Akkasah web: {e}")
                break
        
        return records
    
    def _parse_api_result(self, item: Dict) -> Optional[UniversalDataRecord]:
        """Parse API search result"""
        try:
            record = UniversalDataRecord(
                id=f"akkasah_{item.get('id', '')}",
                source_archive=self.archive_name,
                source_url=f"{self.base_url}/photo/{item.get('id')}",
                title=item.get('title', ''),
                description=item.get('description', ''),
                data_type=DataType.IMAGE,
                date_created=self._parse_date(item.get('date_taken', item.get('date', ''))),
                creator=[item.get('photographer', '')] if item.get('photographer') else [],
                keywords=item.get('tags', []) + item.get('subjects', []),
                raw_metadata={
                    'collection': item.get('collection', ''),
                    'accession_number': item.get('accession_number', ''),
                    'medium': item.get('medium', ''),
                    'dimensions': item.get('dimensions', ''),
                    'copyright': item.get('copyright', '')
                }
            )
            
            # Add location
            if item.get('location'):
                record.location = {
                    'place_name': item['location'].get('name', ''),
                    'country': item['location'].get('country', ''),
                    'region': item['location'].get('region', '')
                }
                
                if item['location'].get('coordinates'):
                    record.location['lat'] = item['location']['coordinates'].get('lat')
                    record.location['lon'] = item['location']['coordinates'].get('lng')
            
            # Add image URLs
            if item.get('images'):
                # Get highest resolution
                if item['images'].get('full'):
                    record.download_url = item['images']['full']
                elif item['images'].get('large'):
                    record.download_url = item['images']['large']
                
                record.thumbnail_url = item['images'].get('thumbnail', record.download_url)
            
            return record
            
        except Exception as e:
            logger.error(f"Error parsing Akkasah API result: {e}")
            return None
    
    def _parse_web_result(self, item) -> Optional[UniversalDataRecord]:
        """Parse web search result"""
        try:
            # Extract link and ID
            link_elem = item.select_one('a[href*="/photo/"]')
            if not link_elem:
                return None
            
            photo_url = urljoin(self.base_url, link_elem.get('href'))
            photo_id = re.search(r'/photo/(\d+)', photo_url)
            
            record = UniversalDataRecord(
                id=f"akkasah_{photo_id.group(1) if photo_id else ''}",
                source_archive=self.archive_name,
                source_url=photo_url,
                title=self._extract_text(item, '.title, .photo-title, h3'),
                description=self._extract_text(item, '.description, .caption'),
                data_type=DataType.IMAGE
            )
            
            # Extract thumbnail
            img_elem = item.select_one('img')
            if img_elem:
                record.thumbnail_url = urljoin(self.base_url, img_elem.get('src', ''))
            
            # Extract metadata
            metadata_elem = item.select_one('.metadata, .photo-info')
            if metadata_elem:
                # Date
                date_text = self._extract_text(metadata_elem, '.date, .year')
                if date_text:
                    record.date_created = self._parse_date(date_text)
                
                # Photographer
                photographer = self._extract_text(metadata_elem, '.photographer, .creator')
                if photographer:
                    record.creator = [photographer]
                
                # Location
                location = self._extract_text(metadata_elem, '.location, .place')
                if location:
                    record.location = {'place_name': location}
            
            return record
            
        except Exception as e:
            logger.error(f"Error parsing Akkasah web result: {e}")
            return None
    
    def _extract_photo_details(self, url: str) -> Optional[UniversalDataRecord]:
        """Extract detailed photo information"""
        try:
            response = self.session.get(url)
            if not response.ok:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract photo ID
            photo_id = re.search(r'/photo/(\d+)', url)
            
            record = UniversalDataRecord(
                id=f"akkasah_{photo_id.group(1) if photo_id else ''}",
                source_archive=self.archive_name,
                source_url=url,
                data_type=DataType.IMAGE
            )
            
            # Title
            record.title = self._extract_text(soup, 'h1, .photo-title')
            
            # Full image URL
            img_elem = soup.select_one('.full-image, .main-image, img.photo')
            if img_elem:
                record.download_url = urljoin(self.base_url, img_elem.get('src', ''))
                record.thumbnail_url = record.download_url
            
            # Metadata table/list
            metadata_container = soup.select_one('.photo-metadata, .details, .info-table')
            if metadata_container:
                # Parse all metadata fields
                for row in metadata_container.select('tr, .info-row, .field'):
                    label = self._extract_text(row, '.label, th, .field-label').lower()
                    value = self._extract_text(row, '.value, td, .field-value')
                    
                    if not value:
                        continue
                    
                    if 'description' in label:
                        record.description = value
                    elif 'date' in label or 'year' in label:
                        record.date_created = self._parse_date(value)
                    elif 'photographer' in label or 'creator' in label:
                        record.creator = [value]
                    elif 'location' in label or 'place' in label:
                        record.location = {'place_name': value}
                    elif 'subject' in label or 'tag' in label:
                        record.keywords = [k.strip() for k in value.split(',')]
                    elif 'collection' in label:
                        record.raw_metadata['collection'] = value
                    elif 'accession' in label:
                        record.raw_metadata['accession_number'] = value
                    elif 'copyright' in label or 'rights' in label:
                        record.rights = value
            
            return record
            
        except Exception as e:
            logger.error(f"Error extracting Akkasah photo details: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
        
        # Common formats in Akkasah
        formats = [
            '%Y',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%B %Y',
            '%b %Y',
            '%Y-%m',
            'circa %Y',
            'c. %Y'
        ]
        
        # Clean date string
        date_str = date_str.strip()
        date_str = re.sub(r'circa\s+|c\.\s+', '', date_str, flags=re.IGNORECASE)
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Extract year
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', date_str)
        if year_match:
            try:
                return datetime(int(year_match.group(1)), 1, 1)
            except:
                pass
        
        return None
    
    def _extract_text(self, element, selector: str) -> str:
        """Safely extract text from element"""
        elem = element.select_one(selector)
        return elem.get_text(strip=True) if elem else ''


# Specialized searches for architectural documentation
def search_levantine_architecture_akkasah():
    """Search for Levantine and Syrian architectural photography"""
    scraper = AkkasahScraper()
    
    search_terms = [
        'Syria architecture',
        'Damascus mosque',
        'Aleppo',
        'Levant Ottoman',
        'Syrian heritage',
        'Antioch',
        'Antakya'
    ]
    
    all_records = []
    for term in search_terms:
        records = scraper.scrape(search_terms=[term], max_pages=2)
        all_records.extend(records)
    
    return scraper._deduplicate_records(all_records)