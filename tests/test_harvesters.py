import os, sys, pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_collection.archnet_harvester import ArchnetHarvester


def test_archnet_harvester_transform():
    harvester = ArchnetHarvester()
    sample = {
        "id": "123",
        "title": "Test",
        "images": {"full": "http://example.com/img.jpg"},
    }
    rec = harvester.transform(sample)
    assert rec.identifier == "archnet:123"
    assert rec.title == "Test"
