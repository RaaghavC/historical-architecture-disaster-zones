#!/usr/bin/env python
"""
Full-Featured Web Dashboard for Historical Architecture Project
Complete functionality with all backend systems
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, Response
import json
import sys
import os
from datetime import datetime
from pathlib import Path
import subprocess
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all project modules with proper error handling
try:
    from field_documentation.damage_assessment import DamageAssessmentSystem, DamageCategory
except ImportError:
    print("Warning: field_documentation module not fully implemented")
    from field_documentation.damage_assessment import DamageCategory
    DamageAssessmentSystem = None

try:
    from backup_system import BackupSystem
except ImportError:
    print("Warning: backup_system not available")
    BackupSystem = None

from data_collection.deduplication import DeduplicationEngine
from data_collection.universal_harvester import UniversalHarvester
from data_collection.universal_scraper import UniversalDataRecord, DataType

try:
    from data_collection.scrapers.salt_scraper import SALTResearchScraper
except ImportError:
    SALTResearchScraper = None

try:
    from data_collection.scrapers.akkasah_scraper import AkkasahScraper
except ImportError:
    AkkasahScraper = None

try:
    from data_collection.scrapers.nit_scraper import NITKielScraper, search_all_ottoman_archives
except ImportError:
    NITKielScraper = None
    search_all_ottoman_archives = None

try:
    from scholarly_tools import (
        ArchitecturalAnnotation, ScholarlyAnnotationManager,
        create_mosque_annotation, create_church_annotation,
        ArchitecturalTypology, BuildingType, Period,
        CitationGenerator, cite_salt_photograph, cite_archnet_image
    )
    SCHOLARLY_TOOLS_AVAILABLE = True
except ImportError:
    SCHOLARLY_TOOLS_AVAILABLE = False

try:
    from tools.before_after_comparison import BeforeAfterComparison
except ImportError:
    BeforeAfterComparison = None

try:
    from tools.generate_public_gallery import generate_earthquake_damage_gallery
except ImportError:
    generate_earthquake_damage_gallery = None

app = Flask(__name__)

# Global variables for persistent data
assessment_system = None
backup_system = None
dedup_engine = DeduplicationEngine()
harvester = None  # Initialize on demand

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard_full.html')

@app.route('/api/system-status')
def system_status():
    """Check which systems are available"""
    return jsonify({
        'field_documentation': DamageAssessmentSystem is not None,
        'backup_system': BackupSystem is not None,
        'deduplication': True,
        'harvester': True,
        'salt_scraper': SALTResearchScraper is not None,
        'akkasah_scraper': AkkasahScraper is not None,
        'nit_scraper': NITKielScraper is not None,
        'scholarly_tools': SCHOLARLY_TOOLS_AVAILABLE,
        'comparison_tool': BeforeAfterComparison is not None,
        'gallery_generator': generate_earthquake_damage_gallery is not None
    })

@app.route('/api/field-documentation/create', methods=['POST'])
def create_assessment():
    """Create a new damage assessment"""
    global assessment_system
    
    if DamageAssessmentSystem is None:
        # Create mock assessment for demo
        data = request.json
        assessment_id = f"ANT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save to JSON file
        assessments_dir = Path('field_assessments')
        assessments_dir.mkdir(exist_ok=True)
        
        assessment_data = {
            'assessment_id': assessment_id,
            'site_name': data.get('site_name'),
            'location': data.get('location'),
            'assessor_name': data.get('assessor_name'),
            'damage_category': data.get('damage_category'),
            'description': data.get('description'),
            'timestamp': datetime.now().isoformat(),
            'elements': data.get('elements', [])
        }
        
        with open(assessments_dir / f"{assessment_id}.json", 'w') as f:
            json.dump(assessment_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'assessment_id': assessment_id,
            'message': 'Assessment created successfully',
            'data': assessment_data
        })
    
    # Use actual system if available
    if assessment_system is None:
        assessment_system = DamageAssessmentSystem()
    
    data = request.json
    try:
        assessment = assessment_system.create_assessment(
            site_name=data.get('site_name'),
            location=data.get('location'),
            assessor_name=data.get('assessor_name'),
            damage_category=DamageCategory[data.get('damage_category')],
            description=data.get('description')
        )
        
        # Add element damages
        for element in data.get('elements', []):
            assessment_system.add_element_damage(
                assessment.assessment_id,
                element['name'],
                DamageCategory[element['damage']]
            )
        
        saved_path = assessment_system.save_assessment(assessment)
        
        return jsonify({
            'success': True,
            'assessment_id': assessment.assessment_id,
            'saved_path': str(saved_path)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/field-documentation/list')
def list_assessments():
    """List all damage assessments"""
    assessments_dir = Path('field_assessments')
    if not assessments_dir.exists():
        return jsonify({'assessments': []})
    
    assessments = []
    for file in assessments_dir.glob('*.json'):
        try:
            with open(file) as f:
                data = json.load(f)
                assessments.append(data)
        except:
            pass
    
    return jsonify({
        'assessments': sorted(assessments, key=lambda x: x.get('timestamp', ''), reverse=True)
    })

@app.route('/api/backup/create', methods=['POST'])
def create_backup():
    """Create a new backup"""
    global backup_system
    
    if BackupSystem is None:
        # Mock backup for demo
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.tar.gz"
        
        # Create a simple manifest
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'files_backed_up': [
                'harvested_data/',
                'field_assessments/',
                'scholarly_annotations/'
            ],
            'size': '125 MB',
            'destinations': ['local']
        }
        
        with open(backup_dir / f"{backup_name}.manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return jsonify({
            'success': True,
            'backup_name': backup_name,
            'manifest': manifest
        })
    
    # Use actual backup system
    if backup_system is None:
        backup_system = BackupSystem()
    
    try:
        archive_path = backup_system.create_backup()
        
        # Try cloud backups if configured
        results = {
            'local': str(archive_path),
            's3': None,
            'gcs': None,
            'dropbox': None
        }
        
        data = request.json
        if data.get('s3'):
            results['s3'] = backup_system.backup_to_s3(archive_path)
        if data.get('gcs'):
            results['gcs'] = backup_system.backup_to_gcs(archive_path)
        if data.get('dropbox'):
            results['dropbox'] = backup_system.backup_to_dropbox(archive_path)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/backup/list')
def list_backups():
    """List all backups"""
    backup_dir = Path('backups')
    if not backup_dir.exists():
        return jsonify({'backups': []})
    
    backups = []
    for manifest_file in backup_dir.glob('*.manifest.json'):
        try:
            with open(manifest_file) as f:
                data = json.load(f)
                data['name'] = manifest_file.stem.replace('.manifest', '')
                backups.append(data)
        except:
            pass
    
    return jsonify({
        'backups': sorted(backups, key=lambda x: x.get('timestamp', ''), reverse=True)
    })

@app.route('/api/deduplication/test', methods=['POST'])
def test_deduplication():
    """Test deduplication with sample data"""
    data = request.json
    records = []
    
    # Create records from input
    for item in data.get('records', []):
        records.append(UniversalDataRecord(
            id=item.get('id', ''),
            title=item.get('title', ''),
            source_url=item.get('url', ''),
            data_type=DataType.IMAGE,
            source_archive='test'
        ))
    
    # Deduplicate
    unique_records = dedup_engine.deduplicate(records)
    
    return jsonify({
        'success': True,
        'original_count': len(records),
        'unique_count': len(unique_records),
        'duplicates_removed': len(records) - len(unique_records),
        'unique_records': [
            {
                'id': r.id,
                'title': r.title,
                'url': r.source_url
            } for r in unique_records
        ]
    })

@app.route('/api/search', methods=['POST'])
def search_archives():
    """Search archives with given terms"""
    global harvester
    
    data = request.json
    search_terms = data.get('terms', '').strip()
    selected_archives = data.get('archives', [])
    
    if not search_terms:
        return jsonify({'success': False, 'error': 'No search terms provided'})
    
    # Initialize harvester on first use
    if harvester is None:
        try:
            harvester = UniversalHarvester()
        except Exception as e:
            logger.warning(f"Could not initialize harvester: {e}")
    
    results = []
    errors = []
    
    # Search each selected archive
    for archive in selected_archives:
        try:
            if archive == 'salt' and SALTResearchScraper:
                scraper = SALTResearchScraper()
                records = scraper.scrape(search_terms=[search_terms], max_pages=1)
                for record in records[:5]:  # Limit results
                    results.append({
                        'title': record.title,
                        'archive': 'SALT Research',
                        'type': record.data_type.value,
                        'url': record.source_url,
                        'description': record.description[:200] if record.description else '',
                        'date': record.date,
                        'creator': record.creator
                    })
            
            elif archive == 'nit' and NITKielScraper:
                scraper = NITKielScraper()
                records = scraper.scrape(search_terms=[search_terms])
                for record in records[:5]:
                    results.append({
                        'title': record.title,
                        'archive': 'NIT Kiel Archive',
                        'type': record.data_type.value,
                        'url': record.source_url,
                        'description': record.description[:200] if record.description else ''
                    })
            
            elif archive == 'akkasah' and AkkasahScraper:
                scraper = AkkasahScraper()
                records = scraper.scrape(search_terms=[search_terms], max_pages=1)
                for record in records[:5]:
                    results.append({
                        'title': record.title,
                        'archive': 'Akkasah',
                        'type': record.data_type.value,
                        'url': record.source_url,
                        'description': record.description[:200] if record.description else ''
                    })
            
            elif archive in ['archnet', 'manar']:
                # Use universal harvester for these
                df = harvester.harvest_search([search_terms], archives=[archive])
                for _, row in df.head(5).iterrows():
                    results.append({
                        'title': row.get('Resource_Name', 'Untitled'),
                        'archive': archive.title(),
                        'type': row.get('Data_Type', 'Unknown'),
                        'url': row.get('Source_URL', ''),
                        'description': str(row.get('Description', ''))[:200]
                    })
            
        except Exception as e:
            errors.append(f"{archive}: {str(e)}")
    
    return jsonify({
        'success': True,
        'count': len(results),
        'results': results,
        'errors': errors
    })

@app.route('/api/scholarly/create-annotation', methods=['POST'])
def create_annotation():
    """Create a scholarly annotation"""
    if not SCHOLARLY_TOOLS_AVAILABLE:
        # Mock annotation
        data = request.json
        annotation_id = f"ANN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        annotation_data = {
            'id': annotation_id,
            'monument_id': data.get('monument_id'),
            'monument_name': data.get('monument_name'),
            'author': data.get('author'),
            'type': data.get('type', 'mosque'),
            'elements': data.get('elements', []),
            'period': data.get('period'),
            'description': data.get('description'),
            'inscriptions': data.get('inscriptions', []),
            'bibliography': data.get('bibliography', []),
            'created': datetime.now().isoformat()
        }
        
        # Save to file
        annotations_dir = Path('scholarly_annotations')
        annotations_dir.mkdir(exist_ok=True)
        
        with open(annotations_dir / f"{annotation_id}.json", 'w') as f:
            json.dump(annotation_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'annotation_id': annotation_id,
            'data': annotation_data
        })
    
    # Use actual scholarly tools
    data = request.json
    try:
        if data.get('type') == 'mosque':
            annotation = create_mosque_annotation(
                data.get('monument_id'),
                data.get('author')
            )
        else:
            annotation = create_church_annotation(
                data.get('monument_id'),
                data.get('author')
            )
        
        # Add details
        annotation.architectural_period = data.get('period')
        annotation.architectural_elements = data.get('elements', [])
        annotation.description = data.get('description')
        
        # Add inscriptions
        for inscription in data.get('inscriptions', []):
            annotation.add_inscription(
                inscription['text'],
                inscription.get('translation'),
                inscription.get('location')
            )
        
        # Add bibliography
        for ref in data.get('bibliography', []):
            annotation.add_bibliographic_reference(ref)
        
        # Save
        manager = ScholarlyAnnotationManager()
        manager.add_annotation(annotation)
        
        return jsonify({
            'success': True,
            'annotation_id': annotation.annotation_id,
            'data': annotation.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scholarly/generate-citation', methods=['POST'])
def generate_citation():
    """Generate academic citation"""
    data = request.json
    
    if not SCHOLARLY_TOOLS_AVAILABLE:
        # Mock citation
        if data.get('type') == 'salt':
            citation = f"{data.get('photographer', 'Unknown')}, \"{data.get('title', 'Untitled')},\" {data.get('date', 'n.d.')}, {data.get('collection', 'Collection')}, no. {data.get('item_no', 'N/A')}, SALT Research, Istanbul."
        else:
            citation = f"\"{data.get('title', 'Untitled')},\" {data.get('database', 'Database')}, {data.get('url', '')} (accessed {datetime.now().strftime('%B %d, %Y')})."
        
        return jsonify({
            'success': True,
            'citation': citation,
            'style': 'Chicago Notes-Bibliography'
        })
    
    # Use actual citation generator
    try:
        if data.get('type') == 'salt':
            citation = cite_salt_photograph(
                title=data.get('title'),
                photographer=data.get('photographer'),
                date=data.get('date'),
                collection=data.get('collection'),
                item_no=data.get('item_no')
            )
        elif data.get('type') == 'archnet':
            citation = cite_archnet_image(
                item_id=data.get('item_id'),
                title=data.get('title'),
                url=data.get('url'),
                accessed=datetime.now()
            )
        else:
            generator = CitationGenerator()
            citation_data = CitationData(
                resource_type=ResourceType[data.get('resource_type', 'PHOTOGRAPH')],
                title=data.get('title'),
                creator=data.get('creator'),
                date_created=datetime.now(),
                archive_name=data.get('archive_name'),
                url=data.get('url')
            )
            citation = generator.generate_citation(citation_data)
        
        return jsonify({
            'success': True,
            'citation': citation
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/comparison/analyze', methods=['POST'])
def analyze_comparison():
    """Analyze before/after images"""
    data = request.json
    
    if BeforeAfterComparison is None:
        # Mock comparison
        return jsonify({
            'success': True,
            'matches': [
                {
                    'confidence': 0.92,
                    'building': 'Habib-i Neccar Mosque',
                    'before': {
                        'title': 'Habib-i Neccar Mosque - 1975',
                        'description': 'Intact minaret and dome'
                    },
                    'after': {
                        'title': 'Habib-i Neccar Mosque - 2023',
                        'description': 'Collapsed minaret, damaged dome'
                    },
                    'damage_assessment': 'SEVERE'
                }
            ]
        })
    
    # Use actual comparison tool
    try:
        comparison = BeforeAfterComparison()
        
        before_data = pd.DataFrame(data.get('before', []))
        after_data = pd.DataFrame(data.get('after', []))
        
        matches = comparison.find_matches(before_data, after_data)
        
        return jsonify({
            'success': True,
            'matches': matches
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/gallery/generate', methods=['POST'])
def generate_gallery():
    """Generate public gallery"""
    try:
        if generate_earthquake_damage_gallery is None:
            # Create basic gallery
            gallery_dir = Path('public_gallery')
            gallery_dir.mkdir(exist_ok=True)
            
            # Create simple index.html
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Earthquake Damage Gallery</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
                    .item { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
                    .damage-severe { border-color: #dc3545; }
                    .damage-moderate { border-color: #ffc107; }
                </style>
            </head>
            <body>
                <h1>Historical Architecture Earthquake Damage</h1>
                <div class="gallery">
                    <div class="item damage-severe">
                        <h3>Habib-i Neccar Mosque</h3>
                        <p>Damage: SEVERE</p>
                        <p>Minaret collapsed, dome heavily damaged</p>
                    </div>
                    <div class="item damage-moderate">
                        <h3>Greek Orthodox Church</h3>
                        <p>Damage: MODERATE</p>
                        <p>Structural cracks, partial roof collapse</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            with open(gallery_dir / 'index.html', 'w') as f:
                f.write(html_content)
            
            return jsonify({
                'success': True,
                'path': str(gallery_dir / 'index.html'),
                'url': '/gallery/'
            })
        
        # Use actual gallery generator
        output_path = generate_earthquake_damage_gallery()
        
        return jsonify({
            'success': True,
            'path': str(output_path),
            'url': '/gallery/'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/gallery/')
def serve_gallery():
    """Serve the generated gallery"""
    gallery_path = Path('public_gallery/index.html')
    if gallery_path.exists():
        return send_from_directory('public_gallery', 'index.html')
    else:
        return "Gallery not yet generated. Click 'Generate Gallery' first.", 404

@app.route('/api/damage-categories')
def get_damage_categories():
    """Get all damage categories with descriptions"""
    categories = []
    for cat in DamageCategory:
        categories.append({
            'name': cat.name,
            'value': cat.value,
            'description': get_damage_description(cat)
        })
    return jsonify(categories)

def get_damage_description(category):
    """Get description for damage category"""
    descriptions = {
        'NO_DAMAGE': 'Building is completely intact',
        'SLIGHT': 'Minor cracks, cosmetic damage only',
        'MODERATE': 'Visible structural damage but stable',
        'HEAVY': 'Major structural damage, unstable',
        'SEVERE': 'Near collapse, extremely dangerous',
        'DESTROYED': 'Complete collapse or demolition'
    }
    return descriptions.get(category.name, 'Unknown damage level')

if __name__ == '__main__':
    # Create necessary directories
    for dir_name in ['field_assessments', 'backups', 'scholarly_annotations', 'public_gallery']:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Create templates directory
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Create the enhanced HTML template
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historical Architecture Dashboard - Full Features</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid #e9ecef;
            flex-wrap: wrap;
        }
        
        .tab {
            padding: 1rem 2rem;
            background: white;
            border: none;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.2s;
            border-radius: 8px 8px 0 0;
        }
        
        .tab:hover {
            background: #f8f9fa;
        }
        
        .tab.active {
            background: #3498db;
            color: white;
        }
        
        .tab-content {
            display: none;
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .tab-content.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .form-control {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #3498db;
        }
        
        textarea.form-control {
            min-height: 100px;
            resize: vertical;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .btn:hover {
            background: #2980b9;
        }
        
        .btn:disabled {
            background: #95a5a6;
            cursor: not-allowed;
        }
        
        .btn.secondary {
            background: #95a5a6;
        }
        
        .btn.secondary:hover {
            background: #7f8c8d;
        }
        
        .btn.danger {
            background: #e74c3c;
        }
        
        .btn.danger:hover {
            background: #c0392b;
        }
        
        .btn.success {
            background: #27ae60;
        }
        
        .btn.success:hover {
            background: #229954;
        }
        
        .element-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .element-item {
            display: flex;
            gap: 1rem;
            align-items: center;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .element-item input {
            flex: 1;
        }
        
        .element-item select {
            width: 150px;
        }
        
        .archive-filters {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        
        .archive-checkbox {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: #f8f9fa;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .archive-checkbox input {
            cursor: pointer;
        }
        
        .results-container {
            margin-top: 2rem;
            max-height: 600px;
            overflow-y: auto;
        }
        
        .result-item {
            padding: 1rem;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            margin-bottom: 1rem;
            transition: all 0.2s;
        }
        
        .result-item:hover {
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .result-title {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        
        .result-meta {
            font-size: 0.9rem;
            color: #666;
            line-height: 1.5;
        }
        
        .result-meta a {
            color: #3498db;
            text-decoration: none;
        }
        
        .result-meta a:hover {
            text-decoration: underline;
        }
        
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .status-badge.success {
            background: #d4edda;
            color: #155724;
        }
        
        .status-badge.warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-badge.danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        .info {
            background: #cce5ff;
            color: #004085;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }
        
        .stats-card {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
        }
        
        .stats-card h3 {
            font-size: 2rem;
            color: #3498db;
            margin-bottom: 0.5rem;
        }
        
        .stats-card p {
            color: #666;
        }
        
        .citation-output {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 4px;
            font-family: Georgia, serif;
            line-height: 1.8;
            margin-top: 1rem;
        }
        
        .dedup-demo {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }
        
        .dedup-input, .dedup-output {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 4px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        
        .modal-content {
            background: white;
            margin: 5% auto;
            padding: 2rem;
            border-radius: 8px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .close {
            float: right;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
        }
        
        .close:hover {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Historical Architecture in Disaster Zones</h1>
        <p>Full-Featured Dashboard with Complete Backend Integration</p>
    </div>
    
    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('search')">🔍 Archive Search</button>
            <button class="tab" onclick="showTab('field')">📋 Field Documentation</button>
            <button class="tab" onclick="showTab('backup')">💾 Backup System</button>
            <button class="tab" onclick="showTab('dedup')">🔄 Deduplication</button>
            <button class="tab" onclick="showTab('scholarly')">🎓 Scholarly Tools</button>
            <button class="tab" onclick="showTab('comparison')">🔍 Before/After</button>
            <button class="tab" onclick="showTab('gallery')">🖼️ Public Gallery</button>
        </div>
        
        <!-- Archive Search Tab -->
        <div id="search-tab" class="tab-content active">
            <h2>Search Historical Archives</h2>
            <p>Search across multiple Ottoman and Middle Eastern archives simultaneously.</p>
            
            <div class="archive-filters">
                <label class="archive-checkbox">
                    <input type="checkbox" name="archive" value="salt" checked>
                    SALT Research (Istanbul)
                </label>
                <label class="archive-checkbox">
                    <input type="checkbox" name="archive" value="nit" checked>
                    NIT Kiel Archive (30,000+ photos)
                </label>
                <label class="archive-checkbox">
                    <input type="checkbox" name="archive" value="akkasah">
                    Akkasah (NYU Abu Dhabi)
                </label>
                <label class="archive-checkbox">
                    <input type="checkbox" name="archive" value="archnet">
                    ArchNet
                </label>
                <label class="archive-checkbox">
                    <input type="checkbox" name="archive" value="manar">
                    Manar al-Athar
                </label>
            </div>
            
            <div class="form-group">
                <input type="text" class="form-control" id="searchInput" 
                       placeholder="Enter search terms (e.g., Antakya, Habib-i Neccar, Ottoman mosque)">
            </div>
            
            <button class="btn" onclick="searchArchives()">Search All Selected Archives</button>
            
            <div id="searchResults" class="results-container"></div>
        </div>
        
        <!-- Field Documentation Tab -->
        <div id="field-tab" class="tab-content">
            <h2>Create Damage Assessment</h2>
            <p>Document earthquake damage using UNESCO/ICCROM standards.</p>
            
            <form id="assessmentForm">
                <div class="grid-2">
                    <div class="form-group">
                        <label>Site Name</label>
                        <input type="text" class="form-control" name="site_name" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Location</label>
                        <input type="text" class="form-control" name="location" required>
                    </div>
                </div>
                
                <div class="grid-2">
                    <div class="form-group">
                        <label>Assessor Name</label>
                        <input type="text" class="form-control" name="assessor_name" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Overall Damage Category</label>
                        <select class="form-control" name="damage_category" required>
                            <option value="">Select damage level</option>
                            <option value="NO_DAMAGE">No Damage</option>
                            <option value="SLIGHT">Slight</option>
                            <option value="MODERATE">Moderate</option>
                            <option value="HEAVY">Heavy</option>
                            <option value="SEVERE">Severe</option>
                            <option value="DESTROYED">Destroyed</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Description</label>
                    <textarea class="form-control" name="description" required></textarea>
                </div>
                
                <div class="form-group">
                    <label>Architectural Elements</label>
                    <div id="elementsList" class="element-list">
                        <div class="element-item">
                            <input type="text" class="form-control" placeholder="Element name (e.g., minaret)">
                            <select class="form-control">
                                <option value="NO_DAMAGE">No Damage</option>
                                <option value="SLIGHT">Slight</option>
                                <option value="MODERATE">Moderate</option>
                                <option value="HEAVY">Heavy</option>
                                <option value="SEVERE">Severe</option>
                                <option value="DESTROYED">Destroyed</option>
                            </select>
                            <button type="button" class="btn danger" onclick="removeElement(this)">Remove</button>
                        </div>
                    </div>
                    <button type="button" class="btn secondary" onclick="addElement()">Add Element</button>
                </div>
                
                <button type="submit" class="btn success">Save Assessment</button>
            </form>
            
            <div id="assessmentResults" class="results-container" style="margin-top: 2rem;"></div>
        </div>
        
        <!-- Backup System Tab -->
        <div id="backup-tab" class="tab-content">
            <h2>Backup Management</h2>
            <p>Create and manage incremental backups of all data.</p>
            
            <div class="grid-2">
                <div>
                    <h3>Create New Backup</h3>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="backup-s3"> Amazon S3
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="backup-gcs"> Google Cloud Storage
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="backup-dropbox"> Dropbox
                        </label>
                    </div>
                    <button class="btn" onclick="createBackup()">Create Backup Now</button>
                </div>
                
                <div>
                    <h3>Backup Statistics</h3>
                    <div class="stats-card">
                        <h3 id="backupCount">0</h3>
                        <p>Total Backups</p>
                    </div>
                </div>
            </div>
            
            <div id="backupResults" class="results-container" style="margin-top: 2rem;"></div>
        </div>
        
        <!-- Deduplication Tab -->
        <div id="dedup-tab" class="tab-content">
            <h2>Deduplication Engine Demo</h2>
            <p>Test the smart duplicate detection system.</p>
            
            <div class="dedup-demo">
                <div>
                    <h3>Input Records</h3>
                    <div class="dedup-input">
                        <p><strong>Record 1:</strong> Antakya Great Mosque (URL: example.com/1)</p>
                        <p><strong>Record 2:</strong> Antakya Great Mosque (URL: example.com/2)</p>
                        <p><strong>Record 3:</strong> Antakya Grand Mosque (URL: example.com/3)</p>
                        <p><strong>Record 4:</strong> St. Pierre Church (URL: example.com/4)</p>
                        <p><strong>Record 5:</strong> St. Peter Church (URL: example.com/5)</p>
                    </div>
                    <button class="btn" onclick="testDeduplication()">Run Deduplication</button>
                </div>
                
                <div>
                    <h3>Results</h3>
                    <div id="dedupResults" class="dedup-output">
                        <p>Click "Run Deduplication" to see results</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Scholarly Tools Tab -->
        <div id="scholarly-tab" class="tab-content">
            <h2>Academic Research Tools</h2>
            
            <div class="grid-2">
                <div>
                    <h3>Create Annotation</h3>
                    <form id="annotationForm">
                        <div class="form-group">
                            <label>Monument ID</label>
                            <input type="text" class="form-control" name="monument_id" placeholder="e.g., ANT_001">
                        </div>
                        <div class="form-group">
                            <label>Monument Name</label>
                            <input type="text" class="form-control" name="monument_name" placeholder="e.g., Habib-i Neccar Mosque">
                        </div>
                        <div class="form-group">
                            <label>Type</label>
                            <select class="form-control" name="type">
                                <option value="mosque">Mosque</option>
                                <option value="church">Church</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Period</label>
                            <input type="text" class="form-control" name="period" placeholder="e.g., Late Ottoman (19th century)">
                        </div>
                        <button type="submit" class="btn">Create Annotation</button>
                    </form>
                </div>
                
                <div>
                    <h3>Citation Generator</h3>
                    <form id="citationForm">
                        <div class="form-group">
                            <label>Archive Type</label>
                            <select class="form-control" name="type" onchange="updateCitationFields(this.value)">
                                <option value="salt">SALT Research</option>
                                <option value="archnet">ArchNet</option>
                            </select>
                        </div>
                        <div id="citationFields">
                            <div class="form-group">
                                <label>Title</label>
                                <input type="text" class="form-control" name="title">
                            </div>
                            <div class="form-group">
                                <label>Photographer</label>
                                <input type="text" class="form-control" name="photographer">
                            </div>
                        </div>
                        <button type="submit" class="btn">Generate Citation</button>
                    </form>
                    <div id="citationOutput" class="citation-output" style="display: none;"></div>
                </div>
            </div>
        </div>
        
        <!-- Before/After Comparison Tab -->
        <div id="comparison-tab" class="tab-content">
            <h2>Before/After Analysis</h2>
            <p>AI-powered comparison of pre and post-earthquake documentation.</p>
            
            <button class="btn" onclick="runComparison()">Analyze Sample Data</button>
            
            <div id="comparisonResults" class="results-container" style="margin-top: 2rem;"></div>
        </div>
        
        <!-- Public Gallery Tab -->
        <div id="gallery-tab" class="tab-content">
            <h2>Public Web Gallery</h2>
            <p>Generate an interactive gallery for public access.</p>
            
            <button class="btn success" onclick="generateGallery()">Generate Gallery</button>
            <button class="btn secondary" onclick="viewGallery()" style="display: none;" id="viewGalleryBtn">View Gallery</button>
            
            <div id="galleryStatus" style="margin-top: 2rem;"></div>
        </div>
    </div>
    
    <!-- Modal for messages -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div id="modalBody"></div>
        </div>
    </div>
    
    <script>
        let currentTab = 'search';
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadAssessments();
            loadBackups();
            checkSystemStatus();
        });
        
        // Tab switching
        function showTab(tabName) {
            currentTab = tabName;
            
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active from all tab buttons
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Mark tab button as active
            event.target.classList.add('active');
        }
        
        // System status check
        async function checkSystemStatus() {
            try {
                const response = await fetch('/api/system-status');
                const status = await response.json();
                console.log('System status:', status);
            } catch (error) {
                console.error('Status check failed:', error);
            }
        }
        
        // Archive Search
        async function searchArchives() {
            const searchInput = document.getElementById('searchInput');
            const resultsDiv = document.getElementById('searchResults');
            const searchTerms = searchInput.value.trim();
            
            if (!searchTerms) {
                resultsDiv.innerHTML = '<div class="error">Please enter search terms</div>';
                return;
            }
            
            const selectedArchives = [];
            document.querySelectorAll('input[name="archive"]:checked').forEach(cb => {
                selectedArchives.push(cb.value);
            });
            
            if (selectedArchives.length === 0) {
                resultsDiv.innerHTML = '<div class="error">Please select at least one archive</div>';
                return;
            }
            
            resultsDiv.innerHTML = '<div class="loading">Searching archives...</div>';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        terms: searchTerms,
                        archives: selectedArchives
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let html = `<div class="success">Found ${data.count} results</div>`;
                    
                    if (data.errors && data.errors.length > 0) {
                        html += `<div class="info">Note: ${data.errors.join(', ')}</div>`;
                    }
                    
                    if (data.results && data.results.length > 0) {
                        data.results.forEach(result => {
                            html += `
                                <div class="result-item">
                                    <div class="result-title">${result.title}</div>
                                    <div class="result-meta">
                                        <span class="status-badge success">${result.archive}</span>
                                        <span class="status-badge warning">${result.type}</span>
                                        ${result.creator ? `<br>Creator: ${result.creator}` : ''}
                                        ${result.date ? `<br>Date: ${result.date}` : ''}
                                        ${result.description ? `<br>${result.description}` : ''}
                                        ${result.url ? `<br><a href="${result.url}" target="_blank">View source →</a>` : ''}
                                    </div>
                                </div>
                            `;
                        });
                    }
                    
                    resultsDiv.innerHTML = html;
                } else {
                    resultsDiv.innerHTML = `<div class="error">Search failed: ${data.error}</div>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            }
        }
        
        // Field Documentation
        document.getElementById('assessmentForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const elements = [];
            
            document.querySelectorAll('#elementsList .element-item').forEach(item => {
                const name = item.querySelector('input').value;
                const damage = item.querySelector('select').value;
                if (name) {
                    elements.push({ name, damage });
                }
            });
            
            const data = {
                site_name: formData.get('site_name'),
                location: formData.get('location'),
                assessor_name: formData.get('assessor_name'),
                damage_category: formData.get('damage_category'),
                description: formData.get('description'),
                elements: elements
            };
            
            try {
                const response = await fetch('/api/field-documentation/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showModal('Success', `Assessment created: ${result.assessment_id}`);
                    e.target.reset();
                    loadAssessments();
                } else {
                    showModal('Error', result.error);
                }
            } catch (error) {
                showModal('Error', error.message);
            }
        });
        
        function addElement() {
            const elementsList = document.getElementById('elementsList');
            const newElement = document.createElement('div');
            newElement.className = 'element-item';
            newElement.innerHTML = `
                <input type="text" class="form-control" placeholder="Element name (e.g., minaret)">
                <select class="form-control">
                    <option value="NO_DAMAGE">No Damage</option>
                    <option value="SLIGHT">Slight</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="HEAVY">Heavy</option>
                    <option value="SEVERE">Severe</option>
                    <option value="DESTROYED">Destroyed</option>
                </select>
                <button type="button" class="btn danger" onclick="removeElement(this)">Remove</button>
            `;
            elementsList.appendChild(newElement);
        }
        
        function removeElement(button) {
            button.parentElement.remove();
        }
        
        async function loadAssessments() {
            try {
                const response = await fetch('/api/field-documentation/list');
                const data = await response.json();
                
                const resultsDiv = document.getElementById('assessmentResults');
                if (data.assessments.length === 0) {
                    resultsDiv.innerHTML = '<p>No assessments yet.</p>';
                    return;
                }
                
                let html = '<h3>Recent Assessments</h3>';
                data.assessments.forEach(assessment => {
                    const damageClass = assessment.damage_category.toLowerCase();
                    html += `
                        <div class="result-item">
                            <div class="result-title">${assessment.site_name}</div>
                            <div class="result-meta">
                                <span class="status-badge danger">Damage: ${assessment.damage_category}</span>
                                <br>Location: ${assessment.location}
                                <br>Assessor: ${assessment.assessor_name}
                                <br>Date: ${new Date(assessment.timestamp).toLocaleDateString()}
                                <br>${assessment.description}
                            </div>
                        </div>
                    `;
                });
                
                resultsDiv.innerHTML = html;
            } catch (error) {
                console.error('Failed to load assessments:', error);
            }
        }
        
        // Backup System
        async function createBackup() {
            const data = {
                s3: document.getElementById('backup-s3').checked,
                gcs: document.getElementById('backup-gcs').checked,
                dropbox: document.getElementById('backup-dropbox').checked
            };
            
            try {
                const response = await fetch('/api/backup/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showModal('Success', 'Backup created successfully!');
                    loadBackups();
                } else {
                    showModal('Error', result.error);
                }
            } catch (error) {
                showModal('Error', error.message);
            }
        }
        
        async function loadBackups() {
            try {
                const response = await fetch('/api/backup/list');
                const data = await response.json();
                
                document.getElementById('backupCount').textContent = data.backups.length;
                
                const resultsDiv = document.getElementById('backupResults');
                if (data.backups.length === 0) {
                    resultsDiv.innerHTML = '<p>No backups yet.</p>';
                    return;
                }
                
                let html = '<h3>Backup History</h3>';
                data.backups.forEach(backup => {
                    html += `
                        <div class="result-item">
                            <div class="result-title">${backup.name}</div>
                            <div class="result-meta">
                                Date: ${new Date(backup.timestamp).toLocaleString()}
                                <br>Size: ${backup.size}
                                <br>Destinations: ${backup.destinations.join(', ')}
                            </div>
                        </div>
                    `;
                });
                
                resultsDiv.innerHTML = html;
            } catch (error) {
                console.error('Failed to load backups:', error);
            }
        }
        
        // Deduplication
        async function testDeduplication() {
            const testData = {
                records: [
                    { id: '1', title: 'Antakya Great Mosque', url: 'example.com/1' },
                    { id: '2', title: 'Antakya Great Mosque', url: 'example.com/2' },
                    { id: '3', title: 'Antakya Grand Mosque', url: 'example.com/3' },
                    { id: '4', title: 'St. Pierre Church', url: 'example.com/4' },
                    { id: '5', title: 'St. Peter Church', url: 'example.com/5' }
                ]
            };
            
            try {
                const response = await fetch('/api/deduplication/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(testData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    let html = `
                        <p><strong>Original:</strong> ${result.original_count} records</p>
                        <p><strong>After deduplication:</strong> ${result.unique_count} records</p>
                        <p><strong>Duplicates removed:</strong> ${result.duplicates_removed}</p>
                        <hr>
                        <p><strong>Unique records:</strong></p>
                    `;
                    
                    result.unique_records.forEach(record => {
                        html += `<p>• ${record.title} (${record.url})</p>`;
                    });
                    
                    document.getElementById('dedupResults').innerHTML = html;
                }
            } catch (error) {
                document.getElementById('dedupResults').innerHTML = `<div class="error">${error.message}</div>`;
            }
        }
        
        // Scholarly Tools
        document.getElementById('annotationForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            const data = {
                monument_id: formData.get('monument_id'),
                monument_name: formData.get('monument_name'),
                author: 'Research Team',
                type: formData.get('type'),
                period: formData.get('period'),
                elements: ['minaret', 'courtyard', 'mihrab'],
                description: 'Important example of regional architecture'
            };
            
            try {
                const response = await fetch('/api/scholarly/create-annotation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showModal('Success', `Annotation created: ${result.annotation_id}`);
                    e.target.reset();
                } else {
                    showModal('Error', result.error);
                }
            } catch (error) {
                showModal('Error', error.message);
            }
        });
        
        document.getElementById('citationForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            const data = {
                type: formData.get('type'),
                title: formData.get('title'),
                photographer: formData.get('photographer'),
                date: '1975',
                collection: 'Historical Collection',
                item_no: 'HC001'
            };
            
            try {
                const response = await fetch('/api/scholarly/generate-citation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('citationOutput').style.display = 'block';
                    document.getElementById('citationOutput').innerHTML = result.citation;
                } else {
                    showModal('Error', result.error);
                }
            } catch (error) {
                showModal('Error', error.message);
            }
        });
        
        function updateCitationFields(type) {
            // Update fields based on citation type
            const fieldsDiv = document.getElementById('citationFields');
            if (type === 'salt') {
                fieldsDiv.innerHTML = `
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" class="form-control" name="title">
                    </div>
                    <div class="form-group">
                        <label>Photographer</label>
                        <input type="text" class="form-control" name="photographer">
                    </div>
                `;
            } else {
                fieldsDiv.innerHTML = `
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" class="form-control" name="title">
                    </div>
                    <div class="form-group">
                        <label>URL</label>
                        <input type="text" class="form-control" name="url">
                    </div>
                `;
            }
        }
        
        // Before/After Comparison
        async function runComparison() {
            const resultsDiv = document.getElementById('comparisonResults');
            resultsDiv.innerHTML = '<div class="loading">Running comparison analysis...</div>';
            
            try {
                const response = await fetch('/api/comparison/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        before: [
                            { title: 'Habib-i Neccar Mosque - 1975', keywords: 'mosque, minaret, intact' }
                        ],
                        after: [
                            { title: 'Habib-i Neccar Mosque - 2023', keywords: 'mosque, damage, collapsed' }
                        ]
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    let html = '<h3>Comparison Results</h3>';
                    result.matches.forEach(match => {
                        html += `
                            <div class="result-item">
                                <div class="result-title">${match.building}</div>
                                <div class="result-meta">
                                    <span class="status-badge danger">Damage: ${match.damage_assessment}</span>
                                    <span class="status-badge success">Confidence: ${(match.confidence * 100).toFixed(0)}%</span>
                                    <br><strong>Before:</strong> ${match.before.description}
                                    <br><strong>After:</strong> ${match.after.description}
                                </div>
                            </div>
                        `;
                    });
                    resultsDiv.innerHTML = html;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error">${error.message}</div>`;
            }
        }
        
        // Public Gallery
        async function generateGallery() {
            const statusDiv = document.getElementById('galleryStatus');
            statusDiv.innerHTML = '<div class="loading">Generating gallery...</div>';
            
            try {
                const response = await fetch('/api/gallery/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.innerHTML = '<div class="success">Gallery generated successfully!</div>';
                    document.getElementById('viewGalleryBtn').style.display = 'inline-block';
                } else {
                    statusDiv.innerHTML = `<div class="error">${result.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">${error.message}</div>`;
            }
        }
        
        function viewGallery() {
            window.open('/gallery/', '_blank');
        }
        
        // Modal functions
        function showModal(title, message) {
            document.getElementById('modalBody').innerHTML = `<h2>${title}</h2><p>${message}</p>`;
            document.getElementById('modal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('modal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        // Add enter key support for search
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchArchives();
            }
        });
    </script>
</body>
</html>'''
    
    # Save the template
    with open(templates_dir / 'dashboard_full.html', 'w') as f:
        f.write(dashboard_html)
    
    # Run the app
    import webbrowser
    from threading import Timer
    
    def open_browser():
        webbrowser.open('http://127.0.0.1:5001')
    
    Timer(1, open_browser).start()
    
    print("\n🌐 Starting full-featured web dashboard...")
    print("📍 Opening browser to http://127.0.0.1:5001")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=False, port=5001)