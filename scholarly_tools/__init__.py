"""
Scholarly Tools for Architectural History Research
Tools designed for academic research on Islamic and Byzantine architecture
"""

from .annotation_system import (
    ArchitecturalAnnotation,
    ScholarlyAnnotationManager,
    ArchitecturalElement,
    ScholarlyField,
    BibliographicReference,
    create_mosque_annotation,
    create_church_annotation
)

from .architectural_typology import (
    ArchitecturalTypology,
    TypologyDatabase,
    BuildingType,
    Period,
    MosqueType,
    ChurchType,
    RegionalStyle,
    create_habib_neccar_typology
)

from .citation_generator import (
    CitationGenerator,
    CitationStyle,
    ResourceType,
    CitationData,
    cite_archnet_image,
    cite_salt_photograph,
    cite_kiel_archive,
    create_figure_list
)

__all__ = [
    # Annotation system
    'ArchitecturalAnnotation',
    'ScholarlyAnnotationManager',
    'ArchitecturalElement',
    'ScholarlyField',
    'BibliographicReference',
    'create_mosque_annotation',
    'create_church_annotation',
    
    # Typology system
    'ArchitecturalTypology',
    'TypologyDatabase',
    'BuildingType',
    'Period',
    'MosqueType',
    'ChurchType',
    'RegionalStyle',
    'create_habib_neccar_typology',
    
    # Citation system
    'CitationGenerator',
    'CitationStyle',
    'ResourceType',
    'CitationData',
    'cite_archnet_image',
    'cite_salt_photograph',
    'cite_kiel_archive',
    'create_figure_list'
]