"""
Medical Data Platform - Production-Ready ETL & ML Analytics Platform

A comprehensive, production-ready data platform for medical data processing
that includes both ETL and ML analytics capabilities.
"""

from dagster import Definitions
from .pipelines import medical_etl_pipeline, medical_etl_pipeline_v2
from .resources import database_resource, storage_resource

# Define the Dagster application
defs = Definitions(
    jobs=[
        medical_etl_pipeline,      # Legacy ETL pipeline for backwards compatibility
        medical_etl_pipeline_v2    # New ETL pipeline with individual clear steps
    ],
    resources={
        "database": database_resource,
        "storage": storage_resource
    }
)