"""
Archnet harvester – pulls items tagged with a *site* or *location* that
matches 'Antakya' or the ancient toponym 'Antioch'.

Documentation:
https://archnet.org/api
"""
import requests
from datetime import datetime
from typing import Iterable, Dict
from pydantic import HttpUrl
from config import settings
from utils.metadata import DCRecord
from .base_harvester import BaseHarvester

BASE_URL = "https://archnet.org/api/v1/"


class ArchnetHarvester(BaseHarvester):
    dataset = "ARCHNET"

    def query_remote_source(self, per_page: int = 75) -> Iterable[Dict]:
        params = {
            "api_key": settings.ARCHNET_API_KEY,
            "q": "Antakya OR Antioch",
            "type": "image",
            "per_page": per_page,
        }
        url = BASE_URL + "search"
        next_url = url
        while next_url:
            resp = requests.get(next_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data["data"]:
                yield item
            next_url = data["links"].get("next")

    def transform(self, item: Dict) -> DCRecord:
        identifier = f"archnet:{item['id']}"
        title = item.get("title", "Untitled")
        creator = item.get("creator")
        date = datetime.fromisoformat(item["date_captured"]) if item.get("date_captured") else None
        description = item.get("description")
        lat = item.get("latitude")
        lon = item.get("longitude")

        return DCRecord(
            identifier=identifier,
            title=title,
            creator=creator,
            date=date,
            description=description,
            source=HttpUrl(url=item["images"]["full"]) if item["images"].get("full") else None,
            spatial_lat=lat,
            spatial_lon=lon,
            rights=item.get("license", "\u00a9 Archnet"),
            extra={"raw": item},
        )
