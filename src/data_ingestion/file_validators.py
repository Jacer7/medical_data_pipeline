import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def validate_csv_file(file_path: Path) -> bool:
    """Validate that file exists and is readable CSV"""
    try:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
            
        df = pd.read_csv(file_path)
        logger.info(f"CSV file validated: {len(df)} rows, {len(df.columns)} columns")
        return True
        
    except Exception as e:
        logger.error(f"CSV validation failed for {file_path}: {e}")
        return False

def validate_json_file(file_path: Path) -> bool:
    """Validate that file exists and is readable JSON"""
    try:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
            
        with open(file_path) as f:
            data = json.load(f)
            
        logger.info(f"JSON file validated: {len(data) if isinstance(data, list) else 1} records")
        return True
        
    except Exception as e:
        logger.error(f"JSON validation failed for {file_path}: {e}")
        return False