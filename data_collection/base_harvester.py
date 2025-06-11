"""
Abstract base class that all concrete harvesters inherit from.
It enforces a two-step pattern:

    (1)  query_remote_source(**kwargs)  -> list[dict]
    (2)  transform(item)               -> utils.metadata.DCRecord
"""
from abc import ABC, abstractmethod
from typing import Iterable, List, Dict
from utils.logging_config import get_logger

log = get_logger(__name__)


class BaseHarvester(ABC):
    dataset: str = "BASE"

    @abstractmethod
    def query_remote_source(self, **kwargs) -> Iterable[Dict]:
        pass

    @abstractmethod
    def transform(self, item: Dict) -> "DCRecord":
        pass

    def harvest(self, **kwargs) -> List["DCRecord"]:
        raw_items = self.query_remote_source(**kwargs)
        records = []
        for raw in raw_items:
            try:
                records.append(self.transform(raw))
            except Exception as exc:
                log.error("Transform failed for %s - %s", raw.get("id"), exc, exc_info=exc)
        log.info("\u2714 %s: harvested %d records", self.dataset, len(records))
        return records
