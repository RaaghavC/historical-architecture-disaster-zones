"""
Earthquake Damage Documentation Sources
Specialized scraper for earthquake damage reports and assessments
"""

import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from data_collection.universal_scraper import UniversalArchiveScraper, UniversalDataRecord, DataType

logger = logging.getLogger(__name__)


class EarthquakeDamageSourcesScraper:
    """
    Aggregates earthquake damage documentation from multiple sources:
    - AFAD (Turkey Disaster Management)
    - UNESCO damage assessments
    - ICOMOS Turkey reports
    - Academic earthquake databases
    - News archives with damage documentation
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Antakya Heritage Documentation)'
        })
        
        # Define specialized sources
        self.sources = {
            'afad': {
                'name': 'AFAD - Turkey Disaster Management',
                'base_url': 'https://www.afad.gov.tr',
                'search_patterns': [
                    '/tr/deprem-hasar-tespit',
                    '/earthquake-damage-assessment'
                ]
            },
            'unesco': {
                'name': 'UNESCO Damage Assessments',
                'base_url': 'https://whc.unesco.org',
                'search_url': 'https://whc.unesco.org/en/news/search/',
                'keywords': ['Turkey earthquake', 'Antakya', 'heritage damage']
            },
            'icomos_turkey': {
                'name': 'ICOMOS Turkey',
                'base_url': 'http://www.icomos.org.tr',
                'report_sections': ['/haberler/', '/raporlar/']
            },
            'reliefweb': {
                'name': 'ReliefWeb Disaster Reports',
                'api_url': 'https://api.reliefweb.int/v1/reports',
                'filters': {
                    'filter[field]': 'country.iso3:tur',
                    'filter[value]': 'earthquake AND (heritage OR cultural OR monument)',
                    'filter[operator]': 'AND'
                }
            },
            'maxar': {
                'name': 'Maxar Satellite Imagery',
                'base_url': 'https://www.maxar.com',
                'open_data': 'https://www.maxar.com/open-data/turkey-earthquake-2023'
            }
        }
    
    def search_all_sources(self, focus_area: str = "Antakya") -> List[UniversalDataRecord]:
        """Search all earthquake damage sources"""
        all_records = []
        
        logger.info(f"Searching earthquake damage sources for: {focus_area}")
        
        # Search each source
        for source_id, source_config in self.sources.items():
            try:
                logger.info(f"Searching {source_config['name']}...")
                
                if source_id == 'reliefweb':
                    records = self._search_reliefweb(source_config, focus_area)
                elif source_id == 'unesco':
                    records = self._search_unesco(source_config, focus_area)
                elif source_id == 'maxar':
                    records = self._search_maxar_imagery(source_config, focus_area)
                else:
                    records = self._search_generic_source(source_id, source_config, focus_area)
                
                all_records.extend(records)
                logger.info(f"Found {len(records)} records from {source_config['name']}")
                
            except Exception as e:
                logger.error(f"Error searching {source_config['name']}: {e}")
        
        return all_records
    
    def _search_reliefweb(self, config: Dict, focus_area: str) -> List[UniversalDataRecord]:
        """Search ReliefWeb API for earthquake damage reports"""
        records = []
        
        params = {
            'appname': 'antakya-heritage',
            'query[value]': f'Turkey earthquake 2023 {focus_area} damage assessment',
            'limit': 100
        }
        params.update(config.get('filters', {}))
        
        try:
            response = self.session.get(config['api_url'], params=params)
            if response.ok:
                data = response.json()
                
                for item in data.get('data', []):
                    fields = item.get('fields', {})
                    
                    record = UniversalDataRecord(
                        id=f"reliefweb_{item.get('id', '')}",
                        source_archive='ReliefWeb',
                        source_url=fields.get('url_alias', ''),
                        title=fields.get('title', ''),
                        description=fields.get('body', ''),
                        data_type=DataType.TEXT,
                        date_created=datetime.fromisoformat(fields.get('date', {}).get('created', '').replace('Z', '+00:00')) if fields.get('date') else None,
                        keywords=['earthquake', 'damage assessment', focus_area],
                        raw_metadata={
                            'source': 'ReliefWeb',
                            'disaster_type': 'earthquake',
                            'country': 'Turkey',
                            'format': fields.get('format', []),
                            'theme': fields.get('theme', [])
                        }
                    )
                    
                    # Check for PDF attachments
                    if fields.get('file'):
                        for file_info in fields['file']:
                            if file_info.get('mimetype') == 'application/pdf':
                                record.download_url = file_info.get('url')
                                record.data_type = DataType.PDF
                                break
                    
                    records.append(record)
                    
        except Exception as e:
            logger.error(f"ReliefWeb API error: {e}")
        
        return records
    
    def _search_unesco(self, config: Dict, focus_area: str) -> List[UniversalDataRecord]:
        """Search UNESCO for heritage damage assessments"""
        records = []
        
        # Search UNESCO news for earthquake damage reports
        search_terms = ['Turkey earthquake 2023', 'Antakya heritage', 'Hatay cultural damage']
        
        for term in search_terms:
            try:
                url = f"{config['base_url']}/en/news/search/?q={term}"
                response = self.session.get(url)
                
                if response.ok:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find news items
                    for article in soup.select('.news-item, .search-result'):
                        title_elem = article.select_one('h3, .title')
                        link_elem = article.select_one('a')
                        desc_elem = article.select_one('.summary, .description')
                        
                        if title_elem and link_elem:
                            record = UniversalDataRecord(
                                id=f"unesco_{link_elem.get('href', '').split('/')[-1]}",
                                source_archive='UNESCO',
                                source_url=urljoin(config['base_url'], link_elem.get('href', '')),
                                title=title_elem.get_text(strip=True),
                                description=desc_elem.get_text(strip=True) if desc_elem else '',
                                data_type=DataType.TEXT,
                                keywords=['UNESCO', 'earthquake', 'heritage damage', focus_area],
                                raw_metadata={
                                    'source': 'UNESCO World Heritage Centre',
                                    'search_term': term
                                }
                            )
                            records.append(record)
                            
            except Exception as e:
                logger.error(f"UNESCO search error for '{term}': {e}")
        
        return records
    
    def _search_maxar_imagery(self, config: Dict, focus_area: str) -> List[UniversalDataRecord]:
        """Search Maxar satellite imagery for damage documentation"""
        records = []
        
        try:
            # Check Maxar open data page
            response = self.session.get(config['open_data'])
            
            if response.ok:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for imagery links
                for link in soup.select('a[href*="earthquake"], a[href*="turkey"]'):
                    href = link.get('href', '')
                    if any(ext in href.lower() for ext in ['.tif', '.jpg', '.png', 'download']):
                        
                        record = UniversalDataRecord(
                            id=f"maxar_{href.split('/')[-1]}",
                            source_archive='Maxar Open Data',
                            source_url=urljoin(config['base_url'], href),
                            title=f"Satellite Imagery - {link.get_text(strip=True)}",
                            description=f"High-resolution satellite imagery showing earthquake damage in {focus_area} region",
                            data_type=DataType.IMAGE,
                            download_url=urljoin(config['base_url'], href),
                            keywords=['satellite', 'imagery', 'earthquake damage', 'Maxar', focus_area],
                            date_created=datetime(2023, 2, 6),  # Earthquake date
                            raw_metadata={
                                'source': 'Maxar Technologies',
                                'imagery_type': 'satellite',
                                'disaster_date': '2023-02-06',
                                'resolution': 'high'
                            }
                        )
                        records.append(record)
                        
        except Exception as e:
            logger.error(f"Maxar search error: {e}")
        
        return records
    
    def _search_generic_source(self, source_id: str, config: Dict, focus_area: str) -> List[UniversalDataRecord]:
        """Generic search for other sources"""
        records = []
        
        # This is a placeholder for sources that would need specific access
        # In practice, you would implement specific scrapers for each source
        
        # Create informational records pointing to potential sources
        record = UniversalDataRecord(
            id=f"{source_id}_info",
            source_archive=config['name'],
            source_url=config['base_url'],
            title=f"{config['name']} - Earthquake Damage Documentation",
            description=f"Visit {config['name']} for official earthquake damage assessments and reports for {focus_area}",
            data_type=DataType.TEXT,
            keywords=['earthquake', 'damage assessment', 'official source', focus_area],
            raw_metadata={
                'source_type': 'reference',
                'requires_manual_access': True
            }
        )
        records.append(record)
        
        return records
    
    def search_social_media_documentation(self, platform: str = "twitter", 
                                        hashtags: List[str] = None) -> List[UniversalDataRecord]:
        """
        Search social media for citizen-documented damage
        Note: This would require API access in production
        """
        if not hashtags:
            hashtags = ['#AntakyaEarthquake', '#HatayDeprem', '#TurkeyEarthquake2023']
        
        records = []
        
        # Create reference record for social media documentation
        record = UniversalDataRecord(
            id=f"social_media_{platform}_reference",
            source_archive=f"{platform.title()} Documentation",
            source_url=f"https://{platform}.com/search",
            title=f"Citizen Documentation on {platform.title()}",
            description=f"Search {platform.title()} using hashtags: {', '.join(hashtags)} for citizen-documented earthquake damage photos and reports",
            data_type=DataType.TEXT,
            keywords=['social media', 'citizen documentation', 'earthquake'] + hashtags,
            raw_metadata={
                'platform': platform,
                'hashtags': hashtags,
                'documentation_type': 'crowd-sourced'
            }
        )
        records.append(record)
        
        return records
    
    def create_damage_report_template(self, site_name: str, site_id: str) -> Dict:
        """Create a standardized damage report template"""
        return {
            'report_id': f"damage_report_{site_id}_{datetime.now().strftime('%Y%m%d')}",
            'site': {
                'name': site_name,
                'id': site_id,
                'location': 'Antakya, Hatay Province, Turkey'
            },
            'earthquake': {
                'date': '2023-02-06',
                'magnitude': '7.8 and 7.5',
                'epicenter': 'Kahramanmaraş'
            },
            'damage_sources': {
                'official_reports': [],
                'satellite_imagery': [],
                'field_assessments': [],
                'news_documentation': [],
                'social_media': []
            },
            'assessment_status': 'pending',
            'created_date': datetime.now().isoformat()
        }


# Quick function to search for specific monument damage
def search_monument_damage(monument_name: str) -> List[UniversalDataRecord]:
    """
    Quick search for damage documentation of a specific monument
    """
    scraper = EarthquakeDamageSourcesScraper()
    
    # Search with monument-specific terms
    records = []
    
    # Search all sources
    general_records = scraper.search_all_sources(monument_name)
    records.extend(general_records)
    
    # Add social media search
    social_records = scraper.search_social_media_documentation(
        hashtags=[f"#{monument_name.replace(' ', '')}", '#TurkeyEarthquake']
    )
    records.extend(social_records)
    
    return records


# Integration with main CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Search earthquake damage documentation")
    parser.add_argument('--monument', help='Specific monument name')
    parser.add_argument('--area', default='Antakya', help='Geographic area')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    scraper = EarthquakeDamageSourcesScraper()
    
    if args.monument:
        records = search_monument_damage(args.monument)
    else:
        records = scraper.search_all_sources(args.area)
    
    print(f"\nFound {len(records)} damage documentation sources")
    
    if args.output:
        # Save to file
        output_data = [r.to_dict() for r in records]
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Saved to: {args.output}")
    else:
        # Print summary
        for record in records[:10]:
            print(f"\n- {record.title}")
            print(f"  Source: {record.source_archive}")
            print(f"  Type: {record.data_type.value}")
            if record.download_url:
                print(f"  Download: {record.download_url}")