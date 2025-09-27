"""
Medical Data Platform Pipelines

Production-ready ETL pipelines with clear individual steps for medical data processing.
"""

from dagster import job, op, In, Out, OpExecutionContext
import pandas as pd
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
import os
import pickle
from typing import Dict, Any

from .config import DatabaseConfig, StorageConfig, DATABASE_SCHEMAS


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_csv_with_fallback(file_path: str) -> pd.DataFrame:
    """Load CSV with encoding fallback"""
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            df.columns = df.columns.str.strip()
            df = df.dropna(how='all')
            return df
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue

    raise ValueError(f"Could not read {file_path} with any supported encoding")


def get_last_processed_timestamp(table_name: str) -> datetime:
    """Get the last processed timestamp for a table from ETL runs"""
    db_config = DatabaseConfig.from_env()

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_config.get_connection_string())

        with engine.connect() as conn:
            # Get the latest timestamp from the table itself
            query = text(f"SELECT MAX(created_at) as last_timestamp FROM {table_name}")
            result = conn.execute(query).fetchone()

            if result and result.last_timestamp:
                return result.last_timestamp
            else:
                # Return a very old timestamp if no data exists
                return datetime(2000, 1, 1)

    except Exception as e:
        # Return a very old timestamp if any error occurs
        return datetime(2000, 1, 1)


# ============================================================================
# STEP 1: EXTRACT OPERATIONS
# ============================================================================

@op(
    description="Extract drugs data from CSV file",
    out=Out(Dict[str, Any], description="Raw drugs data with metadata")
)
def extract_drugs_op(context: OpExecutionContext) -> Dict[str, Any]:
    """Extract drugs data from CSV file"""
    raw_data_path = os.getenv('RAW_DATA_PATH', '/opt/dagster/data/raw')
    file_path = f"{raw_data_path}/drugs.csv"

    context.log.info(f"Starting extraction of drugs data from {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Drugs file not found: {file_path}")

    # Load data
    df = load_csv_with_fallback(file_path)
    file_hash = get_file_hash(file_path)

    context.log.info(f"Successfully extracted {len(df)} rows from drugs.csv")
    context.log.info(f"Columns found: {list(df.columns)}")
    context.log.info(f"File hash: {file_hash}")

    return {
        "data": df,
        "file_hash": file_hash,
        "source_file": "drugs.csv",
        "total_rows": len(df)
    }


@op(
    description="Extract PubMed data from CSV file",
    out=Out(Dict[str, Any], description="Raw PubMed data with metadata")
)
def extract_pubmed_op(context: OpExecutionContext) -> Dict[str, Any]:
    """Extract PubMed data from CSV file"""
    raw_data_path = os.getenv('RAW_DATA_PATH', '/opt/dagster/data/raw')
    file_path = f"{raw_data_path}/pubmed.csv"

    context.log.info(f"Starting extraction of PubMed data from {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PubMed file not found: {file_path}")

    # Load data
    df = load_csv_with_fallback(file_path)
    file_hash = get_file_hash(file_path)

    context.log.info(f"Successfully extracted {len(df)} rows from pubmed.csv")
    context.log.info(f"Columns found: {list(df.columns)}")
    context.log.info(f"File hash: {file_hash}")

    return {
        "data": df,
        "file_hash": file_hash,
        "source_file": "pubmed.csv",
        "total_rows": len(df)
    }


@op(
    description="Extract clinical trials data from CSV file",
    out=Out(Dict[str, Any], description="Raw clinical trials data with metadata")
)
def extract_clinical_trials_op(context: OpExecutionContext) -> Dict[str, Any]:
    """Extract clinical trials data from CSV file"""
    raw_data_path = os.getenv('RAW_DATA_PATH', '/opt/dagster/data/raw')
    file_path = f"{raw_data_path}/clinical_trials.csv"

    context.log.info(f"Starting extraction of clinical trials data from {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Clinical trials file not found: {file_path}")

    # Load data
    df = load_csv_with_fallback(file_path)
    file_hash = get_file_hash(file_path)

    context.log.info(f"Successfully extracted {len(df)} rows from clinical_trials.csv")
    context.log.info(f"Columns found: {list(df.columns)}")
    context.log.info(f"File hash: {file_hash}")

    return {
        "data": df,
        "file_hash": file_hash,
        "source_file": "clinical_trials.csv",
        "total_rows": len(df)
    }


# ============================================================================
# STEP 2: SCHEMA VALIDATION
# ============================================================================

