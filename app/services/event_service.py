"""
Event Service for Virtual Pet Application

This module manages the generation and handling of events for the virtual pet.
It integrates with the LLM to create dynamic scenarios and events.
"""

import random
import logging
from typing import Dict, Any, Optional, List

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
            user_prompt = f"""Generate a base story for a {pet_type} named {pet_name}.

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
    
    def generate_summary(self, previous_events: List[str]) -> str:
        """
        Generate a summary of the previous events.
        
        Args:
            previous_events: List of previous events to summarize
            
        Returns:
            A string containing a summary of the events, or None if generation fails
        """
        if not self.is_llm_available():
            logger.warning("LLM Service not available, cannot generate summary")
            return "Previous events could not be summarized due to LLM unavailability."
        
        try:
            # Format the events for the prompt, with truncated descriptions
            formatted_events = []
            for event in previous_events:
                # Extract and format the key components
                if "Description: " in event and " - Chose: " in event:
                    # Split into parts
                    title_part = event.split(" - Description: ")[0]
                    description_part = event.split(" - Description: ")[1].split(" - Chose: ")[0]
                    choice_part = "Chose: " + event.split(" - Chose: ")[1]
                    
                    # Truncate description if it's too long for the prompt
                    if len(description_part) > 150:
                        description_part = description_part[:150] + "..."
                        
                    # Reassemble with truncated description
                    formatted_event = f"{title_part} - {description_part} - {choice_part}"
                    formatted_events.append(formatted_event)
                else:
                    formatted_events.append(event)
            
            # Format the events as a numbered list for the prompt
            events_text = "\n".join([f"{i+1}. {event}" for i, event in enumerate(formatted_events)])
            
            system_prompt = "You are an AI assistant that generates summaries of events for a virtual pet application."
            user_prompt = f"""
            Generate a concise summary of the following events in the pet's history.
            Focus on the most important events and their outcomes.
            Keep the summary under 200 words and make it a cohesive narrative.
            
            Events to summarize:
            {events_text}
            """
            
            logger.info(f"Generating summary of {len(previous_events)} previous events")
            
            # Define a simple schema for the summary
            summary_schema = {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A concise summary of the previous events"
                    }
                },
                "required": ["summary"]
            }
            
            summary_data = self.llm_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=summary_schema
            )
            
            logger.info("Generated summary of previous events")
            
            # Check if we got a valid summary
            if summary_data and "summary" in summary_data:
                return summary_data["summary"]
            else:
                logger.warning("Failed to generate a proper summary, using fallback")
                return f"The pet has experienced various events including {', '.join([e.split(' - ')[0] for e in previous_events[-5:]])}."
                
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            # Provide a more useful fallback summary
            return f"The pet has experienced various events including {', '.join([e.split(' - ')[0] for e in previous_events[-5:]])}."
    
    def generate_event(self, pet_state: Dict[str, Any], pet_type: str, pet_name: str, previous_events: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate an event based on the current pet state.
        
        Args:
            pet_state: The current state of the pet
            pet_type: The type of pet (e.g., "cat", "dog")
            pet_name: The name of the pet
            previous_events: List of previous events/actions to provide context
            
        Returns:
            A dictionary containing the event data, or None if generation fails
        """
        if not self.is_llm_available():
            logger.warning("LLM Service not available, cannot generate event")
            return None
        
        try:
            # Format the previous events context
            previous_events_context = ""
            if previous_events and len(previous_events) > 0:
                # If we have too many events, generate a summary
                if len(previous_events) > 10:
                    logger.info(f"Generating summary for {len(previous_events)} events")
                    summary = self.generate_summary(previous_events)
                    previous_events_context = f"Summary of previous events:\n{summary}"
                else:
                    # Otherwise, include the full events
                    previous_events_context = "\n"
                    for i, event in enumerate(previous_events):
                        # For the prompt, we need to format the event to a reasonable length
                        # Extract the key components
                        formatted_event = event
                        if "Description: " in event and " - Chose: " in event:
                            # Split into parts
                            title_part = event.split(" - Description: ")[0]
                            description_part = event.split(" - Description: ")[1].split(" - Chose: ")[0]
                            choice_part = "Chose: " + event.split(" - Chose: ")[1]
                                
                            # Reassemble with truncated description
                            formatted_event = f"{title_part} - Description: {description_part} - {choice_part}"
                            
                        previous_events_context += f"{i+1}. {formatted_event}\n"
            
            # This is a placeholder - you'll implement the specific prompts later
            system_prompt = "You are an AI assistant that generates events for a virtual pet application."
            user_prompt = f"""
            Generate an event for a {pet_type} named {pet_name} with the following state:
            - Hunger: {pet_state['hunger']}/10
            - Energy: {pet_state['energy']}/10
            - Happiness: {pet_state['happiness']}/10
            - Current mood: {pet_state['mood']}
            
            INSTRUCTIONS:
            - Create an engaging scenario with 2 options for the user to choose from.
            - Make the story fun and engaging.
            - Look at the previous events and make the next event is relevant to the previous events and the story overall.
            - Pay attention to the pet's stats and make sure the next choices reflect this.  
                - If any are too low you might have to force choices that will help them.  For example if energy is too low (1) you might have to force a rest choice.  You cannot allow the stats to go below 0.
                - You can do something like take a short nap to gain a little energy or take a longer nap to gain more energy.
            - Analyze your story and choices and make sure they make sense based on previous instructions.

            Response in JSON format.
            """
            
            # Add previous events context if available
            if previous_events_context:
                user_prompt += f"""
            ---
            <previous_events>
            {previous_events_context}
            </previous_events>
            ---
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