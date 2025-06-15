"""
Public Web Gallery Generator for Antakya Heritage Collection
Creates a static HTML gallery with search, filtering, and map visualization
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from jinja2 import Template


class PublicGalleryGenerator:
    """Generate a public-facing web gallery of the heritage collection"""
    
    def __init__(self, data_dir: str = ".", output_dir: str = "public_gallery"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.assets_dir = self.output_dir / "assets"
        self.images_dir = self.output_dir / "images"
        self.data_output_dir = self.output_dir / "data"
        
        for dir in [self.assets_dir, self.images_dir, self.data_output_dir]:
            dir.mkdir(exist_ok=True)
    
    def load_collection_data(self) -> pd.DataFrame:
        """Load the master collection data"""
        # Try to find the most recent collection file
        collection_files = list(self.data_dir.glob("MASTER_COLLECTION_*.xlsx"))
        if not collection_files:
            collection_files = list(self.data_dir.glob("USABLE_DATABASE_*.xlsx"))
        
        if not collection_files:
            raise FileNotFoundError("No collection data found")
        
        # Use most recent file
        latest_file = max(collection_files, key=lambda p: p.stat().st_mtime)
        
        # Load data
        df = pd.read_excel(latest_file, sheet_name='All_Records')
        return df
    
    def prepare_gallery_data(self, df: pd.DataFrame) -> List[Dict]:
        """Prepare data for gallery display"""
        gallery_items = []
        
        for _, row in df.iterrows():
            # Skip items without images
            if pd.isna(row.get('Download_URL')) and pd.isna(row.get('Thumbnail_URL')):
                continue
            
            item = {
                'id': row.get('ID', ''),
                'title': row.get('Title', 'Untitled'),
                'description': row.get('Description', ''),
                'category': row.get('Category', 'Other'),
                'archive': row.get('Archive', ''),
                'date': row.get('Date', ''),
                'location': row.get('Location', ''),
                'image_url': row.get('Download_URL', row.get('Thumbnail_URL', '')),
                'thumbnail_url': row.get('Thumbnail_URL', row.get('Download_URL', '')),
                'source_url': row.get('URL', ''),
                'keywords': row.get('Keywords', '').split(', ') if row.get('Keywords') else [],
                'latitude': row.get('Latitude'),
                'longitude': row.get('Longitude')
            }
            
            # Clean up description
            if item['description'] and len(item['description']) > 300:
                item['description'] = item['description'][:297] + '...'
            
            gallery_items.append(item)
        
        return gallery_items
    
    def generate_html(self, gallery_items: List[Dict]) -> str:
        """Generate the main gallery HTML"""
        
        html_template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Antakya Heritage Digital Archive</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 2rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .stats {
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            font-size: 0.9rem;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .controls {
            background: white;
            padding: 1.5rem 0;
            border-bottom: 1px solid #e0e0e0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        .control-row {
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .search-box {
            flex: 1;
            min-width: 300px;
            position: relative;
        }
        
        .search-box input {
            width: 100%;
            padding: 0.75rem 1rem 0.75rem 2.5rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #3498db;
        }
        
        .search-icon {
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0.5;
        }
        
        .filter-group {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        select {
            padding: 0.75rem 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            background: white;
            cursor: pointer;
        }
        
        .view-toggle {
            display: flex;
            gap: 0.5rem;
            background: #f0f0f0;
            padding: 0.25rem;
            border-radius: 8px;
        }
        
        .view-btn {
            padding: 0.5rem 1rem;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.3s;
        }
        
        .view-btn.active {
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .content {
            padding: 2rem 0;
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .gallery-item {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }
        
        .gallery-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .gallery-item img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        
        .item-content {
            padding: 1.5rem;
        }
        
        .item-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #2c3e50;
        }
        
        .item-meta {
            display: flex;
            gap: 1rem;
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.75rem;
        }
        
        .category-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .item-description {
            font-size: 0.9rem;
            line-height: 1.5;
            color: #555;
        }
        
        #map {
            height: 500px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: none;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            overflow-y: auto;
        }
        
        .modal-content {
            background: white;
            max-width: 900px;
            margin: 2rem auto;
            border-radius: 12px;
            overflow: hidden;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .modal-close {
            font-size: 2rem;
            background: none;
            border: none;
            cursor: pointer;
            opacity: 0.5;
            transition: opacity 0.3s;
        }
        
        .modal-close:hover {
            opacity: 1;
        }
        
        .modal-body {
            padding: 1.5rem;
        }
        
        .modal-image {
            width: 100%;
            max-height: 500px;
            object-fit: contain;
            margin-bottom: 1.5rem;
        }
        
        .no-results {
            text-align: center;
            padding: 3rem;
            color: #666;
        }
        
        footer {
            background: #2c3e50;
            color: white;
            padding: 2rem 0;
            text-align: center;
            margin-top: 4rem;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
        }
        
        .spinner {
            display: inline-block;
            width: 50px;
            height: 50px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 2rem;
            }
            
            .gallery {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            }
            
            .control-row {
                flex-direction: column;
                align-items: stretch;
            }
            
            .search-box {
                min-width: 100%;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Antakya Heritage Digital Archive</h1>
            <p class="subtitle">Preserving the architectural heritage of ancient Antioch</p>
            <div class="stats">
                <div class="stat-item">
                    <span>📸</span>
                    <span id="total-items">{{ total_items }} items</span>
                </div>
                <div class="stat-item">
                    <span>🏛️</span>
                    <span>{{ categories|length }} categories</span>
                </div>
                <div class="stat-item">
                    <span>📚</span>
                    <span>{{ archives|length }} archives</span>
                </div>
            </div>
        </div>
    </header>
    
    <div class="controls">
        <div class="container">
            <div class="control-row">
                <div class="search-box">
                    <svg class="search-icon" width="20" height="20" viewBox="0 0 20 20">
                        <path fill="currentColor" d="M19 17l-5.15-5.15a7 7 0 1 0-2 2L17 19zM3.5 8A4.5 4.5 0 1 1 8 12.5 4.5 4.5 0 0 1 3.5 8z"/>
                    </svg>
                    <input type="text" id="search" placeholder="Search by title, description, or keywords...">
                </div>
                
                <div class="filter-group">
                    <select id="category-filter">
                        <option value="">All Categories</option>
                        {% for category in categories %}
                        <option value="{{ category }}">{{ category }}</option>
                        {% endfor %}
                    </select>
                    
                    <select id="archive-filter">
                        <option value="">All Archives</option>
                        {% for archive in archives %}
                        <option value="{{ archive }}">{{ archive }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="view-toggle">
                    <button class="view-btn active" data-view="gallery">Gallery</button>
                    <button class="view-btn" data-view="map">Map</button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="content">
        <div class="container">
            <div id="gallery-view" class="gallery">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading collection...</p>
                </div>
            </div>
            
            <div id="map-view" style="display: none;">
                <div id="map"></div>
            </div>
            
            <div id="no-results" class="no-results" style="display: none;">
                <h3>No items found</h3>
                <p>Try adjusting your search or filters</p>
            </div>
        </div>
    </div>
    
    <div id="modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modal-title"></h2>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <img id="modal-image" class="modal-image">
                <div id="modal-details"></div>
            </div>
        </div>
    </div>
    
    <footer>
        <div class="container">
            <p>Antakya Heritage Digital Archive - Preserving cultural memory after the 2023 earthquakes</p>
            <p style="margin-top: 0.5rem; opacity: 0.8;">A Stanford Public Humanities project</p>
        </div>
    </footer>
    
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Gallery data
        const galleryData = {{ gallery_data|tojson }};
        let filteredData = [...galleryData];
        let currentView = 'gallery';
        let map = null;
        let markers = [];
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            renderGallery();
            setupEventListeners();
            initializeMap();
        });
        
        function setupEventListeners() {
            // Search
            document.getElementById('search').addEventListener('input', filterGallery);
            
            // Filters
            document.getElementById('category-filter').addEventListener('change', filterGallery);
            document.getElementById('archive-filter').addEventListener('change', filterGallery);
            
            // View toggle
            document.querySelectorAll('.view-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    toggleView(this.dataset.view);
                });
            });
            
            // Modal
            document.querySelector('.modal-close').addEventListener('click', closeModal);
            document.getElementById('modal').addEventListener('click', function(e) {
                if (e.target === this) closeModal();
            });
        }
        
        function filterGallery() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const categoryFilter = document.getElementById('category-filter').value;
            const archiveFilter = document.getElementById('archive-filter').value;
            
            filteredData = galleryData.filter(item => {
                // Search filter
                const matchesSearch = !searchTerm || 
                    item.title.toLowerCase().includes(searchTerm) ||
                    item.description.toLowerCase().includes(searchTerm) ||
                    item.keywords.some(k => k.toLowerCase().includes(searchTerm));
                
                // Category filter
                const matchesCategory = !categoryFilter || item.category === categoryFilter;
                
                // Archive filter
                const matchesArchive = !archiveFilter || item.archive === archiveFilter;
                
                return matchesSearch && matchesCategory && matchesArchive;
            });
            
            document.getElementById('total-items').textContent = filteredData.length + ' items';
            renderGallery();
            updateMap();
        }
        
        function renderGallery() {
            const container = document.getElementById('gallery-view');
            
            if (filteredData.length === 0) {
                container.style.display = 'none';
                document.getElementById('no-results').style.display = 'block';
                return;
            }
            
            container.style.display = 'grid';
            document.getElementById('no-results').style.display = 'none';
            
            container.innerHTML = filteredData.map(item => `
                <div class="gallery-item" onclick="showModal('${item.id}')">
                    <img src="${item.thumbnail_url}" alt="${item.title}" onerror="this.src='assets/placeholder.jpg'">
                    <div class="item-content">
                        <h3 class="item-title">${item.title}</h3>
                        <div class="item-meta">
                            <span class="category-badge">${item.category}</span>
                            ${item.date ? `<span>📅 ${item.date}</span>` : ''}
                        </div>
                        ${item.description ? `<p class="item-description">${item.description}</p>` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        function initializeMap() {
            map = L.map('map').setView([36.2021, 36.1605], 12); // Antakya coordinates
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            updateMap();
        }
        
        function updateMap() {
            // Clear existing markers
            markers.forEach(marker => map.removeLayer(marker));
            markers = [];
            
            // Add markers for items with coordinates
            filteredData.forEach(item => {
                if (item.latitude && item.longitude) {
                    const marker = L.marker([item.latitude, item.longitude])
                        .bindPopup(`
                            <div style="max-width: 200px;">
                                <img src="${item.thumbnail_url}" style="width: 100%; height: 100px; object-fit: cover; margin-bottom: 10px;">
                                <strong>${item.title}</strong>
                                <br><em>${item.category}</em>
                            </div>
                        `)
                        .on('click', () => showModal(item.id));
                    
                    markers.push(marker);
                    marker.addTo(map);
                }
            });
            
            // Fit map to markers if any exist
            if (markers.length > 0) {
                const group = L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
            }
        }
        
        function toggleView(view) {
            currentView = view;
            
            if (view === 'gallery') {
                document.getElementById('gallery-view').style.display = 'grid';
                document.getElementById('map-view').style.display = 'none';
                document.getElementById('no-results').style.display = filteredData.length === 0 ? 'block' : 'none';
            } else {
                document.getElementById('gallery-view').style.display = 'none';
                document.getElementById('map-view').style.display = 'block';
                document.getElementById('no-results').style.display = 'none';
                document.getElementById('map').style.display = 'block';
                
                // Refresh map
                setTimeout(() => {
                    map.invalidateSize();
                    updateMap();
                }, 100);
            }
        }
        
        function showModal(itemId) {
            const item = galleryData.find(i => i.id === itemId);
            if (!item) return;
            
            document.getElementById('modal-title').textContent = item.title;
            document.getElementById('modal-image').src = item.image_url;
            
            const details = `
                <p><strong>Category:</strong> ${item.category}</p>
                ${item.archive ? `<p><strong>Archive:</strong> ${item.archive}</p>` : ''}
                ${item.date ? `<p><strong>Date:</strong> ${item.date}</p>` : ''}
                ${item.location ? `<p><strong>Location:</strong> ${item.location}</p>` : ''}
                ${item.description ? `<p><strong>Description:</strong> ${item.description}</p>` : ''}
                ${item.keywords.length ? `<p><strong>Keywords:</strong> ${item.keywords.join(', ')}</p>` : ''}
                ${item.source_url ? `<p><a href="${item.source_url}" target="_blank">View original source →</a></p>` : ''}
            `;
            
            document.getElementById('modal-details').innerHTML = details;
            document.getElementById('modal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
        
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    </script>
</body>
</html>
        """)
        
        # Get unique categories and archives
        categories = sorted(set(item['category'] for item in gallery_items if item['category']))
        archives = sorted(set(item['archive'] for item in gallery_items if item['archive']))
        
        return html_template.render(
            gallery_data=gallery_items,
            total_items=len(gallery_items),
            categories=categories,
            archives=archives
        )
    
    def create_placeholder_image(self):
        """Create a placeholder image for missing thumbnails"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create placeholder
        img = Image.new('RGB', (300, 200), color='#e0e0e0')
        draw = ImageDraw.Draw(img)
        
        # Add text
        text = "No Image"
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        except:
            font = ImageFont.load_default()
        
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((300 - text_width) // 2, (200 - text_height) // 2)
        
        draw.text(position, text, fill='#999', font=font)
        
        # Save
        placeholder_path = self.assets_dir / "placeholder.jpg"
        img.save(placeholder_path, quality=85)
        
        return placeholder_path
    
    def copy_sample_images(self, df: pd.DataFrame, limit: int = 100):
        """Copy sample images to gallery directory"""
        # Find downloaded images
        image_dir = self.data_dir / "downloaded_images"
        if not image_dir.exists():
            return
        
        copied = 0
        for category_dir in image_dir.iterdir():
            if category_dir.is_dir():
                for image_file in category_dir.glob("*.jpg"):
                    if copied >= limit:
                        break
                    
                    # Copy to gallery
                    dest = self.images_dir / f"{category_dir.name}_{image_file.name}"
                    shutil.copy2(image_file, dest)
                    copied += 1
    
    def generate(self):
        """Generate the complete public gallery"""
        print("Generating public web gallery...")
        
        # Load data
        try:
            df = self.load_collection_data()
            print(f"Loaded {len(df)} records from collection")
        except FileNotFoundError:
            print("No collection data found. Please run data collection first.")
            return
        
        # Prepare gallery data
        gallery_items = self.prepare_gallery_data(df)
        print(f"Prepared {len(gallery_items)} items for gallery")
        
        # Generate HTML
        html_content = self.generate_html(gallery_items)
        
        # Save HTML
        index_path = self.output_dir / "index.html"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Create placeholder image
        self.create_placeholder_image()
        
        # Copy sample images
        self.copy_sample_images(df)
        
        # Save gallery data as JSON for dynamic loading
        data_path = self.data_output_dir / "gallery_data.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(gallery_items, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Gallery generated successfully!")
        print(f"  Location: {index_path}")
        print(f"  Total items: {len(gallery_items)}")
        print(f"\nTo view the gallery, open: {index_path.absolute()}")
        
        return index_path


# Simple HTTP server for testing
def serve_gallery(port: int = 8080):
    """Serve the gallery with a simple HTTP server"""
    import http.server
    import socketserver
    import os
    
    os.chdir('public_gallery')
    
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"\nServing gallery at: http://localhost:{port}")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate public web gallery")
    parser.add_argument('--serve', action='store_true', help='Serve gallery after generation')
    parser.add_argument('--port', type=int, default=8080, help='Port for serving')
    parser.add_argument('--output', default='public_gallery', help='Output directory')
    
    args = parser.parse_args()
    
    # Generate gallery
    generator = PublicGalleryGenerator(output_dir=args.output)
    generator.generate()
    
    # Serve if requested
    if args.serve:
        serve_gallery(args.port)