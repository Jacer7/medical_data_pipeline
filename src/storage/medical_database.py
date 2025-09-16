import psycopg2
import logging

logger = logging.getLogger(__name__)

def get_medical_database_connection():
    """Connection to medical_data database"""
    return psycopg2.connect(
        host="postgres",
        user="pipeline_user", 
        password="pipeline_password",
        database="medical_data"
    )

def create_medical_tables():
    """Create business tables in medical_data database with existence checking"""
    conn = get_medical_database_connection()
    cursor = conn.cursor()
    
    try:
        tables_to_create = {
            'raw_drugs': """
                CREATE TABLE raw_drugs (
                    id SERIAL PRIMARY KEY,
                    atccode VARCHAR(20) NOT NULL,
                    drug_name VARCHAR(200) NOT NULL,
                    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
                    ingestion_batch_id VARCHAR(50),
                    source_file VARCHAR(100) DEFAULT 'drugs.csv'
                );
            """,
            'raw_pubmed': """
                CREATE TABLE raw_pubmed (
                    id SERIAL PRIMARY KEY,
                    source_id VARCHAR(100),
                    title TEXT NOT NULL,
                    publication_date DATE,
                    journal TEXT,
                    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
                    ingestion_batch_id VARCHAR(50),
                    source_file VARCHAR(100) DEFAULT 'pubmed.csv'
                );
            """,
            'raw_clinical_trials': """
                CREATE TABLE raw_clinical_trials (
                    id SERIAL PRIMARY KEY,
                    source_id VARCHAR(100),
                    scientific_title TEXT NOT NULL,
                    publication_date DATE,
                    journal TEXT,
                    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
                    ingestion_batch_id VARCHAR(50), 
                    source_file VARCHAR(100) DEFAULT 'clinical_trials.csv'
                );
            """
        }
        
        # Check which tables already exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('raw_drugs', 'raw_pubmed', 'raw_clinical_trials')
        """)
        
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        created_count = 0
        skipped_count = 0
        
        # Create only missing tables
        for table_name, create_sql in tables_to_create.items():
            if table_name in existing_tables:
                logger.info(f"Table '{table_name}' already exists, skipping creation")
                skipped_count += 1
            else:
                cursor.execute(create_sql)
                logger.info(f"Created table '{table_name}'")
                created_count += 1
        
        # Create indexes if any tables were created
        if created_count > 0:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_drugs_ingestion_timestamp 
                ON raw_drugs(ingestion_timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_raw_pubmed_ingestion_timestamp 
                ON raw_pubmed(ingestion_timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_raw_clinical_trials_ingestion_timestamp 
                ON raw_clinical_trials(ingestion_timestamp);
            """)
            logger.info("Created indexes for new tables")
        
        conn.commit()
        
        # Summary logging
        if created_count > 0:
            logger.info(f"Medical database setup complete: {created_count} tables created, {skipped_count} tables already existed")
        else:
            logger.info(f"All medical database tables already exist ({skipped_count} tables found)")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating medical tables: {e}")
        raise
    finally:
        cursor.close()
        conn.close()