"""
SALT Research Archive Scraper
Turkish architectural photography and Ottoman archives
"""

from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import logging

from ..universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType

logger = logging.getLogger(__name__)


class SALTResearchScraper(UniversalArchiveScraper):
    """Scraper for SALT Research Istanbul archives"""
    
    def __init__(self):
        super().__init__("SALT Research")
        self.base_url = "https://saltresearch.org"
        self.search_url = "https://saltresearch.org/discovery/search"
        
    def _register_extractors(self) -> Dict[str, any]:
        """Register SALT-specific extractors"""
        return {
            'title': self._extract_title,
            'description': self._extract_description,
            'date': self._extract_date,
            'creator': self._extract_creator,
            'location': self._extract_location,
            'subjects': self._extract_subjects
        }
    
    def _scrape_search(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Search SALT Research archives"""
        records = []
        
        # SALT uses Primo discovery system
        params = {
            'query': 'any,contains,' + ' '.join(search_terms),
            'tab': 'default_tab',
            'search_scope': 'MyInst_and_CI',
            'vid': '90GARANTI_INST:90SALT_VU1',
            'lang': 'en',
            'offset': 0
        }
        
        try:
            response = self.session.get(self.search_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find result items
                results = soup.find_all('prm-brief-result-container')
                if not results:
                    # Try alternative selector
                    results = soup.select('.result-item-text')
                
                for result in results[:50]:  # Limit to 50 results
                    record = self._parse_result_item(result)
                    if record:
                        records.append(record)
                        
        except Exception as e:
            logger.error(f"Error searching SALT Research: {e}")
            
        logger.info(f"Found {len(records)} records from SALT Research")
        return records
    
    def _parse_result_item(self, item) -> Optional[UniversalDataRecord]:
        """Parse a single result item"""
        try:
            # Extract basic info
            title_elem = item.find('h3') or item.find('.item-title')
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            
            # Extract URL
            link = item.find('a', href=True)
            if link:
                url = link['href']
                if not url.startswith('http'):
                    url = self.base_url + url
            else:
                url = self.search_url
            
            # Create record
            record = UniversalDataRecord(
                id=self._generate_id(url),
                source_archive=self.archive_name,
                source_url=url,
                title=title,
                description=self._extract_description_from_item(item),
                data_type=DataType.IMAGE,  # SALT is primarily photographic
                harvested_date=datetime.now()
            )
            
            # Try to get more details
            if 'fulldisplay' in url:
                self._enrich_record_details(record, url)
                
            return record
            
        except Exception as e:
            logger.error(f"Error parsing SALT item: {e}")
            return None
    
    def _enrich_record_details(self, record: UniversalDataRecord, url: str):
        """Fetch and add detailed information"""
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract metadata fields
                metadata_fields = soup.select('.full-view-field')
                for field in metadata_fields:
                    label = field.find('.label')
                    value = field.find('.value')
                    if label and value:
                        self._process_metadata_field(
                            record, 
                            label.get_text(strip=True), 
                            value.get_text(strip=True)
                        )
                
                # Extract images
                images = soup.select('img.thumbnail, img.full-image')
                for img in images:
                    if 'src' in img.attrs:
                        img_url = img['src']
                        if not img_url.startswith('http'):
                            img_url = self.base_url + img_url
                        if 'thumbnail' in img.get('class', []):
                            record.thumbnail_url = img_url
                        else:
                            record.download_url = img_url
                            
        except Exception as e:
            logger.error(f"Error enriching SALT record: {e}")
    
    def _process_metadata_field(self, record: UniversalDataRecord, label: str, value: str):
        """Process metadata field based on label"""
        label_lower = label.lower()
        
        if 'date' in label_lower or 'year' in label_lower:
            record.date_display = value
            # Try to parse date
            if re.search(r'\d{4}', value):
                year = re.search(r'\d{4}', value).group()
                try:
                    record.date_created = datetime(int(year), 1, 1)
                except:
                    pass
                    
        elif 'creator' in label_lower or 'photographer' in label_lower:
            record.creator.append(value)
            
        elif 'location' in label_lower or 'place' in label_lower:
            record.location = {'place_name': value}
            record.coverage_spatial.append(value)
            
        elif 'subject' in label_lower:
            subjects = [s.strip() for s in value.split(';')]
            record.subject.extend(subjects)
            record.keywords.extend(subjects)
            
        elif 'description' in label_lower:
            record.description = value
            
        elif 'rights' in label_lower or 'license' in label_lower:
            record.rights = value
    
    def _extract_title(self, soup) -> str:
        """Extract title from page"""
        title = soup.find('h1', class_='title') or soup.find('h1')
        return title.get_text(strip=True) if title else "Untitled"
    
    def _extract_description(self, soup) -> str:
        """Extract description"""
        desc = soup.find('div', class_='description') or soup.find('meta', {'name': 'description'})
        if desc:
            return desc.get('content', '') if desc.name == 'meta' else desc.get_text(strip=True)
        return ""
    
    def _extract_date(self, soup) -> Optional[str]:
        """Extract date information"""
        date_elem = soup.find(text=re.compile(r'Date|Year', re.I))
        if date_elem:
            parent = date_elem.parent
            if parent:
                return parent.get_text(strip=True)
        return None
    
    def _extract_creator(self, soup) -> List[str]:
        """Extract creator/photographer"""
        creators = []
        creator_elems = soup.find_all(text=re.compile(r'Creator|Photographer|Author', re.I))
        for elem in creator_elems:
            parent = elem.parent
            if parent:
                text = parent.get_text(strip=True)
                # Clean up the text
                text = re.sub(r'(Creator|Photographer|Author)[:\s]*', '', text, flags=re.I)
                if text:
                    creators.append(text)
        return creators
    
    def _extract_location(self, soup) -> Optional[Dict[str, any]]:
        """Extract location information"""
        location_elem = soup.find(text=re.compile(r'Location|Place', re.I))
        if location_elem:
            parent = location_elem.parent
            if parent:
                place = parent.get_text(strip=True)
                place = re.sub(r'(Location|Place)[:\s]*', '', place, flags=re.I)
                if place:
                    return {'place_name': place}
        return None
    
    def _extract_subjects(self, soup) -> List[str]:
        """Extract subject terms"""
        subjects = []
        subject_elems = soup.find_all(text=re.compile(r'Subject', re.I))
        for elem in subject_elems:
            parent = elem.parent
            if parent:
                text = parent.get_text(strip=True)
                text = re.sub(r'Subject[:\s]*', '', text, flags=re.I)
                if text:
                    # Split by common delimiters
                    for subj in re.split(r'[;,]', text):
                        subj = subj.strip()
                        if subj:
                            subjects.append(subj)
        return subjects
    
    def _extract_description_from_item(self, item) -> str:
        """Extract description from search result item"""
        desc_elem = item.find('.item-description') or item.find('p')
        if desc_elem:
            return desc_elem.get_text(strip=True)
        return ""