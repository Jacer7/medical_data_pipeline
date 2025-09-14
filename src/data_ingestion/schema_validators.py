import pandas as pd
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Production schema validation with detailed error reporting"""
    
    @staticmethod
    def validate_drugs_schema(df: pd.DataFrame) -> pd.DataFrame:
        """Validate drugs.csv schema and data quality"""
        required_columns = ['atccode', 'drug']
        
        # Column validation
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Drugs file missing columns: {missing_cols}")
        
        # Data quality checks
        if df['atccode'].isnull().any():
            raise ValueError("ATC codes cannot be null")
            
        if df['drug'].isnull().any():
            raise ValueError("Drug names cannot be null")
            
        # Clean and standardize
        df['drug'] = df['drug'].str.strip().str.upper()
        df['atccode'] = df['atccode'].str.strip()
        
        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates(subset=['atccode'])
        if len(df) < initial_count:
            logger.warning(f"Removed {initial_count - len(df)} duplicate drugs")
            
        return df
    
    @staticmethod
    def validate_pubmed_schema(df: pd.DataFrame) -> pd.DataFrame:
        """Validate pubmed data schema"""
        required_columns = ['id', 'title', 'date', 'journal']
        
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"PubMed file missing columns: {missing_cols}")
        
        # Data cleaning
        df['title'] = df['title'].fillna('').str.strip()
        df['journal'] = df['journal'].fillna('').str.strip()
        
        # Date validation and standardization
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        invalid_dates = df['date'].isnull().sum()
        if invalid_dates > 0:
            logger.warning(f"Found {invalid_dates} invalid dates in PubMed data")
            
        return df
    
    @staticmethod
    def validate_clinical_trials_schema(df: pd.DataFrame) -> pd.DataFrame:
        """Validate clinical trials schema"""
        required_columns = ['id', 'scientific_title', 'date', 'journal']
        
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Clinical trials file missing columns: {missing_cols}")
            
        # Standardize column names for consistency
        df = df.rename(columns={'scientific_title': 'title'})
        
        # Data cleaning
        df['title'] = df['title'].fillna('').str.strip()
        df['journal'] = df['journal'].fillna('').str.strip()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        return df