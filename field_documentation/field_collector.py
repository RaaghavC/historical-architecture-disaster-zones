"""
Field Data Collector - Mobile-friendly data collection interface
Designed to work offline and sync when connection available
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from .damage_assessment import (
    DamageAssessmentForm, 
    GPSLocation, 
    PhotoDocumentation,
    DamageCategory,
    UrgencyLevel
)


class FieldDataCollector:
    """
    Manages field data collection with offline capability
    """
    
    def __init__(self, base_directory: str = "field_data"):
        self.base_dir = Path(base_directory)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.pending_dir = self.base_dir / "pending"
        self.synced_dir = self.base_dir / "synced"
        self.photos_dir = self.base_dir / "photos"
        self.exports_dir = self.base_dir / "exports"
        
        for dir in [self.pending_dir, self.synced_dir, self.photos_dir, self.exports_dir]:
            dir.mkdir(exist_ok=True)
        
        # Session info
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.pending_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
    
    def create_assessment(self, site_name: str, site_id: str) -> DamageAssessmentForm:
        """Create a new assessment form"""
        assessment = DamageAssessmentForm(
            site_name=site_name,
            site_id=site_id
        )
        return assessment
    
    def add_photo(self, assessment: DamageAssessmentForm, 
                  photo_path: str, caption: str = "", 
                  angle: str = "", extract_gps: bool = True) -> PhotoDocumentation:
        """
        Add a photo to the assessment with metadata extraction
        """
        photo_path = Path(photo_path)
        if not photo_path.exists():
            raise FileNotFoundError(f"Photo not found: {photo_path}")
        
        # Generate unique filename
        file_hash = self._get_file_hash(photo_path)
        ext = photo_path.suffix
        new_filename = f"{assessment.site_id}_{file_hash[:8]}{ext}"
        
        # Copy to photos directory
        dest_path = self.photos_dir / new_filename
        shutil.copy2(photo_path, dest_path)
        
        # Create photo documentation
        photo_doc = PhotoDocumentation(
            filename=new_filename,
            caption=caption,
            angle=angle
        )
        
        # Extract GPS if available
        if extract_gps:
            gps_data = self._extract_gps_from_image(photo_path)
            if gps_data:
                photo_doc.gps_location = gps_data
        
        assessment.photos.append(photo_doc)
        return photo_doc
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate file hash for unique identification"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _extract_gps_from_image(self, image_path: Path) -> Optional[GPSLocation]:
        """Extract GPS coordinates from image EXIF data"""
        try:
            image = Image.open(image_path)
            exifdata = image.getexif()
            
            if not exifdata:
                return None
            
            # Extract GPS info
            gps_info = {}
            for key, val in exifdata.items():
                if key in TAGS:
                    if TAGS[key] == "GPSInfo":
                        gps_data = exifdata.get_ifd(key)
                        for gps_key in gps_data:
                            sub_decoded = GPSTAGS.get(gps_key, gps_key)
                            gps_info[sub_decoded] = gps_data[gps_key]
            
            if not gps_info:
                return None
            
            # Parse GPS coordinates
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                lat = convert_to_degrees(gps_info["GPSLatitude"])
                lon = convert_to_degrees(gps_info["GPSLongitude"])
                
                # Apply hemisphere
                if gps_info.get("GPSLatitudeRef") == "S":
                    lat = -lat
                if gps_info.get("GPSLongitudeRef") == "W":
                    lon = -lon
                
                altitude = None
                if "GPSAltitude" in gps_info:
                    altitude = float(gps_info["GPSAltitude"])
                
                return GPSLocation(
                    latitude=lat,
                    longitude=lon,
                    altitude=altitude
                )
        except Exception as e:
            print(f"Error extracting GPS: {e}")
            return None
    
    def save_assessment(self, assessment: DamageAssessmentForm) -> Path:
        """Save assessment to pending directory"""
        filepath = assessment.save(self.session_dir)
        
        # Also create a backup
        backup_path = self.session_dir / f"backup_{filepath.name}"
        shutil.copy2(filepath, backup_path)
        
        return filepath
    
    def get_pending_assessments(self) -> List[Dict[str, Any]]:
        """Get all pending assessments awaiting sync"""
        pending = []
        
        for session_dir in self.pending_dir.iterdir():
            if session_dir.is_dir():
                for json_file in session_dir.glob("assessment_*.json"):
                    if "backup_" not in json_file.name:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            data['_filepath'] = str(json_file)
                            pending.append(data)
        
        return pending
    
    def mark_as_synced(self, assessment_filepath: str):
        """Move assessment from pending to synced"""
        source = Path(assessment_filepath)
        if source.exists():
            # Move entire session directory
            session_dir = source.parent
            dest_session_dir = self.synced_dir / session_dir.name
            shutil.move(str(session_dir), str(dest_session_dir))
    
    def export_for_offline(self, output_name: str = None) -> Path:
        """
        Export all pending assessments as a bundle for offline transfer
        """
        if not output_name:
            output_name = f"field_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        export_path = self.exports_dir / output_name
        export_path.mkdir(exist_ok=True)
        
        # Copy all pending assessments
        pending_export = export_path / "assessments"
        if self.pending_dir.exists():
            shutil.copytree(self.pending_dir, pending_export)
        
        # Copy all photos
        photos_export = export_path / "photos"
        if self.photos_dir.exists():
            shutil.copytree(self.photos_dir, photos_export)
        
        # Create manifest
        manifest = {
            "export_date": datetime.now().isoformat(),
            "export_name": output_name,
            "assessment_count": len(self.get_pending_assessments()),
            "photo_count": len(list(self.photos_dir.glob("*")))
        }
        
        with open(export_path / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create zip file
        zip_path = self.exports_dir / f"{output_name}.zip"
        shutil.make_archive(str(zip_path.with_suffix('')), 'zip', export_path)
        
        return zip_path
    
    def import_from_offline(self, import_path: str):
        """Import assessments from offline bundle"""
        import_path = Path(import_path)
        
        if import_path.suffix == '.zip':
            # Extract zip
            extract_dir = self.base_dir / "temp_import"
            shutil.unpack_archive(import_path, extract_dir)
            import_path = extract_dir
        
        # Import assessments
        assessments_dir = import_path / "assessments"
        if assessments_dir.exists():
            for item in assessments_dir.iterdir():
                if item.is_dir():
                    dest = self.pending_dir / item.name
                    if not dest.exists():
                        shutil.copytree(item, dest)
        
        # Import photos
        photos_dir = import_path / "photos"
        if photos_dir.exists():
            for photo in photos_dir.glob("*"):
                if photo.is_file():
                    dest = self.photos_dir / photo.name
                    if not dest.exists():
                        shutil.copy2(photo, dest)
        
        # Clean up
        if 'extract_dir' in locals():
            shutil.rmtree(extract_dir)
    
    def generate_field_report(self) -> Dict[str, Any]:
        """Generate summary report of field data collection"""
        assessments = self.get_pending_assessments()
        
        # Categorize by damage level
        damage_summary = {
            "no_damage": 0,
            "slight": 0,
            "moderate": 0,
            "heavy": 0,
            "severe": 0,
            "destroyed": 0
        }
        
        urgency_summary = {
            "immediate": 0,
            "urgent": 0,
            "short_term": 0,
            "medium_term": 0,
            "long_term": 0
        }
        
        site_types = {}
        
        for assessment in assessments:
            # Damage level
            damage = assessment.get('overall_damage', 'ND')
            if damage == 'ND':
                damage_summary['no_damage'] += 1
            elif damage == 'SL':
                damage_summary['slight'] += 1
            elif damage == 'MD':
                damage_summary['moderate'] += 1
            elif damage == 'HV':
                damage_summary['heavy'] += 1
            elif damage == 'SV':
                damage_summary['severe'] += 1
            elif damage == 'DT':
                damage_summary['destroyed'] += 1
            
            # Urgency
            urgency = assessment.get('urgency_level', 'LT')
            if urgency == 'IM':
                urgency_summary['immediate'] += 1
            elif urgency == 'UR':
                urgency_summary['urgent'] += 1
            elif urgency == 'ST':
                urgency_summary['short_term'] += 1
            elif urgency == 'MT':
                urgency_summary['medium_term'] += 1
            elif urgency == 'LT':
                urgency_summary['long_term'] += 1
            
            # Site types
            site_type = assessment.get('site_type', 'Unknown')
            site_types[site_type] = site_types.get(site_type, 0) + 1
        
        report = {
            "summary": {
                "total_assessments": len(assessments),
                "assessment_period": {
                    "start": min([a['assessment_date'] for a in assessments]) if assessments else None,
                    "end": max([a['assessment_date'] for a in assessments]) if assessments else None
                },
                "total_photos": len(list(self.photos_dir.glob("*")))
            },
            "damage_summary": damage_summary,
            "urgency_summary": urgency_summary,
            "site_types": site_types,
            "critical_sites": [
                {
                    "site_name": a['site_name'],
                    "damage": a['overall_damage'],
                    "urgency": a['urgency_level'],
                    "immediate_danger": a.get('immediate_danger', False)
                }
                for a in assessments
                if a.get('immediate_danger') or a.get('urgency_level') in ['IM', 'UR']
            ]
        }
        
        # Save report
        report_path = self.exports_dir / f"field_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report


# Quick assessment function for rapid documentation
def quick_damage_assessment(site_name: str, site_id: str, 
                          overall_damage: str, urgency: str,
                          photos: List[str] = None) -> DamageAssessmentForm:
    """
    Create a quick assessment with minimal required fields
    Useful for rapid field documentation
    """
    damage_map = {
        'none': DamageCategory.NO_DAMAGE,
        'slight': DamageCategory.SLIGHT,
        'moderate': DamageCategory.MODERATE,
        'heavy': DamageCategory.HEAVY,
        'severe': DamageCategory.SEVERE,
        'destroyed': DamageCategory.DESTROYED
    }
    
    urgency_map = {
        'immediate': UrgencyLevel.IMMEDIATE,
        'urgent': UrgencyLevel.URGENT,
        'short': UrgencyLevel.SHORT_TERM,
        'medium': UrgencyLevel.MEDIUM_TERM,
        'long': UrgencyLevel.LONG_TERM
    }
    
    assessment = DamageAssessmentForm(
        site_name=site_name,
        site_id=site_id,
        overall_damage=damage_map.get(overall_damage.lower(), DamageCategory.NO_DAMAGE),
        urgency_level=urgency_map.get(urgency.lower(), UrgencyLevel.LONG_TERM)
    )
    
    # Add photos if provided
    if photos:
        collector = FieldDataCollector()
        for photo_path in photos:
            try:
                collector.add_photo(assessment, photo_path)
            except Exception as e:
                print(f"Error adding photo {photo_path}: {e}")
    
    return assessment