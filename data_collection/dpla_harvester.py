"""DPLA harvester placeholder"""
import requests
from typing import Iterable, Dict
from config import settings
from utils.metadata import DCRecord
from .base_harvester import BaseHarvester


class DplaHarvester(BaseHarvester):
    dataset = "DPLA"

    def query_remote_source(self, query: str = "Antakya", page_size: int = 100) -> Iterable[Dict]:
        url = "https://api.dp.la/v2/items"
        params = {"api_key": settings.DPLA_API_KEY, "q": query, "page_size": page_size}
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        yield from resp.json().get("docs", [])

    def transform(self, item: Dict) -> DCRecord:
        identifier = f"dpla:{item['id']}"
        title = item.get("sourceResource", {}).get("title", "Untitled")
        return DCRecord(identifier=identifier, title=title, extra={"raw": item})
