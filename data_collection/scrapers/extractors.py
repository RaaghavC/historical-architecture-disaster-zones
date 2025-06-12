"""
Data extractors for different content types.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import re
import logging

from bs4 import BeautifulSoup, Tag
from langdetect import detect_langs, LangDetectException

from ..universal_scraper import DataType

logger = logging.getLogger(__name__)


class DataExtractor(ABC):
    """Base class for data extractors."""
    
    @abstractmethod
    def can_extract(self, element: Any) -> bool:
        """Check if this extractor can handle the element."""
        pass
    
    @abstractmethod
    def extract(self, element: Any, context: Dict) -> Dict[str, Any]:
        """Extract data from element."""
        pass


class ImageExtractor(DataExtractor):
    """Extract image data including detection of handwritten content."""
    
    def __init__(self):
        self.handwritten_indicators = [
            'manuscript', 'handwritten', 'autograph', 'letter',
            'diary', 'notebook', 'inscription', 'graffiti',
            'calligraphy', 'خط', 'el yazması', 'مخطوط'
        ]
        
    def can_extract(self, element: Any) -> bool:
        """Check if element is an image."""
        if isinstance(element, Tag) and element.name == 'img':
            return True
        if isinstance(element, str):
            return any(ext in element.lower() 
                      for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp'])
        return False
    
    def extract(self, element: Any, context: Dict) -> Dict[str, Any]:
        """Extract comprehensive image metadata."""
        data = {
            'data_type': DataType.IMAGE,
            'mime_type': 'image/jpeg'  # Will be updated based on URL
        }
        
        base_url = context.get('base_url', '')
        
        if isinstance(element, Tag):
            # Extract image URL
            img_url = element.get('src') or element.get('data-src') or element.get('data-lazy-src', '')
            if img_url:
                data['download_url'] = urljoin(base_url, img_url)
                
                # Update mime type based on extension
                if '.png' in img_url.lower():
                    data['mime_type'] = 'image/png'
                elif '.tif' in img_url.lower():
                    data['mime_type'] = 'image/tiff'
                elif '.webp' in img_url.lower():
                    data['mime_type'] = 'image/webp'
            
            # Extract alt text and title
            data['title'] = element.get('alt', '')
            data['description'] = element.get('title', '')
            
            # Look for high-resolution versions
            parent = element.parent
            if parent and parent.name == 'a':
                href = parent.get('href', '')
                if href and any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.tif']):
                    data['download_url'] = urljoin(base_url, href)
            
            # Look for captions
            caption = self._extract_caption(element)
            if caption:
                data['description'] = caption
            
            # Check if handwritten
            combined_text = f"{data.get('title', '')} {data.get('description', '')}".lower()
            if self._is_handwritten(combined_text):
                data['data_type'] = DataType.HANDWRITTEN
            
            # Extract dimensions if available
            width = element.get('width')
            height = element.get('height')
            if width and height:
                data['dimensions'] = {
                    'width': int(width) if width.isdigit() else width,
                    'height': int(height) if height.isdigit() else height
                }
        
        return data
    
    def _extract_caption(self, img_element: Tag) -> Optional[str]:
        """Extract caption from various HTML structures."""
        # Check for figure/figcaption structure
        figure = img_element.find_parent('figure')
        if figure:
            figcaption = figure.find('figcaption')
            if figcaption:
                return figcaption.get_text(strip=True)
        
        # Check for adjacent caption elements
        next_sibling = img_element.find_next_sibling()
        if next_sibling and next_sibling.name in ['p', 'div', 'span']:
            text = next_sibling.get_text(strip=True)
            if len(text) < 200:  # Likely a caption
                return text
        
        return None
    
    def _is_handwritten(self, text: str) -> bool:
        """Detect if image contains handwritten content."""
        return any(indicator in text for indicator in self.handwritten_indicators)


class TextExtractor(DataExtractor):
    """Extract textual content with language detection."""
    
    def can_extract(self, element: Any) -> bool:
        """Check if element contains text."""
        if isinstance(element, Tag):
            return element.name in ['p', 'div', 'span', 'article', 'section', 'td', 'li']
        return isinstance(element, str) and len(element.strip()) > 10
    
    def extract(self, element: Any, context: Dict) -> Dict[str, Any]:
        """Extract text with language detection."""
        data = {
            'data_type': DataType.TEXT,
            'mime_type': 'text/plain'
        }
        
        # Get text content
        if isinstance(element, Tag):
            text = element.get_text(strip=True)
        else:
            text = str(element).strip()
        
        data['description'] = text[:1000]  # First 1000 chars
        
        # Detect language
        if len(text) > 20:  # Need sufficient text for detection
            try:
                langs = detect_langs(text)
                data['language'] = [lang.lang for lang in langs if lang.prob > 0.5]
                
                # Detect script based on language
                if 'ar' in data['language']:
                    data['script'] = 'Arabic'
                elif 'tr' in data['language'] and any(c in text for c in 'ğışöüçĞİŞÖÜÇ'):
                    data['script'] = 'Ottoman Turkish' if context.get('historical', False) else 'Modern Turkish'
                elif 'el' in data['language']:
                    data['script'] = 'Greek'
                elif 'hy' in data['language']:
                    data['script'] = 'Armenian'
            except LangDetectException:
                data['language'] = ['unknown']
        
        return data


class ManuscriptExtractor(DataExtractor):
    """Special extractor for manuscripts and archival documents."""
    
    def __init__(self):
        self.manuscript_indicators = [
            'manuscript', 'codex', 'folio', 'recto', 'verso',
            'مخطوط', 'yazmalar', 'el yazması', 'varak',
            'parchment', 'vellum', 'papyrus'
        ]
        
        self.script_indicators = {
            'arabic': ['arabic', 'kufic', 'naskh', 'thuluth', 'عربي'],
            'ottoman': ['ottoman', 'osmanli', 'osmanlı', 'rika', 'divani'],
            'greek': ['greek', 'byzantine', 'ελληνικά'],
            'latin': ['latin', 'roman', 'carolingian'],
            'armenian': ['armenian', 'հայերեն', 'bolorgir', 'notrgir'],
            'syriac': ['syriac', 'estrangelo', 'serto']
        }
    
    def can_extract(self, element: Any) -> bool:
        """Check if element refers to a manuscript."""
        text = str(element).lower()
        return any(indicator in text for indicator in self.manuscript_indicators)
    
    def extract(self, element: Any, context: Dict) -> Dict[str, Any]:
        """Extract manuscript-specific metadata."""
        data = {
            'data_type': DataType.MANUSCRIPT,
            'mime_type': 'image/jpeg'  # Usually scanned images
        }
        
        text = str(element)
        
        # Extract folio/page information
        folio_patterns = [
            r'fol(?:io)?\.?\s*(\d+[rv]?)',
            r'f\.?\s*(\d+[rv]?)',
            r'page\s*(\d+)',
            r'varak\s*(\d+[ab]?)'
        ]
        
        for pattern in folio_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['dimensions'] = {'folio': match.group(1)}
                break
        
        # Extract script type
        text_lower = text.lower()
        for script, indicators in self.script_indicators.items():
            if any(ind in text_lower for ind in indicators):
                data['script'] = script.title()
                break
        
        # Extract date if mentioned
        century_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*century', text, re.IGNORECASE)
        if century_match:
            century = int(century_match.group(1))
            data['date_range'] = f"{century}th century"
        
        # Look for catalog numbers
        catalog_patterns = [
            r'ms\.?\s*(\w+)',
            r'cod(?:ex)?\.?\s*(\w+)',
            r'nr\.?\s*(\d+)',
            r'inv(?:entory)?\.?\s*(\w+)'
        ]
        
        for pattern in catalog_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['catalog_number'] = match.group(1)
                break
        
        return data


class PDFExtractor(DataExtractor):
    """Extract PDF document metadata."""
    
    def can_extract(self, element: Any) -> bool:
        """Check if element is a PDF link."""
        if isinstance(element, Tag) and element.name == 'a':
            href = element.get('href', '').lower()
            return '.pdf' in href
        return isinstance(element, str) and '.pdf' in element.lower()
    
    def extract(self, element: Any, context: Dict) -> Dict[str, Any]:
        """Extract PDF metadata."""
        data = {
            'data_type': DataType.PDF,
            'mime_type': 'application/pdf'
        }
        
        if isinstance(element, Tag):
            # Get PDF URL
            pdf_url = element.get('href', '')
            data['download_url'] = urljoin(context.get('base_url', ''), pdf_url)
            
            # Get link text as title
            data['title'] = element.get_text(strip=True)
            
            # Look for file size
            text = str(element.parent) if element.parent else str(element)
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(KB|MB|GB)', text, re.IGNORECASE)
            if size_match:
                size_num = float(size_match.group(1))
                size_unit = size_match.group(2).upper()
                
                # Convert to bytes
                multipliers = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
                data['file_size'] = int(size_num * multipliers.get(size_unit, 1))
        
        return data


class MapExtractor(DataExtractor):
    """Extract map and cartographic material metadata."""
    
    def __init__(self):
        self.map_indicators = [
            'map', 'plan', 'chart', 'atlas', 'cartographic',
            'harita', 'plan', 'خريطة', 'χάρτης'
        ]
    
    def can_extract(self, element: Any) -> bool:
        """Check if element refers to a map."""
        text = str(element).lower()
        return any(indicator in text for indicator in self.map_indicators)
    
    def extract(self, element: Any, context: Dict) -> Dict[str, Any]:
        """Extract map-specific metadata."""
        data = {
            'data_type': DataType.MAP,
            'mime_type': 'image/jpeg'
        }
        
        text = str(element)
        
        # Extract scale if mentioned
        scale_match = re.search(r'1\s*:\s*([\d,]+)', text)
        if scale_match:
            data['scale'] = f"1:{scale_match.group(1)}"
        
        # Extract coverage area
        coverage_patterns = [
            r'covers?\s+(.+?)(?:\.|,|;|$)',
            r'shows?\s+(.+?)(?:\.|,|;|$)',
            r'depicting\s+(.+?)(?:\.|,|;|$)'
        ]
        
        for pattern in coverage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['coverage'] = match.group(1).strip()
                break
        
        return data