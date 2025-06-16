#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Monument, Source
from connectors.wikimedia import WikimediaConnector
from connectors.archnet import ArchnetConnector
from connectors.manar import ManarConnector

# Load environment
load_dotenv()
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_connector(ConnectorClass, source_name, monument_name):
    print(f"\n=== Testing {source_name} for '{monument_name}' ===")
    session = Session()
    try:
        # Get source
        source = session.query(Source).filter_by(name=source_name).first()
        if not source:
            print(f"Creating source: {source_name}")
            source = Source(name=source_name, base_url='https://example.com')
            session.add(source)
            session.commit()
        
        # Get monument
        monument = session.query(Monument).filter_by(name_en=monument_name).first()
        if not monument:
            monument = Monument(name_en=monument_name)
            session.add(monument)
            session.commit()
        
        # Test connector
        connector = ConnectorClass(session)
        count = 0
        
        for metadata in connector.search(monument_name):
            count += 1
            print(f"Found: {metadata.get('title', 'Unknown')}")
            if count >= 3:  # Limit to 3 results for testing
                break
        
        print(f"Total found: {count}")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # Test each connector
    test_connector(WikimediaConnector, 'wikimedia', 'Antakya')
    test_connector(ArchnetConnector, 'archnet', 'Alhambra')
    test_connector(ManarConnector, 'manar', 'Damascus')