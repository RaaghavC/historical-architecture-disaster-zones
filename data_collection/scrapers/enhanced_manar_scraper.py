"""
Enhanced Manar al-Athar scraper with better data extraction.
"""
import hashlib
import logging
import re
from typing import Dict, List
from urllib.parse import urljoin, quote, parse_qs, urlparse

from bs4 import BeautifulSoup

from ..universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType
from .extractors import ImageExtractor, TextExtractor, ManuscriptExtractor

logger = logging.getLogger(__name__)


class EnhancedManarScraper(UniversalArchiveScraper):
    """Enhanced Oxford Manar al-Athar scraper for Islamic archaeology."""
    
    def __init__(self):
        super().__init__("Manar al-Athar", "https://www.manar-al-athar.ox.ac.uk")
        self.requires_login = False
        
    def _register_extractors(self) -> Dict[str, any]:
        """Register extractors for Manar content."""
        return {
            'image': ImageExtractor(),
            'text': TextExtractor(),
            'manuscript': ManuscriptExtractor()
        }
    
    def _scrape_search(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Search Manar al-Athar with comprehensive extraction."""
        records = []
        
        for term in search_terms:
            logger.info(f"Searching Manar al-Athar for: {term}")
            
            # Use their search interface
            search_url = f"{self.base_url}/pages/search.php?search={quote(term)}&go=1&k=&restypes=1%2C2%2C3%2C4"
            
            try:
                html = self._fetch_content(search_url)
                soup = self._get_soup(html)
                
                # Extract search results
                results = self._extract_search_results(soup)
                logger.info(f"Found {len(results)} results for '{term}'")
                
                for result in results[:20]:  # Process up to 20 results
                    try:
                        record = self._create_detailed_record(result, soup)
                        if record:
                            records.append(record)
                    except Exception as e:
                        logger.error(f"Error processing result: {e}")
                        
            except Exception as e:
                logger.error(f"Error searching for {term}: {e}")
        
        # Also try geographic browsing for relevant regions
        records.extend(self._browse_geographic_regions(search_terms))
        
        return records
    
    def _browse_geographic_regions(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Browse specific geographic regions related to search terms."""
        records = []
        
        # Map search terms to geographic locations
        location_mapping = {
            'antakya': ['Turkey', 'Hatay', 'Antioch'],
            'antioch': ['Turkey', 'Hatay', 'Antakya'],
            'hatay': ['Turkey', 'Antakya', 'Antioch'],
            'syria': ['Syria', 'Damascus', 'Aleppo'],
            'ottoman': ['Turkey', 'Ottoman'],
            'byzantine': ['Byzantine', 'Constantinople']
        }
        
        locations_to_search = set()
        for term in search_terms:
            term_lower = term.lower()
            for key, values in location_mapping.items():
                if key in term_lower:
                    locations_to_search.update(values)
        
        # Browse collections by location
        for location in locations_to_search:
            try:
                browse_url = f"{self.base_url}/pages/search.php?search={quote(location)}&country={quote(location)}"
                records.extend(self._scrape_browse_page(browse_url))
            except Exception as e:
                logger.error(f"Error browsing {location}: {e}")
        
        return records
    
    def _extract_search_results(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract detailed information from search results."""
        results = []
        
        # Look for resource panels - Manar uses ResourcePanel divs
        resource_panels = soup.select('.ResourcePanel, .ResourcePanelSmall')
        
        for panel in resource_panels:
            result = {}
            
            # Extract image URL
            img = panel.select_one('img.ImageBorder, img')
            if img:
                # Get thumbnail URL
                thumb_url = img.get('src', '')
                if thumb_url:
                    result['thumbnail_url'] = urljoin(self.base_url, thumb_url)
                    
                    # Convert to full size URL
                    # Manar uses specific patterns for different sizes
                    full_url = thumb_url.replace('thm_', 'scr_').replace('pre_', 'scr_')
                    result['image_url'] = full_url
                
                # Get image ID from onclick or other attributes
                onclick = img.get('onclick', '')
                if 'load_modal' in onclick:
                    # Extract resource ID
                    match = re.search(r"load_modal\((\d+)", onclick)
                    if match:
                        result['resource_id'] = match.group(1)
            
            # Extract title/caption
            title_elem = panel.select_one('.ResourcePanelInfo, .ImageDisplay')
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
            
            # Extract metadata link
            metadata_link = panel.select_one('a[href*="view.php"]')
            if metadata_link:
                result['metadata_url'] = urljoin(self.base_url, metadata_link['href'])
            
            if result:
                results.append(result)
        
        return results
    
    def _create_detailed_record(self, result: Dict, search_soup: BeautifulSoup) -> UniversalDataRecord:
        """Create a detailed record with all available metadata."""
        # Create base record
        record = UniversalDataRecord(
            id=hashlib.md5(result.get('image_url', '').encode()).hexdigest(),
            source_archive=self.archive_name,
            source_url=result.get('metadata_url', result.get('image_url', '')),
            data_type=DataType.IMAGE,
            download_url=result.get('image_url'),
            thumbnail_url=result.get('thumbnail_url'),
            title=result.get('title', 'Manar al-Athar Image')
        )
        
        # Try to get detailed metadata if we have a metadata URL
        if result.get('metadata_url'):
            try:
                self._extract_detailed_metadata(result['metadata_url'], record)
            except Exception as e:
                logger.error(f"Error extracting detailed metadata: {e}")
        
        # Extract basic metadata from search result
        if result.get('title'):
            # Parse title for location and subject information
            title_parts = result['title'].split(',')
            if len(title_parts) > 1:
                # Often formatted as "Location, Monument, Details"
                record.coverage_spatial.extend([part.strip() for part in title_parts[:2]])
                
                # First part is often the location
                location_part = title_parts[0].strip()
                record.location = {'place_name': location_part}
                
                # Check for country names
                for country in ['Turkey', 'Syria', 'Jordan', 'Lebanon', 'Iraq', 'Iran']:
                    if country in result['title']:
                        record.location['country'] = country
                        break
        
        # Extract temporal information from title
        temporal_data = self._extract_temporal_data(result.get('title', ''))
        if temporal_data:
            for key, value in temporal_data.items():
                setattr(record, key, value)
        
        # Add processing notes
        if result.get('resource_id'):
            record.processing_notes.append(f"Manar Resource ID: {result['resource_id']}")
        
        return record
    
    def _extract_detailed_metadata(self, metadata_url: str, record: UniversalDataRecord):
        """Extract detailed metadata from the resource view page."""
        try:
            html = self._fetch_content(metadata_url)
            soup = self._get_soup(html)
            
            # Extract title
            title_elem = soup.select_one('h2, .Title')
            if title_elem:
                record.title = title_elem.get_text(strip=True)
            
            # Extract metadata table
            metadata_table = soup.select_one('table.RecordData, #metadatatable')
            if metadata_table:
                rows = metadata_table.select('tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map metadata fields
                        if 'date' in label:
                            temporal = self._extract_temporal_data(value)
                            if temporal.get('date_created'):
                                record.date_created = temporal['date_created']
                            if temporal.get('date_uncertainty'):
                                record.date_uncertainty = temporal['date_uncertainty']
                        
                        elif 'location' in label or 'place' in label:
                            if not record.location:
                                record.location = {}
                            record.location['place_name'] = value
                            record.coverage_spatial.append(value)
                        
                        elif 'country' in label:
                            if not record.location:
                                record.location = {}
                            record.location['country'] = value
                            record.coverage_spatial.append(value)
                        
                        elif 'photographer' in label or 'creator' in label:
                            record.creator.append(value)
                        
                        elif 'description' in label:
                            record.description = value
                        
                        elif 'subject' in label or 'monument' in label:
                            record.subject.append(value)
                        
                        elif 'material' in label:
                            record.keywords.append(value)
                        
                        elif 'rights' in label or 'copyright' in label:
                            record.rights = value
                        
                        elif 'collection' in label:
                            record.is_part_of = value
            
            # Extract larger image URL
            large_img = soup.select_one('img#PreviewImage, .Picture img')
            if large_img:
                img_url = large_img.get('src', '')
                if img_url:
                    full_url = urljoin(self.base_url, img_url)
                    # Try to get even larger version
                    record.download_url = full_url.replace('scr_', 'hpr_').replace('pre_', 'hpr_')
            
            # Extract related images
            related_images = soup.select('.RelatedResourcesBox img, .HorizontalSlidePanel img')
            related_urls = []
            for img in related_images:
                src = img.get('src', '')
                if src:
                    related_urls.append(urljoin(self.base_url, src))
            
            if related_urls:
                record.related_items = related_urls
                record.raw_metadata['related_images'] = related_urls
                
        except Exception as e:
            logger.error(f"Error fetching metadata from {metadata_url}: {e}")
    
    def _scrape_browse_page(self, browse_url: str) -> List[UniversalDataRecord]:
        """Scrape a browse/collection page."""
        records = []
        
        try:
            html = self._fetch_content(browse_url)
            soup = self._get_soup(html)
            
            # Extract results using same method as search
            results = self._extract_search_results(soup)
            
            for result in results:
                record = self._create_detailed_record(result, soup)
                if record:
                    records.append(record)
                    
        except Exception as e:
            logger.error(f"Error scraping browse page {browse_url}: {e}")
            
        return records