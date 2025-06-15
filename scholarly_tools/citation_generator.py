"""
Academic Citation Generator for Heritage Documentation
Supports Chicago, MLA, and specialized formats for architectural history
Author: Prof. Patricia Blessing
"""

import re
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum


class CitationStyle(Enum):
    """Academic citation styles"""
    CHICAGO_NOTES = "Chicago Notes-Bibliography"
    CHICAGO_AUTHOR_DATE = "Chicago Author-Date"
    MLA = "MLA 9th Edition"
    APA = "APA 7th Edition"
    HARVARD = "Harvard"
    OXFORD = "Oxford"
    

class ResourceType(Enum):
    """Types of resources for citation"""
    PHOTOGRAPH = "photograph"
    ARCHIVE_ITEM = "archive_item"
    DIGITAL_IMAGE = "digital_image"
    MANUSCRIPT = "manuscript"
    BOOK = "book"
    JOURNAL_ARTICLE = "journal_article"
    WEBSITE = "website"
    DATABASE_ENTRY = "database_entry"
    ARCHAEOLOGICAL_REPORT = "archaeological_report"
    ARCHITECTURAL_DRAWING = "architectural_drawing"


@dataclass
class CitationData:
    """Data needed for generating citations"""
    # Basic information
    resource_type: ResourceType
    title: str
    
    # Author/Creator
    creator: Optional[str] = None  # Photographer, author, etc.
    creator_role: Optional[str] = None  # "photographer", "architect", etc.
    
    # Publication/Archive info
    archive_name: Optional[str] = None
    collection: Optional[str] = None
    item_number: Optional[str] = None
    publisher: Optional[str] = None
    place_of_publication: Optional[str] = None
    
    # Dates
    date_created: Optional[datetime] = None
    date_accessed: Optional[datetime] = None
    publication_date: Optional[str] = None
    
    # Online resources
    url: Optional[str] = None
    database_name: Optional[str] = None
    doi: Optional[str] = None
    
    # Additional info
    page_numbers: Optional[str] = None
    figure_number: Optional[str] = None
    dimensions: Optional[str] = None
    medium: Optional[str] = None
    
    # For manuscripts/archives
    folio_numbers: Optional[str] = None
    box_folder: Optional[str] = None
    
    # For architectural items
    building_name: Optional[str] = None
    location: Optional[str] = None
    
    # Notes
    additional_notes: Optional[str] = None


