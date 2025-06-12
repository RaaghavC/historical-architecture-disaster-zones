#!/usr/bin/env python3
"""
SUPER SIMPLE HERITAGE SEARCH
Just run: python3 search.py
"""

import os
import webbrowser
import pandas as pd
from pathlib import Path

# Auto-setup if needed
if not list(Path('.').glob('USABLE_DATABASE_*.xlsx')):
    print("Setting up database (one-time only)...")
    os.system('python3 fix_database.py 2>/dev/null')

# Read database
excel_file = sorted(Path('.').glob('USABLE_DATABASE_*.xlsx'))[-1]
df = pd.read_excel(excel_file, sheet_name='All_Records')

# Create beautiful search page
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Antakya Heritage - Simple Search</title>
    <meta charset="utf-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, Arial, sans-serif; 
            background: #f5f5f5;
        }}
        
        /* Header */
        .hero {{
            background: linear-gradient(rgba(139,69,19,0.9), rgba(139,69,19,0.9)), 
                        url('https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Antakya_view.jpg/1200px-Antakya_view.jpg') center/cover;
            color: white;
            padding: 60px 20px;
            text-align: center;
        }}
        .hero h1 {{
            font-size: 48px;
            font-weight: 300;
            margin-bottom: 20px;
        }}
        
        /* Search */
        .search-wrapper {{
            max-width: 600px;
            margin: -30px auto 40px;
            padding: 0 20px;
        }}
        #searchBox {{
            width: 100%;
            padding: 20px;
            font-size: 18px;
            border: none;
            border-radius: 50px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        
        /* Quick buttons */
        .quick-search {{
            text-align: center;
            margin: 30px 0;
        }}
        .tag {{
            display: inline-block;
            margin: 5px;
            padding: 10px 20px;
            background: white;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .tag:hover {{
            background: #D2691E;
            color: white;
            transform: scale(1.1);
        }}
        
        /* Results */
        #results {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
        }}
        
        .item {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: all 0.3s;
            cursor: pointer;
        }}
        .item:hover {{
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }}
        
        .item-image {{
            width: 100%;
            height: 220px;
            background: #eee;
            position: relative;
            overflow: hidden;
        }}
        .item-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .item-category {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
        }}
        
        .item-content {{
            padding: 20px;
        }}
        .item-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
            line-height: 1.3;
        }}
        .item-desc {{
            color: #666;
            font-size: 14px;
            line-height: 1.5;
            margin-bottom: 15px;
            max-height: 60px;
            overflow: hidden;
        }}
        
        .item-actions {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .item-source {{
            font-size: 12px;
            color: #999;
        }}
        .view-btn {{
            background: #4CAF50;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 14px;
        }}
        .view-btn:hover {{
            background: #45a049;
        }}
        
        /* Loading */
        #loading {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        
        /* Stats */
        .stats {{
            text-align: center;
            padding: 20px;
            background: white;
            margin: 20px auto;
            max-width: 800px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        /* No scroll loading */
        #loadMore {{
            text-align: center;
            padding: 20px;
            margin: 20px;
        }}
        #loadMore button {{
            padding: 15px 40px;
            background: #D2691E;
            color: white;
            border: none;
            border-radius: 30px;
            font-size: 16px;
            cursor: pointer;
        }}
        #loadMore button:hover {{
            background: #A0522D;
        }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>🏛️ Antakya Heritage Search</h1>
        <p style="font-size: 20px; opacity: 0.9;">{len(df)} historical records • {len(df[df['Category'] == 'Antakya_Heritage'])} from Antakya</p>
    </div>
    
    <div class="search-wrapper">
        <input type="text" id="searchBox" placeholder="Search for anything... (church, mosque, Byzantine, Ottoman, earthquake)" autofocus>
    </div>
    
    <div class="quick-search">
        <span class="tag" onclick="search('church')">⛪ Churches</span>
        <span class="tag" onclick="search('mosque')">🕌 Mosques</span>
        <span class="tag" onclick="search('habib')">📿 Habib-i Neccar</span>
        <span class="tag" onclick="search('byzantine')">🏛️ Byzantine</span>
        <span class="tag" onclick="search('ottoman')">🏰 Ottoman</span>
        <span class="tag" onclick="search('earthquake')">🆘 Earthquake 2023</span>
        <span class="tag" onclick="search('archaeological')">🏺 Archaeological</span>
        <span class="tag" onclick="search('')">📋 Show All</span>
    </div>
    
    <div id="loading" style="display:none;">
        <h3>Searching...</h3>
    </div>
    
    <div id="results"></div>
    
    <div id="loadMore" style="display:none;">
        <button onclick="loadMore()">Load More Results</button>
    </div>

    <script>
        // Data
        const allData = """ + df.to_json(orient='records') + """;
        let currentResults = [];
        let displayedCount = 0;
        const itemsPerPage = 50;
        
        // Search function
        function search(term) {
            document.getElementById('searchBox').value = term;
            performSearch();
        }
        
        function performSearch() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            displayedCount = 0;
            
            if (searchTerm === '') {
                currentResults = allData;
            } else {
                currentResults = allData.filter(item => {
                    const title = (item.Title || '').toLowerCase();
                    const desc = (item.Description || '').toLowerCase();
                    const cat = (item.Category || '').toLowerCase();
                    // Split search into words and check if ALL words are found
                    const searchWords = searchTerm.split(' ').filter(word => word.length > 0);
                    return searchWords.every(word => 
                        title.includes(word) || desc.includes(word) || cat.includes(word)
                    );
                });
            }
            
            document.getElementById('loading').style.display = 'none';
            displayResults();
        }
        
        function displayResults() {
            const resultsDiv = document.getElementById('results');
            const start = displayedCount;
            const end = Math.min(displayedCount + itemsPerPage, currentResults.length);
            
            if (start === 0 && currentResults.length === 0) {
                resultsDiv.innerHTML = '<div style="text-align:center; padding:60px; color:#666;"><h2>No results found</h2><p>Try different search terms</p></div>';
                document.getElementById('loadMore').style.display = 'none';
                return;
            }
            
            if (start === 0) {
                resultsDiv.innerHTML = '<div class="stats">Found ' + currentResults.length + ' results</div>';
            }
            
            for (let i = start; i < end; i++) {
                const item = currentResults[i];
                const itemDiv = document.createElement('div');
                itemDiv.className = 'item';
                itemDiv.onclick = () => window.open(item.Image_URL, '_blank');
                
                const title = item.Title.length > 60 ? item.Title.substring(0, 60) + '...' : item.Title;
                const desc = item.Description && item.Description !== 'No description available' 
                    ? (item.Description.length > 120 ? item.Description.substring(0, 120) + '...' : item.Description)
                    : 'Click to view full details';
                
                itemDiv.innerHTML = `
                    <div class="item-image">
                        <img src="${item.Thumbnail_URL || item.Image_URL}" 
                             onerror="this.style.display='none'; this.parentElement.style.background='#f0f0f0'; this.parentElement.innerHTML='<div style=\"padding:80px 20px; text-align:center; color:#999;\">🖼️<br>Click to view</div>' + this.parentElement.innerHTML">
                        <div class="item-category">${item.Category.replace(/_/g, ' ')}</div>
                    </div>
                    <div class="item-content">
                        <div class="item-title">${title}</div>
                        <div class="item-desc">${desc}</div>
                        <div class="item-actions">
                            <span class="item-source">${item.Archive || 'Archive'}</span>
                            <a href="${item.Image_URL}" target="_blank" class="view-btn" onclick="event.stopPropagation()">View</a>
                        </div>
                    </div>
                `;
                
                resultsDiv.appendChild(itemDiv);
            }
            
            displayedCount = end;
            document.getElementById('loadMore').style.display = displayedCount < currentResults.length ? 'block' : 'none';
        }
        
        function loadMore() {
            displayResults();
        }
        
        // Search on type
        let searchTimeout;
        document.getElementById('searchBox').addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performSearch, 300);
        });
        
        // Search on enter
        document.getElementById('searchBox').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // Show all on load
        performSearch();
    </script>
</body>
</html>"""

# Save and open
with open("heritage_search.html", "w", encoding="utf-8") as f:
    f.write(html)

# Open in browser
webbrowser.open(f"file://{os.path.abspath('heritage_search.html')}")

print("""
✅ HERITAGE SEARCH OPENED IN YOUR BROWSER!

How to use:
1. Type anything in the search box (it searches as you type)
2. Click the category buttons for quick searches
3. Click any image card to view full size
4. Click "Load More" to see more results

The page has all 782 heritage items ready to search!

To run again: python3 search.py
""")