"""
Advanced deduplication system for heritage data
Uses multiple strategies to identify and merge duplicate records
"""

import hashlib
import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
import logging
from urllib.parse import urlparse, unquote

from .universal_scraper import UniversalDataRecord

logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """Group of duplicate records with similarity scores"""
    primary_record: UniversalDataRecord
    duplicates: List[Tuple[UniversalDataRecord, float]]  # (record, similarity_score)
    merge_strategy: str = "keep_most_complete"


class DeduplicationEngine:
    """
    Advanced deduplication engine for heritage records
    Uses multiple strategies:
    1. Exact URL matching
    2. Image hash matching
    3. Title similarity
    4. Combined metadata similarity
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.url_cache: Dict[str, List[UniversalDataRecord]] = {}
        self.title_cache: Dict[str, List[UniversalDataRecord]] = {}
        self.image_hashes: Dict[str, List[UniversalDataRecord]] = {}
        
    def deduplicate(self, records: List[UniversalDataRecord]) -> List[UniversalDataRecord]:
        """
        Main deduplication method
        Returns list of unique records with duplicates merged
        """
        logger.info(f"Starting deduplication of {len(records)} records")
        
        # Build caches for fast lookup
        self._build_caches(records)
        
        # Find duplicate groups
        duplicate_groups = self._find_duplicate_groups(records)
        
        # Merge duplicates
        unique_records = self._merge_duplicate_groups(duplicate_groups)
        
        # Add records that weren't in any duplicate group
        processed_ids = set()
        for group in duplicate_groups:
            processed_ids.add(group.primary_record.id)
            for dup, _ in group.duplicates:
                processed_ids.add(dup.id)
        
        for record in records:
            if record.id not in processed_ids:
                unique_records.append(record)
        
        logger.info(f"Deduplication complete: {len(records)} -> {len(unique_records)} records")
        return unique_records
    
    def _build_caches(self, records: List[UniversalDataRecord]):
        """Build lookup caches for fast duplicate detection"""
        self.url_cache.clear()
        self.title_cache.clear()
        self.image_hashes.clear()
        
        for record in records:
            # URL cache - normalize URLs
            if record.download_url:
                norm_url = self._normalize_url(record.download_url)
                if norm_url not in self.url_cache:
                    self.url_cache[norm_url] = []
                self.url_cache[norm_url].append(record)
            
            # Title cache - normalize titles
            if record.title:
                norm_title = self._normalize_title(record.title)
                if norm_title not in self.title_cache:
                    self.title_cache[norm_title] = []
                self.title_cache[norm_title].append(record)
            
            # Image hash cache
            if record.raw_metadata and 'image_hash' in record.raw_metadata:
                img_hash = record.raw_metadata['image_hash']
                if img_hash not in self.image_hashes:
                    self.image_hashes[img_hash] = []
                self.image_hashes[img_hash].append(record)
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        # Remove protocol
        url = re.sub(r'^https?://', '', url.lower())
        # Remove www
        url = re.sub(r'^www\.', '', url)
        # Remove trailing slashes
        url = url.rstrip('/')
        # Decode URL encoding
        url = unquote(url)
        # Remove common tracking parameters
        url = re.sub(r'[?&](utm_[^&]+|fbclid=[^&]+|gclid=[^&]+)', '', url)
        return url
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Lowercase
        title = title.lower()
        # Remove punctuation and extra spaces
        title = re.sub(r'[^\w\s]', ' ', title)
        title = ' '.join(title.split())
        # Remove common suffixes
        title = re.sub(r'\s*(jpg|jpeg|png|tif|tiff|pdf)$', '', title)
        return title
    
    def _find_duplicate_groups(self, records: List[UniversalDataRecord]) -> List[DuplicateGroup]:
        """Find groups of duplicate records"""
        groups = []
        processed = set()
        
        for i, record in enumerate(records):
            if record.id in processed:
                continue
            
            duplicates = []
            
            # Check exact URL matches
            if record.download_url:
                norm_url = self._normalize_url(record.download_url)
                url_matches = self.url_cache.get(norm_url, [])
                for match in url_matches:
                    if match.id != record.id and match.id not in processed:
                        duplicates.append((match, 1.0))  # Perfect match
                        processed.add(match.id)
            
            # Check title similarity if no exact URL match
            if not duplicates and record.title:
                similar_records = self._find_similar_by_title(record, records)
                for similar, score in similar_records:
                    if similar.id not in processed and score >= self.similarity_threshold:
                        duplicates.append((similar, score))
                        processed.add(similar.id)
            
            # Check combined metadata similarity
            if not duplicates:
                similar_records = self._find_similar_by_metadata(record, records)
                for similar, score in similar_records:
                    if similar.id not in processed and score >= self.similarity_threshold:
                        duplicates.append((similar, score))
                        processed.add(similar.id)
            
            # Create group if duplicates found
            if duplicates:
                processed.add(record.id)
                groups.append(DuplicateGroup(
                    primary_record=record,
                    duplicates=duplicates
                ))
        
        return groups
    
    def _find_similar_by_title(self, record: UniversalDataRecord, 
                              all_records: List[UniversalDataRecord]) -> List[Tuple[UniversalDataRecord, float]]:
        """Find records with similar titles"""
        similar = []
        norm_title = self._normalize_title(record.title)
        
        for other in all_records:
            if other.id == record.id or not other.title:
                continue
            
            other_norm = self._normalize_title(other.title)
            
            # Quick check - if lengths are very different, skip
            if abs(len(norm_title) - len(other_norm)) > max(len(norm_title), len(other_norm)) * 0.5:
                continue
            
            # Calculate similarity
            similarity = SequenceMatcher(None, norm_title, other_norm).ratio()
            
            # Also check if one title contains the other (common for image variants)
            if norm_title in other_norm or other_norm in norm_title:
                similarity = max(similarity, 0.9)
            
            if similarity >= self.similarity_threshold:
                similar.append((other, similarity))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)
    
    def _find_similar_by_metadata(self, record: UniversalDataRecord,
                                 all_records: List[UniversalDataRecord]) -> List[Tuple[UniversalDataRecord, float]]:
        """Find records with similar metadata"""
        similar = []
        
        for other in all_records:
            if other.id == record.id:
                continue
            
            score = 0.0
            factors = 0
            
            # Compare location
            if record.location and other.location:
                if (record.location.get('place_name') == other.location.get('place_name') or
                    (record.location.get('lat') and other.location.get('lat') and
                     abs(record.location['lat'] - other.location['lat']) < 0.001 and
                     abs(record.location['lon'] - other.location['lon']) < 0.001)):
                    score += 0.3
                factors += 0.3
            
            # Compare dates
            if record.date_created and other.date_created:
                if record.date_created == other.date_created:
                    score += 0.2
                factors += 0.2
            
            # Compare creators
            if record.creator and other.creator:
                creator_match = len(set(record.creator) & set(other.creator)) / max(len(record.creator), len(other.creator))
                score += creator_match * 0.2
                factors += 0.2
            
            # Compare keywords
            if record.keywords and other.keywords:
                keyword_match = len(set(record.keywords) & set(other.keywords)) / max(len(record.keywords), len(other.keywords))
                score += keyword_match * 0.3
                factors += 0.3
            
            # Normalize score
            if factors > 0:
                final_score = score / factors
                if final_score >= self.similarity_threshold:
                    similar.append((other, final_score))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)
    
    def _merge_duplicate_groups(self, groups: List[DuplicateGroup]) -> List[UniversalDataRecord]:
        """Merge duplicate groups into single records"""
        merged_records = []
        
        for group in groups:
            if group.merge_strategy == "keep_most_complete":
                merged = self._merge_keep_most_complete(group)
            else:
                merged = group.primary_record  # Default: keep primary
            
            # Add merge metadata
            merged.raw_metadata['deduplication'] = {
                'merged_count': len(group.duplicates) + 1,
                'duplicate_ids': [group.primary_record.id] + [d[0].id for d in group.duplicates],
                'similarity_scores': [1.0] + [d[1] for d in group.duplicates]
            }
            
            merged_records.append(merged)
        
        return merged_records
    
    def _merge_keep_most_complete(self, group: DuplicateGroup) -> UniversalDataRecord:
        """Merge strategy: keep most complete record and fill in missing fields"""
        # Start with primary record
        merged = group.primary_record
        all_records = [group.primary_record] + [d[0] for d in group.duplicates]
        
        # Calculate completeness scores
        def completeness_score(record):
            score = 0
            if record.title: score += 1
            if record.description: score += len(record.description) / 100
            if record.download_url: score += 2
            if record.thumbnail_url: score += 1
            if record.date_created: score += 1
            if record.location: score += 1
            if record.creator: score += len(record.creator)
            if record.keywords: score += len(record.keywords) * 0.5
            return score
        
        # Find most complete record
        most_complete = max(all_records, key=completeness_score)
        
        # Create new merged record starting from most complete
        merged = UniversalDataRecord(
            id=most_complete.id,
            source_archive=most_complete.source_archive,
            source_url=most_complete.source_url
        )
        
        # Copy all fields from most complete
        for field in most_complete.__dataclass_fields__:
            setattr(merged, field, getattr(most_complete, field))
        
        # Fill in missing fields from other records
        for record in all_records:
            if record.id == most_complete.id:
                continue
            
            # Title - keep longest
            if record.title and len(record.title) > len(merged.title or ''):
                merged.title = record.title
            
            # Description - keep longest
            if record.description and len(record.description) > len(merged.description or ''):
                merged.description = record.description
            
            # URLs - prefer higher resolution
            if record.download_url and not merged.download_url:
                merged.download_url = record.download_url
            
            if record.thumbnail_url and not merged.thumbnail_url:
                merged.thumbnail_url = record.thumbnail_url
            
            # Location - prefer more specific
            if record.location and not merged.location:
                merged.location = record.location
            elif record.location and merged.location:
                # Merge location data
                if 'lat' in record.location and 'lat' not in merged.location:
                    merged.location['lat'] = record.location['lat']
                    merged.location['lon'] = record.location['lon']
            
            # Combine keywords
            if record.keywords:
                merged.keywords = list(set(merged.keywords or []) | set(record.keywords))
            
            # Combine creators
            if record.creator:
                merged.creator = list(set(merged.creator or []) | set(record.creator))
            
            # Merge raw metadata
            if record.raw_metadata:
                for key, value in record.raw_metadata.items():
                    if key not in merged.raw_metadata:
                        merged.raw_metadata[key] = value
        
        return merged


def deduplicate_dataframe(df):
    """
    Deduplicate a pandas DataFrame of heritage records
    """
    import pandas as pd
    
    # Convert DataFrame to UniversalDataRecord objects
    records = []
    for _, row in df.iterrows():
        record = UniversalDataRecord(
            id=row.get('ID', ''),
            source_archive=row.get('Archive', ''),
            source_url=row.get('URL', '')
        )
        record.title = row.get('Title', '')
        record.description = row.get('Description', '')
        record.download_url = row.get('Download_URL', '')
        record.thumbnail_url = row.get('Thumbnail_URL', '')
        
        # Parse location if available
        if 'Latitude' in row and pd.notna(row['Latitude']):
            record.location = {
                'lat': row['Latitude'],
                'lon': row['Longitude'],
                'place_name': row.get('Location', '')
            }
        
        records.append(record)
    
    # Deduplicate
    engine = DeduplicationEngine()
    unique_records = engine.deduplicate(records)
    
    # Convert back to DataFrame
    data = []
    for record in unique_records:
        row_data = {
            'ID': record.id,
            'Archive': record.source_archive,
            'URL': record.source_url,
            'Title': record.title,
            'Description': record.description,
            'Download_URL': record.download_url,
            'Thumbnail_URL': record.thumbnail_url,
        }
        
        if record.location:
            row_data['Location'] = record.location.get('place_name', '')
            row_data['Latitude'] = record.location.get('lat')
            row_data['Longitude'] = record.location.get('lon')
        
        # Add deduplication info
        if 'deduplication' in record.raw_metadata:
            row_data['Merged_Count'] = record.raw_metadata['deduplication']['merged_count']
        
        data.append(row_data)
    
    return pd.DataFrame(data)