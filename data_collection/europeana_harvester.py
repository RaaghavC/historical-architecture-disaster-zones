"""Europeana harvester placeholder"""
import requests
from typing import Iterable, Dict
from config import settings
from utils.metadata import DCRecord
from .base_harvester import BaseHarvester


class EuropeanaHarvester(BaseHarvester):
    dataset = "EUROPEANA"

    def query_remote_source(self, query: str = "Antakya", rows: int = 100) -> Iterable[Dict]:
        url = "https://api.europeana.eu/record/v2/search.json"
        params = {"wskey": settings.EUROPEANA_API_KEY, "query": query, "rows": rows}
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        for item in resp.json().get("items", []):
            yield item

    def transform(self, item: Dict) -> DCRecord:
        identifier = f"europeana:{item['id']}"
        title = item.get("title", ["Untitled"])[0]
        return DCRecord(identifier=identifier, title=title, extra={"raw": item})
