"""
Manar al-Athar Search Functionality Test
This script demonstrates how to search and extract results from https://www.manar-al-athar.ox.ac.uk
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import json

class ManarSearcher:
    def __init__(self):
        self.base_url = "https://www.manar-al-athar.ox.ac.uk"
        self.search_url = f"{self.base_url}/pages/search.php"
        
    def search(self, query, per_page=48, offset=0):
        """
        Search the Manar al-Athar database
        
        Args:
            query: Search term (e.g., "Damascus", "Syria")
            per_page: Number of results per page (24, 48, 72, 120, 240)
            offset: Pagination offset
        """
        params = {
            'search': query,
            'offset': offset,
            'order_by': 'relevance',
            'sort': 'DESC',
            'archive': '0',
            'display': 'thumbs',
            'per_page': per_page
        }
        
        try:
            response = requests.get(self.search_url, params=params)
            response.raise_for_status()
            return self.parse_results(response.text)
        except requests.RequestException as e:
            print(f"Error fetching search results: {e}")
            return None
    
    def parse_results(self, html_content):
        """
        Parse search results from HTML content
        
        Returns a list of dictionaries containing:
        - thumbnail_url: URL of the thumbnail image
        - full_view_url: URL to the full resource page
        - filename: Original filename
        - description: Brief description/location
        - resource_id: Resource reference ID
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        # CSS Selectors for extracting results
        selectors = {
            'result_container': '.ResourcePanel',
            'thumbnail_link': 'a[href*="view.php"]',
            'thumbnail_img': 'img',
            'filename': 'a[href*="view.php"]',  # Text content
            'description': '.ResourcePanelInfo',  # May contain location/description
        }
        
        # Find all result panels
        result_panels = soup.select(selectors['result_container'])
        
        for panel in result_panels:
            result = {}
            
            # Extract thumbnail URL
            thumb_img = panel.select_one('img')
            if thumb_img and 'src' in thumb_img.attrs:
                result['thumbnail_url'] = urljoin(self.base_url, thumb_img['src'])
            
            # Extract link to full view
            view_link = panel.select_one('a[href*="view.php"]')
            if view_link and 'href' in view_link.attrs:
                result['full_view_url'] = urljoin(self.base_url, view_link['href'])
                # Extract resource ID from URL
                if 'ref=' in view_link['href']:
                    result['resource_id'] = view_link['href'].split('ref=')[-1].split('&')[0]
            
            # Extract filename
            if view_link:
                filename_text = view_link.get_text(strip=True)
                if filename_text:
                    result['filename'] = filename_text
            
            # Extract description/location
            # Look for text nodes that might contain location info
            panel_text = panel.get_text(separator=' ', strip=True)
            # Remove filename from text to get description
            if 'filename' in result and result['filename'] in panel_text:
                description = panel_text.replace(result['filename'], '').strip()
                if description:
                    result['description'] = description
            
            if result:
                results.append(result)
        
        # Extract total results count
        total_results = None
        results_text = soup.find(text=lambda t: 'results' in t and t.strip())
        if results_text:
            import re
            match = re.search(r'(\d+(?:,\d+)*)\s+results', results_text)
            if match:
                total_results = match.group(1).replace(',', '')
        
        return {
            'total_results': total_results,
            'results': results
        }
    
    def get_image_metadata(self, resource_id):
        """
        Get detailed metadata for a specific resource
        Note: This might require authentication or have access restrictions
        """
        view_url = f"{self.base_url}/pages/view.php?ref={resource_id}"
        
        try:
            response = requests.get(view_url)
            if response.status_code == 403:
                return {"error": "Access forbidden - may require authentication"}
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            metadata = {}
            
            # Extract metadata fields (these selectors would need to be determined
            # from an accessible resource page)
            metadata_selectors = {
                'title': '.Title',
                'description': '.Description',
                'location': '.Location',
                'date': '.Date',
                'creator': '.Creator',
                'full_image': 'img.Picture'
            }
            
            for field, selector in metadata_selectors.items():
                element = soup.select_one(selector)
                if element:
                    if field == 'full_image' and 'src' in element.attrs:
                        metadata[field] = urljoin(self.base_url, element['src'])
                    else:
                        metadata[field] = element.get_text(strip=True)
            
            return metadata
        except requests.RequestException as e:
            return {"error": f"Error fetching metadata: {e}"}


# Example usage
if __name__ == "__main__":
    searcher = ManarSearcher()
    
    # Test search for Damascus
    print("Searching for 'Damascus'...")
    damascus_results = searcher.search("Damascus", per_page=24)
    
    if damascus_results and damascus_results['results']:
        print(f"\nTotal results: {damascus_results['total_results']}")
        print(f"Showing first {len(damascus_results['results'])} results:\n")
        
        for i, result in enumerate(damascus_results['results'][:5], 1):
            print(f"Result {i}:")
            print(f"  Filename: {result.get('filename', 'N/A')}")
            print(f"  Description: {result.get('description', 'N/A')}")
            print(f"  Thumbnail: {result.get('thumbnail_url', 'N/A')}")
            print(f"  Resource ID: {result.get('resource_id', 'N/A')}")
            print(f"  Full View: {result.get('full_view_url', 'N/A')}")
            print()
    
    # Test search for Syria
    print("\nSearching for 'Syria'...")
    syria_results = searcher.search("Syria", per_page=10)
    
    if syria_results and syria_results['results']:
        print(f"Found {syria_results['total_results']} results for 'Syria'")
        print(f"First result: {syria_results['results'][0].get('filename', 'N/A')}")