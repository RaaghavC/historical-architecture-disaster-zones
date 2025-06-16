# database/models.py
import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Monument(Base):
    __tablename__ = 'monuments'
    id = Column(Integer, primary_key=True)
    name_en = Column(String, nullable=False, unique=True, index=True)
    name_tr = Column(String)
    monument_type = Column(String, index=True)
    historical_period = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    assets = relationship("Asset", back_populates="monument", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Monument(name_en='{self.name_en}')>"

class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    monument_id = Column(Integer, ForeignKey('monuments.id'), nullable=False)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    asset_type = Column(String, nullable=False, default='image')
    file_path = Column(String, nullable=False, unique=True)
    file_hash_sha256 = Column(String(64), nullable=False, unique=True, index=True)
    mime_type = Column(String)
    source_url = Column(String, nullable=False)
    download_url = Column(String, nullable=False)
    ingested_at = Column(DateTime, default=datetime.datetime.utcnow)
    monument = relationship("Monument", back_populates="assets")
    source = relationship("Source", back_populates="assets")
    metadata_tags = relationship("MetadataTag", back_populates="asset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Asset(id={self.id}, file_path='{self.file_path}')>"

class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    base_url = Column(String, nullable=False)
    assets = relationship("Asset", back_populates="source")

    def __repr__(self):
        return f"<Source(name='{self.name}')>"

class MetadataTag(Base):
    __tablename__ = 'metadata_tags'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    key = Column(String, nullable=False, index=True)
    value = Column(Text, nullable=False)
    asset = relationship("Asset", back_populates="metadata_tags")

    def __repr__(self):
        return f"<MetadataTag(key='{self.key}', value='{self.value[:30]}...')>"