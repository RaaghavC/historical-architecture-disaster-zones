"""
Command-line interface for field documentation system
"""

import click
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .damage_assessment import (
    DamageAssessmentForm,
    DamageCategory,
    UrgencyLevel,
    MOSQUE_TEMPLATE,
    CHURCH_TEMPLATE
)
from .field_collector import FieldDataCollector, quick_damage_assessment
from .comparison_tool import BeforeAfterComparison, ComparisonPair


@click.group()
def cli():
    """Antakya Heritage Field Documentation System"""
    pass


@cli.command()
@click.option('--site-name', required=True, help='Name of the heritage site')
@click.option('--site-id', required=True, help='Unique site identifier')
@click.option('--template', type=click.Choice(['mosque', 'church', 'none']), 
              default='none', help='Use a predefined template')
@click.option('--assessor', help='Name of the assessor')
@click.option('--output-dir', default='field_data', help='Output directory')
def new_assessment(site_name: str, site_id: str, template: str, 
                  assessor: Optional[str], output_dir: str):
    """Create a new damage assessment form"""
    collector = FieldDataCollector(output_dir)
    
    # Create assessment based on template
    if template == 'mosque':
        assessment = MOSQUE_TEMPLATE
        assessment.site_name = site_name
        assessment.site_id = site_id
    elif template == 'church':
        assessment = CHURCH_TEMPLATE
        assessment.site_name = site_name
        assessment.site_id = site_id
    else:
        assessment = collector.create_assessment(site_name, site_id)
    
    if assessor:
        assessment.assessor_name = assessor
    
    # Save assessment
    filepath = collector.save_assessment(assessment)
    click.echo(f"✓ Created new assessment: {filepath}")
    click.echo(f"Assessment ID: {assessment.assessment_id}")


@cli.command()
@click.option('--site-name', required=True, help='Name of the heritage site')
@click.option('--site-id', required=True, help='Unique site identifier')
@click.option('--damage', required=True, 
              type=click.Choice(['none', 'slight', 'moderate', 'heavy', 'severe', 'destroyed']),
              help='Overall damage level')
@click.option('--urgency', required=True,
              type=click.Choice(['immediate', 'urgent', 'short', 'medium', 'long']),
              help='Urgency of intervention')
@click.option('--photos', multiple=True, help='Photo paths to attach')
@click.option('--output-dir', default='field_data', help='Output directory')
def quick_assess(site_name: str, site_id: str, damage: str, 
                urgency: str, photos: tuple, output_dir: str):
    """Create a quick damage assessment"""
    assessment = quick_damage_assessment(
        site_name=site_name,
        site_id=site_id,
        overall_damage=damage,
        urgency=urgency,
        photos=list(photos) if photos else None
    )
    
    collector = FieldDataCollector(output_dir)
    filepath = collector.save_assessment(assessment)
    
    click.echo(f"✓ Quick assessment saved: {filepath}")
    click.echo(f"  Damage: {damage}")
    click.echo(f"  Urgency: {urgency}")
    if photos:
        click.echo(f"  Photos: {len(photos)} attached")


@cli.command()
@click.option('--output-dir', default='field_data', help='Field data directory')
def list_pending(output_dir: str):
    """List all pending assessments"""
    collector = FieldDataCollector(output_dir)
    pending = collector.get_pending_assessments()
    
    if not pending:
        click.echo("No pending assessments found.")
        return
    
    click.echo(f"\nPending Assessments ({len(pending)} total):")
    click.echo("-" * 60)
    
    for assessment in pending:
        date = assessment.get('assessment_date', 'Unknown')
        damage = assessment.get('overall_damage', 'Unknown')
        urgency = assessment.get('urgency_level', 'Unknown')
        
        click.echo(f"\n{assessment['site_name']} (ID: {assessment['site_id']})")
        click.echo(f"  Date: {date}")
        click.echo(f"  Damage: {damage} | Urgency: {urgency}")
        if assessment.get('immediate_danger'):
            click.echo("  ⚠️  IMMEDIATE DANGER")


@cli.command()
@click.option('--output-dir', default='field_data', help='Field data directory')
@click.option('--name', help='Export bundle name')
def export(output_dir: str, name: Optional[str]):
    """Export field data for offline transfer"""
    collector = FieldDataCollector(output_dir)
    
    click.echo("Exporting field data...")
    export_path = collector.export_for_offline(name)
    
    # Get summary
    pending = collector.get_pending_assessments()
    
    click.echo(f"\n✓ Export completed: {export_path}")
    click.echo(f"  Assessments: {len(pending)}")
    click.echo(f"  Photos: {len(list(collector.photos_dir.glob('*')))}")