class CitationGenerator:
    """Generate academic citations for heritage documentation"""
    
    def __init__(self, default_style: CitationStyle = CitationStyle.CHICAGO_NOTES):
        self.default_style = default_style
        
    def generate_citation(self, data: CitationData, style: Optional[CitationStyle] = None) -> str:
        """Generate citation in specified style"""
        if not style:
            style = self.default_style
            
        if style == CitationStyle.CHICAGO_NOTES:
            return self._chicago_notes(data)
        elif style == CitationStyle.CHICAGO_AUTHOR_DATE:
            return self._chicago_author_date(data)
        elif style == CitationStyle.MLA:
            return self._mla(data)
        else:
            return self._chicago_notes(data)  # Default fallback
    
    def _chicago_notes(self, data: CitationData) -> str:
        """Generate Chicago Notes-Bibliography style citation"""
        citation_parts = []
        
        if data.resource_type == ResourceType.PHOTOGRAPH:
            # Photographer
            if data.creator:
                citation_parts.append(f"{data.creator}")
                if data.creator_role and data.creator_role != "photographer":
                    citation_parts[-1] += f" ({data.creator_role})"
                citation_parts[-1] += ","
            
            # Title
            if data.title:
                citation_parts.append(f'"{data.title},"')
            
            # Date
            if data.date_created:
                citation_parts.append(f"{data.date_created.year},")
            elif data.publication_date:
                citation_parts.append(f"{data.publication_date},")
            
            # Medium
            if data.medium:
                citation_parts.append(f"{data.medium},")
            
            # Archive information
            if data.archive_name:
                archive_info = []
                if data.collection:
                    archive_info.append(data.collection)
                if data.item_number:
                    archive_info.append(f"no. {data.item_number}")
                if data.box_folder:
                    archive_info.append(data.box_folder)
                
                if archive_info:
                    citation_parts.append(f"{', '.join(archive_info)},")
                citation_parts.append(f"{data.archive_name}")
                
                if data.place_of_publication:
                    citation_parts[-1] += f", {data.place_of_publication}"
                citation_parts[-1] += "."
            
        elif data.resource_type == ResourceType.DIGITAL_IMAGE:
            # Creator/Database
            if data.creator:
                citation_parts.append(f"{data.creator},")
            
            # Title
            if data.title:
                citation_parts.append(f'"{data.title},"')
            
            # Date
            if data.date_created:
                citation_parts.append(f"{data.date_created.year},")
            
            # Database/Website
            if data.database_name:
                citation_parts.append(f"{data.database_name},")
            elif data.archive_name:
                citation_parts.append(f"{data.archive_name},")
            
            # URL and access date
            if data.url:
                citation_parts.append(data.url)
                if data.date_accessed:
                    citation_parts.append(f"(accessed {self._format_date(data.date_accessed)})")
                citation_parts[-1] += "."
                
        elif data.resource_type == ResourceType.ARCHIVE_ITEM:
            # Title or description
            if data.title:
                citation_parts.append(f'"{data.title},"')
            
            # Date
            if data.date_created:
                citation_parts.append(f"{data.date_created.year},")
            
            # Collection details
            if data.collection:
                citation_parts.append(f"{data.collection},")
            
            if data.item_number:
                citation_parts.append(f"item {data.item_number},")
            elif data.folio_numbers:
                citation_parts.append(f"fols. {data.folio_numbers},")
            
            if data.box_folder:
                citation_parts.append(f"{data.box_folder},")
            
            # Archive
            if data.archive_name:
                citation_parts.append(data.archive_name)
                if data.place_of_publication:
                    citation_parts[-1] += f", {data.place_of_publication}"
                citation_parts[-1] += "."
        
        elif data.resource_type == ResourceType.ARCHITECTURAL_DRAWING:
            # Creator
            if data.creator:
                citation_parts.append(f"{data.creator},")
            
            # Title
            if data.title:
                citation_parts.append(f'"{data.title},"')
            elif data.building_name:
                citation_parts.append(f'"Drawing of {data.building_name},"')
            
            # Date
            if data.date_created:
                citation_parts.append(f"{data.date_created.year},")
            
            # Medium
            if data.medium:
                citation_parts.append(f"{data.medium},")
            
            # Dimensions
            if data.dimensions:
                citation_parts.append(f"{data.dimensions},")
            
            # Archive
            if data.archive_name:
                if data.collection:
                    citation_parts.append(f"{data.collection},")
                citation_parts.append(data.archive_name)
                if data.place_of_publication:
                    citation_parts[-1] += f", {data.place_of_publication}"
                citation_parts[-1] += "."
        
        # Add notes if any
        if data.additional_notes:
            citation_parts.append(data.additional_notes)
        
        return " ".join(citation_parts)
    
    def _chicago_author_date(self, data: CitationData) -> str:
        """Generate Chicago Author-Date style citation"""
        citation_parts = []
        
        # Author
        if data.creator:
            citation_parts.append(f"{data.creator}.")
        
        # Year
        year = None
        if data.date_created:
            year = data.date_created.year
        elif data.publication_date:
            year = data.publication_date
        
        if year:
            citation_parts.append(f"{year}.")
        
        # Title
        if data.title:
            citation_parts.append(f'"{data.title}."')
        
        # Rest similar to notes style but reordered
        if data.archive_name:
            archive_parts = []
            if data.collection:
                archive_parts.append(data.collection)
            if data.item_number:
                archive_parts.append(f"no. {data.item_number}")
            
            if archive_parts:
                citation_parts.append(f"{', '.join(archive_parts)}.")
            citation_parts.append(f"{data.archive_name}")
            if data.place_of_publication:
                citation_parts[-1] += f", {data.place_of_publication}"
            citation_parts[-1] += "."
        
        if data.url and data.date_accessed:
            citation_parts.append(f"Accessed {self._format_date(data.date_accessed)}.")
            citation_parts.append(data.url)
        
        return " ".join(citation_parts)
    
    def _mla(self, data: CitationData) -> str:
        """Generate MLA style citation"""
        citation_parts = []
        
        # Creator
        if data.creator:
            # Last name, First name format
            name_parts = data.creator.split()
            if len(name_parts) > 1:
                citation_parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}.")
            else:
                citation_parts.append(f"{data.creator}.")
        
        # Title
        if data.title:
            if data.resource_type in [ResourceType.PHOTOGRAPH, ResourceType.DIGITAL_IMAGE]:
                citation_parts.append(f'"{data.title}."')
            else:
                citation_parts.append(f"*{data.title}.*")
        
        # Container (archive/database)
        if data.archive_name:
            citation_parts.append(f"*{data.archive_name}*,")
        
        # Publisher info
        if data.publisher:
            citation_parts.append(f"{data.publisher},")
        
        # Date
        if data.date_created:
            citation_parts.append(f"{data.date_created.year},")
        elif data.publication_date:
            citation_parts.append(f"{data.publication_date},")
        
        # Location (for physical items)
        if data.collection:
            citation_parts.append(f"{data.collection},")
        
        if data.item_number:
            citation_parts.append(f"item {data.item_number}.")
        
        # URL
        if data.url:
            citation_parts.append(data.url + ".")
        
        # Access date
        if data.date_accessed:
            citation_parts.append(f"Accessed {self._format_date(data.date_accessed, 'mla')}.")
        
        return " ".join(citation_parts)
    
    def _format_date(self, date: datetime, style: str = "chicago") -> str:
        """Format date according to citation style"""
        if style == "mla":
            return date.strftime("%-d %b. %Y")
        else:  # Chicago
            return date.strftime("%B %-d, %Y")
    
    def create_image_caption(self, data: CitationData) -> str:
        """Create a figure caption for academic publication"""
        caption_parts = []
        
        # Figure number
        if data.figure_number:
            caption_parts.append(f"Figure {data.figure_number}.")
        
        # Building/subject
        if data.building_name:
            caption_parts.append(data.building_name)
            if data.location:
                caption_parts[-1] += f", {data.location}"
            caption_parts[-1] += "."
        elif data.title:
            caption_parts.append(f"{data.title}.")
        
        # Creator and date
        attribution = []
        if data.creator:
            attribution.append(f"Photo: {data.creator}")
        if data.date_created:
            attribution.append(f"{data.date_created.year}")
        elif data.publication_date:
            attribution.append(data.publication_date)
        
        if attribution:
            caption_parts.append(f"({', '.join(attribution)}).")
        
        # Source
        if data.archive_name:
            source_parts = []
            if data.collection:
                source_parts.append(data.collection)
            if data.item_number:
                source_parts.append(f"no. {data.item_number}")
            
            if source_parts:
                caption_parts.append(f"Source: {', '.join(source_parts)},")
                caption_parts.append(f"{data.archive_name}.")
            else:
                caption_parts.append(f"Source: {data.archive_name}.")
        
        return " ".join(caption_parts)
    
    def create_bibliography_entry(self, citations: List[str], style: CitationStyle = None) -> str:
        """Format multiple citations as bibliography"""
        if not style:
            style = self.default_style
        
        # Sort alphabetically
        sorted_citations = sorted(citations)
        
        if style in [CitationStyle.CHICAGO_NOTES, CitationStyle.CHICAGO_AUTHOR_DATE]:
            # Hanging indent style
            formatted = []
            for citation in sorted_citations:
                formatted.append(citation)
            return "\n\n".join(formatted)
        else:
            return "\n".join(sorted_citations)


