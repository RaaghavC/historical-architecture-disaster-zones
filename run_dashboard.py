#!/usr/bin/env python
"""
Launch the full-featured web dashboard
"""

import subprocess
import sys

print("🏛️  Starting Historical Architecture Dashboard...")
print("📍 This will open in your browser at http://127.0.0.1:5001")
print("\nPress Ctrl+C to stop the server\n")

# Run the full dashboard
subprocess.call([sys.executable, "web_dashboard_full.py"])