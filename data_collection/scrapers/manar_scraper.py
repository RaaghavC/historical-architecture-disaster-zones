"""
Manar al-Athar (Oxford) archive scraper implementation.
"""
import hashlib
import logging
from typing import Dict, List
from urllib.parse import urljoin, quote

from ..universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType
from .extractors import ImageExtractor, TextExtractor, ManuscriptExtractor

logger = logging.getLogger(__name__)


class ManarAlAtharScraper(UniversalArchiveScraper):
    """Oxford Manar al-Athar scraper for Islamic archaeology."""
    
    def __init__(self):
        super().__init__("Manar al-Athar", "https://www.manar-al-athar.ox.ac.uk")
        self.requires_login = False  # Start without login
        
    def _register_extractors(self) -> Dict[str, any]:
        """Register extractors for Manar content."""
        return {
            'image': ImageExtractor(),
            'text': TextExtractor(),
            'manuscript': ManuscriptExtractor()
        }
    
    def _scrape_search(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Search Manar al-Athar with geographic focus."""
        records = []
        
        # First try direct search
        for term in search_terms:
            logger.info(f"Searching Manar al-Athar for: {term}")
            
            search_url = f"{self.base_url}/pages/search.php?search={quote(term)}"
            
            try:
                html = self._fetch_content(search_url)
                soup = self._get_soup(html)
                
                # Extract search results
                image_links = self._extract_search_results(soup)
                
                for img_url in image_links[:10]:  # Limit for testing
                    try:
                        record = self._create_record_from_result(img_url, soup)
                        if record:
                            records.append(record)
                    except Exception as e:
                        logger.error(f"Error processing result {img_url}: {e}")
                        
            except Exception as e:
                logger.error(f"Error searching for {term}: {e}")
        
        # Also try browsing Turkey/Hatay region for Antakya content
        try:
            records.extend(self._browse_geographic_region())
        except Exception as e:
            logger.error(f"Error browsing geographic region: {e}")
            
        return records
    
    def _browse_geographic_region(self) -> List[UniversalDataRecord]:
        """Browse Turkey → Hatay region specifically."""
        records = []
        
        # Navigate to collections page
        browse_url = f"{self.base_url}/pages/collections_featured.php"
        
        try:
            html = self._fetch_content(browse_url)
            soup = self._get_soup(html)
            
            # Look for Turkey/Hatay links
            for link in soup.select('a'):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if 'Turkey' in text or 'Hatay' in text or 'Antioch' in text:
                    collection_url = urljoin(self.base_url, href)
                    records.extend(self._scrape_collection(collection_url))
                    
        except Exception as e:
            logger.error(f"Error browsing collections: {e}")
            
        return records
    
    def _scrape_collection(self, collection_url: str) -> List[UniversalDataRecord]:
        """Scrape a specific collection page."""
        records = []
        
        try:
            html = self._fetch_content(collection_url)
            soup = self._get_soup(html)
            
            # Extract all images in collection
            for img in soup.select('img.ResourceThumbnail, img[src*="/thumbnail/"]'):
                record = self._create_record_from_image(img, collection_url)
                if record:
                    records.append(record)
                    
        except Exception as e:
            logger.error(f"Error scraping collection {collection_url}: {e}")
            
        return records
    
    def _extract_search_results(self, soup) -> List[str]:
        """Extract image URLs from search results."""
        urls = []
        
        # Look for result thumbnails
        for img in soup.select('img.ResourceThumbnail, div.ResourcePanel img'):
            src = img.get('src', '')
            if src:
                # Convert thumbnail to full size
                full_url = src.replace('/thumbnail/', '/full/')
                urls.append(urljoin(self.base_url, full_url))
                
        return urls
    
    def _create_record_from_result(self, img_url: str, soup) -> UniversalDataRecord:
        """Create record from search result."""
        record = UniversalDataRecord(
            id=hashlib.md5(img_url.encode()).hexdigest(),
            source_archive=self.archive_name,
            source_url=img_url,
            data_type=DataType.IMAGE,
            download_url=img_url,
            thumbnail_url=img_url.replace('/full/', '/thumbnail/')
        )
        
        # Try to extract metadata from surrounding context
        # This is simplified - in reality would need more sophisticated extraction
        record.title = "Manar al-Athar Archaeological Image"
        
        return record
    
    def _create_record_from_image(self, img_element, page_url: str) -> UniversalDataRecord:
        """Create record from image element with metadata extraction."""
        img_data = self.data_extractors['image'].extract(img_element, {'base_url': self.base_url})
        
        record = UniversalDataRecord(
            id=hashlib.md5(img_data.get('download_url', '').encode()).hexdigest(),
            source_archive=self.archive_name,
            source_url=page_url,
            data_type=img_data.get('data_type', DataType.IMAGE),
            download_url=img_data.get('download_url'),
            thumbnail_url=img_data.get('download_url', '').replace('/full/', '/thumbnail/'),
            title=img_data.get('title', ''),
            description=img_data.get('description', '')
        )
        
        # Extract additional metadata from parent elements
        parent = img_element.parent
        if parent:
            # Look for caption or metadata
            caption = parent.find('div', class_='ResourcePanelInfo')
            if caption:
                metadata_text = caption.get_text(strip=True)
                
                # Extract location
                if 'Turkey' in metadata_text or 'Hatay' in metadata_text:
                    record.coverage_spatial.append('Turkey')
                    record.location = {'country': 'Turkey', 'region': 'Hatay'}
                
                # Extract date if present
                temporal_data = self._extract_temporal_data(metadata_text)
                if temporal_data:
                    record.date_created = temporal_data.get('date_created')
                    record.date_uncertainty = temporal_data.get('date_uncertainty')
                    
        return record