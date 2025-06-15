"""
Architectural Typology Classification System
Based on established art historical scholarship for Islamic and Byzantine architecture
Author: Prof. Patricia Blessing
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
import json
from pathlib import Path


class Period(Enum):
    """Historical periods for Anatolia and Syria"""
    # Byzantine Periods
    EARLY_BYZANTINE = "Early Byzantine (330-610)"
    MIDDLE_BYZANTINE = "Middle Byzantine (610-1081)"
    LATE_BYZANTINE = "Late Byzantine (1081-1453)"
    
    # Islamic Periods
    UMAYYAD = "Umayyad (661-750)"
    ABBASID = "Abbasid (750-1258)"
    SELJUK = "Seljuk (1037-1308)"
    AYYUBID = "Ayyubid (1171-1260)"
    MAMLUK = "Mamluk (1250-1517)"
    OTTOMAN_EARLY = "Early Ottoman (1299-1453)"
    OTTOMAN_CLASSICAL = "Classical Ottoman (1453-1603)"
    OTTOMAN_LATE = "Late Ottoman (1603-1923)"
    
    # Transitional
    ROMANO_BYZANTINE = "Romano-Byzantine (300-600)"
    CRUSADER = "Crusader (1098-1291)"
    BEYLIK = "Beylik Period (1071-1453)"


class BuildingType(Enum):
    """Primary building typologies"""
    # Religious - Islamic
    MOSQUE = "Mosque"
    MASJID = "Masjid (small mosque)"
    MUSALLA = "Musalla (open-air prayer space)"
    MADRASA = "Madrasa"
    KHANQAH = "Khanqah"
    ZAWIYA = "Zawiya"
    TEKKE = "Tekke"
    TURBE = "Turbe (tomb)"
    
    # Religious - Christian
    CHURCH = "Church"
    BASILICA = "Basilica"
    CHAPEL = "Chapel"
    MONASTERY = "Monastery"
    BAPTISTERY = "Baptistery"
    MARTYRION = "Martyrion"
    
    # Commercial
    BEDESTEN = "Bedesten"
    HAN = "Han (urban)"
    CARAVANSERAI = "Caravanserai (rural)"
    ARASTA = "Arasta"
    MARKET = "Market/Bazaar"
    
    # Public/Civic
    HAMAM = "Hamam"
    SEBIL = "Sebil"
    CESME = "Cesme (fountain)"
    MEKTEP = "Mektep (school)"
    DARUSSIFA = "Darussifa (hospital)"
    IMARET = "Imaret (soup kitchen)"
    
    # Fortification
    CASTLE = "Castle/Fortress"
    CITY_WALLS = "City Walls"
    TOWER = "Tower"
    GATE = "Gate"
    
    # Infrastructure
    BRIDGE = "Bridge"
    AQUEDUCT = "Aqueduct"
    CISTERN = "Cistern"


class MosqueType(Enum):
    """Specific mosque typologies following Kuban/Goodwin classification"""
    HYPOSTYLE = "Hypostyle"
    SINGLE_DOME = "Single dome"
    MULTI_DOME = "Multi-dome"
    T_PLAN = "T-plan (inverted T)"
    COURTYARD = "Courtyard mosque"
    BASILICAL = "Basilical plan"
    CENTRALIZED = "Centralized plan"
    OTTOMAN_IMPERIAL = "Ottoman Imperial type"


class ChurchType(Enum):
    """Church plan typologies"""
    BASILICA = "Basilica"
    CROSS_IN_SQUARE = "Cross-in-square"
    INSCRIBED_CROSS = "Inscribed cross"
    CENTRALIZED = "Centralized"
    DOMED_BASILICA = "Domed basilica"
    CROSS_DOMED = "Cross-domed"
    SINGLE_NAVE = "Single nave"
    HALL_CHURCH = "Hall church"
    CAVE_CHURCH = "Cave church"


@dataclass
class RegionalStyle:
    """Regional architectural characteristics"""
    region: str
    characteristics: List[str]
    typical_materials: List[str]
    distinctive_features: List[str]
    major_examples: List[str]


@dataclass
class ArchitecturalTypology:
    """
    Complete architectural typology for a monument
    Following established art historical classifications
    """
    monument_id: str
    monument_name: str
    
    # Primary Classification
    building_type: BuildingType
    specific_type: Optional[str] = None  # e.g., MosqueType or ChurchType
    
    # Chronology
    period: Period
    construction_date: Optional[str] = None  # Can be precise or range
    construction_phases: List[Dict[str, str]] = field(default_factory=list)
    
    # Spatial Organization
    plan_type: str = ""  # Detailed plan description
    spatial_hierarchy: List[str] = field(default_factory=list)  # Main spaces in order
    orientation: Optional[str] = None  # e.g., "SE qibla orientation"
    
    # Structural System
    structural_system: str = ""  # e.g., "Load-bearing masonry"
    roofing_system: List[str] = field(default_factory=list)  # e.g., ["dome on pendentives", "barrel vault"]
    support_system: List[str] = field(default_factory=list)  # e.g., ["columns", "piers"]
    
    # Materials and Techniques
    primary_materials: List[str] = field(default_factory=list)
    construction_technique: str = ""
    decorative_techniques: List[str] = field(default_factory=list)
    
    # Regional Classification
    regional_style: Optional[RegionalStyle] = None
    local_features: List[str] = field(default_factory=list)
    
    # Functional Aspects
    original_function: str = ""
    liturgical_arrangement: Optional[str] = None  # For religious buildings
    associated_structures: List[str] = field(default_factory=list)  # e.g., ["minaret", "şadırvan"]
    
    # Patronage and Context
    patron: Optional[str] = None
    architect: Optional[str] = None
    workshop_attribution: Optional[str] = None
    
    # Comparative Analysis
    typological_comparanda: List[str] = field(default_factory=list)
    influences: List[str] = field(default_factory=list)
    innovative_features: List[str] = field(default_factory=list)
    
    # Scholarly References
    primary_publications: List[str] = field(default_factory=list)
    typological_studies: List[str] = field(default_factory=list)
    
    def classify_mosque(self, mosque_type: MosqueType):
        """Classify mosque according to established typologies"""
        self.specific_type = mosque_type.value
        
        # Set typical features based on type
        if mosque_type == MosqueType.HYPOSTYLE:
            self.spatial_hierarchy = ["courtyard", "prayer hall", "qibla wall"]
            self.roofing_system = ["flat roof", "wooden roof"]
            self.support_system = ["columns", "arcades"]
        elif mosque_type == MosqueType.SINGLE_DOME:
            self.spatial_hierarchy = ["entrance", "main prayer space", "mihrab"]
            self.roofing_system = ["central dome", "semi-domes"]
            self.support_system = ["load-bearing walls", "pendentives"]
        elif mosque_type == MosqueType.T_PLAN:
            self.spatial_hierarchy = ["entrance", "central hall", "lateral spaces", "qibla hall"]
            self.plan_type = "Inverted T-plan with emphasized qibla axis"
        elif mosque_type == MosqueType.OTTOMAN_IMPERIAL:
            self.spatial_hierarchy = ["courtyard", "central dome space", "lateral galleries", "mihrab"]
            self.roofing_system = ["central dome", "cascading semi-domes", "smaller domes"]
            self.support_system = ["piers", "pendentives", "external buttresses"]
    
    def classify_church(self, church_type: ChurchType):
        """Classify church according to established typologies"""
        self.specific_type = church_type.value
        
        if church_type == ChurchType.BASILICA:
            self.spatial_hierarchy = ["narthex", "nave", "aisles", "apse"]
            self.roofing_system = ["timber roof", "clerestory"]
            self.support_system = ["columns", "arcades"]
        elif church_type == ChurchType.CROSS_IN_SQUARE:
            self.spatial_hierarchy = ["narthex", "naos", "four corner bays", "sanctuary"]
            self.roofing_system = ["central dome", "barrel vaults on arms"]
            self.plan_type = "Cross-in-square with central dome"
        elif church_type == ChurchType.CAVE_CHURCH:
            self.spatial_hierarchy = ["entrance", "nave", "apse"]
            self.construction_technique = "Rock-cut architecture"
            self.structural_system = "Carved from living rock"
    
    def add_construction_phase(self, phase_name: str, date: str, description: str):
        """Document construction phases"""
        self.construction_phases.append({
            'phase': phase_name,
            'date': date,
            'description': description
        })
    
    def set_regional_style(self, region: str):
        """Set regional architectural style"""
        # Anatolian regional styles
        if region == "Central Anatolia":
            self.regional_style = RegionalStyle(
                region=region,
                characteristics=["Austere decoration", "Emphasis on structure", "Limited windows"],
                typical_materials=["Local stone", "Brick", "Wood"],
                distinctive_features=["Stone carving", "Geometric patterns", "Pointed arches"],
                major_examples=["Alaeddin Mosque Konya", "Sultanhanı"]
            )
        elif region == "Southeast Anatolia":
            self.regional_style = RegionalStyle(
                region=region,
                characteristics=["Syrian influence", "Courtyard emphasis", "Ablaq masonry"],
                typical_materials=["Basalt", "Limestone", "Marble"],
                distinctive_features=["Striped masonry", "Muqarnas portals", "Courtyard fountains"],
                major_examples=["Ulu Cami Diyarbakır", "Zinciriye Medresesi"]
            )
        elif region == "Western Anatolia":
            self.regional_style = RegionalStyle(
                region=region,
                characteristics=["Byzantine substrate", "Ottoman synthesis", "Tile decoration"],
                typical_materials=["Marble", "Brick", "Glazed tiles"],
                distinctive_features=["Pendentive domes", "Tile revetment", "Marble mihrab"],
                major_examples=["Yeşil Cami Bursa", "Isa Bey Mosque"]
            )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'monument_id': self.monument_id,
            'monument_name': self.monument_name,
            'building_type': self.building_type.value,
            'specific_type': self.specific_type,
            'period': self.period.value,
            'construction_date': self.construction_date,
            'construction_phases': self.construction_phases,
            'plan_type': self.plan_type,
            'spatial_hierarchy': self.spatial_hierarchy,
            'orientation': self.orientation,
            'structural_system': self.structural_system,
            'roofing_system': self.roofing_system,
            'support_system': self.support_system,
            'primary_materials': self.primary_materials,
            'construction_technique': self.construction_technique,
            'decorative_techniques': self.decorative_techniques,
            'regional_style': {
                'region': self.regional_style.region,
                'characteristics': self.regional_style.characteristics,
                'typical_materials': self.regional_style.typical_materials,
                'distinctive_features': self.regional_style.distinctive_features,
                'major_examples': self.regional_style.major_examples
            } if self.regional_style else None,
            'local_features': self.local_features,
            'original_function': self.original_function,
            'liturgical_arrangement': self.liturgical_arrangement,
            'associated_structures': self.associated_structures,
            'patron': self.patron,
            'architect': self.architect,
            'workshop_attribution': self.workshop_attribution,
            'typological_comparanda': self.typological_comparanda,
            'influences': self.influences,
            'innovative_features': self.innovative_features,
            'primary_publications': self.primary_publications,
            'typological_studies': self.typological_studies
        }


class TypologyDatabase:
    """Database of architectural typologies for research"""
    
    def __init__(self, base_directory: str = "scholarly_annotations"):
        self.base_dir = Path(base_directory)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.typology_file = self.base_dir / "architectural_typologies.json"
        self.load_typologies()
    
    def load_typologies(self):
        """Load existing typologies"""
        if self.typology_file.exists():
            with open(self.typology_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.typologies = {t['monument_id']: t for t in data}
        else:
            self.typologies = {}
    
    def save_typologies(self):
        """Save all typologies"""
        data = list(self.typologies.values())
        with open(self.typology_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_typology(self, typology: ArchitecturalTypology):
        """Add or update typology"""
        self.typologies[typology.monument_id] = typology.to_dict()
        self.save_typologies()
    
    def search_by_type(self, building_type: BuildingType, 
                      period: Period = None) -> List[Dict]:
        """Search monuments by type and period"""
        results = []
        
        for typology in self.typologies.values():
            if typology['building_type'] == building_type.value:
                if not period or typology['period'] == period.value:
                    results.append(typology)
        
        return results
    
    def find_comparanda(self, monument_id: str) -> List[Dict]:
        """Find comparable monuments based on typology"""
        if monument_id not in self.typologies:
            return []
        
        source = self.typologies[monument_id]
        comparanda = []
        
        for tid, typology in self.typologies.items():
            if tid == monument_id:
                continue
            
            # Score similarity
            score = 0
            
            # Same building type
            if typology['building_type'] == source['building_type']:
                score += 3
            
            # Same specific type
            if typology.get('specific_type') == source.get('specific_type'):
                score += 3
            
            # Same period
            if typology['period'] == source['period']:
                score += 2
            
            # Same regional style
            if (typology.get('regional_style', {}).get('region') == 
                source.get('regional_style', {}).get('region')):
                score += 2
            
            # Similar plan type
            if typology.get('plan_type') and source.get('plan_type'):
                if typology['plan_type'] == source['plan_type']:
                    score += 2
            
            if score >= 5:  # Threshold for relevance
                comparanda.append({
                    'monument': typology,
                    'similarity_score': score
                })
        
        # Sort by similarity
        return sorted(comparanda, key=lambda x: x['similarity_score'], reverse=True)
    
    def generate_typological_report(self, building_type: BuildingType) -> str:
        """Generate scholarly report on a building type"""
        monuments = self.search_by_type(building_type)
        
        if not monuments:
            return f"No monuments of type {building_type.value} in database."
        
        report = f"# Typological Analysis: {building_type.value}\n\n"
        report += f"Total monuments analyzed: {len(monuments)}\n\n"
        
        # Group by period
        by_period = {}
        for m in monuments:
            period = m['period']
            if period not in by_period:
                by_period[period] = []
            by_period[period].append(m)
        
        report += "## Chronological Distribution\n"
        for period, mons in sorted(by_period.items()):
            report += f"\n### {period}\n"
            for m in mons:
                report += f"- **{m['monument_name']}**"
                if m.get('construction_date'):
                    report += f" ({m['construction_date']})"
                if m.get('specific_type'):
                    report += f" - {m['specific_type']}"
                report += "\n"
                
                if m.get('innovative_features'):
                    report += f"  - Innovations: {', '.join(m['innovative_features'])}\n"
        
        # Regional variations
        report += "\n## Regional Variations\n"
        by_region = {}
        for m in monuments:
            if m.get('regional_style'):
                region = m['regional_style']['region']
                if region not in by_region:
                    by_region[region] = []
                by_region[region].append(m)
        
        for region, mons in by_region.items():
            report += f"\n### {region}\n"
            report += f"Monuments: {len(mons)}\n"
            if mons[0]['regional_style'].get('distinctive_features'):
                report += "Distinctive features:\n"
                for feature in mons[0]['regional_style']['distinctive_features']:
                    report += f"- {feature}\n"
        
        return report


# Example typologies for Antakya monuments
def create_habib_neccar_typology() -> ArchitecturalTypology:
    """Create typology for Habib-i Neccar Mosque"""
    typology = ArchitecturalTypology(
        monument_id="ANT_001",
        monument_name="Habib-i Neccar Mosque",
        building_type=BuildingType.MOSQUE,
        period=Period.OTTOMAN_LATE
    )
    
    typology.classify_mosque(MosqueType.COURTYARD)
    typology.construction_date = "1859 (rebuilt after 1853 earthquake)"
    
    typology.add_construction_phase(
        "Roman Temple",
        "2nd century CE",
        "Original structure was a Roman temple"
    )
    typology.add_construction_phase(
        "Early Islamic Conversion",
        "638 CE",
        "Converted to mosque after Islamic conquest"
    )
    typology.add_construction_phase(
        "Mamluk Reconstruction",
        "13th century",
        "Major reconstruction under Mamluks"
    )
    typology.add_construction_phase(
        "Ottoman Rebuilding",
        "1859",
        "Complete rebuilding after 1853 earthquake"
    )
    
    typology.primary_materials = ["Limestone", "Marble columns (spolia)", "Wood"]
    typology.roofing_system = ["Timber roof", "Central dome (destroyed 2023)"]
    typology.associated_structures = ["Minaret (17th century)", "Courtyard fountain"]
    
    typology.set_regional_style("Southeast Anatolia")
    
    typology.typological_comparanda = [
        "Ulu Cami, Diyarbakır",
        "Ulu Cami, Mardin",
        "Great Mosque of Hama"
    ]
    
    typology.primary_publications = [
        "Çağaptay, S. (2020). The Seljuks of Anatolia. Cambridge.",
        "Blessing, P. (2022). Architecture and Material Politics. Cambridge."
    ]
    
    return typology