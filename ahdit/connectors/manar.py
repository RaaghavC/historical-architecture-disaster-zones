# connectors/manar.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from .base import BaseConnector

class ManarConnector(BaseConnector):
    SOURCE_NAME = "manar"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.base_url = "https://www.manar-al-athar.ox.ac.uk"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'AHDIT/1.0 (Antakya Heritage Digital Ingest Toolkit)'
        }
        self.session.headers.update(self.headers)
    
    def search(self, monument_name: str, **kwargs):
        """Search Manar al-Athar for assets related to the monument."""
        # Use regular search.php instead of advanced_search.php
        search_params = {
            'search': monument_name,
            'offset': 0,
            'per_page': 48,
            'display': 'thumbs',
            'order_by': 'relevance',
            'sort': 'DESC'
        }
        search_url = f"{self.base_url}/pages/search.php"
        
        try:
            response = self.session.get(search_url, params=search_params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all ResourcePanel divs
            results = soup.find_all('div', class_='ResourcePanel')
            
            print(f"Found {len(results)} results on Manar al-Athar")
            
            for result in results:
                # Find the view link
                view_link = result.find('a', href=lambda x: x and 'view.php' in x)
                if not view_link:
                    continue
                    
                page_url = urljoin(self.base_url, view_link['href'])
                
                # Find thumbnail image
                img = result.find('img')
                thumbnail_url = ''
                if img and img.get('src'):
                    thumbnail_url = urljoin(self.base_url, img['src'])
                
                # Extract filename and description from ResourcePanelInfo
                info_div = result.find('div', class_='ResourcePanelInfo')
                title = 'Unknown'
                description = ''
                
                if info_div:
                    # First line is usually the filename
                    text_lines = [t.strip() for t in info_div.stripped_strings]
                    if text_lines:
                        title = text_lines[0]
                        if len(text_lines) > 1:
                            description = ' '.join(text_lines[1:])
                
                yield {
                    'page_url': page_url,
                    'title': title,
                    'description': description,
                    'thumbnail_url': thumbnail_url
                }
                    
        except requests.RequestException as e:
            print(f"Error searching Manar al-Athar: {e}")
            return
    
    def download_asset(self, raw_metadata: dict) -> tuple[bytes, str]:
        """Download the asset and extract metadata."""
        # Update raw_metadata with source_url
        raw_metadata['source_url'] = raw_metadata.get('page_url', '')
        
        # For Manar, we'll use the thumbnail and convert to full-size image URL
        thumbnail_url = raw_metadata.get('thumbnail_url', '')
        if not thumbnail_url:
            return b'', ''
        
        try:
            # Convert thumbnail URL to screen resolution version
            # Thumbnails: ...pre_[hash].jpg
            # Screen res: ...scr_[hash].jpg
            download_url = thumbnail_url.replace('pre_', 'scr_')
            
            # Sometimes the full resolution might be available too
            # but we'll use screen resolution which is more reliable
            raw_metadata['download_url'] = download_url
            
            # Extract metadata from what we have
            raw_metadata['tags'] = {
                'Title': raw_metadata.get('title', 'Unknown'),
                'Description': raw_metadata.get('description', ''),
                'Source': 'Manar al-Athar',
                'Copyright': '© Manar al-Athar / University of Oxford'
            }
            
            print(f"Downloading: {download_url}")
            
            # Download the actual asset
            asset_response = self.session.get(download_url, timeout=60)
            asset_response.raise_for_status()
            
            # Get MIME type from response headers
            content_type = asset_response.headers.get('Content-Type', 'image/jpeg')
            mime_type = content_type.split(';')[0].strip()
            
            return asset_response.content, mime_type
            
        except requests.RequestException as e:
            print(f"Error downloading asset: {e}")
            # Try the thumbnail if screen resolution fails
            if thumbnail_url and 'pre_' in thumbnail_url:
                try:
                    print(f"Trying thumbnail instead: {thumbnail_url}")
                    asset_response = self.session.get(thumbnail_url, timeout=60)
                    asset_response.raise_for_status()
                    content_type = asset_response.headers.get('Content-Type', 'image/jpeg')
                    mime_type = content_type.split(';')[0].strip()
                    return asset_response.content, mime_type
                except:
                    pass
            
            return b'', ''