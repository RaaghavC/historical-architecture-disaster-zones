"""
ArchNet archive scraper implementation.
"""
import hashlib
import logging
from typing import Dict, List
from urllib.parse import urljoin, quote

from bs4 import BeautifulSoup

from ..universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType
from .extractors import ImageExtractor, TextExtractor, ManuscriptExtractor, PDFExtractor

logger = logging.getLogger(__name__)


class ArchNetUniversalScraper(UniversalArchiveScraper):
    """ArchNet specific implementation."""
    
    def __init__(self):
        super().__init__("ArchNet", "https://www.archnet.org")
        
    def _register_extractors(self) -> Dict[str, any]:
        """Register extractors for ArchNet content."""
        return {
            'image': ImageExtractor(),
            'text': TextExtractor(),
            'manuscript': ManuscriptExtractor(),
            'pdf': PDFExtractor()
        }
    
    def _scrape_search(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Search ArchNet for terms."""
        records = []
        
        for term in search_terms:
            logger.info(f"Searching ArchNet for: {term}")
            
            # Use their search endpoint
            search_url = f"{self.base_url}/search/site/{quote(term)}"
            
            try:
                html = self._fetch_content(search_url)
                soup = self._get_soup(html)
                
                # Extract search results
                results = self._extract_search_results(soup)
                
                # Get details for each result
                for result_url in results[:10]:  # Limit to first 10 for testing
                    try:
                        record = self._scrape_item_detail(result_url)
                        if record:
                            records.append(record)
                    except Exception as e:
                        logger.error(f"Error scraping {result_url}: {e}")
                        
            except Exception as e:
                logger.error(f"Error searching for {term}: {e}")
                
        return records
    
    def _extract_search_results(self, soup: BeautifulSoup) -> List[str]:
        """Extract URLs from search results page."""
        urls = []
        
        # Look for search result items
        for link in soup.select('a.search-result-link, h3.search-result-title a, .views-row a'):
            href = link.get('href', '')
            if href and '/sites/' in href:  # Filter for site pages
                full_url = urljoin(self.base_url, href)
                urls.append(full_url)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
                
        return unique_urls
    
    def _scrape_item_detail(self, url: str) -> UniversalDataRecord:
        """Extract detailed item data from ArchNet site page."""
        logger.info(f"Scraping ArchNet item: {url}")
        
        html = self._fetch_content(url)
        soup = self._get_soup(html)
        
        # Initialize record
        record = UniversalDataRecord(
            id=hashlib.md5(url.encode()).hexdigest(),
            source_archive=self.archive_name,
            source_url=url
        )
        
        # Extract title
        title_elem = soup.select_one('h1.page-title, h1.site-title, h1')
        if title_elem:
            record.title = title_elem.get_text(strip=True)
        
        # Extract description
        desc_elem = soup.select_one('.field-name-body, .site-description, .description')
        if desc_elem:
            record.description = desc_elem.get_text(strip=True)[:1000]
        
        # Extract metadata from various fields
        self._extract_metadata_fields(soup, record)
        
        # Extract images
        images = self._extract_images(soup)
        if images:
            # First image as thumbnail
            record.thumbnail_url = images[0].get('download_url')
            record.data_type = DataType.IMAGE
            
            # Store all images in raw metadata
            record.raw_metadata['images'] = images
        
        # Extract geographic data
        self._extract_location(soup, record)
        
        # Extract temporal data
        self._extract_dates(soup, record)
        
        return record
    
    def _extract_metadata_fields(self, soup: BeautifulSoup, record: UniversalDataRecord):
        """Extract structured metadata fields."""
        # Common ArchNet field patterns
        field_mappings = {
            'architect': 'creator',
            'patron': 'contributor',
            'style': 'subject',
            'period': 'subject',
            'materials': 'keywords',
            'building-type': 'subject',
            'dynasty': 'subject'
        }
        
        for field_class, record_field in field_mappings.items():
            elements = soup.select(f'.field-name-field-{field_class} .field-item')
            for elem in elements:
                value = elem.get_text(strip=True)
                if value:
                    if record_field in ['creator', 'contributor', 'subject', 'keywords']:
                        getattr(record, record_field).append(value)
                    else:
                        setattr(record, record_field, value)
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all images from the page."""
        images = []
        
        # Look for image galleries
        for img in soup.select('.field-name-field-images img, .image-gallery img, .views-field-field-images img'):
            img_data = self.data_extractors['image'].extract(img, {'base_url': self.base_url})
            if img_data.get('download_url'):
                images.append(img_data)
        
        # Also check for linked images
        for link in soup.select('a[href*="/image/"], a[href$=".jpg"], a[href$=".jpeg"]'):
            if link.find('img'):  # Has thumbnail
                img = link.find('img')
                img_data = self.data_extractors['image'].extract(img, {'base_url': self.base_url})
                # Use link href as full resolution
                img_data['download_url'] = urljoin(self.base_url, link['href'])
                images.append(img_data)
        
        return images
    
    def _extract_location(self, soup: BeautifulSoup, record: UniversalDataRecord):
        """Extract geographic information."""
        # Look for location fields
        location_elem = soup.select_one('.field-name-field-location, .location-field')
        if location_elem:
            location_text = location_elem.get_text(strip=True)
            record.location = {'place_name': location_text}
            record.coverage_spatial.append(location_text)
        
        # Look for country/region
        country_elem = soup.select_one('.field-name-field-site-country .field-item')
        if country_elem:
            country = country_elem.get_text(strip=True)
            if not record.location:
                record.location = {}
            record.location['country'] = country
            record.coverage_spatial.append(country)
        
        # Look for coordinates (if available)
        coords_elem = soup.select_one('.field-name-field-coordinates, .coordinates')
        if coords_elem:
            coords_text = coords_elem.get_text(strip=True)
            # Try to parse coordinates
            import re
            coord_match = re.search(r'([-\d.]+)[,\s]+([-\d.]+)', coords_text)
            if coord_match:
                if not record.location:
                    record.location = {}
                record.location['lat'] = float(coord_match.group(1))
                record.location['lon'] = float(coord_match.group(2))
    
    def _extract_dates(self, soup: BeautifulSoup, record: UniversalDataRecord):
        """Extract temporal information."""
        # Look for date fields
        date_selectors = [
            '.field-name-field-site-date',
            '.field-name-field-construction-date',
            '.date-field',
            '.field-name-field-period'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                temporal_data = self._extract_temporal_data(date_text)
                
                if temporal_data.get('date_created'):
                    record.date_created = temporal_data['date_created']
                if temporal_data.get('date_range_start'):
                    record.date_range_start = temporal_data['date_range_start']
                if temporal_data.get('date_range_end'):
                    record.date_range_end = temporal_data['date_range_end']
                if temporal_data.get('date_uncertainty'):
                    record.date_uncertainty = temporal_data['date_uncertainty']
                    
                break  # Use first date found