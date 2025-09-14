import pandas as pd
import json
from pathlib import Path
from typing import Union, Dict, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class DataFileReader:
    """Production-grade file reader with error handling and validation"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def read_csv(self, filename: str, required_columns: list = None) -> pd.DataFrame:
        """Read CSV with retry logic and validation"""
        file_path = self.data_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Required data file not found: {file_path}")
            
        try:
            # Read with explicit encoding handling
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Strip whitespace from column names (common data issue)
            df.columns = df.columns.str.strip()
            
            # Validate required columns
            if required_columns:
                missing_cols = set(required_columns) - set(df.columns)
                if missing_cols:
                    raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            logger.info(f"Successfully read {filename}: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except pd.errors.EmptyDataError:
            raise ValueError(f"File {filename} is empty")
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse {filename}: {e}")
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def read_json(self, filename: str) -> list:
        """Read JSON with retry logic and validation"""
        file_path = self.data_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Required data file not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to fix common JSON issues
            content = content.rstrip().rstrip(',')  # Remove trailing commas
            
            data = json.loads(content)
                
            if not isinstance(data, list):
                raise ValueError(f"Expected JSON array in {filename}, got {type(data)}")
                
            logger.info(f"Successfully read {filename}: {len(data)} records")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed at line {e.lineno}, column {e.colno}")
            raise ValueError(f"Invalid JSON in {filename}: {e}")