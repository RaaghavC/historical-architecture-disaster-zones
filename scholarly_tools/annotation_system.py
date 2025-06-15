"""
Scholarly Annotation System for Architectural Research
Designed for academic research on Islamic and Byzantine architecture
Author: Prof. Patricia Blessing
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class ArchitecturalElement(Enum):
    """Standardized architectural elements for consistent tagging"""
    # Structural Elements
    DOME = "dome"
    SEMI_DOME = "semi_dome"
    PENDENTIVE = "pendentive"
    SQUINCH = "squinch"
    ARCH = "arch"
    VAULT = "vault"
    COLUMN = "column"
    PIER = "pier"
    CAPITAL = "capital"
    
    # Islamic Architecture
    MIHRAB = "mihrab"
    MINBAR = "minbar"
    MINARET = "minaret"
    QIBLA_WALL = "qibla_wall"
    SAHN = "sahn"
    RIWAQ = "riwaq"
    DIKKA = "dikka"
    SHADIRVAN = "shadirvan"
    
    # Byzantine/Christian
    APSE = "apse"
    NARTHEX = "narthex"
    NAOS = "naos"
    BEMA = "bema"
    SYNTHRONON = "synthronon"
    ICONOSTASIS = "iconostasis"
    AMBO = "ambo"
    
    # Decorative Elements
    MUQARNAS = "muqarnas"
    CALLIGRAPHY = "calligraphy"
    GEOMETRIC_PATTERN = "geometric_pattern"
    VEGETAL_PATTERN = "vegetal_pattern"
    FIGURATIVE = "figurative"
    MOSAIC = "mosaic"
    FRESCO = "fresco"
    STUCCO = "stucco"
    TILEWORK = "tilework"
    
    # Spatial Elements
    PORTAL = "portal"
    WINDOW = "window"
    DOOR = "door"
    COURTYARD = "courtyard"
    FOUNTAIN = "fountain"
    IWAN = "iwan"


class ScholarlyField(Enum):
    """Academic fields of analysis"""
    ARCHITECTURAL_HISTORY = "architectural_history"
    ART_HISTORY = "art_history"
    ARCHAEOLOGY = "archaeology"
    EPIGRAPHY = "epigraphy"
    CONSERVATION = "conservation"
    STRUCTURAL_ANALYSIS = "structural_analysis"
    ICONOGRAPHY = "iconography"
    LITURGY = "liturgy"
    SOCIAL_HISTORY = "social_history"


@dataclass
class BibliographicReference:
    """Scholarly citation"""
    citation_key: str  # e.g., "Blessing2022"
    full_citation: str  # Full bibliographic entry
    ref_type: str = "article"  # article, book, chapter, etc.
    page_numbers: Optional[str] = None
    notes: Optional[str] = None
    
    def to_chicago_note(self) -> str:
        """Format as Chicago Manual of Style footnote"""
        if self.page_numbers:
            return f"{self.full_citation}, {self.page_numbers}."
        return f"{self.full_citation}."


@dataclass
class ArchitecturalAnnotation:
    """
    Detailed scholarly annotation for architectural features
    Following art historical methodology
    """
    annotation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""  # ID of the item being annotated
    author: str = ""  # Scholar making the annotation
    author_orcid: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Classification
    elements: List[ArchitecturalElement] = field(default_factory=list)
    fields: List[ScholarlyField] = field(default_factory=list)
    
    # Dating and Chronology
    date_assessment: Optional[str] = None  # e.g., "Late 12th century based on muqarnas type"
    period: Optional[str] = None  # e.g., "Ayyubid", "Middle Byzantine"
    construction_phases: List[str] = field(default_factory=list)
    
    # Detailed Analysis
    description: str = ""  # Detailed architectural description
    iconographic_program: Optional[str] = None
    patronage: Optional[str] = None  # Patron information if known
    inscriptions: List[Dict[str, str]] = field(default_factory=list)  # Text and translation
    
    # Comparative Analysis
    comparanda: List[str] = field(default_factory=list)  # Similar monuments
    influences: List[str] = field(default_factory=list)  # Architectural influences
    
    # Condition and Conservation
    condition_assessment: Optional[str] = None
    previous_restorations: List[str] = field(default_factory=list)
    conservation_recommendations: Optional[str] = None
    
    # References
    bibliography: List[BibliographicReference] = field(default_factory=list)
    archival_sources: List[str] = field(default_factory=list)
    
    # Research Metadata
    research_project: Optional[str] = None
    funding_acknowledgment: Optional[str] = None
    peer_reviewed: bool = False
    version: int = 1
    
    def add_bibliographic_reference(self, citation: str, key: str = None, pages: str = None):
        """Add a scholarly reference"""
        if not key:
            # Generate key from citation (e.g., "Author2023")
            key = citation.split()[0] + citation[-4:]
        
        ref = BibliographicReference(
            citation_key=key,
            full_citation=citation,
            page_numbers=pages
        )
        self.bibliography.append(ref)
    
    def add_inscription(self, text: str, translation: str = None, 
                       script: str = "Arabic", location: str = None):
        """Add epigraphic documentation"""
        inscription = {
            'text': text,
            'translation': translation,
            'script': script,
            'location': location,  # e.g., "mihrab arch, left side"
            'transcriber': self.author,
            'date_transcribed': datetime.now().isoformat()
        }
        self.inscriptions.append(inscription)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'annotation_id': self.annotation_id,
            'item_id': self.item_id,
            'author': self.author,
            'author_orcid': self.author_orcid,
            'timestamp': self.timestamp.isoformat(),
            'elements': [e.value for e in self.elements],
            'fields': [f.value for f in self.fields],
            'date_assessment': self.date_assessment,
            'period': self.period,
            'construction_phases': self.construction_phases,
            'description': self.description,
            'iconographic_program': self.iconographic_program,
            'patronage': self.patronage,
            'inscriptions': self.inscriptions,
            'comparanda': self.comparanda,
            'influences': self.influences,
            'condition_assessment': self.condition_assessment,
            'previous_restorations': self.previous_restorations,
            'conservation_recommendations': self.conservation_recommendations,
            'bibliography': [
                {
                    'key': ref.citation_key,
                    'citation': ref.full_citation,
                    'pages': ref.page_numbers,
                    'notes': ref.notes
                } for ref in self.bibliography
            ],
            'archival_sources': self.archival_sources,
            'research_project': self.research_project,
            'funding_acknowledgment': self.funding_acknowledgment,
            'peer_reviewed': self.peer_reviewed,
            'version': self.version
        }


class ScholarlyAnnotationManager:
    """Manage scholarly annotations for research project"""
    
    def __init__(self, base_directory: str = "scholarly_annotations"):
        self.base_dir = Path(base_directory)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.annotations_file = self.base_dir / "annotations.json"
        self.load_annotations()
    
    def load_annotations(self):
        """Load existing annotations"""
        if self.annotations_file.exists():
            with open(self.annotations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.annotations = {
                    ann['annotation_id']: ann for ann in data
                }
        else:
            self.annotations = {}
    
    def save_annotations(self):
        """Save all annotations"""
        data = list(self.annotations.values())
        with open(self.annotations_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_annotation(self, annotation: ArchitecturalAnnotation):
        """Add or update annotation"""
        # Check if updating existing
        existing = self.get_annotations_for_item(annotation.item_id, annotation.author)
        if existing:
            # Increment version
            annotation.version = max(ann['version'] for ann in existing) + 1
        
        self.annotations[annotation.annotation_id] = annotation.to_dict()
        self.save_annotations()
    
    def get_annotations_for_item(self, item_id: str, author: str = None) -> List[Dict]:
        """Get all annotations for a specific item"""
        annotations = [
            ann for ann in self.annotations.values()
            if ann['item_id'] == item_id
        ]
        
        if author:
            annotations = [
                ann for ann in annotations
                if ann['author'] == author
            ]
        
        return sorted(annotations, key=lambda x: x['version'], reverse=True)
    
    def search_annotations(self, 
                          elements: List[ArchitecturalElement] = None,
                          period: str = None,
                          author: str = None,
                          keywords: List[str] = None) -> List[Dict]:
        """Search annotations by various criteria"""
        results = list(self.annotations.values())
        
        if elements:
            element_values = [e.value for e in elements]
            results = [
                ann for ann in results
                if any(elem in ann['elements'] for elem in element_values)
            ]
        
        if period:
            results = [
                ann for ann in results
                if ann.get('period') and period.lower() in ann['period'].lower()
            ]
        
        if author:
            results = [
                ann for ann in results
                if author.lower() in ann['author'].lower()
            ]
        
        if keywords:
            results = [
                ann for ann in results
                if any(
                    keyword.lower() in ann.get('description', '').lower() or
                    keyword.lower() in ann.get('iconographic_program', '').lower()
                    for keyword in keywords
                )
            ]
        
        return results
    
    def generate_bibliography(self, item_ids: List[str] = None) -> List[str]:
        """Generate consolidated bibliography from annotations"""
        all_refs = {}
        
        annotations = self.annotations.values()
        if item_ids:
            annotations = [
                ann for ann in annotations
                if ann['item_id'] in item_ids
            ]
        
        for ann in annotations:
            for ref in ann.get('bibliography', []):
                key = ref['key']
                if key not in all_refs:
                    all_refs[key] = ref['citation']
        
        # Sort alphabetically
        return sorted(all_refs.values())
    
    def export_for_publication(self, item_id: str, format: str = "markdown") -> str:
        """Export annotations in publication-ready format"""
        annotations = self.get_annotations_for_item(item_id)
        
        if not annotations:
            return ""
        
        # Use most recent version
        ann = annotations[0]
        
        if format == "markdown":
            output = f"# Architectural Analysis: {item_id}\n\n"
            output += f"**Author**: {ann['author']}\n"
            output += f"**Date**: {ann['timestamp']}\n\n"
            
            if ann.get('period'):
                output += f"**Period**: {ann['period']}\n"
            
            if ann.get('date_assessment'):
                output += f"**Dating**: {ann['date_assessment']}\n\n"
            
            output += "## Architectural Elements\n"
            for elem in ann.get('elements', []):
                output += f"- {elem.replace('_', ' ').title()}\n"
            
            output += f"\n## Description\n{ann.get('description', '')}\n"
            
            if ann.get('iconographic_program'):
                output += f"\n## Iconographic Program\n{ann['iconographic_program']}\n"
            
            if ann.get('inscriptions'):
                output += "\n## Inscriptions\n"
                for i, insc in enumerate(ann['inscriptions'], 1):
                    output += f"\n### Inscription {i}\n"
                    output += f"**Text**: {insc['text']}\n"
                    if insc.get('translation'):
                        output += f"**Translation**: {insc['translation']}\n"
                    if insc.get('location'):
                        output += f"**Location**: {insc['location']}\n"
            
            if ann.get('bibliography'):
                output += "\n## Bibliography\n"
                for ref in ann['bibliography']:
                    output += f"- {ref['citation']}"
                    if ref.get('pages'):
                        output += f", {ref['pages']}"
                    output += "\n"
            
            return output
        
        return ""


# Quick annotation templates for common monument types
def create_mosque_annotation(item_id: str, author: str) -> ArchitecturalAnnotation:
    """Template for mosque annotation"""
    annotation = ArchitecturalAnnotation(
        item_id=item_id,
        author=author,
        fields=[ScholarlyField.ARCHITECTURAL_HISTORY, ScholarlyField.ART_HISTORY]
    )
    
    # Common mosque elements to check
    annotation.elements = [
        ArchitecturalElement.MIHRAB,
        ArchitecturalElement.MINBAR,
        ArchitecturalElement.QIBLA_WALL
    ]
    
    return annotation


def create_church_annotation(item_id: str, author: str) -> ArchitecturalAnnotation:
    """Template for church annotation"""
    annotation = ArchitecturalAnnotation(
        item_id=item_id,
        author=author,
        fields=[ScholarlyField.ARCHITECTURAL_HISTORY, ScholarlyField.LITURGY]
    )
    
    # Common church elements
    annotation.elements = [
        ArchitecturalElement.APSE,
        ArchitecturalElement.NAOS,
        ArchitecturalElement.NARTHEX
    ]
    
    return annotation