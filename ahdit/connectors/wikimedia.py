# connectors/wikimedia.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote, unquote
from .base import BaseConnector
import time

class WikimediaConnector(BaseConnector):
    SOURCE_NAME = "wikimedia"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.base_url = "https://commons.wikimedia.org"
        self.api_url = f"{self.base_url}/w/api.php"
        self.headers = {
            'User-Agent': 'AHDIT/1.0 (Antakya Heritage Digital Ingest Toolkit)'
        }
    
    def search(self, monument_name: str, **kwargs):
        """Search Wikimedia Commons for images."""
        # Use the API for reliable results
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': f'{monument_name} architecture OR monument OR building',
            'srnamespace': '6',  # File namespace
            'srlimit': 20
        }
        
        try:
            response = requests.get(self.api_url, params=params, headers=self.headers)
            data = response.json()
            
            results = data.get('query', {}).get('search', [])
            print(f"Found {len(results)} results on Wikimedia Commons")
            
            for result in results:
                title = result.get('title', '')
                if title.startswith('File:'):
                    # Get image info
                    info_params = {
                        'action': 'query',
                        'format': 'json',
                        'prop': 'imageinfo',
                        'iiprop': 'url|size|mime|metadata|extmetadata',
                        'titles': title
                    }
                    
                    info_response = requests.get(self.api_url, params=info_params, headers=self.headers)
                    info_data = info_response.json()
                    
                    pages = info_data.get('query', {}).get('pages', {})
                    for page_id, page_info in pages.items():
                        imageinfo = page_info.get('imageinfo', [])
                        if imageinfo:
                            img_data = imageinfo[0]
                            
                            yield {
                                'page_url': f"{self.base_url}/wiki/{quote(title)}",
                                'download_url': img_data.get('url'),
                                'title': title.replace('File:', '').replace('_', ' '),
                                'mime_type': img_data.get('mime'),
                                'width': img_data.get('width'),
                                'height': img_data.get('height'),
                                'metadata': img_data.get('extmetadata', {})
                            }
                    
                    # Be nice to the API
                    time.sleep(0.5)
                    
        except Exception as e:
            print(f"Error searching Wikimedia Commons: {e}")
            return
    
    def download_asset(self, raw_metadata: dict) -> tuple[bytes, str]:
        """Download the asset."""
        download_url = raw_metadata.get('download_url')
        if not download_url:
            return b'', ''
        
        try:
            # Update metadata
            raw_metadata['source_url'] = raw_metadata.get('page_url', download_url)
            
            # Extract metadata tags
            raw_metadata['tags'] = {
                'Title': raw_metadata.get('title', 'Unknown'),
                'Source': 'Wikimedia Commons',
                'License': 'See Wikimedia Commons page'
            }
            
            # Add extended metadata if available
            ext_metadata = raw_metadata.get('metadata', {})
            for key in ['Artist', 'DateTimeOriginal', 'ImageDescription', 'Credit']:
                if key in ext_metadata:
                    value = ext_metadata[key].get('value', '')
                    # Clean HTML from value
                    soup = BeautifulSoup(value, 'html.parser')
                    clean_value = soup.get_text(strip=True)
                    if clean_value:
                        raw_metadata['tags'][key] = clean_value[:200]  # Limit length
            
            # Download the image
            print(f"Downloading: {download_url}")
            response = requests.get(download_url, headers=self.headers, timeout=60)
            response.raise_for_status()
            
            mime_type = raw_metadata.get('mime_type') or response.headers.get('Content-Type', 'image/jpeg')
            
            return response.content, mime_type
            
        except Exception as e:
            print(f"Error downloading from Wikimedia: {e}")
            return b'', ''