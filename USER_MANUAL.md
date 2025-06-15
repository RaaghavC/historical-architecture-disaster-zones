# User Manual - Historical Architecture Project

This manual explains how to use the urgent fixes branch for documenting historical architecture in disaster zones.

## What This Does

This project helps you:
- Find and save photos of historical buildings
- Document earthquake damage
- Create backups of your data
- Search multiple photo archives at once
- Make academic citations
- Generate web galleries

## Quick Start

### 1. See Everything Work

Run this one command to test all features:

```bash
python test_all_features.py
```

This shows you every new feature in action.

### 2. Search for Buildings

To find photos of Antakya buildings:

```bash
python -m data_collection.cli search "Antakya"
```

To search specific archives:

```bash
python -m data_collection.cli search "Antakya mosque" --archives salt nit
```

### 3. Document Damage

If you're in the field documenting damage:

```python
from field_documentation.damage_assessment import DamageAssessmentSystem, DamageCategory

# Create system
system = DamageAssessmentSystem()

# Record damage
assessment = system.create_assessment(
    site_name="Building Name",
    location="Street Address", 
    assessor_name="Your Name",
    damage_category=DamageCategory.SEVERE,  # or MODERATE, HEAVY, etc
    description="What you see"
)

# Save it
system.save_assessment(assessment)
```

### 4. Make Backups

To backup all your data:

```python
from backup_system import BackupSystem

backup = BackupSystem()
backup.create_backup()  # Creates timestamped backup
```

### 5. Generate Web Gallery

To create a website showing the damage:

```bash
python tools/generate_public_gallery.py
```

Then open `public_gallery/index.html` in your browser.

## Main Features Explained

### Archives You Can Search

1. **SALT Research** - Ottoman building photos from Istanbul
2. **NIT Kiel Archive** - 30,000+ Ottoman monument photos  
3. **Akkasah** - Middle Eastern photography (may be offline)
4. **ArchNet** - Islamic architecture database
5. **Manar al-Athar** - Archaeological photos

### Damage Levels

When documenting damage, use these categories:
- **NO_DAMAGE** - Building is fine
- **SLIGHT** - Small cracks, minor damage
- **MODERATE** - Visible damage but stable
- **HEAVY** - Major damage, unstable
- **SEVERE** - Near collapse
- **DESTROYED** - Completely collapsed

### File Organization

Your data is saved in these folders:
- `harvested_data/` - Downloaded photos and data
- `field_assessments/` - Damage documentation
- `backups/` - Automatic backups
- `public_gallery/` - Generated website

## Common Tasks

### Find Pre-Earthquake Photos

```bash
python -m data_collection.cli search "Habib-i Neccar" --archives salt nit
```

### Download Everything About Antakya

```bash
python -m data_collection.cli antakya
```

This searches all archives for Antakya-related content.

### Create Academic Citations

```python
from scholarly_tools import cite_salt_photograph

citation = cite_salt_photograph(
    title="Mosque Name",
    photographer="Photographer Name",
    date="1975",
    collection="Collection Name"
)
print(citation)
```

### Compare Before/After

The system automatically finds potential before/after photo pairs when you run the gallery generator.

## Troubleshooting

### "Module not found" Error

Install missing packages:
```bash
pip install -r requirements_urgent_fixes.txt
```

### Can't Find Buildings

Try different spellings:
- Antakya / Antioch
- Habib-i Neccar / Habib Neccar / Habibi Najjar

### Backup Failed

Check you have space on your drive. Backups go in the `backups/` folder.

## Tips

1. **Regular Backups** - Run backup system daily
2. **Multiple Searches** - Try Turkish and English names
3. **Save Often** - Field assessments auto-save
4. **Check Gallery** - Generate gallery to see your progress

## Getting Help

- Check `SCHOLARLY_FEATURES.md` for advanced features
- Look at `test_all_features.py` for code examples
- Error messages usually tell you what's wrong

## Safety Note

This branch (`urgent-fixes-phase1`) keeps your main branch safe. Nothing here affects the main branch until you decide to merge.