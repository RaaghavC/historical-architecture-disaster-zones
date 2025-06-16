# connectors/nit.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from .base import BaseConnector

class NITConnector(BaseConnector):
    SOURCE_NAME = "nit-istanbul"
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.base_url = "https://www.nit-istanbul.org"
        self.archive_url = f"{self.base_url}/kielarchive/index.php"
        self.headers = {
            'User-Agent': 'AHDIT/1.0 (Antakya Heritage Digital Ingest Toolkit)'
        }
    
    def search(self, monument_name: str, **kwargs):
        """Search NIT Istanbul Kiel Archive for assets related to the monument."""
        # The Kiel archive uses a form-based search system
        # We'll try to search for Turkey/Hatay region where Antakya is located
        
        try:
            # For Antakya, we should search in Turkey
            # The archive uses POST requests with country/city parameters
            search_data = {
                'country': 'Turkey',  # or 'Türkiye' depending on the form
                'city': monument_name
            }
            
            # Try searching via POST
            response = requests.post(self.archive_url, data=search_data, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                # Fallback: try GET request
                response = requests.get(self.archive_url, headers=self.headers, timeout=30)
            
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for result images or links
            # The archive might show results as a table or gallery
            images_found = False
            
            # Check for image results in various possible formats
            # Try table format first
            result_table = soup.find('table', class_='results') or soup.find('table')
            if result_table:
                rows = result_table.find_all('tr')
                for row in rows:
                    # Look for image cells
                    img = row.find('img')
                    if img and img.get('src'):
                        # Extract metadata from the row
                        cells = row.find_all('td')
                        title = ''
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            if text and not cell.find('img'):
                                title = text
                                break
                        
                        yield {
                            'page_url': self.archive_url,
                            'img_url': urljoin(self.base_url, img['src']),
                            'title': title or f'Kiel Archive - {monument_name}',
                            'archive_id': img.get('alt', '')
                        }
                        images_found = True
            
            # Try gallery format
            if not images_found:
                gallery_items = soup.find_all('div', class_=['gallery-item', 'photo-item', 'result-item'])
                for item in gallery_items:
                    img = item.find('img')
                    if img and img.get('src'):
                        title = item.find(['h3', 'h4', 'p', 'span'])
                        title_text = title.get_text(strip=True) if title else ''
                        
                        yield {
                            'page_url': self.archive_url,
                            'img_url': urljoin(self.base_url, img['src']),
                            'title': title_text or f'Kiel Archive - {monument_name}'
                        }
                        images_found = True
            
            # Direct image links
            if not images_found:
                all_images = soup.find_all('img', src=lambda x: x and 'kiel' in x.lower())
                for img in all_images[:5]:  # Limit to first 5
                    yield {
                        'page_url': self.archive_url,
                        'img_url': urljoin(self.base_url, img['src']),
                        'title': img.get('alt', f'Kiel Archive - {monument_name}')
                    }
                    images_found = True
            
            if not images_found:
                print(f"No images found for '{monument_name}' in NIT Kiel Archive")
                print("Note: The Kiel Archive focuses on Ottoman monuments in the Balkans and Turkish Thrace")
                    
        except requests.RequestException as e:
            print(f"Error searching NIT Istanbul: {e}")
            return
    
    def download_asset(self, raw_metadata: dict) -> tuple[bytes, str]:
        """Download the asset and extract metadata."""
        # For NIT, we should have the image URL
        img_url = raw_metadata.get('img_url', '')
        
        if not img_url:
            return b'', ''
        
        try:
            raw_metadata['source_url'] = raw_metadata.get('page_url', self.archive_url)
            raw_metadata['download_url'] = img_url
            
            # Initialize tags
            raw_metadata['tags'] = {
                'Title': raw_metadata.get('title', 'Unknown'),
                'Archive': 'Machiel Kiel Photographic Archive',
                'Institution': 'Netherlands Institute in Turkey',
                'Photographer': 'Prof. Machiel Kiel',
                'Period': '1960s-1990s',
                'Copyright': '© Machiel Kiel / NIT Istanbul'
            }
            
            # Add archive ID if present
            if raw_metadata.get('archive_id'):
                raw_metadata['tags']['Archive ID'] = raw_metadata['archive_id']
            
            print(f"Downloading: {img_url}")
            
            # Download the image
            response = requests.get(img_url, headers=self.headers, timeout=60)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            mime_type = content_type.split(';')[0].strip()
            
            return response.content, mime_type
                
        except requests.RequestException as e:
            print(f"Error downloading from NIT Istanbul: {e}")
            return b'', ''