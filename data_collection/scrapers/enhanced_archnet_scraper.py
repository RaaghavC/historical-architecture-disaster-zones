"""
Enhanced ArchNet scraper with better data extraction.
"""
import hashlib
import logging
import re
from typing import Dict, List
from urllib.parse import urljoin, quote
import json

from bs4 import BeautifulSoup

from ..universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType
from .extractors import ImageExtractor, TextExtractor, ManuscriptExtractor, PDFExtractor

logger = logging.getLogger(__name__)


class EnhancedArchNetScraper(UniversalArchiveScraper):
    """Enhanced ArchNet scraper with comprehensive data extraction."""
    
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
        """Search ArchNet using their actual search interface."""
        records = []
        
        for term in search_terms:
            logger.info(f"Searching ArchNet for: {term}")
            
            # Use the actual search page
            search_url = f"{self.base_url}/search?search_api_fulltext={quote(term)}"
            
            try:
                html = self._fetch_content(search_url)
                soup = self._get_soup(html)
                
                # Extract search results - ArchNet uses specific classes
                results = []
                
                # Look for search result items with various possible selectors
                for selector in ['.search-result', '.views-row', '.node-teaser', 'article']:
                    items = soup.select(selector)
                    for item in items:
                        # Find links to sites
                        links = item.select('a[href*="/sites/"], h2 a, h3 a, .title a')
                        for link in links:
                            href = link.get('href', '')
                            if '/sites/' in href:
                                full_url = urljoin(self.base_url, href)
                                if full_url not in results:
                                    results.append(full_url)
                
                logger.info(f"Found {len(results)} results for {term}")
                
                # Get details for each result
                for result_url in results[:5]:  # Limit for testing
                    try:
                        record = self._scrape_item_detail(result_url)
                        if record:
                            records.append(record)
                    except Exception as e:
                        logger.error(f"Error scraping {result_url}: {e}")
                        
            except Exception as e:
                logger.error(f"Error searching for {term}: {e}")
                
        return records
    
    def _scrape_url(self, url: str) -> List[UniversalDataRecord]:
        """Override to handle ArchNet URLs properly."""
        if '/sites/' in url:
            # This is a site detail page
            record = self._scrape_item_detail(url)
            return [record] if record else []
        else:
            # Use generic extraction
            return super()._scrape_url(url)
    
    def _scrape_item_detail(self, url: str) -> UniversalDataRecord:
        """Extract comprehensive data from ArchNet site page."""
        logger.info(f"Scraping ArchNet item: {url}")
        
        html = self._fetch_content(url)
        soup = self._get_soup(html)
        
        # Initialize record
        record = UniversalDataRecord(
            id=hashlib.md5(url.encode()).hexdigest(),
            source_archive=self.archive_name,
            source_url=url
        )
        
        # Extract title - multiple possible selectors
        for selector in ['h1.page-header', 'h1.page-title', 'h1.site-name', 'h1', '.field-name-title']:
            title_elem = soup.select_one(selector)
            if title_elem:
                record.title = title_elem.get_text(strip=True)
                break
        
        # Extract description - look in multiple places
        desc_selectors = [
            '.field-name-body .field-item',
            '.field-name-field-description',
            '.site-description',
            '.content .field-item',
            'div[property="content:encoded"]'
        ]
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                record.description = desc_elem.get_text(strip=True)
                break
        
        # Extract all metadata fields
        self._extract_comprehensive_metadata(soup, record)
        
        # Extract images with metadata
        images = self._extract_all_images(soup)
        if images:
            record.data_type = DataType.IMAGE
            record.thumbnail_url = images[0].get('thumbnail_url', images[0].get('download_url'))
            record.raw_metadata['images'] = images
            
            # If we have multiple images, create additional records
            image_records = []
            for i, img in enumerate(images):
                if i == 0:
                    # First image updates main record
                    record.download_url = img.get('download_url')
                else:
                    # Additional images as separate records
                    img_record = UniversalDataRecord(
                        id=hashlib.md5(img.get('download_url', '').encode()).hexdigest(),
                        source_archive=self.archive_name,
                        source_url=url,
                        title=f"{record.title} - Image {i+1}",
                        description=img.get('caption', record.description),
                        data_type=DataType.IMAGE,
                        download_url=img.get('download_url'),
                        thumbnail_url=img.get('thumbnail_url'),
                        location=record.location,
                        date_created=record.date_created,
                        creator=record.creator,
                        subject=record.subject
                    )
                    image_records.append(img_record)
            
            # Return main record plus image records
            return [record] + image_records
        
        return record
    
    def _extract_comprehensive_metadata(self, soup: BeautifulSoup, record: UniversalDataRecord):
        """Extract all available metadata fields."""
        
        # Field mappings for ArchNet
        field_mappings = {
            # Creators and contributors
            'architect': ('creator', 'Architect'),
            'field-architect': ('creator', 'Architect'),
            'patron': ('contributor', 'Patron'),
            'field-patron': ('contributor', 'Patron'),
            'client': ('contributor', 'Client'),
            'field-client': ('contributor', 'Client'),
            'calligrapher': ('creator', 'Calligrapher'),
            
            # Subject and keywords
            'style': ('subject', 'Style'),
            'field-style': ('subject', 'Style'),
            'period': ('subject', 'Period'),
            'field-period': ('subject', 'Period'),
            'dynasty': ('subject', 'Dynasty'),
            'field-dynasty': ('subject', 'Dynasty'),
            'building-type': ('subject', 'Building Type'),
            'field-building-type': ('subject', 'Building Type'),
            'materials': ('keywords', 'Materials'),
            'field-materials': ('keywords', 'Materials'),
            
            # Location
            'location': ('location', 'Location'),
            'field-location': ('location', 'Location'),
            'field-site-location': ('location', 'Location'),
            'field-country': ('location', 'Country'),
            'field-region': ('location', 'Region'),
            'field-city': ('location', 'City'),
        }
        
        # Extract fields
        for field_class, (record_field, label) in field_mappings.items():
            # Try multiple selectors
            selectors = [
                f'.field-name-{field_class} .field-item',
                f'.{field_class} .field-item',
                f'.field.{field_class}',
                f'div[class*="{field_class}"] .field-item'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for elem in elements:
                    value = elem.get_text(strip=True)
                    if value:
                        if record_field == 'creator':
                            record.creator.append(f"{value} ({label})")
                        elif record_field == 'contributor':
                            record.contributor.append(f"{value} ({label})")
                        elif record_field == 'subject':
                            record.subject.append(value)
                        elif record_field == 'keywords':
                            record.keywords.extend([v.strip() for v in value.split(',')])
                        elif record_field == 'location':
                            if not record.location:
                                record.location = {}
                            record.location[label.lower()] = value
                            record.coverage_spatial.append(value)
        
        # Extract dates
        self._extract_detailed_dates(soup, record)
        
        # Extract dimensions and measurements
        dimension_fields = soup.select('.field-name-field-dimensions .field-item, .dimensions')
        for dim in dimension_fields:
            dim_text = dim.get_text(strip=True)
            if not record.dimensions:
                record.dimensions = {}
            record.dimensions['text'] = dim_text
        
        # Extract inscription text
        inscription_fields = soup.select('.field-name-field-inscription .field-item')
        for inscription in inscription_fields:
            text = inscription.get_text(strip=True)
            if text:
                record.processing_notes.append(f"Inscription: {text}")
        
        # Extract bibliography/sources
        biblio_fields = soup.select('.field-name-field-bibliography .field-item, .bibliography')
        for bib in biblio_fields:
            text = bib.get_text(strip=True)
            if text:
                record.processing_notes.append(f"Source: {text}")
    
    def _extract_detailed_dates(self, soup: BeautifulSoup, record: UniversalDataRecord):
        """Extract detailed temporal information."""
        date_selectors = [
            '.field-name-field-construction-date',
            '.field-name-field-site-date',
            '.field-name-field-date',
            '.construction-date',
            '.date-display-single',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            date_elems = soup.select(selector)
            for elem in date_elems:
                # Check for datetime attribute
                if elem.name == 'time' and elem.get('datetime'):
                    try:
                        from datetime import datetime
                        record.date_created = datetime.fromisoformat(elem['datetime'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # Extract text and parse
                date_text = elem.get_text(strip=True)
                if date_text:
                    temporal_data = self._extract_temporal_data(date_text)
                    
                    # Also look for AH (Islamic calendar) dates
                    ah_match = re.search(r'(\d+)\s*AH', date_text)
                    if ah_match:
                        record.processing_notes.append(f"Islamic date: {ah_match.group(0)}")
                    
                    # Update record with temporal data
                    for key, value in temporal_data.items():
                        if value and not getattr(record, key, None):
                            setattr(record, key, value)
    
    def _extract_all_images(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all images with comprehensive metadata."""
        images = []
        
        # Multiple strategies for finding images
        
        # 1. Look for image field containers
        image_containers = soup.select('.field-name-field-images .field-item, .field-type-image .field-item')
        for container in image_containers:
            img = container.find('img')
            if img:
                img_data = self._process_image(img, container)
                if img_data:
                    images.append(img_data)
        
        # 2. Look for gallery images
        gallery_images = soup.select('.image-gallery img, .gallery-item img, .views-field-field-images img')
        for img in gallery_images:
            img_data = self._process_image(img, img.parent)
            if img_data:
                images.append(img_data)
        
        # 3. Look for linked images
        image_links = soup.select('a[href*="/media/"], a[href$=".jpg"], a[href$=".jpeg"], a[href$=".png"]')
        for link in image_links:
            img = link.find('img')
            if img:
                img_data = self._process_image(img, link)
                # Use link href as full resolution
                img_data['download_url'] = urljoin(self.base_url, link['href'])
                images.append(img_data)
        
        # 4. Look for figure elements
        figures = soup.select('figure')
        for figure in figures:
            img = figure.find('img')
            if img:
                img_data = self._process_image(img, figure)
                
                # Extract caption
                figcaption = figure.find('figcaption')
                if figcaption:
                    img_data['caption'] = figcaption.get_text(strip=True)
                
                images.append(img_data)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_images = []
        for img in images:
            url = img.get('download_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_images.append(img)
        
        return unique_images
    
    def _process_image(self, img_element, container=None):
        """Process an image element to extract all metadata."""
        img_data = self.data_extractors['image'].extract(img_element, {'base_url': self.base_url})
        
        if not img_data.get('download_url'):
            return None
        
        # Look for high-res version
        if container:
            # Check data attributes
            for attr in ['data-large', 'data-full', 'data-original']:
                if container.get(attr):
                    img_data['download_url'] = urljoin(self.base_url, container[attr])
                    break
        
        # Extract caption from various sources
        if container and not img_data.get('caption'):
            # Look for caption in sibling elements
            caption_selectors = ['.caption', '.image-caption', '.field-caption', 'figcaption']
            for selector in caption_selectors:
                caption = container.select_one(selector)
                if caption:
                    img_data['caption'] = caption.get_text(strip=True)
                    break
        
        # Generate thumbnail URL if not present
        if not img_data.get('thumbnail_url'):
            img_data['thumbnail_url'] = img_data['download_url']
        
        return img_data