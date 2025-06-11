import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from web.api import app

client = TestClient(app)

def test_items_empty():
    resp = client.get('/items')
    assert resp.status_code == 200
    assert resp.json() == []
