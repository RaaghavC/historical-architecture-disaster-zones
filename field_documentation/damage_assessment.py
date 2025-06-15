"""
Damage Assessment Forms and Categories
Based on UNESCO and ICCROM guidelines for post-earthquake heritage assessment
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import uuid
from pathlib import Path


class DamageCategory(Enum):
    """UNESCO-based damage categories for heritage sites"""
    NO_DAMAGE = "ND"  # No visible damage
    SLIGHT = "SL"     # Slight damage (hairline cracks, minor plaster damage)
    MODERATE = "MD"   # Moderate damage (significant cracks, partial collapse of non-structural elements)
    HEAVY = "HV"      # Heavy damage (partial structural failure, large cracks, partial collapse)
    SEVERE = "SV"     # Severe damage (near total collapse, major structural failure)
    DESTROYED = "DT"  # Destroyed (total collapse)


class UrgencyLevel(Enum):
    """Priority levels for intervention"""
    IMMEDIATE = "IM"      # Immediate action required (24-48 hours)
    URGENT = "UR"         # Urgent (within 1 week)
    SHORT_TERM = "ST"     # Short term (within 1 month)
    MEDIUM_TERM = "MT"    # Medium term (within 6 months)
    LONG_TERM = "LT"      # Long term (can wait)


class StructuralElement(Enum):
    """Key structural elements to assess"""
    FOUNDATION = "foundation"
    WALLS = "walls"
    COLUMNS = "columns"
    ARCHES = "arches"
    DOME = "dome"
    MINARET = "minaret"
    ROOF = "roof"
    FLOOR = "floor"
    STAIRS = "stairs"
    DECORATIVE = "decorative_elements"


@dataclass
class GPSLocation:
    """GPS coordinates with accuracy"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None  # in meters
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PhotoDocumentation:
    """Photo metadata for field documentation"""
    photo_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    caption: str = ""
    angle: str = ""  # N, NE, E, SE, S, SW, W, NW, aerial, interior
    element_documented: Optional[StructuralElement] = None
    damage_visible: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    gps_location: Optional[GPSLocation] = None


@dataclass
class ElementAssessment:
    """Assessment of individual structural element"""
    element: StructuralElement
    damage_category: DamageCategory
    description: str
    photos: List[PhotoDocumentation] = field(default_factory=list)
    intervention_needed: bool = False
    safety_concern: bool = False
    notes: str = ""


