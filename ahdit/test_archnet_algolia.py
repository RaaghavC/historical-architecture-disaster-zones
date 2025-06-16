import requests
import json

def test_archnet_algolia_search():
    """
    Test Archnet search using Algolia API directly
    Based on the configuration found in the HTML
    """
    
    # Algolia configuration from the HTML analysis
    algolia_app_id = "ZPU971PZKC"
    algolia_search_key = "8a6ae24beaa5f55705dd42b122554f0b"
    algolia_index = "production"
    
    # Algolia search endpoint
    url = f"https://{algolia_app_id}-dsn.algolia.net/1/indexes/{algolia_index}/query"
    
    # Headers for Algolia
    headers = {
        "X-Algolia-Application-Id": algolia_app_id,
        "X-Algolia-API-Key": algolia_search_key,
        "Content-Type": "application/json"
    }
    
    # Search query
    search_query = "Alhambra"
    
    # Algolia query parameters
    payload = {
        "query": search_query,
        "hitsPerPage": 20,
        "page": 0,
        "attributesToRetrieve": ["*"],
        "attributesToHighlight": ["*"]
    }
    
    print(f"Searching Archnet via Algolia for: '{search_query}'")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    # Make the request
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"=== Search Results ===")
        print(f"Total hits: {data.get('nbHits', 0)}")
        print(f"Processing time: {data.get('processingTimeMS', 0)}ms")
        print(f"Number of results returned: {len(data.get('hits', []))}\n")
        
        # Display results
        hits = data.get('hits', [])
        for i, hit in enumerate(hits[:5]):  # Show first 5 results
            print(f"--- Result {i+1} ---")
            print(f"Object ID: {hit.get('objectID', 'N/A')}")
            print(f"Type: {hit.get('type', 'N/A')}")
            
            # Different types have different fields
            if hit.get('name'):
                print(f"Name: {hit.get('name')}")
            if hit.get('title'):
                print(f"Title: {hit.get('title')}")
            if hit.get('description'):
                desc = hit.get('description', '')[:200]
                print(f"Description: {desc}...")
            if hit.get('location'):
                print(f"Location: {hit.get('location')}")
            if hit.get('url'):
                print(f"URL: https://www.archnet.org{hit.get('url')}")
            
            print()
        
        # Show structure of first hit for reference
        if hits:
            print("\n=== Structure of First Result (for reference) ===")
            print("Available fields:")
            for key in sorted(hits[0].keys()):
                value = hits[0][key]
                if isinstance(value, (str, int, float, bool)):
                    print(f"  - {key}: {type(value).__name__}")
                elif isinstance(value, list):
                    print(f"  - {key}: list[{len(value)} items]")
                elif isinstance(value, dict):
                    print(f"  - {key}: dict[{len(value)} keys]")
                else:
                    print(f"  - {key}: {type(value).__name__}")
        
        # Save full response for analysis
        with open('archnet_algolia_response.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print("\n=== Full response saved to archnet_algolia_response.json ===")
        
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_archnet_algolia_search()