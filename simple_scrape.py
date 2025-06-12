#!/usr/bin/env python3
"""
Simple scraping script without complex dependencies.
"""
import requests
import urllib3
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_url(url):
    """Simple scraping function."""
    print(f"Fetching: {url}")
    
    # Create session with SSL verification disabled
    session = requests.Session()
    session.verify = False
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic data
        results = []
        
        # Get page title
        title = soup.find('title')
        page_title = title.text.strip() if title else "Unknown"
        
        print(f"Page title: {page_title}")
        
        # Extract all images
        images = soup.find_all('img')
        print(f"Found {len(images)} images")
        
        for img in images:
            src = img.get('src', '')
            if not src or src.startswith('data:'):
                continue
                
            # Make URL absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                from urllib.parse import urljoin
                src = urljoin(url, src)
            
            result = {
                'type': 'image',
                'url': src,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'page_url': url,
                'page_title': page_title,
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
        
        # Extract text content
        # Look for main content areas
        content_selectors = [
            'article', '.content', '#content', 'main',
            '.description', '.text', 'p'
        ]
        
        text_content = []
        for selector in content_selectors:
            elements = soup.select(selector)
            for elem in elements[:5]:  # Limit to first 5 of each type
                text = elem.get_text(strip=True)
                if len(text) > 50:  # Skip short text
                    text_content.append(text[:500])
        
        if text_content:
            print(f"Found {len(text_content)} text blocks")
            for i, text in enumerate(text_content[:3]):
                result = {
                    'type': 'text',
                    'content': text,
                    'page_url': url,
                    'page_title': page_title,
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def save_results(results, output_dir="simple_scrape_results"):
    """Save results to files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as JSON
    json_file = output_path / f"results_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON: {json_file}")
    
    # Save as CSV/Excel
    if results:
        df = pd.DataFrame(results)
        
        # Save CSV
        csv_file = output_path / f"results_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Saved CSV: {csv_file}")
        
        # Save Excel
        excel_file = output_path / f"results_{timestamp}.xlsx"
        df.to_excel(excel_file, index=False)
        print(f"Saved Excel: {excel_file}")
        
        # Print summary
        print(f"\nSummary:")
        print(f"Total items: {len(results)}")
        print(f"Images: {len([r for r in results if r['type'] == 'image'])}")
        print(f"Text blocks: {len([r for r in results if r['type'] == 'text'])}")

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://archnet.org/sites/1644"
    
    print(f"Simple scraping of: {url}\n")
    
    results = scrape_url(url)
    
    if results:
        save_results(results)
        print(f"\nSuccess! Found {len(results)} items")
    else:
        print("No results found")

if __name__ == "__main__":
    main()