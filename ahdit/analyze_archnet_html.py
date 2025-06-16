import re
from bs4 import BeautifulSoup

# Read the saved HTML file
with open('archnet_search_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

print("=== Analyzing Archnet Search Page Structure ===\n")

# Look for React/Next.js component classes that might contain results
print("1. React Component Classes Found:")
# Find all classes that contain 'Search' or 'Result'
all_classes = []
for element in soup.find_all(attrs={'class': True}):
    classes = element.get('class', [])
    for class_name in classes:
        if 'Search' in class_name or 'Result' in class_name:
            all_classes.append(class_name)

unique_classes = sorted(set(all_classes))
for class_name in unique_classes:
    print(f"  - {class_name}")

print("\n2. Search Results Container Analysis:")
# Look for specific containers
search_results_sections = soup.find_all('section', attrs={'aria-label': 'Search Results'})
print(f"Found {len(search_results_sections)} section(s) with aria-label='Search Results'")

for i, section in enumerate(search_results_sections):
    print(f"\n  Section {i+1}:")
    print(f"  Classes: {' '.join(section.get('class', []))}")
    
    # Look for child containers
    items_containers = section.find_all('div', class_=lambda x: x and 'items' in ' '.join(x))
    print(f"  Found {len(items_containers)} items container(s)")
    
    for container in items_containers:
        print(f"    Container classes: {' '.join(container.get('class', []))}")

print("\n3. Loading State Analysis:")
# Look for loaders
loaders = soup.find_all('div', class_=lambda x: x and 'loader' in ' '.join(x))
print(f"Found {len(loaders)} loader element(s) - indicates dynamic content loading")

print("\n4. Next.js Data Script:")
# Look for Next.js data script
next_data = soup.find('script', id='__NEXT_DATA__')
if next_data:
    print("Found Next.js data script - this is a Next.js application")
    # Extract some info about the page
    import json
    try:
        data = json.loads(next_data.string)
        print(f"  Page: {data.get('page', 'Unknown')}")
        print(f"  Build ID: {data.get('buildId', 'Unknown')}")
        if 'query' in data:
            print(f"  Query params: {data['query']}")
    except:
        pass

print("\n5. API Configuration:")
# Look for API endpoints in the Next.js data
if next_data:
    try:
        data = json.loads(next_data.string)
        runtime_config = data.get('runtimeConfig', {})
        if 'apiUrl' in runtime_config:
            print(f"  API URL: {runtime_config['apiUrl']}")
        
        page_props = data.get('props', {}).get('pageProps', {})
        if 'algoliaAppId' in page_props:
            print(f"  Algolia App ID: {page_props['algoliaAppId']}")
            print(f"  Algolia Index: {page_props.get('algoliaIndex', 'Unknown')}")
            print("  => This site uses Algolia for search!")
    except:
        pass

print("\n6. Suggested CSS Selectors for Search Results:")
print("Based on the analysis, here are the likely selectors:")
print("  - Container: section[aria-label='Search Results']")
print("  - Items wrapper: .SearchResults_ui__ll4w8")
print("  - Individual items: .ui.divided.link.items > *")
print("  - Loading state: .ui.active.loader")

print("\n7. Important Finding:")
print("The search appears to be powered by Algolia and loads results dynamically.")
print("The page currently shows a loader, indicating results haven't loaded yet.")
print("You'll need to either:")
print("  a) Use Algolia's API directly")
print("  b) Use a browser automation tool like Selenium to wait for results")
print("  c) Analyze network requests to find the API endpoint")