# Specific citation creators for common archives
def cite_archnet_image(item_id: str, title: str, url: str, accessed: datetime = None) -> str:
    """Create citation for ArchNet image"""
    if not accessed:
        accessed = datetime.now()
    
    data = CitationData(
        resource_type=ResourceType.DIGITAL_IMAGE,
        title=title,
        database_name="ArchNet",
        url=url,
        date_accessed=accessed,
        item_number=item_id
    )
    
    generator = CitationGenerator()
    return generator.generate_citation(data)


def cite_salt_photograph(title: str, photographer: str = None, 
                        date: str = None, collection: str = None,
                        item_no: str = None) -> str:
    """Create citation for SALT Research photograph"""
    data = CitationData(
        resource_type=ResourceType.PHOTOGRAPH,
        title=title,
        creator=photographer,
        publication_date=date,
        archive_name="SALT Research",
        place_of_publication="Istanbul",
        collection=collection,
        item_number=item_no
    )
    
    generator = CitationGenerator()
    return generator.generate_citation(data)


def cite_kiel_archive(building_name: str, location: str, 
                     photo_date: str = None, accessed: datetime = None) -> str:
    """Create citation for Machiel Kiel Archive photograph"""
    data = CitationData(
        resource_type=ResourceType.PHOTOGRAPH,
        title=f"{building_name}, {location}",
        creator="Machiel Kiel",
        creator_role="photographer",
        publication_date=photo_date,
        archive_name="Machiel Kiel Photographic Archive, Netherlands Institute in Turkey",
        place_of_publication="Istanbul",
        date_accessed=accessed
    )
    
    generator = CitationGenerator()
    return generator.generate_citation(data)


def create_figure_list(figures: List[Dict[str, any]]) -> str:
    """Create a list of figures for publication"""
    generator = CitationGenerator()
    figure_list = []
    
    for i, fig in enumerate(figures, 1):
        data = CitationData(
            resource_type=fig.get('type', ResourceType.PHOTOGRAPH),
            figure_number=str(i),
            title=fig.get('title'),
            building_name=fig.get('building'),
            location=fig.get('location'),
            creator=fig.get('photographer'),
            date_created=fig.get('date'),
            archive_name=fig.get('archive'),
            collection=fig.get('collection'),
            item_number=fig.get('item_number')
        )
        
        caption = generator.create_image_caption(data)
        figure_list.append(caption)
    
    return "\n\n".join(figure_list)