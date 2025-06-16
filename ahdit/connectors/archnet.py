# connectors/archnet.py
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from .base import BaseConnector

class ArchnetConnector(BaseConnector):
    SOURCE_NAME = "archnet"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.base_url = "https://www.archnet.org"
        self.api_url = "https://zpu971pzkc-dsn.algolia.net/1/indexes/production/query"
        self.headers = {
            'User-Agent': 'AHDIT/1.0 (Antakya Heritage Digital Ingest Toolkit)',
            'X-Algolia-Application-Id': 'ZPU971PZKC',
            'X-Algolia-API-Key': '8a6ae24beaa5f55705dd42b122554f0b',
            'Content-Type': 'application/json'
        }
    
    def search(self, monument_name: str, **kwargs):
        """Search Archnet for assets related to the monument using Algolia API."""
        search_data = {
            "query": monument_name,
            "page": 0,
            "hitsPerPage": 50,
            "getRankingInfo": True
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=search_data, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            hits = data.get('hits', [])
            
            print(f"Found {len(hits)} results on Archnet")
            
            for hit in hits:
                # Different handling based on type
                hit_type = hit.get('type', '').lower()
                
                if hit_type == 'image':
                    # Direct image result
                    image_id = hit.get('objectID') or hit.get('id')
                    if image_id:
                        # For image types, construct URL differently
                        yield {
                            'page_url': f"{self.base_url}/media/{image_id}",
                            'title': hit.get('name', hit.get('title', 'Unknown')),
                            'type': 'image',
                            'image_id': image_id,
                            'api_data': hit,
                            'is_direct_image': True
                        }
                        
                elif hit_type in ['sites', 'site']:
                    # Site/building result
                    slug = hit.get('slug', '')
                    if slug:
                        page_url = f"{self.base_url}/sites/{slug}"
                        
                        yield {
                            'page_url': page_url,
                            'title': hit.get('title', 'Unknown'),
                            'type': 'site',
                            'location': hit.get('location', {}),
                            'images': hit.get('images', []),
                            'api_data': hit
                        }
                else:
                    # Handle other types (publications, etc.)
                    slug = hit.get('slug', '')
                    if slug and hit_type:
                        page_url = f"{self.base_url}/{hit_type}/{slug}"
                        
                        yield {
                            'page_url': page_url,
                            'title': hit.get('title', 'Unknown'),
                            'type': hit_type,
                            'api_data': hit
                        }
                    
        except requests.RequestException as e:
            print(f"Error searching Archnet: {e}")
            return
    
    def download_asset(self, raw_metadata: dict) -> tuple[bytes, str]:
        """Download the asset and extract metadata."""
        # Update raw_metadata with source_url
        raw_metadata['source_url'] = raw_metadata.get('page_url', '')
        
        # Check if this is a direct image result
        if raw_metadata.get('is_direct_image'):
            # Handle direct image results
            image_id = raw_metadata.get('image_id')
            if not image_id:
                return b'', ''
                
            # Try different URL patterns for Archnet images
            url_patterns = [
                f"https://archnet.org/system/media_contents/contents/{image_id}/original/{image_id}.jpg",
                f"https://archnet.org/system/media_contents/contents/{image_id}/medium/{image_id}.jpg",
                f"https://media.archnet.org/system/media_contents/contents/{image_id}/original/{image_id}.jpg"
            ]
            
            download_url = None
            for url in url_patterns:
                try:
                    headers = {'User-Agent': 'AHDIT/1.0'}
                    response = requests.head(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        download_url = url
                        break
                except:
                    continue
                    
            if not download_url:
                download_url = url_patterns[0]  # Use first pattern as default
                
        else:
            # Handle site results with images array
            images = raw_metadata.get('images', [])
            if not images:
                return b'', ''
            
            # Use the first image
            image_data = images[0]
            image_id = image_data.get('id')
            
            if not image_id:
                return b'', ''
            
            download_url = f"https://archnet.org/system/media_contents/contents/{image_id}/original/{image_id}.jpg"
        
        try:
            raw_metadata['download_url'] = download_url
            
            # Extract metadata from API data
            raw_metadata['tags'] = {
                'Title': raw_metadata.get('title', 'Unknown'),
                'Type': raw_metadata.get('type', 'Unknown'),
                'Source': 'Archnet'
            }
            
            # Add location data if available
            location = raw_metadata.get('location', {})
            if location.get('country'):
                raw_metadata['tags']['Country'] = location['country']
            if location.get('city'):
                raw_metadata['tags']['City'] = location['city']
            
            # Add more metadata from API data
            api_data = raw_metadata.get('api_data', {})
            if api_data.get('date_text'):
                raw_metadata['tags']['Date'] = api_data['date_text']
            
            print(f"Downloading: {download_url}")
            
            # Download the actual asset
            headers = {'User-Agent': 'AHDIT/1.0 (Antakya Heritage Digital Ingest Toolkit)'}
            asset_response = requests.get(download_url, headers=headers, timeout=60)
            asset_response.raise_for_status()
            
            # Get MIME type from response headers
            content_type = asset_response.headers.get('Content-Type', 'image/jpeg')
            mime_type = content_type.split(';')[0].strip()
            
            return asset_response.content, mime_type
            
        except requests.RequestException as e:
            print(f"Error downloading asset: {e}")
            return b'', ''