@dataclass
class DamageAssessmentForm:
    """
    Complete damage assessment form for a heritage site
    Based on UNESCO/ICCROM post-earthquake assessment guidelines
    """
    # Basic Information
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    site_name: str = ""
    site_id: str = ""  # from heritage database
    alternative_names: List[str] = field(default_factory=list)
    
    # Location
    address: str = ""
    district: str = ""
    gps_location: Optional[GPSLocation] = None
    
    # Site Type and Heritage Value
    site_type: str = ""  # mosque, church, hammam, etc.
    period: str = ""  # Roman, Byzantine, Ottoman, etc.
    heritage_designation: str = ""  # UNESCO, National Monument, etc.
    significance: str = ""  # architectural, historical, religious, etc.
    
    # Assessment Metadata
    assessment_date: datetime = field(default_factory=datetime.now)
    assessor_name: str = ""
    assessor_organization: str = ""
    weather_conditions: str = ""
    
    # Overall Damage Assessment
    overall_damage: DamageCategory = DamageCategory.NO_DAMAGE
    structural_stability: str = ""  # stable, unstable, partially stable
    immediate_danger: bool = False
    urgency_level: UrgencyLevel = UrgencyLevel.LONG_TERM
    
    # Detailed Element Assessment
    element_assessments: List[ElementAssessment] = field(default_factory=list)
    
    # Access and Safety
    site_accessible: bool = True
    access_restrictions: str = ""
    safety_equipment_required: str = ""
    temporary_supports_installed: bool = False
    
    # Previous Damage/Interventions
    previous_earthquakes: str = ""
    previous_restorations: str = ""
    existing_documentation: str = ""
    
    # Recommendations
    immediate_actions: List[str] = field(default_factory=list)
    short_term_interventions: List[str] = field(default_factory=list)
    long_term_restoration: List[str] = field(default_factory=list)
    
    # Documentation
    photos: List[PhotoDocumentation] = field(default_factory=list)
    sketches: List[str] = field(default_factory=list)  # filenames
    
    # Additional Notes
    general_observations: str = ""
    community_concerns: str = ""
    intangible_heritage_impact: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'assessment_id': self.assessment_id,
            'site_name': self.site_name,
            'site_id': self.site_id,
            'alternative_names': self.alternative_names,
            'address': self.address,
            'district': self.district,
            'gps_location': {
                'latitude': self.gps_location.latitude,
                'longitude': self.gps_location.longitude,
                'altitude': self.gps_location.altitude,
                'accuracy': self.gps_location.accuracy,
                'timestamp': self.gps_location.timestamp.isoformat()
            } if self.gps_location else None,
            'site_type': self.site_type,
            'period': self.period,
            'heritage_designation': self.heritage_designation,
            'significance': self.significance,
            'assessment_date': self.assessment_date.isoformat(),
            'assessor_name': self.assessor_name,
            'assessor_organization': self.assessor_organization,
            'weather_conditions': self.weather_conditions,
            'overall_damage': self.overall_damage.value,
            'structural_stability': self.structural_stability,
            'immediate_danger': self.immediate_danger,
            'urgency_level': self.urgency_level.value,
            'element_assessments': [
                {
                    'element': ea.element.value,
                    'damage_category': ea.damage_category.value,
                    'description': ea.description,
                    'photos': [
                        {
                            'photo_id': p.photo_id,
                            'filename': p.filename,
                            'caption': p.caption,
                            'angle': p.angle,
                            'element_documented': p.element_documented.value if p.element_documented else None,
                            'damage_visible': p.damage_visible,
                            'timestamp': p.timestamp.isoformat()
                        } for p in ea.photos
                    ],
                    'intervention_needed': ea.intervention_needed,
                    'safety_concern': ea.safety_concern,
                    'notes': ea.notes
                } for ea in self.element_assessments
            ],
            'site_accessible': self.site_accessible,
            'access_restrictions': self.access_restrictions,
            'safety_equipment_required': self.safety_equipment_required,
            'temporary_supports_installed': self.temporary_supports_installed,
            'previous_earthquakes': self.previous_earthquakes,
            'previous_restorations': self.previous_restorations,
            'existing_documentation': self.existing_documentation,
            'immediate_actions': self.immediate_actions,
            'short_term_interventions': self.short_term_interventions,
            'long_term_restoration': self.long_term_restoration,
            'photos': [
                {
                    'photo_id': p.photo_id,
                    'filename': p.filename,
                    'caption': p.caption,
                    'angle': p.angle,
                    'timestamp': p.timestamp.isoformat()
                } for p in self.photos
            ],
            'sketches': self.sketches,
            'general_observations': self.general_observations,
            'community_concerns': self.community_concerns,
            'intangible_heritage_impact': self.intangible_heritage_impact
        }
    
    def save(self, directory: Path):
        """Save assessment to JSON file"""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        filename = f"assessment_{self.site_id}_{self.assessment_date.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = directory / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def calculate_priority_score(self) -> float:
        """
        Calculate a priority score for intervention based on multiple factors
        Returns a score from 0-100 (100 being highest priority)
        """
        score = 0.0
        
        # Damage severity (40 points max)
        damage_scores = {
            DamageCategory.NO_DAMAGE: 0,
            DamageCategory.SLIGHT: 10,
            DamageCategory.MODERATE: 20,
            DamageCategory.HEAVY: 30,
            DamageCategory.SEVERE: 35,
            DamageCategory.DESTROYED: 40
        }
        score += damage_scores.get(self.overall_damage, 0)
        
        # Urgency level (30 points max)
        urgency_scores = {
            UrgencyLevel.IMMEDIATE: 30,
            UrgencyLevel.URGENT: 25,
            UrgencyLevel.SHORT_TERM: 15,
            UrgencyLevel.MEDIUM_TERM: 10,
            UrgencyLevel.LONG_TERM: 5
        }
        score += urgency_scores.get(self.urgency_level, 0)
        
        # Safety concerns (20 points max)
        if self.immediate_danger:
            score += 20
        elif self.structural_stability == "unstable":
            score += 15
        elif self.structural_stability == "partially stable":
            score += 10
        
        # Heritage value (10 points max)
        if "UNESCO" in self.heritage_designation:
            score += 10
        elif "National" in self.heritage_designation:
            score += 7
        else:
            score += 3
        
        return min(score, 100.0)


# Pre-defined templates for common Antakya heritage types
MOSQUE_TEMPLATE = DamageAssessmentForm(
    site_type="Mosque",
    element_assessments=[
        ElementAssessment(element=StructuralElement.FOUNDATION, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.WALLS, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.MINARET, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.DOME, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.ARCHES, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.DECORATIVE, damage_category=DamageCategory.NO_DAMAGE, description="Mihrab, minbar, calligraphy")
    ]
)

CHURCH_TEMPLATE = DamageAssessmentForm(
    site_type="Church",
    element_assessments=[
        ElementAssessment(element=StructuralElement.FOUNDATION, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.WALLS, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.DOME, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.ARCHES, damage_category=DamageCategory.NO_DAMAGE, description=""),
        ElementAssessment(element=StructuralElement.DECORATIVE, damage_category=DamageCategory.NO_DAMAGE, description="Frescoes, mosaics, iconostasis")
    ]
)