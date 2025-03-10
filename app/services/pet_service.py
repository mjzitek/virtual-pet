"""
Pet Service for Virtual Pet Application

This module handles pet-related functionality, including state management,
persistence, and pet actions.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from app.config.settings import PET_CONFIG_FILE, PET_DATA_FILE, DEFAULT_PET_STATS
from app.utils.file_helpers import load_json_file, save_json_file

# Configure logging
logger = logging.getLogger(__name__)

class PetService:
    """
    Manages pet-related functionality.
    """
    
    def __init__(self):
        """Initialize the Pet Service."""
        # Ensure data directory exists
        data_dir = os.path.dirname(PET_DATA_FILE)
        os.makedirs(data_dir, exist_ok=True)
        
        self.pet_config = self._load_pet_config()
        logger.info("Pet Service initialized")
    
    def _load_pet_config(self) -> Dict[str, Any]:
        """
        Load pet configuration from the config file.
        
        Returns:
            The pet configuration dictionary
        """
        config = load_json_file(PET_CONFIG_FILE)
        if not config:
            logger.error(f"Failed to load pet configuration from {PET_CONFIG_FILE}")
            raise ValueError(f"Failed to load pet configuration from {PET_CONFIG_FILE}")
        return config
    
    def get_available_pets(self) -> Dict[str, str]:
        """
        Get a dictionary of available pet types and their display names.
        
        Returns:
            A dictionary mapping pet keys to display names
        """
        return {pet_key: pet_data["name"] for pet_key, pet_data in self.pet_config.items()}
    
    def _get_pet_key(self, pet_type: str) -> Optional[str]:
        """
        Get the correct pet key in a case-insensitive way.
        
        Args:
            pet_type: The type of pet (case-insensitive)
            
        Returns:
            The correct pet key, or None if not found
        """
        if not pet_type:
            return None
        
        pet_type_lower = pet_type.lower()
        
        for key in self.pet_config.keys():
            if key.lower() == pet_type_lower:
                return key
        
        return None

    def get_pet_image_path(self, pet_type: str, mood: str) -> str:
        """
        Get the image path for a pet with the specified type and mood.
        
        Args:
            pet_type: The type of pet
            mood: The mood of the pet
            
        Returns:
            The path to the pet image
        """
        # Get the correct pet key
        pet_key = self._get_pet_key(pet_type)
        
        if not pet_key:
            logger.error(f"Invalid pet type: {pet_type}")
            # Return a default image if available
            if "cat" in self.pet_config and "neutral" in self.pet_config["cat"]["images"]:
                return self.pet_config["cat"]["images"]["neutral"]
            return ""
        
        pet_data = self.pet_config[pet_key]
        if mood not in pet_data["images"]:
            logger.warning(f"Invalid mood {mood} for pet type {pet_type}, using neutral")
            mood = "neutral"
        
        return pet_data["images"][mood]
    
    def load_pet_data(self) -> Optional[Dict[str, Any]]:
        """
        Load saved pet data from the data file.
        
        Returns:
            The loaded pet data, or None if no data exists
        """
        data = load_json_file(PET_DATA_FILE)
        if data is None:
            logger.info("No saved pet data found. Starting with a new pet.")
        return data
    
    def save_pet_data(self, pet_data: Dict[str, Any]) -> bool:
        """
        Save pet data to the data file.
        
        Args:
            pet_data: The pet data to save
            
        Returns:
            True if saving was successful, False otherwise
        """
        # Add a timestamp
        pet_data["last_updated"] = datetime.datetime.now().isoformat()
        return save_json_file(PET_DATA_FILE, pet_data)
    
    def update_pet_state(self, pet_state: Dict[str, Any], action: str) -> Dict[str, Any]:
        """
        Update the pet state based on the specified action.
        
        Args:
            pet_state: The current pet state
            action: The action to perform (feed, play, rest)
            
        Returns:
            The updated pet state
        """
        # Create a copy of the state to avoid modifying the original
        updated_state = pet_state.copy()
        
        # Apply the action
        if action == "feed":
            updated_state["hunger"] = min(10, updated_state["hunger"] + 2)
        elif action == "play":
            updated_state["happiness"] = min(10, updated_state["happiness"] + 2)
            # Playing also makes the pet hungry and tired
            updated_state["hunger"] = max(1, updated_state["hunger"] - 1)
            updated_state["energy"] = max(1, updated_state["energy"] - 1)
        elif action == "rest":
            updated_state["energy"] = min(10, updated_state["energy"] + 2)
        
        # Update the mood based on the new state
        updated_state["mood"] = self._determine_mood(updated_state)
        
        return updated_state
    
    def apply_event_effects(self, pet_state: Dict[str, Any], effects: Dict[str, int]) -> Dict[str, Any]:
        """
        Apply event effects to the pet state.
        
        Args:
            pet_state: The current pet state
            effects: The effects to apply
            
        Returns:
            The updated pet state
        """
        # Create a copy of the state to avoid modifying the original
        updated_state = pet_state.copy()
        
        # Apply the effects
        for stat, effect in effects.items():
            if stat in updated_state:
                updated_state[stat] = max(1, min(10, updated_state[stat] + effect))
        
        # Update the mood based on the new state
        updated_state["mood"] = self._determine_mood(updated_state)
        
        return updated_state
    
    def _determine_mood(self, pet_state: Dict[str, Any]) -> str:
        """
        Determine the pet's mood based on its state.
        
        Args:
            pet_state: The pet state
            
        Returns:
            The pet's mood
        """
        if pet_state["hunger"] < 3:
            return "hungry"
        elif pet_state["energy"] < 3:
            return "tired"
        elif pet_state["happiness"] < 3:
            return "sad"
        else:
            return "happy"
    
    def reset_pet_data(self) -> bool:
        """
        Reset pet data by deleting the data file.
        
        Returns:
            True if reset was successful, False otherwise
        """
        try:
            if os.path.exists(PET_DATA_FILE):
                os.remove(PET_DATA_FILE)
            return True
        except Exception as e:
            logger.error(f"Failed to reset pet data: {str(e)}")
            return False 