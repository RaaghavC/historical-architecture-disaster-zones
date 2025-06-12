"""
Generic scraper for unknown archive types.
"""
import hashlib
import logging
from typing import Dict, List
from urllib.parse import urljoin, urlparse

from ..universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType
from .extractors import ImageExtractor, TextExtractor, PDFExtractor, ManuscriptExtractor

logger = logging.getLogger(__name__)


class GenericArchiveScraper(UniversalArchiveScraper):
    """Generic scraper that can handle any website."""
    
    def __init__(self, archive_name: str = "Unknown Archive", base_url: str = ""):
        if not base_url:
            raise ValueError("Base URL is required for generic scraper")
        
        # Extract domain name if archive name not provided
        if archive_name == "Unknown Archive":
            parsed = urlparse(base_url)
            archive_name = parsed.netloc.replace('www.', '')
            
        super().__init__(archive_name, base_url)
        
    def _register_extractors(self) -> Dict[str, any]:
        """Register all available extractors."""
        return {
            'image': ImageExtractor(),
            'text': TextExtractor(),
            'pdf': PDFExtractor(),
            'manuscript': ManuscriptExtractor()
        }
    
    def _scrape_search(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Generic search not implemented - scrape URL instead."""
        logger.warning(f"Search not implemented for {self.archive_name}. Use scrape(url=...) instead.")
        return []
    
    def _scrape_url(self, url: str) -> List[UniversalDataRecord]:
        """Scrape any URL and extract all possible data."""
        logger.info(f"Generic scraping of: {url}")
        records = []
        
        try:
            html = self._fetch_content(url)
            soup = self._get_soup(html)
            
            # Extract page title as context
            page_title = soup.find('title')
            page_title_text = page_title.get_text(strip=True) if page_title else ""
            
            # Extract all images
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if not src or src.startswith('data:'):  # Skip data URLs
                    continue
                    
                record = self._create_image_record(img, url, page_title_text)
                if record:
                    records.append(record)
            
            # Extract all PDFs
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.pdf' in href.lower():
                    record = self._create_pdf_record(link, url)
                    if record:
                        records.append(record)
            
            # Look for gallery or collection structures
            gallery_selectors = [
                '.gallery', '.image-gallery', '.photo-gallery',
                '.collection', '.grid', '.masonry',
                '[class*="gallery"]', '[class*="collection"]'
            ]
            
            for selector in gallery_selectors:
                galleries = soup.select(selector)
                for gallery in galleries:
                    gallery_records = self._extract_from_gallery(gallery, url)
                    records.extend(gallery_records)
            
            # Remove duplicates based on download URL
            seen_urls = set()
            unique_records = []
            for record in records:
                if record.download_url and record.download_url not in seen_urls:
                    seen_urls.add(record.download_url)
                    unique_records.append(record)
                elif not record.download_url:
                    unique_records.append(record)
                    
            logger.info(f"Extracted {len(unique_records)} records from {url}")
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            
        return unique_records
    
    def _create_image_record(self, img_element, page_url: str, page_title: str) -> UniversalDataRecord:
        """Create record from image element."""
        img_data = self.data_extractors['image'].extract(img_element, {'base_url': page_url})
        
        if not img_data.get('download_url'):
            return None
            
        record = UniversalDataRecord(
            id=hashlib.md5(img_data['download_url'].encode()).hexdigest(),
            source_archive=self.archive_name,
            source_url=page_url,
            data_type=img_data.get('data_type', DataType.IMAGE),
            download_url=img_data['download_url'],
            thumbnail_url=img_data.get('thumbnail_url', img_data['download_url']),
            title=img_data.get('title', '') or page_title,
            description=img_data.get('description', ''),
            mime_type=img_data.get('mime_type', 'image/jpeg')
        )
        
        if img_data.get('dimensions'):
            record.dimensions = img_data['dimensions']
            
        return record
    
    def _create_pdf_record(self, link_element, page_url: str) -> UniversalDataRecord:
        """Create record from PDF link."""
        pdf_data = self.data_extractors['pdf'].extract(link_element, {'base_url': page_url})
        
        if not pdf_data.get('download_url'):
            return None
            
        record = UniversalDataRecord(
            id=hashlib.md5(pdf_data['download_url'].encode()).hexdigest(),
            source_archive=self.archive_name,
            source_url=page_url,
            data_type=DataType.PDF,
            download_url=pdf_data['download_url'],
            title=pdf_data.get('title', 'PDF Document'),
            mime_type='application/pdf'
        )
        
        if pdf_data.get('file_size'):
            record.file_size = pdf_data['file_size']
            
        return record
    
    def _extract_from_gallery(self, gallery_element, page_url: str) -> List[UniversalDataRecord]:
        """Extract records from gallery-like structures."""
        records = []
        
        # Look for images in gallery
        for img in gallery_element.find_all('img'):
            record = self._create_image_record(img, page_url, "Gallery Image")
            if record:
                # Try to extract caption from gallery structure
                parent = img.parent
                while parent and parent != gallery_element:
                    caption_elem = parent.find(['figcaption', 'div', 'p'])
                    if caption_elem and caption_elem.get_text(strip=True):
                        record.description = caption_elem.get_text(strip=True)
                        break
                    parent = parent.parent
                    
                records.append(record)
                
        return records