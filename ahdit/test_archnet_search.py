import requests
from bs4 import BeautifulSoup
import json

def test_archnet_search():
    """Test Archnet search functionality and identify result selectors"""
    
    url = "https://www.archnet.org/search?q=Alhambra"
    
    # Headers to mimic a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print(f"Fetching: {url}")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
    print(f"Content-Encoding: {response.headers.get('Content-Encoding', 'None')}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("\n=== Page Title ===")
        title = soup.find('title')
        if title:
            print(f"Title: {title.text.strip()}")
        
        print("\n=== Searching for common search result patterns ===")
        
        # Common patterns for search results
        selectors = [
            # Class-based selectors
            ('class', 'search-result'),
            ('class', 'search-item'),
            ('class', 'result-item'),
            ('class', 'search-listing'),
            ('class', 'listing-item'),
            ('class', 'card'),
            ('class', 'result'),
            ('class', 'item'),
            ('class', 'entry'),
            ('class', 'record'),
            
            # ID-based selectors
            ('id', 'search-results'),
            ('id', 'results'),
            ('id', 'listings'),
            
            # Data attributes
            ('data-result', None),
            ('data-search', None),
            ('data-item', None)
        ]
        
        found_elements = {}
        
        for attr_type, attr_value in selectors:
            if attr_type == 'class':
                # Search for partial class matches
                elements = soup.find_all(attrs={attr_type: lambda x: x and attr_value in x})
            elif attr_type == 'id':
                elements = soup.find_all(attrs={attr_type: attr_value})
            else:
                # Data attributes
                elements = soup.find_all(attrs={attr_type: True})
            
            if elements:
                found_elements[f"{attr_type}*={attr_value}"] = elements
                print(f"\nFound {len(elements)} elements with {attr_type} containing '{attr_value}'")
                # Show first element as sample
                if elements:
                    print(f"Sample element: {elements[0].name}")
                    if elements[0].get('class'):
                        print(f"Classes: {' '.join(elements[0].get('class'))}")
                    # Show a preview of the content
                    text_preview = elements[0].get_text(strip=True)[:150]
                    if text_preview:
                        print(f"Text preview: {text_preview}...")
        
        print("\n=== Analyzing repeating structures ===")
        # Look for containers with multiple similar children
        containers = soup.find_all(['div', 'section', 'article', 'ul', 'ol'])
        for container in containers:
            children = container.find_all(recursive=False)
            if len(children) > 3:
                # Check if children have similar structure
                first_child_classes = children[0].get('class', [])
                first_child_tag = children[0].name
                
                similar_count = sum(1 for child in children 
                                  if child.name == first_child_tag 
                                  and child.get('class', []) == first_child_classes)
                
                if similar_count == len(children) and first_child_classes:
                    print(f"\nFound repeating structure:")
                    print(f"Container: {container.name}.{'.'.join(container.get('class', ['no-class']))}")
                    print(f"Contains {len(children)} {first_child_tag} elements with class: {'.'.join(first_child_classes)}")
                    
                    # Show sample HTML structure
                    sample = children[0]
                    print(f"\nSample HTML structure:")
                    print(f"<{sample.name} class='{' '.join(sample.get('class', []))}'")
                    for child in sample.find_all(recursive=False)[:3]:
                        print(f"  <{child.name} class='{' '.join(child.get('class', []))}'>{child.get_text(strip=True)[:50]}...</{child.name}>")
                    print(f"</{sample.name}>")
        
        print("\n=== Looking for JSON-LD structured data ===")
        # Check for structured data that might contain search results
        scripts = soup.find_all('script', type='application/ld+json')
        if scripts:
            print(f"Found {len(scripts)} JSON-LD scripts")
            for i, script in enumerate(scripts):
                try:
                    data = json.loads(script.string)
                    print(f"\nJSON-LD Script {i+1}:")
                    print(f"Type: {data.get('@type', 'Unknown')}")
                    if 'itemListElement' in data:
                        print(f"Contains itemListElement with {len(data['itemListElement'])} items")
                except:
                    pass
        
        print("\n=== Main content area ===")
        # Look for main content areas
        main_selectors = ['main', '[role="main"]', '#main', '.main-content', '#content', '.content']
        for selector in main_selectors:
            if selector.startswith('['):
                # Attribute selector
                element = soup.select_one(selector)
            elif selector.startswith('#') or selector.startswith('.'):
                # ID or class selector
                element = soup.select_one(selector)
            else:
                # Tag selector
                element = soup.find(selector)
            
            if element:
                print(f"\nFound main content area: {selector}")
                children = element.find_all(recursive=False)
                print(f"Direct children: {len(children)}")
                for i, child in enumerate(children[:5]):
                    print(f"  Child {i+1}: {child.name}.{'.'.join(child.get('class', ['no-class']))}")
        
        # Save the raw HTML for manual inspection
        with open('archnet_search_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\n=== Saved raw HTML to archnet_search_page.html for manual inspection ===")
        
    else:
        print(f"Failed to fetch page. Status code: {response.status_code}")

if __name__ == "__main__":
    test_archnet_search()