@cli.command()
@click.option('--output-dir', default='field_data', help='Field data directory')
@click.option('--format', type=click.Choice(['json', 'summary']), default='summary')
def report(output_dir: str, format: str):
    """Generate field data report"""
    collector = FieldDataCollector(output_dir)
    report_data = collector.generate_field_report()
    
    if format == 'json':
        click.echo(json.dumps(report_data, indent=2))
    else:
        # Summary format
        click.echo("\n" + "="*60)
        click.echo("FIELD DATA COLLECTION REPORT")
        click.echo("="*60)
        
        summary = report_data['summary']
        click.echo(f"\nTotal Assessments: {summary['total_assessments']}")
        click.echo(f"Total Photos: {summary['total_photos']}")
        
        if summary['assessment_period']['start']:
            click.echo(f"Period: {summary['assessment_period']['start']} to {summary['assessment_period']['end']}")
        
        # Damage summary
        click.echo("\nDamage Summary:")
        for level, count in report_data['damage_summary'].items():
            if count > 0:
                click.echo(f"  {level.replace('_', ' ').title()}: {count}")
        
        # Urgency summary
        click.echo("\nUrgency Summary:")
        for level, count in report_data['urgency_summary'].items():
            if count > 0:
                click.echo(f"  {level.replace('_', ' ').title()}: {count}")
        
        # Critical sites
        critical = report_data.get('critical_sites', [])
        if critical:
            click.echo(f"\n⚠️  Critical Sites ({len(critical)}):")
            for site in critical:
                click.echo(f"  - {site['site_name']} ({site['damage']}/{site['urgency']})")


@cli.command()
@click.option('--site-name', required=True, help='Name of the heritage site')
@click.option('--site-id', required=True, help='Unique site identifier')
@click.option('--before', required=True, type=click.Path(exists=True), 
              help='Path to before image')
@click.option('--after', required=True, type=click.Path(exists=True), 
              help='Path to after image')
@click.option('--before-date', help='Date of before image (YYYY-MM-DD)')
@click.option('--after-date', help='Date of after image (YYYY-MM-DD)')
@click.option('--damage', help='Damage assessment')
@click.option('--output-dir', default='comparisons', help='Output directory')
def add_comparison(site_name: str, site_id: str, before: str, after: str,
                  before_date: Optional[str], after_date: Optional[str],
                  damage: Optional[str], output_dir: str):
    """Add a before/after comparison"""
    tool = BeforeAfterComparison(output_dir)
    
    # Parse dates
    before_dt = datetime.strptime(before_date, '%Y-%m-%d') if before_date else None
    after_dt = datetime.strptime(after_date, '%Y-%m-%d') if after_date else None
    
    comparison = ComparisonPair(
        site_id=site_id,
        site_name=site_name,
        before_image=before,
        after_image=after,
        before_date=before_dt,
        after_date=after_dt,
        damage_assessment=damage
    )
    
    tool.add_comparison(comparison)
    
    # Create outputs
    side_by_side = tool.create_side_by_side(comparison)
    slider_html = tool.create_slider_html(comparison)
    
    click.echo(f"✓ Comparison added for {site_name}")
    click.echo(f"  Side-by-side: {side_by_side}")
    click.echo(f"  Interactive: {slider_html}")


@cli.command()
@click.option('--output-dir', default='comparisons', help='Comparisons directory')
def gallery(output_dir: str):
    """Generate comparison gallery"""
    tool = BeforeAfterComparison(output_dir)
    
    if not tool.comparisons:
        click.echo("No comparisons found. Add some first with 'add-comparison'")
        return
    
    click.echo(f"Generating gallery for {len(tool.comparisons)} comparisons...")
    gallery_path = tool.generate_comparison_gallery()
    
    click.echo(f"\n✓ Gallery created: {gallery_path}")
    click.echo(f"  Open in browser to view interactive comparisons")


@cli.command()
def templates():
    """Show available assessment templates"""
    click.echo("\nAvailable Assessment Templates:")
    click.echo("-" * 40)
    
    click.echo("\nMOSQUE Template:")
    click.echo("  Elements assessed:")
    for element in MOSQUE_TEMPLATE.element_assessments:
        click.echo(f"    - {element.element.value}")
    
    click.echo("\nCHURCH Template:")
    click.echo("  Elements assessed:")
    for element in CHURCH_TEMPLATE.element_assessments:
        click.echo(f"    - {element.element.value}")
    
    click.echo("\nDamage Categories:")
    for cat in DamageCategory:
        click.echo(f"  {cat.value}: {cat.name.replace('_', ' ').title()}")
    
    click.echo("\nUrgency Levels:")
    for level in UrgencyLevel:
        click.echo(f"  {level.value}: {level.name.replace('_', ' ').title()}")


if __name__ == '__main__':
    cli()