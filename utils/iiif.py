"""Simple helper to create IIIF image URLs."""
from urllib.parse import quote

def make_iiif_url(src: str, w: int = 256) -> str:
    return f"https://iiif.harvard.edu/iiif/{quote(src)}/full/{w},/0/default.jpg"
