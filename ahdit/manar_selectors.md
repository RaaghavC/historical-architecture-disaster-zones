# Manar al-Athar Search Functionality Documentation

## Search URLs and Parameters

### Basic Search URL
```
https://www.manar-al-athar.ox.ac.uk/pages/search.php
```

### Search Parameters
- `search`: The search query (e.g., "Damascus", "Syria")
- `offset`: Pagination offset (starts at 0)
- `order_by`: Sort field (e.g., "relevance", "date")
- `sort`: Sort direction ("ASC" or "DESC")
- `archive`: Archive filter (default: "0")
- `display`: Display mode ("thumbs", "list", "strip", "map")
- `per_page`: Results per page (24, 48, 72, 120, 240)
- `k`: Optional search key/token
- `restypes`: Resource types filter

### Example Search URLs
```
# Search for Damascus with 48 results per page
https://www.manar-al-athar.ox.ac.uk/pages/search.php?search=Damascus&per_page=48&display=thumbs

# Search for Syria, page 2 (offset 48)
https://www.manar-al-athar.ox.ac.uk/pages/search.php?search=Syria&offset=48&per_page=48
```

## HTML Structure and CSS Selectors

### Search Results Container
```css
#CentralSpaceResources  /* Main container for all results */
.ResourcePanelShell     /* Individual result wrapper */
.ResourcePanel          /* Individual result container */
```

### Individual Result Structure
Each search result has the following structure:
```html
<div class="ResourcePanelShell">
    <div class="ResourcePanel">
        <!-- Thumbnail and link -->
        <a href="/pages/view.php?ref=[resource_id]&search=[query]...">
            <img src="/filestore/[path]/[filename]pre_[hash].jpg" />
        </a>
        
        <!-- Filename -->
        <div class="ResourcePanelInfo">
            <a href="/pages/view.php?ref=[resource_id]...">filename.tif</a>
            <!-- Description/Location text -->
            Damascus - Umayyad (Great) Mosque - courtyard
        </div>
        
        <!-- Action icons -->
        <div class="ResourcePanelIcons">
            <!-- Share, preview, collection buttons -->
        </div>
    </div>
</div>
```

### CSS Selectors for Data Extraction

```python
# Result containers
result_panels = '.ResourcePanel'

# Thumbnail image
thumbnail_img = '.ResourcePanel img'
# Extract: src attribute

# Link to full view
view_link = '.ResourcePanel a[href*="view.php"]'
# Extract: href attribute for full URL, text content for filename

# Resource ID
# Extract from URL parameter: ref=XXXXX

# Description/Location
# Found as text node within .ResourcePanelInfo after the filename link

# Pagination
pagination_links = 'a[href*="offset="]'
total_results = 'text containing "results"'  # Parse number from text
```

## Image URL Patterns

### Thumbnail Images
```
https://www.manar-al-athar.ox.ac.uk/filestore/[collection]/[subfolder]/[filename]pre_[hash].jpg
```

### Full Images
Original files are typically TIF format:
```
https://www.manar-al-athar.ox.ac.uk/filestore/[collection]/[subfolder]/[filename].tif
```

### Screen Resolution Images
```
https://www.manar-al-athar.ox.ac.uk/filestore/[collection]/[subfolder]/[filename]scr_[hash].jpg
```

## Metadata Fields

When viewing individual resources, the following metadata may be available:
- Filename
- Title
- Description
- Location
- Date
- Creator/Photographer
- Collection
- Keywords/Tags
- File size and format

## JavaScript Variables and Functions

Key JavaScript variables found in search pages:
```javascript
baseurl = "https://www.manar-al-athar.ox.ac.uk"
searchparams = {
    search: "[query]",
    order_by: "relevance",
    sort: "DESC",
    // ... other parameters
}
```

## Autocomplete Search

Autocomplete endpoint:
```
https://www.manar-al-athar.ox.ac.uk/pages/ajax/autocomplete_search.php
```
- Requires minimum 3 characters
- Returns JSON with search suggestions

## Alternative Search Interfaces

1. **Advanced Search**: `/pages/search_advanced.php`
2. **Geographic Search**: Available but URL not directly visible
3. **Collection Browse**: Browse by country/region collections

## Example Python Code for Result Extraction

```python
from bs4 import BeautifulSoup
import requests

def extract_search_results(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    for panel in soup.select('.ResourcePanel'):
        result = {}
        
        # Extract thumbnail
        img = panel.select_one('img')
        if img:
            result['thumbnail'] = img.get('src', '')
        
        # Extract link and resource ID
        link = panel.select_one('a[href*="view.php"]')
        if link:
            result['url'] = link.get('href', '')
            # Extract resource ID from URL
            if 'ref=' in result['url']:
                result['id'] = result['url'].split('ref=')[1].split('&')[0]
            
            # Extract filename
            result['filename'] = link.get_text(strip=True)
        
        # Extract description (text after filename)
        info_div = panel.select_one('.ResourcePanelInfo')
        if info_div:
            full_text = info_div.get_text(strip=True)
            # Remove filename to get description
            if result.get('filename') in full_text:
                result['description'] = full_text.replace(result['filename'], '').strip()
        
        results.append(result)
    
    return results
```

## Notes and Limitations

1. Individual resource pages (view.php) may require authentication (403 errors)
2. Full-size images are often in TIF format, which may require special handling
3. The site uses extensive JavaScript for dynamic loading and interactions
4. Search results are paginated with a maximum of 240 results per page
5. The autocomplete feature requires a minimum of 3 characters

## Testing Recommendations

1. Start with simple searches like "Damascus" or "Syria" that return many results
2. Test pagination by adjusting the `offset` parameter
3. Try different `display` modes (thumbs, list, strip, map)
4. Test the autocomplete endpoint separately for search suggestions
5. Be aware of potential rate limiting or access restrictions