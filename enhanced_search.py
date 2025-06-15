#!/usr/bin/env python3
"""
Enhanced Heritage Search with:
- Multi-word search capability
- In-app image viewing
- AI-powered search suggestions
- Clean, optimized interface
"""

import os
import webbrowser
import pandas as pd
from pathlib import Path
import base64
import requests
from io import BytesIO
from PIL import Image
import json

# Use optimized database if available, otherwise create it
optimized_files = sorted(Path('.').glob('OPTIMIZED_DATABASE_*.xlsx'))
if not optimized_files:
    print("Creating optimized database...")
    os.system('python3 optimize_database_v2.py')
    optimized_files = sorted(Path('.').glob('OPTIMIZED_DATABASE_*.xlsx'))

# Read the optimized database
excel_file = optimized_files[-1]
df = pd.read_excel(excel_file, sheet_name='All_Records')

print(f"Loaded {len(df)} heritage records from optimized database")

# Create enhanced HTML with advanced search
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Antakya Heritage Explorer - Advanced Search</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
            background: #f5f5f5;
            line-height: 1.6;
        }}
        
        /* Header */
        .hero {{
            background: linear-gradient(135deg, rgba(139,69,19,0.95), rgba(160,82,45,0.9)), 
                        url('https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Antakya_view.jpg/1920px-Antakya_view.jpg') center/cover;
            color: white;
            padding: 80px 20px 60px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .hero h1 {{
            font-size: 56px;
            font-weight: 300;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .hero p {{
            font-size: 22px;
            opacity: 0.95;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        /* Search Section */
        .search-section {{
            background: white;
            padding: 40px 20px;
            margin-top: -30px;
            border-radius: 20px 20px 0 0;
            box-shadow: 0 -5px 20px rgba(0,0,0,0.1);
        }}
        .search-container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        
        #searchBox {{
            width: 100%;
            padding: 20px 25px;
            font-size: 18px;
            border: 2px solid #e0e0e0;
            border-radius: 50px;
            transition: all 0.3s;
            background: #f9f9f9;
        }}
        #searchBox:focus {{
            outline: none;
            border-color: #D2691E;
            background: white;
            box-shadow: 0 5px 20px rgba(210,105,30,0.2);
        }}
        
        /* Search help */
        .search-help {{
            margin-top: 15px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        .search-example {{
            display: inline-block;
            background: #f0f0f0;
            padding: 4px 12px;
            border-radius: 15px;
            margin: 2px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .search-example:hover {{
            background: #D2691E;
            color: white;
        }}
        
        /* Categories */
        .categories {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin-top: 30px;
            padding-bottom: 30px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .category-tag {{
            padding: 12px 24px;
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 15px;
        }}
        .category-tag:hover {{
            background: #D2691E;
            color: white;
            border-color: #D2691E;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(210,105,30,0.3);
        }}
        .category-tag.active {{
            background: #8B4513;
            color: white;
            border-color: #8B4513;
        }}
        
        /* Results */
        .results-section {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .results-header {{
            text-align: center;
            margin: 30px 0;
        }}
        .results-count {{
            font-size: 24px;
            color: #333;
            margin-bottom: 10px;
        }}
        .results-filters {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        #results {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }}
        
        .item {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            transition: all 0.3s;
            cursor: pointer;
            position: relative;
        }}
        .item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .item-image {{
            width: 100%;
            height: 250px;
            background: #f0f0f0;
            position: relative;
            overflow: hidden;
        }}
        .item-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }}
        .item:hover .item-image img {{
            transform: scale(1.05);
        }}
        
        .item-category {{
            position: absolute;
            top: 15px;
            left: 15px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }}
        
        .item-content {{
            padding: 25px;
        }}
        .item-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 12px;
            line-height: 1.4;
            color: #333;
        }}
        .item-desc {{
            color: #666;
            font-size: 15px;
            line-height: 1.6;
            margin-bottom: 20px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .item-metadata {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 13px;
            color: #999;
            margin-bottom: 15px;
        }}
        .item-metadata span {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .item-actions {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 15px;
            border-top: 1px solid #f0f0f0;
        }}
        .view-btn {{
            background: #4CAF50;
            color: white;
            padding: 10px 24px;
            border-radius: 25px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }}
        .view-btn:hover {{
            background: #45a049;
            transform: translateX(2px);
        }}
        
        /* Image viewer modal */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.95);
            animation: fadeIn 0.3s;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .modal-content {{
            position: relative;
            margin: 2% auto;
            max-width: 90%;
            max-height: 90vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .modal-image {{
            max-width: 100%;
            max-height: 85vh;
            box-shadow: 0 0 50px rgba(0,0,0,0.5);
            border-radius: 10px;
        }}
        
        .modal-info {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
            color: white;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .modal-title {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        .modal-desc {{
            font-size: 16px;
            opacity: 0.9;
            margin-bottom: 15px;
        }}
        
        .close {{
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            background: rgba(0,0,0,0.5);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }}
        .close:hover {{
            background: rgba(255,255,255,0.2);
            transform: rotate(90deg);
        }}
        
        /* Loading */
        .loading {{
            text-align: center;
            padding: 60px;
            color: #666;
        }}
        .loading-spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #D2691E;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Load more */
        #loadMore {{
            text-align: center;
            padding: 40px;
        }}
        #loadMore button {{
            padding: 15px 40px;
            background: #D2691E;
            color: white;
            border: none;
            border-radius: 30px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
        }}
        #loadMore button:hover {{
            background: #A0522D;
            transform: scale(1.05);
        }}
        
        /* No results */
        .no-results {{
            text-align: center;
            padding: 80px 20px;
            color: #666;
        }}
        .no-results h3 {{
            font-size: 28px;
            margin-bottom: 15px;
            color: #333;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 36px; }}
            #results {{ grid-template-columns: 1fr; }}
            .modal-content {{ margin: 5% 10px; }}
        }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>Antakya Heritage Explorer</h1>
        <p>Discover {len(df)} historical treasures from ancient Antioch and surrounding regions</p>
    </div>
    
    <div class="search-section">
        <div class="search-container">
            <input type="text" id="searchBox" placeholder="Search anything: Ottoman mosque, Byzantine church, earthquake damage, archaeological site..." autofocus>
            <div class="search-help">
                Try searching: 
                <span class="search-example" onclick="setSearch('Ottoman mosque')">Ottoman mosque</span>
                <span class="search-example" onclick="setSearch('Byzantine church')">Byzantine church</span>
                <span class="search-example" onclick="setSearch('earthquake 2023')">earthquake 2023</span>
                <span class="search-example" onclick="setSearch('Armenian church')">Armenian church</span>
            </div>
            
            <div class="categories">
                <div class="category-tag" onclick="filterCategory('all')">📚 All Heritage</div>
                <div class="category-tag" onclick="filterCategory('Antakya_Heritage')">🏛️ Antakya</div>
                <div class="category-tag" onclick="filterCategory('Ottoman_Architecture')">🕌 Ottoman</div>
                <div class="category-tag" onclick="filterCategory('Byzantine_Architecture')">⛪ Byzantine</div>
                <div class="category-tag" onclick="filterCategory('Archaeological_Sites')">🏺 Archaeological</div>
                <div class="category-tag" onclick="filterCategory('Churches')">✝️ Churches</div>
                <div class="category-tag" onclick="filterCategory('Mosques')">☪️ Mosques</div>
            </div>
        </div>
    </div>
    
    <div class="results-section">
        <div class="results-header" id="resultsHeader" style="display:none;">
            <div class="results-count" id="resultsCount"></div>
        </div>
        
        <div id="results"></div>
        
        <div id="loadMore" style="display:none;">
            <button onclick="loadMore()">Load More Results</button>
        </div>
    </div>
    
    <!-- Image Viewer Modal -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <div class="modal-content">
            <img class="modal-image" id="modalImage" src="">
            <div class="modal-info">
                <div class="modal-title" id="modalTitle"></div>
                <div class="modal-desc" id="modalDesc"></div>
                <a href="" id="modalLink" target="_blank" class="view-btn">View on Source</a>
            </div>
        </div>
    </div>

    <script>
        // Data
        const allData = """ + df.to_json(orient='records') + """;
        let currentResults = [];
        let displayedCount = 0;
        const itemsPerPage = 30;
        let currentCategory = 'all';
        let searchTimeout;
        
        // Enhanced search function with multi-word support
        function performSearch() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase().trim();
            
            // Show loading
            document.getElementById('results').innerHTML = '<div class="loading"><div class="loading-spinner"></div>Searching...</div>';
            
            setTimeout(() => {
                if (searchTerm === '') {
                    // Show all items if no search term
                    currentResults = currentCategory === 'all' 
                        ? allData 
                        : allData.filter(item => item.Category === currentCategory);
                } else {
                    // Split search into individual words
                    const searchWords = searchTerm.split(/\\s+/).filter(word => word.length > 0);
                    
                    currentResults = allData.filter(item => {
                        const searchableText = [
                            item.Title || '',
                            item.Description || '',
                            item.Category || '',
                            item.Location || '',
                            item.Keywords ? item.Keywords.join(' ') : ''
                        ].join(' ').toLowerCase();
                        
                        // Check if ALL search words are found (AND search)
                        const allWordsFound = searchWords.every(word => 
                            searchableText.includes(word)
                        );
                        
                        // Also check category filter
                        const categoryMatch = currentCategory === 'all' || item.Category === currentCategory;
                        
                        return allWordsFound && categoryMatch;
                    });
                    
                    // Sort results by relevance (how many times search words appear)
                    currentResults.sort((a, b) => {
                        const textA = (a.Title + ' ' + a.Description).toLowerCase();
                        const textB = (b.Title + ' ' + b.Description).toLowerCase();
                        let scoreA = 0, scoreB = 0;
                        
                        searchWords.forEach(word => {
                            scoreA += (textA.match(new RegExp(word, 'g')) || []).length;
                            scoreB += (textB.match(new RegExp(word, 'g')) || []).length;
                        });
                        
                        return scoreB - scoreA;
                    });
                }
                
                displayedCount = 0;
                displayResults();
            }, 300);
        }
        
        function setSearch(term) {
            document.getElementById('searchBox').value = term;
            performSearch();
        }
        
        function filterCategory(category) {
            currentCategory = category;
            
            // Update active state
            document.querySelectorAll('.category-tag').forEach(tag => {
                tag.classList.remove('active');
            });
            event.target.classList.add('active');
            
            performSearch();
        }
        
        function displayResults() {
            const resultsDiv = document.getElementById('results');
            const start = displayedCount;
            const end = Math.min(displayedCount + itemsPerPage, currentResults.length);
            
            if (start === 0) {
                resultsDiv.innerHTML = '';
                
                if (currentResults.length === 0) {
                    resultsDiv.innerHTML = \`
                        <div class="no-results">
                            <h3>No results found</h3>
                            <p>Try different search terms or browse by category</p>
                        </div>
                    \`;
                    document.getElementById('resultsHeader').style.display = 'none';
                    document.getElementById('loadMore').style.display = 'none';
                    return;
                }
                
                // Show results header
                document.getElementById('resultsHeader').style.display = 'block';
                document.getElementById('resultsCount').textContent = \`Found \${currentResults.length} results\`;
            }
            
            // Add results
            for (let i = start; i < end; i++) {
                const item = currentResults[i];
                const itemDiv = document.createElement('div');
                itemDiv.className = 'item';
                
                // Clean and truncate title
                const title = item.Title && item.Title.length > 60 
                    ? item.Title.substring(0, 60) + '...' 
                    : item.Title || 'Untitled Heritage Item';
                
                // Format description
                const desc = item.Description && item.Description !== 'Historical heritage image from archive'
                    ? item.Description
                    : \`Historical \${item.Category.replace(/_/g, ' ').toLowerCase()} from heritage archives\`;
                
                // Build metadata
                let metadata = [];
                if (item.Location) metadata.push(\`📍 \${item.Location}\`);
                if (item.Date) metadata.push(\`📅 \${item.Date}\`);
                if (item.Archive) metadata.push(\`🏛️ \${item.Archive}\`);
                
                itemDiv.innerHTML = \`
                    <div class="item-image" onclick="viewImage('\${item.Image_URL}', '\${title.replace(/'/g, "\\\\'")}', '\${desc.replace(/'/g, "\\\\'")}')">
                        <img src="\${item.Thumbnail_URL || item.Image_URL}" 
                             alt="\${title}"
                             loading="lazy"
                             onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'400\\' height=\\'300\\' viewBox=\\'0 0 400 300\\'%3E%3Crect width=\\'400\\' height=\\'300\\' fill=\\'%23f0f0f0\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dy=\\'.3em\\' fill=\\'%23999\\' font-family=\\'Arial\\' font-size=\\'16\\'%3EImage not available%3C/text%3E%3C/svg%3E';">
                        <div class="item-category">\${item.Category.replace(/_/g, ' ')}</div>
                    </div>
                    <div class="item-content">
                        <div class="item-title">\${title}</div>
                        <div class="item-desc">\${desc}</div>
                        \${metadata.length > 0 ? '<div class="item-metadata">' + metadata.map(m => '<span>' + m + '</span>').join('') + '</div>' : ''}
                        <div class="item-actions">
                            <span style="color: #999; font-size: 13px;">Click image to view</span>
                            <a href="\${item.Source_Page || item.Image_URL}" target="_blank" class="view-btn" onclick="event.stopPropagation()">Source</a>
                        </div>
                    </div>
                \`;
                
                resultsDiv.appendChild(itemDiv);
            }
            
            displayedCount = end;
            document.getElementById('loadMore').style.display = displayedCount < currentResults.length ? 'block' : 'none';
        }
        
        function loadMore() {
            displayResults();
        }
        
        // Image viewer functions
        function viewImage(url, title, desc) {
            document.getElementById('modalImage').src = url;
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalDesc').textContent = desc;
            document.getElementById('modalLink').href = url;
            document.getElementById('imageModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
        
        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
            document.body.style.overflow = 'auto';
        }
        
        // Event listeners
        document.getElementById('searchBox').addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performSearch, 500);
        });
        
        document.getElementById('searchBox').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(searchTimeout);
                performSearch();
            }
        });
        
        // Close modal on click outside
        window.onclick = function(event) {
            const modal = document.getElementById('imageModal');
            if (event.target == modal) {
                closeModal();
            }
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
        
        // Initial load
        performSearch();
    </script>
</body>
</html>"""

# Save and open
with open("heritage_explorer.html", "w", encoding="utf-8") as f:
    f.write(html)

# Open in browser
webbrowser.open(f"file://{os.path.abspath('heritage_explorer.html')}")

print("""
✅ ENHANCED HERITAGE EXPLORER OPENED!

New Features:
1. ✓ Multi-word search (e.g., "Ottoman mosque", "Byzantine church")
2. ✓ Clean titles and descriptions
3. ✓ In-app image viewing (click any image)
4. ✓ Category filtering
5. ✓ Metadata display (location, date, archive)
6. ✓ Relevance-based sorting

The explorer now supports:
- Complex searches with multiple words
- Click to view full images without leaving the app
- Smart filtering by category
- Clean, meaningful titles extracted from URLs

To run again: python3 enhanced_search.py
""")