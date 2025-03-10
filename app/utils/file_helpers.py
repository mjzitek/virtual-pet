"""
File Helper Functions

Utility functions for file operations in the Virtual Pet Application.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        The loaded JSON data as a dictionary, or None if loading fails
    """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load JSON file {file_path}: {str(e)}")
        return None

def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        file_path: Path to the JSON file
        data: The data to save
        
    Returns:
        True if saving was successful, False otherwise
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w") as file:
            json.dump(data, file, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {file_path}: {str(e)}")
        return False 