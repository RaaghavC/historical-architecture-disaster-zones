#!/usr/bin/env python3
"""
EASY HERITAGE SEARCH - One command to search and view everything!
Just run: python3 easy_heritage_search.py
"""

import pandas as pd
from pathlib import Path
import webbrowser
import os
from datetime import datetime

print("""
╔══════════════════════════════════════════════════╗
║     ANTAKYA HERITAGE DATABASE - EASY SEARCH      ║
╚══════════════════════════════════════════════════╝
""")

# Auto-fix the database if needed
if not list(Path('.').glob('USABLE_DATABASE_*.xlsx')):
    print("First time setup - preparing database...")
    os.system('python3 fix_database.py')

# Read the database
excel_file = sorted(Path('.').glob('USABLE_DATABASE_*.xlsx'))[-1]
df = pd.read_excel(excel_file, sheet_name='All_Records')

# Create the search interface
def create_search_page(search_term=""):
    """Create an interactive HTML search page."""
    
    # Filter results if search term provided
    if search_term:
        mask = (
            df['Title'].str.contains(search_term, case=False, na=False) | 
            df['Description'].str.contains(search_term, case=False, na=False)
        )
        results = df[mask]
    else:
        results = df
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Antakya Heritage Search</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, Arial, sans-serif; 
            margin: 0; 
            padding: 0;
            background: #f0f2f5;
        }}
        .header {{
            background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
            color: white;
            padding: 30px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 36px;
            font-weight: 300;
        }}
        .stats {{
            margin-top: 15px;
            font-size: 18px;
            opacity: 0.9;
        }}
        .search-container {{
            background: white;
            padding: 30px;
            margin: 20px auto;
            max-width: 800px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .search-box {{
            width: 100%;
            padding: 15px 20px;
            font-size: 18px;
            border: 2px solid #ddd;
            border-radius: 50px;
            outline: none;
            transition: all 0.3s;
        }}
        .search-box:focus {{
            border-color: #D2691E;
            box-shadow: 0 0 0 3px rgba(210, 105, 30, 0.1);
        }}
        .search-btn {{
            margin-top: 15px;
            padding: 12px 40px;
            font-size: 16px;
            background: #D2691E;
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .search-btn:hover {{
            background: #A0522D;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .quick-searches {{
            margin-top: 20px;
            text-align: center;
        }}
        .quick-btn {{
            display: inline-block;
            margin: 5px;
            padding: 8px 20px;
            background: #f0f2f5;
            color: #333;
            text-decoration: none;
            border-radius: 20px;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .quick-btn:hover {{
            background: #D2691E;
            color: white;
            transform: scale(1.05);
        }}
        .results {{
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 20px;
        }}
        .result-info {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: all 0.3s;
            cursor: pointer;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}
        .card-image {{
            width: 100%;
            height: 200px;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}
        .card-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .card-content {{
            padding: 15px;
        }}
        .card-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            line-height: 1.3;
        }}
        .card-desc {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
            line-height: 1.4;
            max-height: 40px;
            overflow: hidden;
        }}
        .card-meta {{
            font-size: 12px;
            color: #999;
            border-top: 1px solid #f0f0f0;
            padding-top: 10px;
        }}
        .category-badge {{
            display: inline-block;
            padding: 4px 12px;
            background: #f0f2f5;
            border-radius: 20px;
            font-size: 12px;
            margin-bottom: 10px;
        }}
        .download-btn {{
            display: inline-block;
            margin-top: 8px;
            padding: 6px 15px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-size: 12px;
            transition: all 0.2s;
        }}
        .download-btn:hover {{
            background: #45a049;
            transform: scale(1.05);
        }}
        .no-results {{
            text-align: center;
            padding: 60px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Antakya Heritage Database</h1>
        <div class="stats">
            {len(df)} Total Records • {len(df[df['Category'] == 'Antakya_Heritage'])} Antakya Specific • 7 Categories
        </div>
    </div>
    
    <div class="search-container">
        <form method="get" action="">
            <input type="text" class="search-box" name="q" 
                   placeholder="Search for churches, mosques, Byzantine, Ottoman, earthquake..." 
                   value="{search_term}" autofocus>
            <br>
            <center>
                <button type="submit" class="search-btn">🔍 Search Heritage</button>
            </center>
        </form>
        
        <div class="quick-searches">
            <p style="color: #666; margin-bottom: 10px;">Quick searches:</p>
            <a href="?q=church" class="quick-btn">⛪ Churches</a>
            <a href="?q=mosque" class="quick-btn">🕌 Mosques</a>
            <a href="?q=byzantine" class="quick-btn">🏛️ Byzantine</a>
            <a href="?q=ottoman" class="quick-btn">🏰 Ottoman</a>
            <a href="?q=earthquake" class="quick-btn">🆘 Earthquake</a>
            <a href="?q=habib+neccar" class="quick-btn">📿 Habib-i Neccar</a>
            <a href="?q=archaeological" class="quick-btn">🏺 Archaeological</a>
            <a href="?q=" class="quick-btn">📋 Show All</a>
        </div>
    </div>
    
    <div class="results">
"""
    
    if search_term:
        html += f"""
        <div class="result-info">
            <h2>Search Results for "{search_term}"</h2>
            <p>Found {len(results)} items</p>
        </div>
        """
    
    if len(results) > 0:
        # Group by category
        for category in results['Category'].unique():
            cat_results = results[results['Category'] == category]
            
            html += f"""
            <h2 style="color: #8B4513; margin: 30px 0 20px 0;">
                {category.replace('_', ' ')} ({len(cat_results)} items)
            </h2>
            <div class="gallery">
            """
            
            for idx, row in cat_results.head(50).iterrows():  # Show up to 50 per category
                title = row['Title'][:80] + '...' if len(row['Title']) > 80 else row['Title']
                desc = row['Description'][:120] + '...' if len(row['Description']) > 120 else row['Description']
                
                html += f"""
                <div class="card" onclick="window.open('{row['Image_URL']}', '_blank')">
                    <div class="card-image">
                        <img src="{row.get('Thumbnail_URL', row['Image_URL'])}" 
                             onerror="this.style.display='none'; this.parentElement.innerHTML='<div style=\\"padding:20px;color:#999;\\">🖼️<br>Click to view image</div>'"
                             alt="{title}">
                    </div>
                    <div class="card-content">
                        <div class="category-badge">{category.replace('_', ' ')}</div>
                        <div class="card-title">{title}</div>
                        <div class="card-desc">{desc}</div>
                        <div class="card-meta">
                            Source: {row.get('Archive', 'Unknown')}
                            <br>
                            <a href="{row['Image_URL']}" target="_blank" class="download-btn" 
                               onclick="event.stopPropagation()">View Full Size</a>
                        </div>
                    </div>
                </div>
                """
            
            html += "</div>"
    else:
        html += """
        <div class="no-results">
            <h2>😔 No results found</h2>
            <p>Try searching for: church, mosque, Byzantine, Ottoman, or earthquake</p>
        </div>
        """
    
    html += """
    </div>
</body>
</html>
"""
    
    return html

# Main search interface
print("Choose an option:")
print("1. Open visual search in browser (recommended)")
print("2. Quick text search")
print("3. Download specific category")
print("4. Show statistics")

choice = input("\nEnter choice (1-4) or press Enter for option 1: ").strip() or "1"

if choice == "1":
    # Create and open the search page
    html_content = create_search_page()
    
    # Create a simple web server
    with open("heritage_search.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Open in browser
    webbrowser.open(f"file://{os.path.abspath('heritage_search.html')}")
    
    print("\n✅ Search page opened in your browser!")
    print("\nYou can:")
    print("- Type anything in the search box")
    print("- Click the quick search buttons")
    print("- Click any image to view full size")
    print("- The page updates automatically with results")

elif choice == "2":
    # Quick text search
    search = input("\nWhat are you looking for? ").strip()
    
    if search:
        mask = (
            df['Title'].str.contains(search, case=False, na=False) | 
            df['Description'].str.contains(search, case=False, na=False)
        )
        results = df[mask]
        
        print(f"\nFound {len(results)} results for '{search}':\n")
        
        for idx, row in results.head(20).iterrows():
            print(f"{idx+1}. {row['Title'][:60]}...")
            print(f"   Category: {row['Category']}")
            print(f"   URL: {row['Image_URL']}\n")

elif choice == "3":
    # Download category
    print("\nAvailable categories:")
    for i, cat in enumerate(df['Category'].unique(), 1):
        count = len(df[df['Category'] == cat])
        print(f"{i}. {cat} ({count} items)")
    
    cat_choice = input("\nEnter category number: ").strip()
    
    try:
        category = list(df['Category'].unique())[int(cat_choice)-1]
        cat_df = df[df['Category'] == category]
        
        # Save to Excel
        filename = f"{category}_collection.xlsx"
        cat_df.to_excel(filename, index=False)
        print(f"\n✅ Saved {len(cat_df)} items to {filename}")
        
    except:
        print("Invalid choice")

elif choice == "4":
    # Show statistics
    print("\n📊 DATABASE STATISTICS")
    print("=" * 40)
    print(f"Total Records: {len(df)}")
    print(f"\nBy Category:")
    for cat, count in df['Category'].value_counts().items():
        print(f"  - {cat}: {count} items")
    
    print(f"\nAntakya Specific:")
    antakya_df = df[df['Category'] == 'Antakya_Heritage']
    print(f"  - Total: {len(antakya_df)} items")
    print(f"  - Churches: {len(antakya_df[antakya_df['Title'].str.contains('church|Church', na=False)])} items")
    print(f"  - Mosques: {len(antakya_df[antakya_df['Title'].str.contains('mosque|Mosque', na=False)])} items")

print("\n✨ To run again, just type: python3 easy_heritage_search.py")