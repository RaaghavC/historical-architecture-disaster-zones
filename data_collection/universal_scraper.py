"""
Universal scraper base classes and data models for archive harvesting.
"""
from abc import ABC
from typing import Dict, List, Optional, Any, Union, Iterable
from enum import Enum
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, field
import json
import logging
from urllib.parse import urljoin, urlparse
import time

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from ratelimit import limits, sleep_and_retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Types of data that can be harvested from archives."""
    IMAGE = "image"
    TEXT = "text"
    HANDWRITTEN = "handwritten"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    MANUSCRIPT = "manuscript"
    MAP = "map"
    DRAWING = "drawing"
    UNKNOWN = "unknown"


@dataclass
class UniversalDataRecord:
    """Universal data record for any archive item."""
    # Core identifiers
    id: str
    source_archive: str
    source_url: str
    
    # Temporal data
    date_created: Optional[datetime] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    date_uncertainty: Optional[str] = None  # e.g., "circa", "approximately"
    
    # Content description
    title: str = ""
    description: str = ""
    subject: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Data type and format
    data_type: DataType = DataType.UNKNOWN
    mime_type: str = ""
    file_format: str = ""
    
    # Physical/digital characteristics
    dimensions: Optional[Dict[str, Any]] = None  # width, height, pages, duration
    file_size: Optional[int] = None
    resolution: Optional[str] = None
    
    # Geographic data
    location: Optional[Dict[str, Any]] = None  # lat, lon, place_name, region
    coverage_spatial: List[str] = field(default_factory=list)
    
    # Creator/contributor
    creator: List[str] = field(default_factory=list)
    contributor: List[str] = field(default_factory=list)
    publisher: Optional[str] = None
    
    # Rights and access
    rights: Optional[str] = None
    license: Optional[str] = None
    access_restrictions: Optional[str] = None
    
    # Language and script
    language: List[str] = field(default_factory=list)
    script: Optional[str] = None  # e.g., "Arabic", "Ottoman Turkish"
    
    # Relationships
    is_part_of: Optional[str] = None
    related_items: List[str] = field(default_factory=list)
    
    # Technical metadata
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    iiif_manifest: Optional[str] = None
    
    # Processing metadata
    harvested_date: datetime = field(default_factory=datetime.now)
    processing_notes: List[str] = field(default_factory=list)
    confidence_score: float = 1.0  # For AI-extracted data
    
    # Original metadata (preserved as-is)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


class UniversalArchiveScraper(ABC):
    """Base class for all archive scrapers with maximum flexibility."""
    
    def __init__(self, archive_name: str, base_url: str):
        self.archive_name = archive_name
        self.base_url = base_url
        self.session = self._init_session()
        self.browser = None
        self.data_extractors = self._register_extractors()
        self.results_cache = []
        self.ua = UserAgent()
        self.rate_limit_delay = 1.0  # seconds between requests
        
    def _init_session(self):
        """Initialize scraping session with proper headers."""
        import requests
        import urllib3
        
        # Suppress SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Use regular requests session instead of cloudscraper for now
        session = requests.Session()
        
        # Disable SSL verification
        session.verify = False
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def _register_extractors(self) -> Dict[str, Any]:
        """Register data extractors for different content types."""
        # Default implementation - subclasses can override
        return {}
    
    def scrape(self, url: str = None, search_terms: List[str] = None) -> List[UniversalDataRecord]:
        """Main scraping method - can scrape single URL or search."""
        if url:
            return self._scrape_url(url)
        elif search_terms:
            return self._scrape_search(search_terms)
        else:
            return self._scrape_full_archive()
    
    def _scrape_url(self, url: str) -> List[UniversalDataRecord]:
        """Scrape a specific URL."""
        content = self._fetch_content(url)
        records = self._extract_records(content, url)
        return records
    
    def _scrape_search(self, search_terms: List[str]) -> List[UniversalDataRecord]:
        """Search the archive with given terms."""
        # Default implementation - subclasses should override
        logger.warning(f"{self.__class__.__name__} doesn't implement search functionality")
        return []
    
    def _scrape_full_archive(self) -> List[UniversalDataRecord]:
        """Scrape the entire archive (if supported)."""
        logger.warning(f"Full archive scraping not implemented for {self.archive_name}")
        return []
    
    @sleep_and_retry
    @limits(calls=10, period=60)  # 10 calls per minute
    def _fetch_content(self, url: str, use_browser: bool = False) -> str:
        """Fetch page content with rate limiting."""
        time.sleep(self.rate_limit_delay)  # Additional delay
        
        if use_browser:
            return self._fetch_with_browser(url)
        else:
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                raise
    
    def _fetch_with_browser(self, url: str) -> str:
        """Use Selenium for JavaScript-heavy pages."""
        if not self.browser:
            self._init_browser()
        
        try:
            self.browser.get(url)
            # Wait for page to load
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # Additional wait for dynamic content
            
            # Handle lazy loading
            self._scroll_page()
            
            return self.browser.page_source
        except Exception as e:
            logger.error(f"Browser error fetching {url}: {e}")
            raise
    
    def _init_browser(self):
        """Initialize headless Chrome with anti-detection."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={self.ua.random}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Anti-detection measures
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.browser = webdriver.Chrome(options=options)
        
        # Additional anti-detection
        self.browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
    
    def _scroll_page(self):
        """Scroll page to load lazy content."""
        if not self.browser:
            return
            
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down to bottom
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait to load page
            time.sleep(2)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def _get_soup(self, html: str) -> BeautifulSoup:
        """Parse HTML into BeautifulSoup object."""
        return BeautifulSoup(html, 'lxml')
    
    def _extract_records(self, html: str, url: str) -> List[UniversalDataRecord]:
        """Extract records from HTML content."""
        soup = self._get_soup(html)
        records = []
        
        # This is a generic implementation - override in subclasses
        # for archive-specific extraction
        logger.warning(f"Using generic extraction for {url}")
        
        # Try to extract any images
        for img in soup.find_all('img'):
            record = self._create_record_from_image(img, url)
            if record:
                records.append(record)
        
        return records
    
    def _create_record_from_image(self, img_element, page_url: str) -> Optional[UniversalDataRecord]:
        """Create a record from an image element."""
        img_url = img_element.get('src', '')
        if not img_url:
            return None
            
        # Resolve relative URLs
        img_url = urljoin(page_url, img_url)
        
        record = UniversalDataRecord(
            id=hashlib.md5(img_url.encode()).hexdigest(),
            source_archive=self.archive_name,
            source_url=page_url,
            data_type=DataType.IMAGE,
            download_url=img_url,
            thumbnail_url=img_url,
            title=img_element.get('alt', ''),
            description=img_element.get('title', '')
        )
        
        return record
    
    def _detect_data_type(self, element: Any, url: str = None) -> DataType:
        """Intelligently detect data type."""
        # Check URL/filename
        if url:
            mime_type, _ = mimetypes.guess_type(url)
            if mime_type:
                if mime_type.startswith('image'):
                    return DataType.IMAGE
                elif mime_type == 'application/pdf':
                    return DataType.PDF
                elif mime_type.startswith('video'):
                    return DataType.VIDEO
                elif mime_type.startswith('audio'):
                    return DataType.AUDIO
        
        # Check HTML elements
        if hasattr(element, 'name'):
            if element.name == 'img':
                return DataType.IMAGE
            elif element.name in ['p', 'div', 'span', 'article']:
                return DataType.TEXT
        
        # Check for manuscript indicators
        text = str(element).lower()
        if any(term in text for term in ['manuscript', 'handwritten', 'codex']):
            return DataType.MANUSCRIPT
        elif any(term in text for term in ['map', 'plan', 'chart']):
            return DataType.MAP
        elif any(term in text for term in ['drawing', 'sketch', 'illustration']):
            return DataType.DRAWING
        
        return DataType.UNKNOWN
    
    def _extract_temporal_data(self, text: str) -> Dict[str, Any]:
        """Extract dates from various formats."""
        import dateparser
        import re
        
        temporal_data = {}
        
        if not text:
            return temporal_data
        
        # Look for date patterns
        date_patterns = [
            (r'\b(\d{4})\b', 'year'),  # Year
            (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', 'date'),  # MM/DD/YYYY
            (r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b', 'date'),
            (r'\b(circa|c\.|ca\.?)\s*(\d{4})\b', 'circa'),  # Circa dates
            (r'\b(\d{4})\s*-\s*(\d{4})\b', 'range'),  # Date ranges
            (r'\b(\d+)(?:st|nd|rd|th)\s+century\b', 'century'),  # Century
        ]
        
        for pattern, pattern_type in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if pattern_type == 'circa':
                    temporal_data['date_uncertainty'] = 'circa'
                    if len(matches[0]) > 1:
                        parsed = dateparser.parse(matches[0][1])
                        if parsed:
                            temporal_data['date_created'] = parsed
                elif pattern_type == 'range' and len(matches[0]) == 2:
                    start = dateparser.parse(matches[0][0])
                    end = dateparser.parse(matches[0][1])
                    if start and end:
                        temporal_data['date_range_start'] = start
                        temporal_data['date_range_end'] = end
                elif pattern_type == 'century':
                    century = int(matches[0])
                    temporal_data['date_range_start'] = datetime((century - 1) * 100, 1, 1)
                    temporal_data['date_range_end'] = datetime(century * 100 - 1, 12, 31)
                    temporal_data['date_uncertainty'] = 'century'
                else:
                    parsed_date = dateparser.parse(' '.join(matches[0]) if isinstance(matches[0], tuple) else matches[0])
                    if parsed_date:
                        temporal_data['date_created'] = parsed_date
                        
                break  # Use first match
        
        return temporal_data
    
    def close(self):
        """Clean up resources."""
        if self.browser:
            self.browser.quit()
            self.browser = None
        if self.session:
            self.session.close()