# Archnet Search Functionality Analysis

## Summary

Archnet uses **Algolia** as its search backend, which loads results dynamically via API calls. The search page is built with Next.js and React.

## Key Findings

### 1. Search Technology
- **Search Provider**: Algolia
- **App ID**: `ZPU971PZKC`
- **Search API Key**: `8a6ae24beaa5f55705dd42b122554f0b`
- **Index Name**: `production`
- **API Endpoint**: `https://ZPU971PZKC-dsn.algolia.net/1/indexes/production/query`

### 2. HTML Structure

#### CSS Selectors for Search Results
```css
/* Main containers */
section[aria-label="Search Results"]  /* Search results section */
.SearchResults_ui__ll4w8              /* Results container class */
.ui.divided.link.items                /* Items wrapper */

/* Loading state */
.ui.active.loader                     /* Shows when loading */

/* Search input */
.SearchInput_searchInput__hGizm input /* Search input field */
```

#### HTML Structure Pattern
```html
<section aria-label="Search Results" class="SearchResults_ui__ll4w8 SearchResults_container__6Y3i5 SearchResults_searchResults__wLHc_">
  <div class="ui divided link items SearchResults_ui__ll4w8">
    <!-- Individual result items would appear here when loaded -->
  </div>
</section>
```

### 3. Search Result Data Structure

Each search result from Algolia contains:
- `objectID`: Unique identifier
- `type`: Type of result (e.g., "Image", "Site", "Publication")
- `name`: Name/title of the result
- `url`: Relative URL path (prefix with `https://www.archnet.org`)
- `sites`: Associated sites
- `authorities`: Associated authorities
- `collections`: Associated collections
- `_geoloc`: Geographic coordinates
- Various image URLs (`content_url`, `content_thumbnail_url`, etc.)

### 4. Example API Request

```python
import requests

# Algolia configuration
headers = {
    "X-Algolia-Application-Id": "ZPU971PZKC",
    "X-Algolia-API-Key": "8a6ae24beaa5f55705dd42b122554f0b",
    "Content-Type": "application/json"
}

# Search query
payload = {
    "query": "Alhambra",
    "hitsPerPage": 20,
    "page": 0
}

# Make request
url = "https://ZPU971PZKC-dsn.algolia.net/1/indexes/production/query"
response = requests.post(url, headers=headers, json=payload)
results = response.json()
```

### 5. Implementation Recommendations

For extracting search results from Archnet:

1. **Recommended Approach**: Use the Algolia API directly
   - Faster and more reliable than web scraping
   - No need to wait for JavaScript rendering
   - Direct access to all result data

2. **Alternative Approach**: Use Selenium/Playwright
   - Only if you need the exact rendered HTML
   - Wait for `.ui.active.loader` to disappear
   - Then extract results from `section[aria-label="Search Results"]`

3. **Data Processing**:
   - Results come in different types (Image, Site, Publication, etc.)
   - Each type has slightly different fields
   - Always check for field existence before accessing

### 6. Sample Results

For the search query "Alhambra", the API returns:
- Total hits: 1159
- Results include images, sites, and publications
- Each result has a unique URL that can be accessed on Archnet

## Files Created

1. `test_archnet_search.py` - Initial HTML analysis script
2. `analyze_archnet_html.py` - Detailed HTML structure analysis
3. `test_archnet_algolia.py` - Algolia API test script
4. `analyze_archnet_search.js` - Browser console analysis script
5. `archnet_algolia_response.json` - Sample API response data