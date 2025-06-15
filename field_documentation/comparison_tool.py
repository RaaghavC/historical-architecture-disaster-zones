"""
Before/After Comparison Tool for Heritage Sites
Enables visual comparison of pre and post-earthquake conditions
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import json
from dataclasses import dataclass, field
from PIL import Image, ImageDraw, ImageFont
import numpy as np


@dataclass
class ComparisonPair:
    """A pair of before/after images for comparison"""
    site_id: str
    site_name: str
    before_image: str
    after_image: str
    before_date: Optional[datetime] = None
    after_date: Optional[datetime] = None
    before_source: str = ""
    after_source: str = ""
    damage_assessment: Optional[str] = None
    notes: str = ""
    gps_location: Optional[Tuple[float, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'site_id': self.site_id,
            'site_name': self.site_name,
            'before_image': self.before_image,
            'after_image': self.after_image,
            'before_date': self.before_date.isoformat() if self.before_date else None,
            'after_date': self.after_date.isoformat() if self.after_date else None,
            'before_source': self.before_source,
            'after_source': self.after_source,
            'damage_assessment': self.damage_assessment,
            'notes': self.notes,
            'gps_location': list(self.gps_location) if self.gps_location else None
        }


class BeforeAfterComparison:
    """
    Tool for creating and managing before/after comparisons
    """
    
    def __init__(self, base_directory: str = "comparisons"):
        self.base_dir = Path(base_directory)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.pairs_dir = self.base_dir / "pairs"
        self.output_dir = self.base_dir / "output"
        self.pairs_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        self.comparisons: List[ComparisonPair] = []
        self.load_comparisons()
    
    def load_comparisons(self):
        """Load existing comparisons from disk"""
        comparisons_file = self.base_dir / "comparisons.json"
        if comparisons_file.exists():
            with open(comparisons_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.comparisons = [
                    ComparisonPair(
                        site_id=c['site_id'],
                        site_name=c['site_name'],
                        before_image=c['before_image'],
                        after_image=c['after_image'],
                        before_date=datetime.fromisoformat(c['before_date']) if c.get('before_date') else None,
                        after_date=datetime.fromisoformat(c['after_date']) if c.get('after_date') else None,
                        before_source=c.get('before_source', ''),
                        after_source=c.get('after_source', ''),
                        damage_assessment=c.get('damage_assessment'),
                        notes=c.get('notes', ''),
                        gps_location=tuple(c['gps_location']) if c.get('gps_location') else None
                    )
                    for c in data
                ]
    
    def save_comparisons(self):
        """Save comparisons to disk"""
        comparisons_file = self.base_dir / "comparisons.json"
        data = [c.to_dict() for c in self.comparisons]
        with open(comparisons_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_comparison(self, comparison: ComparisonPair) -> ComparisonPair:
        """Add a new comparison pair"""
        # Copy images to pairs directory
        before_path = Path(comparison.before_image)
        after_path = Path(comparison.after_image)
        
        if before_path.exists() and after_path.exists():
            # Create unique filenames
            before_dest = self.pairs_dir / f"{comparison.site_id}_before{before_path.suffix}"
            after_dest = self.pairs_dir / f"{comparison.site_id}_after{after_path.suffix}"
            
            # Copy images
            Image.open(before_path).save(before_dest)
            Image.open(after_path).save(after_dest)
            
            # Update paths
            comparison.before_image = str(before_dest)
            comparison.after_image = str(after_dest)
        
        self.comparisons.append(comparison)
        self.save_comparisons()
        return comparison
    
    def create_side_by_side(self, comparison: ComparisonPair, 
                           output_path: Optional[str] = None,
                           add_labels: bool = True) -> str:
        """Create a side-by-side comparison image"""
        # Load images
        before_img = Image.open(comparison.before_image)
        after_img = Image.open(comparison.after_image)
        
        # Resize to same height
        target_height = min(before_img.height, after_img.height, 800)
        before_img = self._resize_to_height(before_img, target_height)
        after_img = self._resize_to_height(after_img, target_height)
        
        # Create combined image
        total_width = before_img.width + after_img.width + 10  # 10px separator
        combined = Image.new('RGB', (total_width, target_height), 'white')
        
        # Paste images
        combined.paste(before_img, (0, 0))
        combined.paste(after_img, (before_img.width + 10, 0))
        
        # Add separator line
        draw = ImageDraw.Draw(combined)
        separator_x = before_img.width + 5
        draw.line([(separator_x, 0), (separator_x, target_height)], fill='black', width=2)
        
        # Add labels if requested
        if add_labels:
            self._add_labels(draw, comparison, before_img.width, target_height)
        
        # Save output
        if not output_path:
            output_path = self.output_dir / f"{comparison.site_id}_comparison.jpg"
        else:
            output_path = Path(output_path)
        
        combined.save(output_path, quality=95)
        return str(output_path)
    
    def create_overlay(self, comparison: ComparisonPair, 
                      output_path: Optional[str] = None,
                      opacity: float = 0.5) -> str:
        """Create an overlay comparison with adjustable opacity"""
        # Load images
        before_img = Image.open(comparison.before_image).convert('RGBA')
        after_img = Image.open(comparison.after_image).convert('RGBA')
        
        # Resize to same size
        target_size = (
            min(before_img.width, after_img.width, 1200),
            min(before_img.height, after_img.height, 800)
        )
        before_img = before_img.resize(target_size, Image.Resampling.LANCZOS)
        after_img = after_img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Create overlay
        after_img.putalpha(int(255 * opacity))
        combined = Image.alpha_composite(before_img, after_img)
        
        # Save output
        if not output_path:
            output_path = self.output_dir / f"{comparison.site_id}_overlay.png"
        else:
            output_path = Path(output_path)
        
        combined.save(output_path)
        return str(output_path)
    
    def create_slider_html(self, comparison: ComparisonPair,
                          output_path: Optional[str] = None) -> str:
        """Create an interactive HTML slider comparison"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_name} - Before/After Comparison</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        .comparison-container {{
            position: relative;
            width: 100%;
            overflow: hidden;
        }}
        .image-container {{
            position: relative;
            width: 100%;
            height: 600px;
        }}
        .image {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        .after-image {{
            clip-path: inset(0 0 0 50%);
        }}
        .slider {{
            position: absolute;
            top: 0;
            left: 50%;
            width: 4px;
            height: 100%;
            background: white;
            cursor: ew-resize;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }}
        .slider::before {{
            content: '◀ ▶';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 20px;
        }}
        .info {{
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
        }}
        .damage-assessment {{
            padding: 10px;
            margin-top: 10px;
            background: #fee;
            border-left: 4px solid #c00;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{site_name}</h1>
        <div class="comparison-container">
            <div class="image-container" id="imageContainer">
                <img src="{before_image}" class="image before-image" alt="Before">
                <img src="{after_image}" class="image after-image" alt="After" id="afterImage">
                <div class="slider" id="slider"></div>
            </div>
        </div>
        <div class="info">
            <p><strong>Before:</strong> {before_date} (Source: {before_source})</p>
            <p><strong>After:</strong> {after_date} (Source: {after_source})</p>
            {damage_info}
            {notes_info}
        </div>
    </div>
    
    <script>
        const slider = document.getElementById('slider');
        const afterImage = document.getElementById('afterImage');
        const container = document.getElementById('imageContainer');
        let isDown = false;
        
        slider.addEventListener('mousedown', () => isDown = true);
        document.addEventListener('mouseup', () => isDown = false);
        document.addEventListener('mousemove', (e) => {{
            if (!isDown) return;
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percent = (x / rect.width) * 100;
            if (percent >= 0 && percent <= 100) {{
                slider.style.left = percent + '%';
                afterImage.style.clipPath = `inset(0 0 0 ${{percent}}%)`;
            }}
        }});
        
        // Touch support
        slider.addEventListener('touchstart', () => isDown = true);
        document.addEventListener('touchend', () => isDown = false);
        document.addEventListener('touchmove', (e) => {{
            if (!isDown) return;
            const rect = container.getBoundingClientRect();
            const x = e.touches[0].clientX - rect.left;
            const percent = (x / rect.width) * 100;
            if (percent >= 0 && percent <= 100) {{
                slider.style.left = percent + '%';
                afterImage.style.clipPath = `inset(0 0 0 ${{percent}}%)`;
            }}
        }});
    </script>
</body>
</html>
        """
        
        # Format dates
        before_date = comparison.before_date.strftime('%Y-%m-%d') if comparison.before_date else 'Unknown'
        after_date = comparison.after_date.strftime('%Y-%m-%d') if comparison.after_date else 'Unknown'
        
        # Format damage info
        damage_info = ""
        if comparison.damage_assessment:
            damage_info = f'<div class="damage-assessment"><strong>Damage Assessment:</strong> {comparison.damage_assessment}</div>'
        
        # Format notes
        notes_info = ""
        if comparison.notes:
            notes_info = f'<p><strong>Notes:</strong> {comparison.notes}</p>'
        
        # Copy images to output directory for HTML access
        before_filename = f"{comparison.site_id}_before.jpg"
        after_filename = f"{comparison.site_id}_after.jpg"
        
        before_dest = self.output_dir / before_filename
        after_dest = self.output_dir / after_filename
        
        Image.open(comparison.before_image).save(before_dest)
        Image.open(comparison.after_image).save(after_dest)
        
        # Generate HTML
        html_content = html_template.format(
            site_name=comparison.site_name,
            before_image=before_filename,
            after_image=after_filename,
            before_date=before_date,
            after_date=after_date,
            before_source=comparison.before_source,
            after_source=comparison.after_source,
            damage_info=damage_info,
            notes_info=notes_info
        )
        
        # Save HTML
        if not output_path:
            output_path = self.output_dir / f"{comparison.site_id}_comparison.html"
        else:
            output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _resize_to_height(self, img: Image.Image, target_height: int) -> Image.Image:
        """Resize image to target height maintaining aspect ratio"""
        ratio = target_height / img.height
        target_width = int(img.width * ratio)
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    def _add_labels(self, draw: ImageDraw.Draw, comparison: ComparisonPair,
                   separator_x: int, height: int):
        """Add labels to the comparison image"""
        # Try to use a better font if available
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            font = ImageFont.load_default()
            title_font = font
        
        # Add site name at top
        title = comparison.site_name
        draw.text((10, 10), title, fill='white', font=title_font, stroke_width=2, stroke_fill='black')
        
        # Add "BEFORE" and "AFTER" labels
        draw.text((10, height - 30), "BEFORE", fill='white', font=font, stroke_width=2, stroke_fill='black')
        draw.text((separator_x + 20, height - 30), "AFTER", fill='white', font=font, stroke_width=2, stroke_fill='black')
        
        # Add dates if available
        if comparison.before_date:
            date_text = comparison.before_date.strftime('%Y-%m-%d')
            draw.text((10, height - 55), date_text, fill='white', font=font, stroke_width=1, stroke_fill='black')
        
        if comparison.after_date:
            date_text = comparison.after_date.strftime('%Y-%m-%d')
            draw.text((separator_x + 20, height - 55), date_text, fill='white', font=font, stroke_width=1, stroke_fill='black')
    
    def generate_comparison_gallery(self, output_path: Optional[str] = None) -> str:
        """Generate an HTML gallery of all comparisons"""
        if not output_path:
            output_path = self.output_dir / "comparison_gallery.html"
        else:
            output_path = Path(output_path)
        
        # Create comparison images
        comparison_files = []
        for comp in self.comparisons:
            try:
                img_path = self.create_side_by_side(comp)
                html_path = self.create_slider_html(comp)
                comparison_files.append({
                    'site_name': comp.site_name,
                    'image': Path(img_path).name,
                    'slider': Path(html_path).name,
                    'damage': comp.damage_assessment or 'Not assessed'
                })
            except Exception as e:
                print(f"Error creating comparison for {comp.site_name}: {e}")
        
        # Generate gallery HTML
        gallery_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Antakya Heritage - Before/After Comparisons</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .comparison-card {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .comparison-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .comparison-image {{
            width: 100%;
            height: 250px;
            object-fit: cover;
        }}
        .card-content {{
            padding: 15px;
        }}
        .site-name {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .damage-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            color: white;
            margin-bottom: 10px;
        }}
        .damage-severe {{ background-color: #d32f2f; }}
        .damage-heavy {{ background-color: #f57c00; }}
        .damage-moderate {{ background-color: #fbc02d; }}
        .damage-slight {{ background-color: #689f38; }}
        .damage-none {{ background-color: #388e3c; }}
        .view-link {{
            display: inline-block;
            padding: 8px 15px;
            background-color: #1976d2;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .view-link:hover {{
            background-color: #1565c0;
        }}
        .stats {{
            max-width: 1400px;
            margin: 0 auto 30px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <h1>Antakya Heritage Sites - Before/After Earthquake Comparisons</h1>
    
    <div class="stats">
        <h2>Summary</h2>
        <p>Total sites documented: {total_sites}</p>
        <p>Earthquake date: February 6, 2023</p>
    </div>
    
    <div class="gallery">
        {gallery_items}
    </div>
</body>
</html>
        """
        
        # Generate gallery items
        gallery_items = []
        for comp in comparison_files:
            damage_class = 'damage-none'
            if 'severe' in comp['damage'].lower():
                damage_class = 'damage-severe'
            elif 'heavy' in comp['damage'].lower():
                damage_class = 'damage-heavy'
            elif 'moderate' in comp['damage'].lower():
                damage_class = 'damage-moderate'
            elif 'slight' in comp['damage'].lower():
                damage_class = 'damage-slight'
            
            item_html = f"""
            <div class="comparison-card">
                <img src="{comp['image']}" class="comparison-image" alt="{comp['site_name']}">
                <div class="card-content">
                    <div class="site-name">{comp['site_name']}</div>
                    <div class="damage-badge {damage_class}">{comp['damage']}</div>
                    <br>
                    <a href="{comp['slider']}" class="view-link">View Interactive Comparison</a>
                </div>
            </div>
            """
            gallery_items.append(item_html)
        
        # Write gallery
        html_content = gallery_html.format(
            total_sites=len(self.comparisons),
            gallery_items='\n'.join(gallery_items)
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)