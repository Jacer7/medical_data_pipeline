"""
Configuration Management for Medical Data Platform
"""
import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = "postgres"
    port: int = 5432
    database: str = "medical_data"
    username: str = "pipeline_user"
    password: str = "pipeline_password_secure123"

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "medical_data"),
            username=os.getenv("DB_USER", "pipeline_user"),
            password=os.getenv("DB_PASSWORD", "pipeline_password_secure123")
        )

    def get_connection_string(self) -> str:
        """Get SQLAlchemy connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_psycopg2_params(self) -> dict:
        """Get psycopg2 connection parameters"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.username,
            "password": self.password
        }


@dataclass
class StorageConfig:
    """Data storage configuration"""
    raw_data_path: str = "/opt/dagster/data/raw"
    processed_data_path: str = "/opt/dagster/data/processed"
    model_artifacts_path: str = "/opt/dagster/data/models"

    @classmethod
    def from_env(cls):
        """Load storage configuration from environment"""
        return cls(
            raw_data_path=os.getenv("RAW_DATA_PATH", "/opt/dagster/data/raw"),
            processed_data_path=os.getenv("PROCESSED_DATA_PATH", "/opt/dagster/data/processed"),
            model_artifacts_path=os.getenv("MODEL_ARTIFACTS_PATH", "/opt/dagster/data/models")
        )


# Database table schemas
DATABASE_SCHEMAS = {
    "raw_drugs": """
        CREATE TABLE IF NOT EXISTS raw_drugs (
            id SERIAL PRIMARY KEY,
            atccode VARCHAR(50),
            drug_name VARCHAR(255),
            batch_id VARCHAR(100),
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Add missing columns if they don't exist
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_drugs' AND column_name='batch_id') THEN
                ALTER TABLE raw_drugs ADD COLUMN batch_id VARCHAR(100);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_drugs' AND column_name='source_file') THEN
                ALTER TABLE raw_drugs ADD COLUMN source_file VARCHAR(255);
            END IF;
            -- Rename ingestion_batch_id to batch_id if it exists
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_drugs' AND column_name='ingestion_batch_id') THEN
                UPDATE raw_drugs SET batch_id = ingestion_batch_id WHERE batch_id IS NULL;
            END IF;
        END $$;

        CREATE INDEX IF NOT EXISTS idx_raw_drugs_atccode ON raw_drugs(atccode);
        CREATE INDEX IF NOT EXISTS idx_raw_drugs_batch_id ON raw_drugs(batch_id);
    """,

    "raw_pubmed": """
        CREATE TABLE IF NOT EXISTS raw_pubmed (
            id SERIAL PRIMARY KEY,
            source_id VARCHAR(50),
            title TEXT,
            publication_date DATE,
            journal VARCHAR(255),
            batch_id VARCHAR(100),
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Add missing columns if they don't exist
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_pubmed' AND column_name='batch_id') THEN
                ALTER TABLE raw_pubmed ADD COLUMN batch_id VARCHAR(100);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_pubmed' AND column_name='source_file') THEN
                ALTER TABLE raw_pubmed ADD COLUMN source_file VARCHAR(255);
            END IF;
            -- Copy data from ingestion_batch_id to batch_id if it exists
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_pubmed' AND column_name='ingestion_batch_id') THEN
                UPDATE raw_pubmed SET batch_id = ingestion_batch_id WHERE batch_id IS NULL;
            END IF;
        END $$;

        CREATE INDEX IF NOT EXISTS idx_raw_pubmed_source_id ON raw_pubmed(source_id);
        CREATE INDEX IF NOT EXISTS idx_raw_pubmed_batch_id ON raw_pubmed(batch_id);
    """,

    "raw_clinical_trials": """
        CREATE TABLE IF NOT EXISTS raw_clinical_trials (
            id SERIAL PRIMARY KEY,
            source_id VARCHAR(50),
            scientific_title TEXT,
            publication_date DATE,
            journal VARCHAR(255),
            batch_id VARCHAR(100),
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Add missing columns if they don't exist
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_clinical_trials' AND column_name='batch_id') THEN
                ALTER TABLE raw_clinical_trials ADD COLUMN batch_id VARCHAR(100);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_clinical_trials' AND column_name='source_file') THEN
                ALTER TABLE raw_clinical_trials ADD COLUMN source_file VARCHAR(255);
            END IF;
            -- Copy data from ingestion_batch_id to batch_id if it exists
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='raw_clinical_trials' AND column_name='ingestion_batch_id') THEN
                UPDATE raw_clinical_trials SET batch_id = ingestion_batch_id WHERE batch_id IS NULL;
            END IF;
        END $$;

        CREATE INDEX IF NOT EXISTS idx_raw_clinical_trials_source_id ON raw_clinical_trials(source_id);
        CREATE INDEX IF NOT EXISTS idx_raw_clinical_trials_batch_id ON raw_clinical_trials(batch_id);
    """,

    "etl_runs": """
        CREATE TABLE IF NOT EXISTS etl_runs (
            run_id VARCHAR(100) PRIMARY KEY,
            pipeline_name VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            records_processed INTEGER,
            error_message TEXT,
            metadata JSON
        );
        CREATE INDEX IF NOT EXISTS idx_etl_runs_pipeline_name ON etl_runs(pipeline_name);
        CREATE INDEX IF NOT EXISTS idx_etl_runs_status ON etl_runs(status);
    """,

    "model_training_runs": """
        CREATE TABLE IF NOT EXISTS model_training_runs (
            run_id VARCHAR(100) PRIMARY KEY,
            model_name VARCHAR(100) NOT NULL,
            model_version VARCHAR(50) NOT NULL,
            training_data_version VARCHAR(100),
            hyperparameters JSON,
            metrics JSON,
            model_path VARCHAR(255),
            status VARCHAR(20) NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_model_training_runs_model_name ON model_training_runs(model_name);
        CREATE INDEX IF NOT EXISTS idx_model_training_runs_status ON model_training_runs(status);
    """,

    "delta_checkpoints": """
        CREATE TABLE IF NOT EXISTS delta_checkpoints (
            source_file VARCHAR(255) PRIMARY KEY,
            last_processed_timestamp TIMESTAMP,
            last_processed_row_count INTEGER,
            file_hash VARCHAR(64),
            last_file_size BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
}