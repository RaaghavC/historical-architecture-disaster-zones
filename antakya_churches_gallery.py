#!/usr/bin/env python3
"""
Create a visual gallery of Antakya churches.
"""
import pandas as pd
from pathlib import Path

print("Creating Antakya Churches Gallery...\n")

# Read the church list
church_list = pd.read_csv("antakya_churches/antakya_churches_list.csv")
print(f"Found {len(church_list)} churches")

# Create HTML gallery
html = """<!DOCTYPE html>
<html>
<head>
    <title>Antakya Churches Collection</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #f5f5f5; 
        }
        h1 { 
            color: #8B0000; 
            text-align: center; 
            border-bottom: 3px solid #8B0000;
            padding-bottom: 20px;
        }
        .intro {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .gallery { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 20px; 
        }
        .church-card { 
            background: white; 
            padding: 15px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .church-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .church-card h3 { 
            font-size: 16px; 
            margin: 10px 0; 
            color: #333;
        }
        .church-card p { 
            font-size: 14px; 
            color: #666; 
            margin: 5px 0;
        }
        .image-container {
            width: 100%;
            height: 250px;
            background: #eee;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            border-radius: 4px;
        }
        .church-img { 
            max-width: 100%; 
            max-height: 100%; 
            object-fit: contain;
        }
        .metadata { 
            font-size: 12px; 
            color: #999; 
            border-top: 1px solid #eee;
            padding-top: 10px;
            margin-top: 10px;
        }
        .download-link {
            display: inline-block;
            margin-top: 10px;
            padding: 5px 10px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 12px;
        }
        .download-link:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <h1>Churches of Antakya (Antioch)</h1>
    
    <div class="intro">
        <h2>Historical Churches in Antakya Region</h2>
        <p>This collection contains """ + str(len(church_list)) + """ churches from the Antakya (ancient Antioch) region, 
        including Armenian, Orthodox, and Catholic churches. These represent the diverse Christian heritage
        of this historically significant city.</p>
        <p><strong>Churches included:</strong></p>
        <ul>
            <li>Armenian churches in villages (Batiayaz, Yogunoluk)</li>
            <li>Rum Orthodox Church in Arsuz</li>
            <li>Catholic Church of Antakya</li>
            <li>New Apostolic Church</li>
            <li>Historical church sites and ruins</li>
        </ul>
    </div>
    
    <div class="gallery">
"""

# Add each church
for idx, row in church_list.iterrows():
    # Extract filename from URL
    filename = row['Image_URL'].split('/')[-1]
    
    # Check if local file exists
    local_files = list(Path("antakya_churches").glob(f"*{idx}*.jpg"))
    if local_files:
        local_path = local_files[0].name
    else:
        local_path = None
    
    html += f"""
        <div class="church-card">
            <div class="image-container">
                <img src="{row['Image_URL']}" alt="{row['Title']}" class="church-img" 
                     onerror="this.src='https://via.placeholder.com/300x250?text=Image+Not+Available'">
            </div>
            <h3>{idx+1}. {row['Title']}</h3>
            <div class="metadata">
                <p><strong>Category:</strong> {row['Category']}</p>
                <p><strong>Source:</strong> {row.get('Archive', 'Wikimedia Commons')}</p>
                <p><strong>Filename:</strong> {filename}</p>
            </div>
            <a href="{row['Image_URL']}" target="_blank" class="download-link">View Full Size</a>
        </div>
    """

html += """
    </div>
    
    <div class="intro" style="margin-top: 30px;">
        <h3>About This Collection</h3>
        <p>These churches represent the rich Christian heritage of Antakya (ancient Antioch), 
        one of the most important cities in early Christianity. St. Peter is believed to have 
        established one of the first Christian communities here, and the city served as a major 
        center of Christianity for centuries.</p>
        <p>Many of these buildings were damaged or destroyed in the February 2023 earthquakes, 
        making this digital preservation effort crucial for documenting this heritage.</p>
    </div>
</body>
</html>
"""

# Save the gallery
gallery_file = "antakya_churches_gallery.html"
with open(gallery_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ Created gallery: {gallery_file}")
print("\nYou can now open this file in your browser to see all the churches!")

# Also create a simple text summary
summary = """ANTAKYA CHURCHES SUMMARY
========================

Total Churches Found: """ + str(len(church_list)) + """

Types of Churches:
1. Armenian Churches (5 churches)
   - Armenian church in Batiayaz village (2 views)
   - Armenian church in Yogunoluk village (3 views)

2. Orthodox Churches (1 church)
   - Rum Orthodox Church in Arsuz

3. Catholic Churches (2 churches)
   - Antakya Catholic Church
   - Roman Catholic church garden

4. Other Churches (6 churches)
   - New Apostolic Church (2 views)
   - St. Peter's Church (historical wall view from 1754)
   - Various unidentified historical churches
   - Antiochian Greek Christians
   - Antiochian Orthodox Christians

Historical Significance:
- Antakya (ancient Antioch) was one of the earliest centers of Christianity
- St. Peter established one of the first Christian communities here
- The city name "Christians" was first used in Antioch
- These churches represent centuries of diverse Christian traditions

Conservation Status:
- Many churches were damaged in the February 2023 earthquakes
- This digital collection helps preserve their memory
- Documentation is crucial for future restoration efforts
"""

with open("antakya_churches_summary.txt", 'w') as f:
    f.write(summary)

print(f"✅ Created summary: antakya_churches_summary.txt")