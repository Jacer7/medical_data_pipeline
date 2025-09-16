from dagster import asset
import pandas as pd
import uuid
from datetime import datetime
from storage.medical_database import get_medical_database_connection

@asset(group_name="data_ingestion")
def ingest_drugs_batch():
    """Ingest drugs.csv into PostgreSQL"""
    
    # Generate unique batch ID
    batch_id = f"drugs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    # Read CSV
    df = pd.read_csv("/opt/dagster/data/raw/drugs.csv")
    
    # Add ingestion metadata
    df['ingestion_batch_id'] = batch_id
    df['ingestion_timestamp'] = datetime.now()
    
    # Rename columns to match schema
    df = df.rename(columns={'drug': 'drug_name'})
    
    # Insert to database
    conn = get_medical_database_connection()
    df.to_sql('raw_drugs', conn, if_exists='append', index=False, method='multi')
    conn.close()
    
    return f"Ingested {len(df)} drugs records with batch_id: {batch_id}"

@asset(group_name="data_ingestion")
def ingest_pubmed_batch():
    """Ingest pubmed.csv into PostgreSQL"""
    
    batch_id = f"pubmed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    df = pd.read_csv("/opt/dagster/data/raw/pubmed.csv")
    df['ingestion_batch_id'] = batch_id
    df['ingestion_timestamp'] = datetime.now()
    
    # Rename columns
    df = df.rename(columns={
        'id': 'source_id', 
        'date': 'publication_date'
    })
    
    conn = get_medical_database_connection()
    df.to_sql('raw_pubmed', conn, if_exists='append', index=False, method='multi')
    conn.close()
    
    return f"Ingested {len(df)} pubmed records with batch_id: {batch_id}"

@asset(group_name="data_ingestion")
def ingest_clinical_trials_batch():
    """Ingest clinical_trials.csv into PostgreSQL"""
    
    batch_id = f"clinical_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    df = pd.read_csv("/opt/dagster/data/raw/clinical_trials.csv")
    df['ingestion_batch_id'] = batch_id
    df['ingestion_timestamp'] = datetime.now()
    
    # Rename columns
    df = df.rename(columns={
        'id': 'source_id',
        'date': 'publication_date'
    })
    
    conn = get_medical_database_connection()
    df.to_sql('raw_clinical_trials', conn, if_exists='append', index=False, method='multi')
    conn.close()
    
    return f"Ingested {len(df)} clinical trials records with batch_id: {batch_id}"

@asset(group_name="data_ingestion")
def ingestion_summary(ingest_drugs_batch, ingest_pubmed_batch, ingest_clinical_trials_batch):
    """Summary of complete ingestion batch"""
    return {
        "drugs": ingest_drugs_batch,
        "pubmed": ingest_pubmed_batch, 
        "clinical_trials": ingest_clinical_trials_batch,
        "completed_at": datetime.now().isoformat()
    }