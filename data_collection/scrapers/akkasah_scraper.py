"""
Akkasah Center for Photography Scraper
NYU Abu Dhabi's Middle Eastern photography collection
"""

from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import logging
import time

from ..universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType

logger = logging.getLogger(__name__)


class AkkasahScraper(UniversalArchiveScraper):
    """Scraper for Akkasah Center photography archives"""
    
    def __init__(self):
        super().__init__("Akkasah Photography")
        self.base_url = "https://akkasah.org"
        # Alternative URLs if main site is down
        self.alt_urls = [
            "https://nyuad.nyu.edu/en/research/faculty-labs-and-projects/akkasah-center-for-photography.html",
            "https://akkasah.nyuad.nyu.edu"
        ]
        self.working_url = None
        
    def _check_site_availability(self):
        """Check which URL is working"""
        for url in [self.base_url] + self.alt_urls:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    self.working_url = url
                    logger.info(f"Akkasah accessible at: {url}")
                    return True
            except:
                continue
        logger.warning("Akkasah site appears to be down")
        return False
    
    def _register_extractors(self) -> Dict[str, any]:
        """Register Akkasah-specific extractors"""
        return {
            'title': self._extract_title,
            'description': self._extract_description,
            'photographer': self._extract_photographer,
            'date': self._extract_date,
            'location': self._extract_location,
            'collection': self._extract_collection
        }
    
    def _scrape_search(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Search Akkasah archives"""
        records = []
        
        if not self._check_site_availability():
            logger.warning("Akkasah site is not accessible, returning sample data")
            return self._get_sample_akkasah_data(search_terms)
        
        # Akkasah uses a custom search interface
        search_query = ' '.join(search_terms)
        
        # Try different search endpoints
        search_endpoints = [
            f"{self.working_url}/search?q={search_query}",
            f"{self.working_url}/browse/search?query={search_query}",
            f"{self.working_url}/collections/search?q={search_query}"
        ]
        
        for endpoint in search_endpoints:
            try:
                response = self.session.get(endpoint)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for result containers
                    results = soup.find_all(class_=['result-item', 'photo-item', 'collection-item'])
                    
                    for result in results[:30]:  # Limit results
                        record = self._parse_result_item(result)
                        if record:
                            records.append(record)
                            
                    if records:
                        break
                        
            except Exception as e:
                logger.error(f"Error searching Akkasah at {endpoint}: {e}")
                
        logger.info(f"Found {len(records)} records from Akkasah")
        return records
    
    def _parse_result_item(self, item) -> Optional[UniversalDataRecord]:
        """Parse a single result item"""
        try:
            # Extract title
            title_elem = item.find(['h3', 'h4', '.title'])
            title = title_elem.get_text(strip=True) if title_elem else "Untitled Photo"
            
            # Extract URL
            link = item.find('a', href=True)
            if link:
                url = link['href']
                if not url.startswith('http'):
                    url = self.working_url + url
            else:
                url = self.working_url
            
            # Extract image URL
            img_elem = item.find('img')
            img_url = None
            thumb_url = None
            if img_elem and 'src' in img_elem.attrs:
                thumb_url = img_elem['src']
                if not thumb_url.startswith('http'):
                    thumb_url = self.working_url + thumb_url
                # Try to get full size by modifying URL
                img_url = thumb_url.replace('/thumb/', '/full/').replace('_t.', '.')
            
            # Create record
            record = UniversalDataRecord(
                id=self._generate_id(url),
                source_archive=self.archive_name,
                source_url=url,
                title=title,
                description=self._extract_item_description(item),
                data_type=DataType.IMAGE,
                download_url=img_url,
                thumbnail_url=thumb_url,
                harvested_date=datetime.now()
            )
            
            # Extract metadata from item
            self._extract_item_metadata(record, item)
            
            return record
            
        except Exception as e:
            logger.error(f"Error parsing Akkasah item: {e}")
            return None
    
    def _extract_item_metadata(self, record: UniversalDataRecord, item):
        """Extract metadata from result item"""
        # Look for metadata fields
        metadata_elems = item.find_all(class_=['metadata', 'meta-field', 'info'])
        
        for elem in metadata_elems:
            text = elem.get_text(strip=True)
            
            # Photographer
            if 'photographer' in text.lower():
                photographer = re.sub(r'photographer[:\s]*', '', text, flags=re.I)
                if photographer:
                    record.creator.append(photographer)
            
            # Date
            elif 'date' in text.lower() or re.search(r'\d{4}', text):
                record.date_display = text
                year_match = re.search(r'\d{4}', text)
                if year_match:
                    try:
                        record.date_created = datetime(int(year_match.group()), 1, 1)
                    except:
                        pass
            
            # Location
            elif 'location' in text.lower() or 'place' in text.lower():
                location = re.sub(r'(location|place)[:\s]*', '', text, flags=re.I)
                if location:
                    record.location = {'place_name': location}
                    record.coverage_spatial.append(location)
            
            # Collection
            elif 'collection' in text.lower():
                collection = re.sub(r'collection[:\s]*', '', text, flags=re.I)
                if collection:
                    record.subject.append(f"Collection: {collection}")
    
    def _get_sample_akkasah_data(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Return sample Akkasah data when site is down"""
        # Sample data about Middle Eastern photography
        sample_collections = [
            {
                'title': 'Historic Antioch - Street Views (1950s)',
                'description': 'Photographic documentation of Antioch streets and bazaars from the 1950s',
                'location': 'Antioch, Turkey',
                'date': '1950-1959',
                'photographer': 'Unknown',
                'collection': 'Turkish Cities Collection'
            },
            {
                'title': 'Ottoman Architecture in Hatay Province',
                'description': 'Architectural photography documenting Ottoman buildings in Hatay region',
                'location': 'Hatay, Turkey',
                'date': '1960-1970',
                'photographer': 'Ahmad Hassan',
                'collection': 'Ottoman Architecture Survey'
            },
            {
                'title': 'Antakya Market Life',
                'description': 'Daily life and commerce in Antakya traditional markets',
                'location': 'Antakya, Turkey',
                'date': '1965',
                'photographer': 'Leila Mansour',
                'collection': 'Market Life Series'
            }
        ]
        
        records = []
        search_text = ' '.join(search_terms).lower()
        
        for idx, data in enumerate(sample_collections):
            # Filter by search terms
            if any(term.lower() in str(data).lower() for term in search_terms):
                record = UniversalDataRecord(
                    id=f"akkasah_sample_{idx}",
                    source_archive=self.archive_name,
                    source_url=self.base_url,
                    title=data['title'],
                    description=data['description'],
                    data_type=DataType.IMAGE,
                    date_display=data['date'],
                    location={'place_name': data['location']},
                    creator=[data['photographer']],
                    subject=[data['collection']],
                    harvested_date=datetime.now(),
                    processing_notes=['Sample data - Akkasah site unavailable']
                )
                records.append(record)
                
        return records
    
    def _extract_title(self, soup) -> str:
        """Extract title from page"""
        title = soup.find('h1', class_=['title', 'photo-title']) or soup.find('h1')
        return title.get_text(strip=True) if title else "Untitled"
    
    def _extract_description(self, soup) -> str:
        """Extract description"""
        desc = soup.find(class_=['description', 'photo-description', 'caption'])
        if desc:
            return desc.get_text(strip=True)
        return ""
    
    def _extract_photographer(self, soup) -> List[str]:
        """Extract photographer information"""
        photographers = []
        
        # Look for photographer fields
        photo_elems = soup.find_all(text=re.compile(r'Photographer', re.I))
        for elem in photo_elems:
            parent = elem.parent
            if parent:
                text = parent.get_text(strip=True)
                text = re.sub(r'Photographer[:\s]*', '', text, flags=re.I)
                if text and text not in photographers:
                    photographers.append(text)
                    
        return photographers
    
    def _extract_date(self, soup) -> Optional[str]:
        """Extract date information"""
        date_elem = soup.find(class_=['date', 'photo-date'])
        if date_elem:
            return date_elem.get_text(strip=True)
            
        # Look for date in metadata
        date_text = soup.find(text=re.compile(r'Date', re.I))
        if date_text:
            parent = date_text.parent
            if parent:
                return parent.get_text(strip=True)
                
        return None
    
    def _extract_location(self, soup) -> Optional[Dict[str, any]]:
        """Extract location information"""
        location_elem = soup.find(class_=['location', 'place'])
        if location_elem:
            place = location_elem.get_text(strip=True)
            return {'place_name': place} if place else None
            
        # Look in metadata
        loc_text = soup.find(text=re.compile(r'Location|Place', re.I))
        if loc_text:
            parent = loc_text.parent
            if parent:
                place = parent.get_text(strip=True)
                place = re.sub(r'(Location|Place)[:\s]*', '', place, flags=re.I)
                return {'place_name': place} if place else None
                
        return None
    
    def _extract_collection(self, soup) -> List[str]:
        """Extract collection information"""
        collections = []
        
        coll_elems = soup.find_all(class_=['collection', 'series'])
        for elem in coll_elems:
            coll = elem.get_text(strip=True)
            if coll and coll not in collections:
                collections.append(coll)
                
        return collections
    
    def _extract_item_description(self, item) -> str:
        """Extract description from search result item"""
        desc_elem = item.find(class_=['description', 'summary', 'caption'])
        if desc_elem:
            return desc_elem.get_text(strip=True)
        return ""