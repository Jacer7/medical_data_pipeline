from dagster import Definitions
from .assets import (
    ingest_drugs_batch,
    ingest_pubmed_batch,
    ingest_clinical_trials_batch,
    ingestion_summary
)
from .setup_assets import setup_medical_database_job

defs = Definitions(
    assets=[
        ingest_drugs_batch,
        ingest_pubmed_batch,
        ingest_clinical_trials_batch,
        ingestion_summary
    ],
    jobs=[
        setup_medical_database_job  # Run this once manually
    ]
)