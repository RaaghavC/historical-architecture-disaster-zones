#!/usr/bin/env python3
"""
Heritage Explorer - Simple launcher for the optimized heritage search system
Just run: python3 heritage_explorer.py
"""

import os
import sys
import webbrowser
from pathlib import Path

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          ANTAKYA HERITAGE EXPLORER - LAUNCH MENU             ║
╚══════════════════════════════════════════════════════════════╝

Welcome to the enhanced heritage exploration system!
Now with support for 5 major archives:
- ArchNet (Islamic Architecture)
- Manar al-Athar (Oxford Archaeological Photos)  
- SALT Research (Turkish/Ottoman Photography)
- Akkasah (Middle Eastern Photography)
- NIT Kiel Archive (30,000+ Ottoman Photos)

What would you like to do?

1. 🔍 Open Heritage Explorer (recommended)
   - Multi-word search support
   - In-app image viewing
   - Clean, optimized interface

2. 🌐 Search All Archives
   - Search across all 5 archives
   - Comprehensive results

3. 🏛️ Quick Antakya Search
   - Pre-configured Antakya/Antioch search
   - Earthquake damage documentation

4. 📚 View Current Database
   - Browse existing records
   - No new search

5. 🧪 Test All Archives
   - Verify all archives are working
   - See sample results

6. ❓ Help
   - Show usage instructions

Choice (1-6): """, end='')
    
    choice = input().strip()
    
    if choice == '1':
        print("\n✨ Launching Heritage Explorer...")
        os.system('python3 enhanced_search.py')
        
    elif choice == '2':
        search_terms = input("\nEnter search terms (e.g., Ottoman mosque): ").strip()
        if search_terms:
            print(f"\n🔍 Searching for '{search_terms}' across all archives...")
            os.system(f'python3 unified_heritage_system.py search {search_terms}')
        else:
            print("No search terms provided")
            
    elif choice == '3':
        print("\n🏛️ Searching for Antakya heritage...")
        os.system('python3 unified_heritage_system.py antakya')
        
    elif choice == '4':
        print("\n📚 Opening current database...")
        os.system('python3 unified_heritage_system.py view')
        
    elif choice == '5':
        print("\n🧪 Testing all archives...")
        os.system('python3 test_all_archives.py')
        
    elif choice == '6':
        print("""
USAGE GUIDE:
============

The system supports multiple ways to explore heritage data:

1. Enhanced Search Interface (heritage_explorer.py)
   - Beautiful web interface
   - Multi-word search: "Ottoman mosque", "Byzantine church"
   - Click images to view full size
   - Filter by categories
   
2. Command Line Interface (unified_heritage_system.py)
   Commands:
   - search <terms>: Search all archives
   - add <url>: Add specific archive page
   - view: View current database
   - antakya: Special Antakya search
   
3. Direct Archive URLs Supported:
   - https://archnet.org/...
   - https://manar-al-athar.ox.ac.uk/...
   - https://saltresearch.org/...
   - https://akkasah.org/...
   - https://www.nit-istanbul.org/...

Features:
- ✓ Clean titles (no HTML/clutter)
- ✓ Filtered peripheral images
- ✓ Multi-word search
- ✓ In-app image viewing
- ✓ 5 major archives integrated
- ✓ Offline fallback data

Examples:
- Search: python3 unified_heritage_system.py search "earthquake damage" "Antakya"
- Add page: python3 unified_heritage_system.py add https://archnet.org/sites/1644
""")
    else:
        print("\nInvalid choice. Please run the script again.")
        
    print("\n✨ Thank you for using Heritage Explorer!")

if __name__ == '__main__':
    main()