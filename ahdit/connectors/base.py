# connectors/base.py
import os
import hashlib
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from database.models import Asset, MetadataTag
import requests

class BaseConnector(ABC):
    SOURCE_NAME = ""
    ASSETS_DIR = "data/assets"

    def __init__(self, db_session: Session):
        if not self.SOURCE_NAME:
            raise NotImplementedError("A connector must define a SOURCE_NAME.")
        self.session = db_session
        self.source_dir = os.path.join(self.ASSETS_DIR, self.SOURCE_NAME)
        os.makedirs(self.source_dir, exist_ok=True)

    @abstractmethod
    def search(self, monument_name: str, **kwargs):
        """Searches the source and yields dictionaries of raw metadata for each found asset."""
        pass

    @abstractmethod
    def download_asset(self, raw_metadata: dict) -> tuple[bytes, str]:
        """Downloads the binary content and returns (content, mime_type)."""
        pass

    def process_and_store(self, raw_metadata: dict, monument, source_obj):
        """Shared logic to process and store a single asset."""
        print(f"Processing asset from source URL: {raw_metadata.get('source_url')}")
        try:
            content, mime_type = self.download_asset(raw_metadata)
            if not content:
                print(f"Warning: Failed to download asset from {raw_metadata.get('download_url')}. Content is empty.")
                return
        except requests.exceptions.RequestException as e:
            print(f"Error downloading asset from {raw_metadata.get('download_url')}: {e}")
            return
        except Exception as e:
            print(f"An unexpected error occurred during download: {e}")
            return

        file_hash = hashlib.sha256(content).hexdigest()
        existing_asset = self.session.query(Asset).filter_by(file_hash_sha256=file_hash).first()
        if existing_asset:
            print(f"Skipping duplicate asset (hash: {file_hash[:10]}...).")
            return

        # Use a safe part of the mime type for the extension
        file_extension = mime_type.split('/')[-1].split(';')[0]
        file_path = os.path.join(self.source_dir, f"{file_hash}.{file_extension}")
        with open(file_path, 'wb') as f:
            f.write(content)

        new_asset = Asset(
            monument_id=monument.id,
            source_id=source_obj.id,
            file_path=file_path,
            file_hash_sha256=file_hash,
            mime_type=mime_type,
            source_url=raw_metadata.get('source_url'),
            download_url=raw_metadata.get('download_url')
        )
        self.session.add(new_asset)
        self.session.flush()

        for key, value in raw_metadata.get('tags', {}).items():
            if value:
                tag = MetadataTag(asset_id=new_asset.id, key=str(key), value=str(value))
                self.session.add(tag)

        print(f"Successfully ingested and stored asset: {file_path}")