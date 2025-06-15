"""
Master orchestrator for universal archive harvesting.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

import pandas as pd

from .universal_scraper import UniversalDataRecord
from .organizer import UniversalDataOrganizer
from .scrapers.enhanced_archnet_scraper import EnhancedArchNetScraper
from .scrapers.enhanced_manar_scraper import EnhancedManarScraper
from .scrapers.generic_scraper import GenericArchiveScraper

logger = logging.getLogger(__name__)


class UniversalHarvester:
    """Master harvester that can scrape any archive."""
    
    def __init__(self, output_dir: str = "harvested_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scrapers = {}
        self._register_scrapers()
        
    def _register_scrapers(self):
        """Register all available scrapers."""
        from .scrapers.salt_scraper import SALTResearchScraper
        from .scrapers.akkasah_scraper import AkkasahScraper
        from .scrapers.nit_scraper import NITKielScraper
        
        self.scrapers = {
            'archnet': EnhancedArchNetScraper(),
            'manar': EnhancedManarScraper(),
            'salt': SALTResearchScraper(),
            'akkasah': AkkasahScraper(),
            'nit': NITKielScraper(),
        }
    
    def _detect_scraper(self, url: str) -> Optional[any]:
        """Detect which scraper to use based on URL."""
        domain = urlparse(url).netloc.lower()
        
        # Map domains to scrapers
        domain_mapping = {
            'archnet.org': self.scrapers.get('archnet'),
            'www.archnet.org': self.scrapers.get('archnet'),
            'manar-al-athar.ox.ac.uk': self.scrapers.get('manar'),
            'www.manar-al-athar.ox.ac.uk': self.scrapers.get('manar'),
            'saltresearch.org': self.scrapers.get('salt'),
            'www.saltresearch.org': self.scrapers.get('salt'),
            'akkasah.org': self.scrapers.get('akkasah'),
            'www.akkasah.org': self.scrapers.get('akkasah'),
            'nit-istanbul.org': self.scrapers.get('nit'),
            'www.nit-istanbul.org': self.scrapers.get('nit'),
        }
        
        for key, scraper in domain_mapping.items():
            if key in domain:
                return scraper
                
        return None
    
    def harvest_url(self, url: str) -> pd.DataFrame:
        """Automatically detect archive and harvest from URL."""
        logger.info(f"Harvesting URL: {url}")
        
        # Detect which scraper to use
        scraper = self._detect_scraper(url)
        
        if not scraper:
            # Use generic scraper for unknown sites
            logger.info(f"Using generic scraper for: {url}")
            scraper = GenericArchiveScraper(base_url=url)
        else:
            logger.info(f"Using {scraper.archive_name} scraper")
        
        try:
            # Harvest data
            records = scraper.scrape(url=url)
            
            if not records:
                logger.warning(f"No records found at {url}")
                return pd.DataFrame()
            
            # Organize and return
            organizer = UniversalDataOrganizer(records)
            
            # Save results
            self._save_results(organizer, f"harvest_url_{urlparse(url).netloc}")
            
            return organizer.df
            
        except Exception as e:
            logger.error(f"Error harvesting {url}: {e}")
            return pd.DataFrame()
        finally:
            # Clean up resources
            if hasattr(scraper, 'close'):
                scraper.close()
    
    def harvest_search(self, search_terms: List[str], archives: List[str] = None) -> pd.DataFrame:
        """Search specific archives or all registered archives."""
        logger.info(f"Searching for terms: {search_terms}")
        
        if archives:
            # Use only specified archives
            selected_scrapers = {
                name: scraper for name, scraper in self.scrapers.items()
                if name in archives
            }
        else:
            # Use all registered archives
            selected_scrapers = self.scrapers
            
        all_records = []
        
        # Run scrapers in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._safe_scrape, scraper, search_terms=search_terms): name
                for name, scraper in selected_scrapers.items()
            }
            
            for future in as_completed(futures):
                archive_name = futures[future]
                try:
                    records = future.result()
                    if records:
                        all_records.extend(records)
                        logger.info(f"Harvested {len(records)} records from {archive_name}")
                    else:
                        logger.warning(f"No records from {archive_name}")
                except Exception as e:
                    logger.error(f"Error harvesting {archive_name}: {e}")
        
        if not all_records:
            logger.warning("No records harvested from any archive")
            return pd.DataFrame()
        
        # Organize all results
        organizer = UniversalDataOrganizer(all_records)
        
        # Save results
        self._save_results(organizer, "harvest_search")
        
        # Print summary
        print(organizer.generate_summary_report())
        
        return organizer.df
    
    def harvest_all_archives(self, search_terms: List[str]) -> pd.DataFrame:
        """Harvest from all registered archives."""
        return self.harvest_search(search_terms, archives=None)
    
    def _safe_scrape(self, scraper, **kwargs) -> List[UniversalDataRecord]:
        """Safely scrape with error handling."""
        try:
            return scraper.scrape(**kwargs)
        except Exception as e:
            logger.error(f"Scraper {scraper.archive_name} failed: {e}")
            return []
        finally:
            # Clean up resources
            if hasattr(scraper, 'close'):
                scraper.close()
    
    def _save_results(self, organizer: UniversalDataOrganizer, prefix: str):
        """Save results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{prefix}_{timestamp}"
        
        # Create subdirectory for this harvest
        harvest_dir = self.output_dir / base_name
        harvest_dir.mkdir(exist_ok=True)
        
        # Save in different formats
        excel_path = harvest_dir / f"{base_name}.xlsx"
        json_path = harvest_dir / f"{base_name}.json"
        db_path = harvest_dir / f"{base_name}.db"
        report_path = harvest_dir / f"{base_name}_report.txt"
        
        try:
            organizer.export_excel(str(excel_path))
            organizer.export_json(str(json_path))
            organizer.export_database(str(db_path))
            
            # Save text report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(organizer.generate_summary_report())
                
            logger.info(f"Results saved to: {harvest_dir}")
            print(f"\nResults saved to: {harvest_dir}")
            print(f"  - Excel: {excel_path.name}")
            print(f"  - JSON: {json_path.name}")
            print(f"  - Database: {db_path.name}")
            print(f"  - Report: {report_path.name}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def list_archives(self) -> List[str]:
        """List all available archives."""
        return list(self.scrapers.keys())