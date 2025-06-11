"""Wikimedia Commons harvester placeholder"""
import requests
from typing import Iterable, Dict
from utils.metadata import DCRecord
from .base_harvester import BaseHarvester


class WikimediaHarvester(BaseHarvester):
    dataset = "WIKIMEDIA"

    def query_remote_source(self, query: str = "Antakya") -> Iterable[Dict]:
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        for item in resp.json().get("query", {}).get("search", []):
            yield item

    def transform(self, item: Dict) -> DCRecord:
        identifier = f"wikimedia:{item['pageid']}"
        title = item.get("title")
        return DCRecord(identifier=identifier, title=title, extra={"raw": item})
