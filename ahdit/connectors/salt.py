# connectors/salt.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from .base import BaseConnector
import json

class SALTConnector(BaseConnector):
    SOURCE_NAME = "salt"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.base_url = "https://archives.saltresearch.org"
        self.headers = {
            'User-Agent': 'AHDIT/1.0 (Antakya Heritage Digital Ingest Toolkit)'
        }
    
    def search(self, monument_name: str, **kwargs):
        """Search SALT Research Archives for assets related to the monument."""
        # Use the archives.saltresearch.org simple search
        search_params = {
            'query': monument_name,
            'sort_by': 'score',
            'order': 'desc',
            'rpp': 20,
            'start': 0
        }
        
        search_url = f"{self.base_url}/handle/123456789/1/simple-search"
        
        try:
            response = requests.get(search_url, params=search_params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the results table
            results_table = soup.find('table', class_='table_discovery')
            if not results_table:
                print("No results table found on SALT Archives")
                return
                
            tbody = results_table.find('tbody')
            if not tbody:
                return
                
            results = tbody.find_all('tr')
            print(f"Found {len(results)} results on SALT Archives")
            
            for row in results:
                # Extract title and URL
                title_cell = row.find('td', headers='t2')
                if not title_cell:
                    continue
                    
                link = title_cell.find('a')
                if not link or not link.get('href'):
                    continue
                    
                page_url = urljoin(self.base_url, link['href'])
                title = link.get_text(strip=True)
                
                # Extract thumbnail
                thumb_cell = row.find('td', headers='t1')
                thumbnail_url = ''
                if thumb_cell:
                    img = thumb_cell.find('img', class_='thumbnailImage')
                    if img and img.get('src'):
                        thumbnail_url = urljoin(self.base_url, img['src'])
                
                # Extract creator and date
                creator = ''
                creator_cell = row.find('td', headers='t3')
                if creator_cell:
                    em = creator_cell.find('em')
                    if em:
                        creator = em.get_text(strip=True)
                
                date = ''
                date_cell = row.find('td', headers='t4')
                if date_cell:
                    em = date_cell.find('em')
                    if em:
                        date = em.get_text(strip=True)
                
                yield {
                    'page_url': page_url,
                    'title': title,
                    'thumbnail_url': thumbnail_url,
                    'creator': creator,
                    'date': date
                }
                    
        except requests.RequestException as e:
            print(f"Error searching SALT Archives: {e}")
            return
    
    def download_asset(self, raw_metadata: dict) -> tuple[bytes, str]:
        """Download the asset and extract metadata."""
        raw_metadata['source_url'] = raw_metadata.get('page_url', '')
        
        # Try to use the thumbnail URL directly
        thumbnail_url = raw_metadata.get('thumbnail_url', '')
        if not thumbnail_url:
            return b'', ''
        
        try:
            # Convert thumbnail to full image URL if possible
            # SALT uses pattern: /retrieve/{id}/{filename}
            # We'll try to get a larger version
            download_url = thumbnail_url
            
            # If it's a retrieve URL, we might be able to get a larger version
            if '/retrieve/' in thumbnail_url:
                # Try modifying the URL for a larger version
                # This is speculative - SALT might have different size options
                download_url = thumbnail_url.replace('?show=thumb', '').replace('&show=thumb', '')
            
            raw_metadata['download_url'] = download_url
            
            # Extract metadata
            raw_metadata['tags'] = {
                'Title': raw_metadata.get('title', 'Unknown'),
                'Creator': raw_metadata.get('creator', ''),
                'Date': raw_metadata.get('date', ''),
                'Source': 'SALT Research Archives',
                'Collection': 'American Board Archives'
            }
            
            print(f"Downloading: {download_url}")
            
            # Download the image
            asset_response = requests.get(download_url, headers=self.headers, timeout=60)
            asset_response.raise_for_status()
            
            content_type = asset_response.headers.get('Content-Type', 'image/jpeg')
            mime_type = content_type.split(';')[0].strip()
            
            return asset_response.content, mime_type
            
        except requests.RequestException as e:
            print(f"Error downloading from SALT Archives: {e}")
            # Try the thumbnail as fallback
            if thumbnail_url:
                try:
                    print(f"Trying thumbnail: {thumbnail_url}")
                    asset_response = requests.get(thumbnail_url, headers=self.headers, timeout=60)
                    asset_response.raise_for_status()
                    content_type = asset_response.headers.get('Content-Type', 'image/jpeg')
                    mime_type = content_type.split(';')[0].strip()
                    return asset_response.content, mime_type
                except:
                    pass
            
            return b'', ''