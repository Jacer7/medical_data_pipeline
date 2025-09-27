"""
Dagster Resources for Medical Data Platform
"""
from dagster import ConfigurableResource
import psycopg2
from sqlalchemy import create_engine
import os
from .config import DatabaseConfig, StorageConfig


class DatabaseResource(ConfigurableResource):
    """Database connection resource"""

    def get_connection(self):
        """Get raw psycopg2 connection"""
        db_config = DatabaseConfig.from_env()
        return psycopg2.connect(**db_config.get_psycopg2_params())

    def get_engine(self):
        """Get SQLAlchemy engine"""
        db_config = DatabaseConfig.from_env()
        return create_engine(db_config.get_connection_string())


class StorageResource(ConfigurableResource):
    """File system storage resource"""

    def get_raw_data_path(self) -> str:
        """Get raw data directory path"""
        storage_config = StorageConfig.from_env()
        return storage_config.raw_data_path

    def get_processed_data_path(self) -> str:
        """Get processed data directory path"""
        storage_config = StorageConfig.from_env()
        return storage_config.processed_data_path

    def get_model_artifacts_path(self) -> str:
        """Get model artifacts directory path"""
        storage_config = StorageConfig.from_env()
        return storage_config.model_artifacts_path

    def ensure_directories(self):
        """Ensure all storage directories exist"""
        storage_config = StorageConfig.from_env()
        for path in [storage_config.raw_data_path, storage_config.processed_data_path, storage_config.model_artifacts_path]:
            os.makedirs(path, exist_ok=True)


# Resource instances
database_resource = DatabaseResource()
storage_resource = StorageResource()