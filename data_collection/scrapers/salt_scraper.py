"""
SALT Research Archive Scraper
Specializes in Ottoman and modern Turkish architectural documentation
Critical for Antakya's Ottoman heritage documentation
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


class SALTResearchScraper(UniversalArchiveScraper):
    """
    Scraper for SALT Research Istanbul archives
    Contains crucial Ottoman architectural documentation and photographs
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://saltresearch.org",
            archive_name="SALT Research"
        )
        self.search_base = "https://saltresearch.org/discovery/search"
        self.vid = "90GARANTI_INST:90SALT_VU1"
        
    def scrape(self, url: str = None, search_terms: List[str] = None, max_pages: int = 5) -> List[UniversalDataRecord]:
        """Scrape SALT Research for architectural documentation"""
        records = []
        
        if search_terms:
            # Search mode
            for term in search_terms:
                logger.info(f"Searching SALT Research for: {term}")
                search_records = self._search_archive(term, max_pages)
                records.extend(search_records)
        elif url:
            # Direct URL scraping
            if "docid=" in url:
                # Single item
                record = self._extract_item_details(url)
                if record:
                    records.append(record)
            else:
                # Collection or search results
                records.extend(self._extract_search_results(url))
        
        return self._deduplicate_records(records)
    
    def _search_archive(self, query: str, max_pages: int) -> List[UniversalDataRecord]:
        """Search SALT Research archive"""
        records = []
        
        # SALT uses a specific search API
        search_params = {
            'query': query,
            'vid': self.vid,
            'lang': 'en',
            'mode': 'advanced',
            'tab': 'Everything',
            'scope': 'MyInst_and_CI',
            'offset': 0
        }
        
        for page in range(max_pages):
            search_params['offset'] = page * 20  # 20 results per page
            
            try:
                response = self.session.get(self.search_base, params=search_params)
                if response.ok:
                    # SALT returns JSON data
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        data = response.json()
                        page_records = self._parse_json_results(data)
                    else:
                        # Fallback to HTML parsing
                        soup = BeautifulSoup(response.text, 'html.parser')
                        page_records = self._parse_html_results(soup)
                    
                    records.extend(page_records)
                    
                    if len(page_records) < 20:  # Less than full page means no more results
                        break
                    
                    time.sleep(self.delay)
                    
            except Exception as e:
                logger.error(f"Error searching SALT Research: {e}")
                break
        
        return records
    
    def _parse_json_results(self, data: Dict) -> List[UniversalDataRecord]:
        """Parse JSON search results"""
        records = []
        
        # Extract results from SALT's JSON structure
        results = data.get('docs', [])
        
        for item in results:
            try:
                record = UniversalDataRecord(
                    id=f"salt_{item.get('id', '')}",
                    source_archive=self.archive_name,
                    source_url=f"{self.base_url}/discovery/fulldisplay?docid={item.get('id')}&vid={self.vid}",
                    title=item.get('title', [''])[0] if isinstance(item.get('title'), list) else item.get('title', ''),
                    description=item.get('description', [''])[0] if isinstance(item.get('description'), list) else item.get('description', ''),
                    data_type=self._determine_data_type(item),
                    date_created=self._parse_date(item.get('date', '')),
                    creator=item.get('creator', []) if isinstance(item.get('creator'), list) else [item.get('creator', '')],
                    keywords=item.get('subject', []) if isinstance(item.get('subject'), list) else [],
                    raw_metadata={
                        'collection': item.get('collection', ''),
                        'format': item.get('format', ''),
                        'language': item.get('language', ''),
                        'rights': item.get('rights', '')
                    }
                )
                
                # Extract location if available
                if 'coverage' in item:
                    coverage = item['coverage']
                    if isinstance(coverage, list):
                        coverage = coverage[0] if coverage else ''
                    record.location = {'place_name': coverage}
                
                records.append(record)
                
            except Exception as e:
                logger.error(f"Error parsing SALT item: {e}")
                continue
        
        return records
    
    def _parse_html_results(self, soup: BeautifulSoup) -> List[UniversalDataRecord]:
        """Parse HTML search results as fallback"""
        records = []
        
        # Find result items - SALT uses primo-explore
        results = soup.select('.result-item, prm-brief-result')
        
        for item in results:
            try:
                # Extract title and link
                title_elem = item.select_one('.item-title, h3')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Get item link
                link_elem = item.select_one('a[href*="docid="]')
                if link_elem:
                    item_url = urljoin(self.base_url, link_elem.get('href'))
                else:
                    continue
                
                # Extract metadata
                record = UniversalDataRecord(
                    id=f"salt_{self._extract_docid(item_url)}",
                    source_archive=self.archive_name,
                    source_url=item_url,
                    title=title,
                    description=self._extract_text(item, '.item-description, .description'),
                    data_type=DataType.IMAGE  # Default, will be refined
                )
                
                # Extract additional metadata
                creator_elem = item.select_one('.creator, .author')
                if creator_elem:
                    record.creator = [creator_elem.get_text(strip=True)]
                
                date_elem = item.select_one('.date, .publication-date')
                if date_elem:
                    record.date_created = self._parse_date(date_elem.get_text(strip=True))
                
                records.append(record)
                
            except Exception as e:
                logger.error(f"Error parsing SALT HTML item: {e}")
                continue
        
        return records
    
    def _extract_item_details(self, url: str) -> Optional[UniversalDataRecord]:
        """Extract detailed information from a single item page"""
        try:
            response = self.session.get(url)
            if not response.ok:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Create base record
            record = UniversalDataRecord(
                id=f"salt_{self._extract_docid(url)}",
                source_archive=self.archive_name,
                source_url=url
            )
            
            # Title
            title_elem = soup.select_one('h1, .title-main, [ng-if*="title"]')
            if title_elem:
                record.title = title_elem.get_text(strip=True)
            
            # Extract all metadata fields
            metadata_sections = soup.select('.metadata-section, .details-section, [class*="metadata"]')
            
            for section in metadata_sections:
                # Look for label-value pairs
                labels = section.select('.label, dt, .metadata-label')
                values = section.select('.value, dd, .metadata-value')
                
                for label, value in zip(labels, values):
                    label_text = label.get_text(strip=True).lower()
                    value_text = value.get_text(strip=True)
                    
                    if 'description' in label_text:
                        record.description = value_text
                    elif 'creator' in label_text or 'author' in label_text:
                        record.creator = [v.strip() for v in value_text.split(';')]
                    elif 'date' in label_text:
                        record.date_created = self._parse_date(value_text)
                    elif 'subject' in label_text:
                        record.keywords = [v.strip() for v in value_text.split(';')]
                    elif 'location' in label_text or 'coverage' in label_text:
                        record.location = {'place_name': value_text}
                    elif 'format' in label_text:
                        record.data_type = self._determine_data_type({'format': value_text})
                    elif 'rights' in label_text:
                        record.rights = value_text
                    elif 'collection' in label_text:
                        record.raw_metadata['collection'] = value_text
            
            # Look for digital objects/images
            digital_objects = soup.select('img[src*="digital"], .digital-object, [ng-src*="digital"]')
            if digital_objects:
                # Get highest resolution image
                for img in digital_objects:
                    src = img.get('src') or img.get('ng-src') or img.get('data-src')
                    if src:
                        record.download_url = urljoin(self.base_url, src)
                        record.thumbnail_url = record.download_url
                        record.data_type = DataType.IMAGE
                        break
            
            return record
            
        except Exception as e:
            logger.error(f"Error extracting SALT item details: {e}")
            return None
    
    def _extract_docid(self, url: str) -> str:
        """Extract document ID from URL"""
        match = re.search(r'docid=([^&]+)', url)
        return match.group(1) if match else ''
    
    def _determine_data_type(self, item: Dict) -> DataType:
        """Determine data type from item metadata"""
        format_str = str(item.get('format', '')).lower()
        
        if any(term in format_str for term in ['photograph', 'image', 'jpg', 'jpeg', 'tiff']):
            return DataType.IMAGE
        elif any(term in format_str for term in ['document', 'text', 'report']):
            return DataType.TEXT
        elif 'pdf' in format_str:
            return DataType.PDF
        elif any(term in format_str for term in ['manuscript', 'handwritten']):
            return DataType.HANDWRITTEN
        else:
            return DataType.IMAGE  # Default for SALT's photographic collections
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats from SALT"""
        if not date_str:
            return None
        
        # Clean date string
        date_str = date_str.strip()
        
        # Try various formats
        formats = [
            '%Y',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d.%m.%Y',
            '%B %d, %Y',
            '%d %B %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try to extract just the year
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


# Specific search for Ottoman architectural photos in Antakya
def search_ottoman_antakya_salt():
    """Search SALT Research for Ottoman Antakya/Hatay architectural documentation"""
    scraper = SALTResearchScraper()
    
    # Key search terms for Ottoman Antakya
    search_terms = [
        'Antakya Ottoman',
        'Hatay architecture',
        'Antioch mosque',
        'Hatay cami',
        'Defterdar mosque',
        'Habib Neccar',
        'Ottoman Antioch'
    ]
    
    all_records = []
    for term in search_terms:
        records = scraper.scrape(search_terms=[term], max_pages=3)
        all_records.extend(records)
        logger.info(f"Found {len(records)} records for '{term}'")
    
    # Deduplicate final results
    unique_records = scraper._deduplicate_records(all_records)
    logger.info(f"Total unique SALT records: {len(unique_records)}")
    
    return unique_records