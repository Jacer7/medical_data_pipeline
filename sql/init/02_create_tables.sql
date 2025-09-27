-- Connect to the medical_data database
\c medical_data;

-- Create simple raw data tables matching CSV structure
CREATE TABLE IF NOT EXISTS raw_pubmed (
    id SERIAL PRIMARY KEY,
    title TEXT,
    date DATE,
    journal TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_clinical_trials (
    id SERIAL PRIMARY KEY,
    scientific_title TEXT,
    date DATE,
    journal TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_drugs (
    id SERIAL PRIMARY KEY,
    atccode VARCHAR(50),
    drug VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create simple ETL metadata tables
CREATE TABLE IF NOT EXISTS etl_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(255) UNIQUE,
    status VARCHAR(50),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS model_training_runs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255),
    version VARCHAR(50),
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS delta_checkpoints (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255),
    last_processed_date TIMESTAMP,
    checkpoint_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create basic indexes
CREATE INDEX IF NOT EXISTS idx_pubmed_date ON raw_pubmed(date);
CREATE INDEX IF NOT EXISTS idx_clinical_trials_date ON raw_clinical_trials(date);
CREATE INDEX IF NOT EXISTS idx_drugs_atccode ON raw_drugs(atccode);
CREATE INDEX IF NOT EXISTS idx_etl_runs_status ON etl_runs(status);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pipeline_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pipeline_user;