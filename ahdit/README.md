# AHDIT - Antakya Heritage Digital Ingest Toolkit

## Overview

AHDIT is a web-based application for systematically collecting and organizing digital assets from online architectural heritage archives. It provides a user-friendly interface to ingest images and metadata from various sources into a structured local database.

## Features

- **Web-based control panel** - No command line needed
- **Modular connector architecture** - Easy to add new archive sources
- **Background processing** - Ingestion runs without blocking the UI
- **Duplicate detection** - SHA256 hashing prevents redundant downloads
- **Structured storage** - PostgreSQL database with organized file system

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ahdit
   ```

2. **Create and activate a Python virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   
   First, ensure PostgreSQL is installed and running. Then create a database:
   ```bash
   createdb antakya_heritage
   ```
   
   Or using psql:
   ```sql
   CREATE DATABASE antakya_heritage;
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file with your database credentials:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/antakya_heritage
   ```

## Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```
   
   You should see output like:
   ```
   * Running on http://127.0.0.1:5000
   * Debug mode: on
   ```

2. **Access the web interface**
   
   Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

3. **Initialize the database** (First time only)
   
   Click the "Initialize Database" button on the web interface. You should see a success message.

4. **Start an ingestion**
   
   - Enter a monument name (e.g., "Habib-i Neccar Mosque")
   - Select "Archnet" from the dropdown
   - Click "Start Ingestion"
   
   The ingestion will run in the background. Check the terminal for progress updates.

## Project Structure

```
ahdit/
├── app.py                 # Main Flask application
├── connectors/           # Archive-specific connectors
│   ├── __init__.py
│   ├── base.py          # Abstract base connector
│   └── archnet.py       # Archnet.org connector
├── database/            # Database models
│   ├── __init__.py
│   └── models.py        # SQLAlchemy ORM models
├── templates/           # HTML templates
│   └── index.html       # Main web interface
├── data/               # Downloaded assets storage
│   └── assets/
│       └── archnet/    # Archnet-specific downloads
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## How to Add a New Connector

The modular design makes it easy to add support for new archives:

### 1. Create a new connector file

Create a new file in the `connectors/` directory (e.g., `connectors/europeana.py`):

```python
# connectors/europeana.py
from .base import BaseConnector

class EuropeanaConnector(BaseConnector):
    SOURCE_NAME = "europeana"
    
    def search(self, monument_name: str, **kwargs):
        """Search for assets related to the monument."""
        # Your implementation here
        # Yield dictionaries with 'page_url' for each result
        pass
        
    def download_asset(self, raw_metadata: dict) -> tuple[bytes, str]:
        """Download asset and extract metadata."""
        # Your implementation here
        # Return (content_bytes, mime_type)
        pass
```

### 2. Implement the required methods

- **`search()`**: Should yield dictionaries containing at minimum a `page_url` key
- **`download_asset()`**: Should:
  - Update `raw_metadata` with `source_url`, `download_url`, and `tags`
  - Download and return the asset content and MIME type

### 3. Register the connector

Update `connectors/__init__.py`:
```python
from .europeana import EuropeanaConnector
__all__ = ['BaseConnector', 'ArchnetConnector', 'EuropeanaConnector']
```

Update `app.py`:
```python
from connectors.europeana import EuropeanaConnector

CONNECTORS = {
    'archnet': ArchnetConnector,
    'europeana': EuropeanaConnector,  # Add this line
}
```

## Database Schema

The application uses four main tables:

- **monuments**: Stores monument information (name, type, period, coordinates)
- **sources**: Stores archive sources (archnet, europeana, etc.)
- **assets**: Stores downloaded files with metadata and hashes
- **metadata_tags**: Stores flexible key-value metadata for each asset

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Check your DATABASE_URL in the .env file
- Verify the database exists: `psql -l`

### Import Errors
- Make sure you're in the virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### No Results from Archnet
- Some searches may return no results
- Try searching for known monuments like "Blue Mosque" or "Topkapi Palace"
- Check the terminal for error messages

### Port Already in Use
- Another application may be using port 5000
- Stop the other application or change the port in `app.py`

## Contributing

To contribute to AHDIT:

1. Fork the repository
2. Create a feature branch
3. Add your connector or feature
4. Write tests if applicable
5. Submit a pull request

## License

This project is part of the Antakya Heritage Preservation Initiative.

## Acknowledgments

- Stanford Public Humanities for funding
- The international heritage preservation community
- All archive sources that make their data available