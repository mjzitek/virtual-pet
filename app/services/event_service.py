"""
Event Service for Virtual Pet Application

This module manages the generation and handling of events for the virtual pet.
It integrates with the LLM to create dynamic scenarios and events.
"""

import random
import logging
from typing import Dict, Any, Optional

from app.services.llm_service import LLMService
from app.models.schemas import PET_EVENT_SCHEMA, PET_REACTION_SCHEMA, PET_TIP_SCHEMA
from app.config.settings import (
    EVENT_COOLDOWN_MIN, EVENT_COOLDOWN_MAX,
    EVENT_CHANCE_NORMAL, EVENT_CHANCE_CRITICAL,
    CRITICAL_STAT_THRESHOLD
)

# Configure logging
logger = logging.getLogger(__name__)

class EventService:
    """
    Manages the generation and handling of events for the virtual pet.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the Event Service.
        
        Args:
            model: The OpenAI model to use (optional)
        """
        try:
            self.llm_service = LLMService(model=model) if model else LLMService()
            self.event_cooldown = 0  # Number of interactions before next event
            logger.info("Event Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Event Service: {str(e)}")
            self.llm_service = None
    
    def is_llm_available(self) -> bool:
        """Check if the LLM service is available."""
        return self.llm_service is not None
    
    def should_trigger_event(self, pet_state: Dict[str, Any]) -> bool:
        """
        Determine if an event should be triggered based on pet state and cooldown.
        
        Args:
            pet_state: The current state of the pet
            
        Returns:
            True if an event should be triggered, False otherwise
        """
        # Decrement cooldown if it's active
        if self.event_cooldown > 0:
            self.event_cooldown -= 1
            return False
        
        # Check if any stat is critically low
        critical_stats = [
            pet_state["hunger"] < CRITICAL_STAT_THRESHOLD,
            pet_state["energy"] < CRITICAL_STAT_THRESHOLD,
            pet_state["happiness"] < CRITICAL_STAT_THRESHOLD
        ]
        
        # Higher chance of event if stats are critical
        if any(critical_stats):
            chance = EVENT_CHANCE_CRITICAL
        else:
            chance = EVENT_CHANCE_NORMAL
        
        # Random chance to trigger an event
        should_trigger = random.random() < chance
        
        if should_trigger:
            # Set cooldown for next event
            self.event_cooldown = random.randint(EVENT_COOLDOWN_MIN, EVENT_COOLDOWN_MAX)
            
        print(f"Should trigger: {should_trigger}")
        return should_trigger
    
    def generate_story(self, pet_state: Dict[str, Any], pet_type: str, pet_name: str) -> Optional[Dict[str, Any]]:
        """
        Generate a story based on the current pet state.
        """
        if not self.is_llm_available():
            logger.warning("LLM Service not available, cannot generate story")
            return None
        
        try:
            # This is a placeholder - you'll implement the specific prompts later
            system_prompt = "You are an AI assistant that generates stories for a virtual pet application."
            user_prompt = f"""Generate a base story for a {pet_type} named {pet_name}.s

            Generate a story that is 2-3 paragraphs long.  Make it fun and engaging.
            
            Create an engaging scenario with 2 options for the user to choose from.  Use JSON format.

            Set stats to following:
            - Hunger: 8/10
            - Energy: 8/10
            - Happiness: 8/10
            - Current mood: happys
            """
            print(user_prompt)
            
            event_data = self.llm_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=PET_EVENT_SCHEMA
            )
            
            print(event_data)

            logger.info(f"Generated event: {event_data.get('title', 'Unknown event')}")
            return event_data
        except Exception as e:
            logger.error(f"Failed to generate event: {str(e)}")
            return None
    
    def generate_event(self, pet_state: Dict[str, Any], pet_type: str, pet_name: str) -> Optional[Dict[str, Any]]:
        """
        Generate an event based on the current pet state.
        
        Args:
            pet_state: The current state of the pet
            pet_type: The type of pet (e.g., "cat", "dog")
            pet_name: The name of the pet
            
        Returns:
            A dictionary containing the event data, or None if generation fails
        """
        if not self.is_llm_available():
            logger.warning("LLM Service not available, cannot generate event")
            return None
        
        try:
            # This is a placeholder - you'll implement the specific prompts later
            system_prompt = "You are an AI assistant that generates events for a virtual pet application."
            user_prompt = f"""
            Generate an event for a {pet_type} named {pet_name} with the following state:
            - Hunger: {pet_state['hunger']}/10
            - Energy: {pet_state['energy']}/10
            - Happiness: {pet_state['happiness']}/10
            - Current mood: {pet_state['mood']}
            
            Create an engaging scenario with 2 options for the user to choose from.

            Response in JSON format.
            """

            print(user_prompt)
            
            event_data = self.llm_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=PET_EVENT_SCHEMA
            )
            
            print(event_data)

            logger.info(f"Generated event: {event_data.get('title', 'Unknown event')}")
            return event_data
        except Exception as e:
            logger.error(f"Failed to generate event: {str(e)}")
            return None
    
    def handle_event_choice(self, event: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Handle the user's choice for an event.
        
        Args:
            event: The event data
            choice_index: The index of the chosen option
            
        Returns:
            A dictionary with the effects to apply to the pet state
        """
        if not event or "options" not in event or choice_index >= len(event["options"]):
            logger.error("Invalid event or choice index")
            return {"hunger": 0, "energy": 0, "happiness": 0}
        
        chosen_option = event["options"][choice_index]
        return chosen_option["effect"] 