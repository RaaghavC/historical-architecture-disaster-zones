# app.py
import os
import threading
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Monument, Source, Asset
from connectors.archnet import ArchnetConnector
from connectors.manar import ManarConnector
from connectors.salt import SALTConnector
from connectors.nit import NITConnector
from connectors.wikimedia import WikimediaConnector

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Connector registry
CONNECTORS = {
    'archnet': ArchnetConnector,
    'manar': ManarConnector,
    'salt': SALTConnector,
    'nit-istanbul': NITConnector,
    'wikimedia': WikimediaConnector,
}

# Create tables if they don't exist
Base.metadata.create_all(engine)

# Pre-populate sources if they don't exist
session = Session()
try:
    source_urls = {
        'archnet': 'https://www.archnet.org',
        'manar': 'https://www.manar-al-athar.ox.ac.uk',
        'salt': 'https://saltresearch.org',
        'nit-istanbul': 'https://www.nit-istanbul.org',
        'wikimedia': 'https://commons.wikimedia.org'
    }
    
    for name in CONNECTORS.keys():
        existing = session.query(Source).filter_by(name=name).first()
        if not existing:
            source = Source(name=name, base_url=source_urls.get(name, 'https://example.com'))
            session.add(source)
    session.commit()
except:
    session.rollback()
finally:
    session.close()

def run_ingestion_task(app, source_name, monument_name):
    """Background task to run the ingestion process."""
    with app.app_context():
        session = Session()
        try:
            # Get source
            source_obj = session.query(Source).filter_by(name=source_name).first()
            if not source_obj:
                print(f"Error: Source '{source_name}' not found in database.")
                return
            
            # Get or create monument
            monument = session.query(Monument).filter_by(name_en=monument_name).first()
            if not monument:
                print(f"Creating new monument entry: {monument_name}")
                monument = Monument(name_en=monument_name)
                session.add(monument)
                session.commit()
            
            # Initialize connector and run ingestion
            connector_class = CONNECTORS[source_name]
            connector = connector_class(session)
            
            print(f"Starting ingestion from {source_name} for '{monument_name}'...")
            
            for raw_metadata in connector.search(monument_name):
                connector.process_and_store(raw_metadata, monument, source_obj)
            
            session.commit()
            print(f"Ingestion complete for '{monument_name}' from {source_name}")
            
        except Exception as e:
            session.rollback()
            print(f"Error during ingestion: {e}")
            raise
        finally:
            session.close()

@app.route('/')
def index():
    """Main dashboard page."""
    session = Session()
    try:
        monuments = session.query(Monument).order_by(Monument.name_en).all()
        connector_names = list(CONNECTORS.keys())
        return render_template('index.html', monuments=monuments, connectors=connector_names)
    finally:
        session.close()

@app.route('/db-init')
def db_init():
    """Initialize database and pre-populate sources."""
    session = Session()
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Pre-populate sources
        for name, connector_class in CONNECTORS.items():
            existing = session.query(Source).filter_by(name=name).first()
            if not existing:
                if name == 'archnet':
                    source = Source(name=name, base_url='https://www.archnet.org')
                else:
                    source = Source(name=name, base_url='https://example.com')
                session.add(source)
        
        session.commit()
        flash('Database initialized successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error initializing database: {e}', 'error')
    finally:
        session.close()
    
    return redirect(url_for('index'))

@app.route('/ingest', methods=['POST'])
def ingest():
    """Handle ingestion form submission."""
    monument_name = request.form.get('monument_name')
    source_name = request.form.get('source_name')
    
    if not monument_name or not source_name:
        flash('Please provide both monument name and source.', 'error')
        return redirect(url_for('index'))
    
    # Start background thread
    thread = threading.Thread(
        target=run_ingestion_task,
        args=(app, source_name, monument_name)
    )
    thread.daemon = True
    thread.start()
    
    flash(f'Ingestion task for "{monument_name}" from {source_name} has started!', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)