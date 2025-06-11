"""Manar Al-Athar harvester placeholder"""
import requests
from typing import Iterable, Dict
from utils.metadata import DCRecord
from .base_harvester import BaseHarvester


class ManaralatharHarvester(BaseHarvester):
    dataset = "MANARALATHAR"

    def query_remote_source(self, query: str = "Antakya") -> Iterable[Dict]:
        url = "https://example.com/api"  # placeholder
        resp = requests.get(url, params={"q": query}, timeout=30)
        resp.raise_for_status()
        yield from resp.json().get("items", [])

    def transform(self, item: Dict) -> DCRecord:
        identifier = f"manar:{item['id']}"
        title = item.get("title", "Untitled")
        return DCRecord(identifier=identifier, title=title, extra={"raw": item})
