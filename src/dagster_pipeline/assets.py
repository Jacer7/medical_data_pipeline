from storage.medical_database import create_medical_tables, get_medical_database_connection

@asset
def initialize_medical_database():
    """First asset - creates medical database tables"""
    create_medical_tables()
    return "Medical database initialized"

@asset
def ingest_drugs_data(initialize_medical_database):
    """Depends on database initialization"""
    # Your ingestion logic here
    pass