@op(
    ins={
        "drugs_data": In(Dict[str, Any]),
        "pubmed_data": In(Dict[str, Any]),
        "clinical_trials_data": In(Dict[str, Any])
    },
    out=Out(Dict[str, Any], description="Schema validation results"),
    description="Validate data schema against database expectations"
)
def validate_schema_op(
    context: OpExecutionContext,
    drugs_data: Dict[str, Any],
    pubmed_data: Dict[str, Any],
    clinical_trials_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate schema of extracted data against database expectations"""

    context.log.info("Starting schema validation for all datasets")

    validation_results = {}

    # Define expected columns for each dataset
    expected_schemas = {
        "drugs": {
            "required": ["atccode", "drug"],
            "table_columns": ["atccode", "drug_name", "batch_id", "ingestion_timestamp", "source_file", "created_at"]
        },
        "pubmed": {
            "required": ["id", "title", "date", "journal"],
            "table_columns": ["source_id", "title", "journal", "date", "batch_id", "ingestion_timestamp", "source_file", "created_at"]
        },
        "clinical_trials": {
            "required": ["id", "scientific_title", "date", "journal"],
            "table_columns": ["source_id", "scientific_title", "journal", "date", "batch_id", "ingestion_timestamp", "source_file", "created_at"]
        }
    }

    datasets = {
        "drugs": drugs_data,
        "pubmed": pubmed_data,
        "clinical_trials": clinical_trials_data
    }

    for dataset_name, dataset in datasets.items():
        df = dataset["data"]
        expected = expected_schemas[dataset_name]

        context.log.info(f"Validating schema for {dataset_name}")
        context.log.info(f"CSV columns: {list(df.columns)}")
        context.log.info(f"Required columns: {expected['required']}")

        # Check required columns
        missing_cols = set(expected["required"]) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns in {dataset_name}: {missing_cols}")

        # Check for timestamp column (backward compatibility)
        has_timestamp = 'created_at' in df.columns

        validation_results[dataset_name] = {
            "csv_columns": list(df.columns),
            "required_columns": expected["required"],
            "table_columns": expected["table_columns"],
            "has_timestamp": has_timestamp,
            "validation_status": "passed"
        }

        context.log.info(f"Schema validation passed for {dataset_name}")
        context.log.info(f"Timestamp column present: {has_timestamp}")

    context.log.info("Schema validation completed successfully for all datasets")
    return validation_results


# ============================================================================
# STEP 3: TRANSFORMATION OPERATIONS
# ============================================================================

@op(
    ins={
        "drugs_data": In(Dict[str, Any]),
        "validation_results": In(Dict[str, Any])
    },
    out=Out(Dict[str, Any], description="Transformed drugs data"),
    description="Transform drugs data and add required metadata columns"
)
def transform_drugs_op(
    context: OpExecutionContext,
    drugs_data: Dict[str, Any],
    validation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform drugs data and add timestamp/metadata columns"""

    context.log.info("Starting transformation of drugs data")

    df = drugs_data["data"].copy()
    source_file = drugs_data["source_file"]
    file_hash = drugs_data["file_hash"]
    batch_id = str(uuid.uuid4())

    # Handle timestamp column (backward compatible)
    has_timestamp = validation_results["drugs"]["has_timestamp"]
    if has_timestamp:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        context.log.info("Using existing timestamp column for delta processing")
        delta_type = "timestamp_based"

        # Get last processed timestamp and filter for delta processing
        last_timestamp = get_last_processed_timestamp("raw_drugs")
        context.log.info(f"Last processed timestamp: {last_timestamp}")

        # Filter for only new records
        original_count = len(df)
        df = df[df['created_at'] > last_timestamp]
        context.log.info(f"Delta filtering: {original_count} total rows → {len(df)} new rows after {last_timestamp}")

    else:
        # For legacy files without timestamps, use current time
        current_time = datetime.now()
        df['created_at'] = current_time
        context.log.info(f"No timestamp column found - assigning current time {current_time} to all records")
        delta_type = "full"

    # Rename columns to match database schema
    if 'drug' in df.columns:
        df = df.rename(columns={'drug': 'drug_name'})

    # Add metadata columns
    df['batch_id'] = batch_id
    df['ingestion_timestamp'] = datetime.now()
    df['source_file'] = source_file

    context.log.info(f"Transformed {len(df)} drug records")
    context.log.info(f"Delta processing type: {delta_type}")
    context.log.info(f"Batch ID: {batch_id}")

    return {
        "data": df,
        "source_file": source_file,
        "file_hash": file_hash,
        "batch_id": batch_id,
        "delta_type": delta_type,
        "processed_rows": len(df),
        "total_rows": drugs_data["total_rows"]
    }


@op(
    ins={
        "pubmed_data": In(Dict[str, Any]),
        "validation_results": In(Dict[str, Any])
    },
    out=Out(Dict[str, Any], description="Transformed PubMed data"),
    description="Transform PubMed data and add required metadata columns"
)
def transform_pubmed_op(
    context: OpExecutionContext,
    pubmed_data: Dict[str, Any],
    validation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform PubMed data and add timestamp/metadata columns"""

    context.log.info("Starting transformation of PubMed data")

    df = pubmed_data["data"].copy()
    source_file = pubmed_data["source_file"]
    file_hash = pubmed_data["file_hash"]
    batch_id = str(uuid.uuid4())

    # Handle timestamp column (backward compatible)
    has_timestamp = validation_results["pubmed"]["has_timestamp"]
    if has_timestamp:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        context.log.info("Using existing timestamp column for delta processing")
        delta_type = "timestamp_based"

        # Get last processed timestamp and filter for delta processing
        last_timestamp = get_last_processed_timestamp("raw_pubmed")
        context.log.info(f"Last processed timestamp: {last_timestamp}")

        # Filter for only new records
        original_count = len(df)
        df = df[df['created_at'] > last_timestamp]
        context.log.info(f"Delta filtering: {original_count} total rows → {len(df)} new rows after {last_timestamp}")

    else:
        # For legacy files without timestamps, use current time
        current_time = datetime.now()
        df['created_at'] = current_time
        context.log.info(f"No timestamp column found - assigning current time {current_time} to all records")
        delta_type = "full"

    # Transform columns to match database schema (keep original CSV column names)
    df = df.rename(columns={
        'id': 'source_id'
    })

    # Convert date column (keep original name to match CSV structure)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Add metadata columns
    df['batch_id'] = batch_id
    df['ingestion_timestamp'] = datetime.now()
    df['source_file'] = source_file

    context.log.info(f"Transformed {len(df)} PubMed records")
    context.log.info(f"Delta processing type: {delta_type}")
    context.log.info(f"Batch ID: {batch_id}")

    return {
        "data": df,
        "source_file": source_file,
        "file_hash": file_hash,
        "batch_id": batch_id,
        "delta_type": delta_type,
        "processed_rows": len(df),
        "total_rows": pubmed_data["total_rows"]
    }


@op(
    ins={
        "clinical_trials_data": In(Dict[str, Any]),
        "validation_results": In(Dict[str, Any])
    },
    out=Out(Dict[str, Any], description="Transformed clinical trials data"),
    description="Transform clinical trials data and add required metadata columns"
)
def transform_clinical_trials_op(
    context: OpExecutionContext,
    clinical_trials_data: Dict[str, Any],
    validation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform clinical trials data and add timestamp/metadata columns"""

    context.log.info("Starting transformation of clinical trials data")

    df = clinical_trials_data["data"].copy()
    source_file = clinical_trials_data["source_file"]
    file_hash = clinical_trials_data["file_hash"]
    batch_id = str(uuid.uuid4())

    # Handle timestamp column (backward compatible)
    has_timestamp = validation_results["clinical_trials"]["has_timestamp"]
    if has_timestamp:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        context.log.info("Using existing timestamp column for delta processing")
        delta_type = "timestamp_based"

        # Get last processed timestamp and filter for delta processing
        last_timestamp = get_last_processed_timestamp("raw_clinical_trials")
        context.log.info(f"Last processed timestamp: {last_timestamp}")

        # Filter for only new records
        original_count = len(df)
        df = df[df['created_at'] > last_timestamp]
        context.log.info(f"Delta filtering: {original_count} total rows → {len(df)} new rows after {last_timestamp}")

    else:
        # For legacy files without timestamps, use current time
        current_time = datetime.now()
        df['created_at'] = current_time
        context.log.info(f"No timestamp column found - assigning current time {current_time} to all records")
        delta_type = "full"

    # Transform columns to match database schema (keep original CSV column names)
    df = df.rename(columns={
        'id': 'source_id'
    })

    # Convert date column (keep original name to match CSV structure)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Add metadata columns
    df['batch_id'] = batch_id
    df['ingestion_timestamp'] = datetime.now()
    df['source_file'] = source_file

    context.log.info(f"Transformed {len(df)} clinical trial records")
    context.log.info(f"Delta processing type: {delta_type}")
    context.log.info(f"Batch ID: {batch_id}")

    return {
        "data": df,
        "source_file": source_file,
        "file_hash": file_hash,
        "batch_id": batch_id,
        "delta_type": delta_type,
        "processed_rows": len(df),
        "total_rows": clinical_trials_data["total_rows"]
    }


# ============================================================================
# STEP 4: LOAD OPERATIONS
# ============================================================================

@op(
    ins={"transformed_drugs": In(Dict[str, Any])},
    out=Out(Dict[str, Any], description="Load results for drugs"),
    description="Load drugs data into PostgreSQL database"
)
def load_drugs_op(
    context: OpExecutionContext,
    transformed_drugs: Dict[str, Any]
) -> Dict[str, Any]:
    """Load drugs data into PostgreSQL database"""

    context.log.info("Starting load of drugs data into database")

    df = transformed_drugs["data"]
    db_config = DatabaseConfig.from_env()

    try:
        from sqlalchemy import create_engine
        engine = create_engine(db_config.get_connection_string())

        # Load data
        rows_inserted = df.to_sql("raw_drugs", engine, if_exists="append", index=False)

        context.log.info(f"Successfully loaded {len(df)} drug records into raw_drugs table")
        context.log.info(f"Batch ID: {transformed_drugs['batch_id']}")

        return {
            "table_name": "raw_drugs",
            "rows_inserted": len(df),
            "batch_id": transformed_drugs["batch_id"],
            "load_status": "success"
        }

    except Exception as e:
        context.log.error(f"Failed to load drugs data: {str(e)}")
        raise


@op(
    ins={"transformed_pubmed": In(Dict[str, Any])},
    out=Out(Dict[str, Any], description="Load results for PubMed"),
    description="Load PubMed data into PostgreSQL database"
)
def load_pubmed_op(
    context: OpExecutionContext,
    transformed_pubmed: Dict[str, Any]
) -> Dict[str, Any]:
    """Load PubMed data into PostgreSQL database"""

    context.log.info("Starting load of PubMed data into database")

    df = transformed_pubmed["data"]
    db_config = DatabaseConfig.from_env()

    try:
        from sqlalchemy import create_engine
        engine = create_engine(db_config.get_connection_string())

        # Load data
        rows_inserted = df.to_sql("raw_pubmed", engine, if_exists="append", index=False)

        context.log.info(f"Successfully loaded {len(df)} PubMed records into raw_pubmed table")
        context.log.info(f"Batch ID: {transformed_pubmed['batch_id']}")

        return {
            "table_name": "raw_pubmed",
            "rows_inserted": len(df),
            "batch_id": transformed_pubmed["batch_id"],
            "load_status": "success"
        }

    except Exception as e:
        context.log.error(f"Failed to load PubMed data: {str(e)}")
        raise


@op(
    ins={"transformed_clinical_trials": In(Dict[str, Any])},
    out=Out(Dict[str, Any], description="Load results for clinical trials"),
    description="Load clinical trials data into PostgreSQL database"
)
def load_clinical_trials_op(
    context: OpExecutionContext,
    transformed_clinical_trials: Dict[str, Any]
) -> Dict[str, Any]:
    """Load clinical trials data into PostgreSQL database"""

    context.log.info("Starting load of clinical trials data into database")

    df = transformed_clinical_trials["data"]
    db_config = DatabaseConfig.from_env()

    try:
        from sqlalchemy import create_engine
        engine = create_engine(db_config.get_connection_string())

        # Load data
        rows_inserted = df.to_sql("raw_clinical_trials", engine, if_exists="append", index=False)

        context.log.info(f"Successfully loaded {len(df)} clinical trial records into raw_clinical_trials table")
        context.log.info(f"Batch ID: {transformed_clinical_trials['batch_id']}")

        return {
            "table_name": "raw_clinical_trials",
            "rows_inserted": len(df),
            "batch_id": transformed_clinical_trials["batch_id"],
            "load_status": "success"
        }

    except Exception as e:
        context.log.error(f"Failed to load clinical trials data: {str(e)}")
        raise


# ============================================================================
# STEP 5: ETL METADATA TRACKING
# ============================================================================

@op(
    ins={
        "drugs_load_result": In(Dict[str, Any]),
        "pubmed_load_result": In(Dict[str, Any]),
        "clinical_trials_load_result": In(Dict[str, Any]),
        "transformed_drugs": In(Dict[str, Any]),
        "transformed_pubmed": In(Dict[str, Any]),
        "transformed_clinical_trials": In(Dict[str, Any])
    },
    description="Track ETL run metadata and update delta checkpoints"
)
def track_etl_metadata_op(
    context: OpExecutionContext,
    drugs_load_result: Dict[str, Any],
    pubmed_load_result: Dict[str, Any],
    clinical_trials_load_result: Dict[str, Any],
    transformed_drugs: Dict[str, Any],
    transformed_pubmed: Dict[str, Any],
    transformed_clinical_trials: Dict[str, Any]
):
    """Track ETL run metadata and update delta checkpoints"""

    context.log.info("Recording ETL metadata and updating checkpoints")

    db_config = DatabaseConfig.from_env()
    run_id = str(uuid.uuid4())

    # Calculate totals
    total_records = (
        drugs_load_result["rows_inserted"] +
        pubmed_load_result["rows_inserted"] +
        clinical_trials_load_result["rows_inserted"]
    )

    # Create ETL run record
    etl_metadata = {
        "run_id": run_id,
        "pipeline_name": "medical_etl_pipeline_v2",
        "status": "completed",
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "records_processed": total_records,
        "metadata": {
            "drugs_metadata": {
                "processed_rows": transformed_drugs["processed_rows"],
                "total_rows": transformed_drugs["total_rows"],
                "delta_type": transformed_drugs["delta_type"],
                "file_hash": transformed_drugs["file_hash"],
                "batch_id": transformed_drugs["batch_id"]
            },
            "pubmed_metadata": {
                "processed_rows": transformed_pubmed["processed_rows"],
                "total_rows": transformed_pubmed["total_rows"],
                "delta_type": transformed_pubmed["delta_type"],
                "file_hash": transformed_pubmed["file_hash"],
                "batch_id": transformed_pubmed["batch_id"]
            },
            "clinical_trials_metadata": {
                "processed_rows": transformed_clinical_trials["processed_rows"],
                "total_rows": transformed_clinical_trials["total_rows"],
                "delta_type": transformed_clinical_trials["delta_type"],
                "file_hash": transformed_clinical_trials["file_hash"],
                "batch_id": transformed_clinical_trials["batch_id"]
            }
        }
    }

    try:
        from sqlalchemy import create_engine
        import json

        engine = create_engine(db_config.get_connection_string())

        # Insert ETL run record
        etl_run_df = pd.DataFrame([{
            "run_id": etl_metadata["run_id"],
            "pipeline_name": etl_metadata["pipeline_name"],
            "status": etl_metadata["status"],
            "start_time": etl_metadata["start_time"],
            "end_time": etl_metadata["end_time"],
            "records_processed": etl_metadata["records_processed"],
            "metadata": json.dumps(etl_metadata["metadata"])
        }])

        etl_run_df.to_sql("etl_runs", engine, if_exists="append", index=False)

        context.log.info(f"ETL run completed successfully")
        context.log.info(f"Run ID: {run_id}")
        context.log.info(f"Total records processed: {total_records}")
        context.log.info(f"Drugs: {transformed_drugs['processed_rows']} rows")
        context.log.info(f"PubMed: {transformed_pubmed['processed_rows']} rows")
        context.log.info(f"Clinical Trials: {transformed_clinical_trials['processed_rows']} rows")

    except Exception as e:
        context.log.error(f"Failed to record ETL metadata: {str(e)}")
        raise


# ============================================================================
# PIPELINE DEFINITION
# ============================================================================

@job(description="Medical Data ETL Pipeline with Individual Steps")
def medical_etl_pipeline_v2():
    """
    Medical Data ETL Pipeline with clear individual steps:

    1. Extract: Pull data from CSV files (drugs, pubmed, clinical_trials)
    2. Validate: Check schema compatibility with database
    3. Transform: Add timestamps and metadata, rename columns
    4. Load: Insert data into PostgreSQL tables
    5. Track: Record ETL metadata and update checkpoints
    """

    # Step 1: Extract all data sources
    drugs_data = extract_drugs_op()
    pubmed_data = extract_pubmed_op()
    clinical_trials_data = extract_clinical_trials_op()

    # Step 2: Validate schema
    validation_results = validate_schema_op(drugs_data, pubmed_data, clinical_trials_data)

    # Step 3: Transform data
    transformed_drugs = transform_drugs_op(drugs_data, validation_results)
    transformed_pubmed = transform_pubmed_op(pubmed_data, validation_results)
    transformed_clinical_trials = transform_clinical_trials_op(clinical_trials_data, validation_results)

    # Step 4: Load data
    drugs_load_result = load_drugs_op(transformed_drugs)
    pubmed_load_result = load_pubmed_op(transformed_pubmed)
    clinical_trials_load_result = load_clinical_trials_op(transformed_clinical_trials)

    # Step 5: Track metadata
    track_etl_metadata_op(
        drugs_load_result,
        pubmed_load_result,
        clinical_trials_load_result,
        transformed_drugs,
        transformed_pubmed,
        transformed_clinical_trials
    )


# Legacy pipeline for backwards compatibility
medical_etl_pipeline = medical_etl_pipeline_v2