#!/usr/bin/env python3
import requests
import json

# Test Archnet Algolia API directly
headers = {
    'X-Algolia-Application-Id': 'ZPU971PZKC',
    'X-Algolia-API-Key': '8a6ae24beaa5f55705dd42b122554f0b',
    'Content-Type': 'application/json'
}

api_url = "https://zpu971pzkc-dsn.algolia.net/1/indexes/production/query"
search_data = {
    "query": "Alhambra",
    "page": 0,
    "hitsPerPage": 5
}

response = requests.post(api_url, headers=headers, json=search_data)
data = response.json()

print(f"Total hits: {data.get('nbHits', 0)}")
print(f"Number of results: {len(data.get('hits', []))}")

for i, hit in enumerate(data.get('hits', [])[:3]):
    print(f"\nResult {i+1}:")
    print(f"Title: {hit.get('title', 'N/A')}")
    print(f"Type: {hit.get('type', 'N/A')}")
    print(f"Slug: {hit.get('slug', 'N/A')}")
    print(f"Has images: {'Yes' if hit.get('images') else 'No'}")
    if hit.get('images'):
        print(f"Number of images: {len(hit['images'])}")
        print(f"First image ID: {hit['images'][0].get('id', 'N/A')}")