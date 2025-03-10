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
from app.data.story_starters import STORY_STARTERS
import streamlit as st

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
            return self._generate_fallback_story(pet_name)
        
        try:
            # Select a random story starter
            story_starter = random.choice(STORY_STARTERS)
            location = story_starter["location"]
            scenario = story_starter["scenario"]
            
            # Check if young reader mode is enabled
            young_reader_mode = st.session_state.get("young_reader_mode", False)
            
            # Adjust the system prompt based on reading level
            if young_reader_mode:
                system_prompt = """You are an AI assistant that generates stories for young children (ages 4-6) in a virtual pet application.
                Your stories should:
                - Use simple vocabulary appropriate for young readers
                - Have short sentences (5-8 words per sentence)
                - Be brief (2-3 very short paragraphs)
                - Include repetition and simple sentence structures
                - Focus on concrete concepts rather than abstract ones
                - Use sound words that children enjoy (like "splash", "zoom", "meow")
                - Be fun, engaging, and easy to understand
                """
            else:
                system_prompt = "You are an AI assistant that generates stories for a virtual pet application."
            
            # Adjust the user prompt based on reading level
            if young_reader_mode:
                user_prompt = f"""Generate a simple story for young children (ages 4-6) about a {pet_type} named {pet_name}.

                STORY STARTER:
                Place: {location}
                What happens: {scenario}

                Make a very short story (2-3 small paragraphs) with simple words. 
                Use short sentences that are easy for young children to understand.
                Include fun sounds like "meow", "woof", or "splash".
                
                Create 2 very simple choices for the child to pick from. Use JSON format.

                Set stats to following:
                - Hunger: 8/10
                - Energy: 8/10
                - Happiness: 8/10
                - Current mood: happy
                """
            else:
                user_prompt = f"""Generate a base story for a {pet_type} named {pet_name}.

                STORY STARTER:
                Location: {location}
                Scenario: {scenario}

                Using the story starter above, generate a story that is 2-3 paragraphs long. Make it fun and engaging.
                
                Create an engaging scenario with 2 options for the user to choose from. Use JSON format.

                Set stats to following:
                - Hunger: 8/10
                - Energy: 8/10
                - Happiness: 8/10
                - Current mood: happy
                """
            print(user_prompt)
            
            event_data = self.llm_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=PET_EVENT_SCHEMA
            )
            
            print(event_data)

            logger.info(f"Generated event: {event_data.get('title', 'Unknown event')}")
            
            # Generate an image for the event
            if event_data and "description" in event_data:
                try:
                    image_url = self.generate_image(
                        pet_type=pet_type,
                        pet_name=pet_name,
                        pet_state=pet_state.get("mood", "happy"),
                        event_description=event_data["description"]
                    )
                    if image_url:
                        event_data["image_url"] = image_url
                except Exception as e:
                    logger.error(f"Failed to generate image for event: {str(e)}")
            
            return event_data
        except Exception as e:
            logger.error(f"Failed to generate event: {str(e)}")
            return self._generate_fallback_story(pet_name)
    
    def generate_story_title(self, pet_name: str, pet_type: str, current_event: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a title for the pet's story.
        
        Args:
            pet_name: The name of the pet
            pet_type: The type of pet (e.g., "cat", "dog")
            current_event: The current event data (optional)
            
        Returns:
            A string containing the generated title
        """
        if not self.is_llm_available():
            logger.warning("LLM Service not available, cannot generate story title")
            return f"{pet_name}'s Great Adventure"
        
        try:
            # Extract event description if available
            event_description = ""
            if current_event and "description" in current_event:
                event_description = f"Current situation: {current_event['description']}"
                print(f"Debug - Using event description: {event_description[:50]}...")
            else:
                print("Debug - No event description available")
            
            # Check if young reader mode is enabled
            young_reader_mode = st.session_state.get("young_reader_mode", False)
            
            # Create the system prompt based on reading level
            if young_reader_mode:
                system_prompt = (
                    "You are a creative title generator for a virtual pet game for young children (ages 4-6). "
                    "Generate a very short, simple title for the pet's adventure. "
                    "The title should be 2-4 words, include the pet's name, and be easy for young children to read. "
                    "Use simple, familiar words that a 4-6 year old would understand."
                )
            else:
                system_prompt = (
                    "You are a creative title generator for a virtual pet game. "
                    "Generate a short, catchy, and playful title for the pet's adventure. "
                    "The title should be 3-7 words, incorporate the pet's name, and possibly include "
                    "a pun or wordplay related to the type of pet. Make it fun and engaging!"
                )
            
            # Create the user prompt based on reading level
            if young_reader_mode:
                user_prompt = (
                    f"Create a simple title for {pet_name} the {pet_type}'s adventure. "
                    f"The title must include the name '{pet_name}' and use very simple words. "
                    f"{event_description} "
                    f"Return output in JSON format."
                )
            else:
                user_prompt = (
                    f"Create a title for {pet_name} the {pet_type}'s adventure. "
                    f"The title must include the name '{pet_name}' and should be fun and playful. "
                    f"{event_description} "
                    f"Return output in JSON format."
                )
            
            print(f"Debug - User prompt: {user_prompt}")
            
            # Define a simple schema for the title
            title_schema = {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A short, catchy title for the pet's adventure"
                    }
                },
                "required": ["title"]
            }
            
            # Generate the title
            print("Debug - Calling LLM service to generate title")
            response = self.llm_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=title_schema,
                temperature=0.8  # Slightly higher temperature for creativity
            )
            
            # Extract the title from the response
            if response and "title" in response and response["title"]:
                title = response["title"].strip()
                # Ensure the pet's name is in the title
                if pet_name not in title:
                    title = f"{pet_name}'s {title}"
                print(f"Debug - Generated title: {title}")
                return title
            else:
                print(f"Debug - Invalid response from LLM, using default title")
                return f"{pet_name}'s Great Adventure"
                
        except Exception as e:
            logger.error(f"Failed to generate story title: {str(e)}")
            print(f"Debug - Error generating title: {str(e)}")
            return f"{pet_name}'s Great Adventure"
    
    def _generate_fallback_story(self, pet_name: str) -> Dict[str, Any]:
        """
        Generate a fallback story when the LLM service is not available.
        
        Args:
            pet_name: The name of the pet
            
        Returns:
            A dictionary with a basic story structure
        """
        logger.info("Generating fallback story")
        
        # Create a simple fallback story
        return {
            "title": f"{pet_name}'s Day Out",
            "description": f"{pet_name} is having a lovely day exploring the neighborhood. The sun is shining and there's a gentle breeze in the air.",
            "options": [
                {
                    "text": "Go to the park",
                    "effect": {"happiness": 1, "energy": -1, "hunger": -1}
                },
                {
                    "text": "Take a nap",
                    "effect": {"energy": 2, "happiness": -1, "hunger": 0}
                },
                {
                    "text": "Look for food",
                    "effect": {"hunger": 2, "energy": -1, "happiness": 0}
                }
            ]
        }
    
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
            
            # Check if young reader mode is enabled
            young_reader_mode = st.session_state.get("young_reader_mode", False)
            
            # Adjust the system prompt based on reading level
            if young_reader_mode:
                system_prompt = """You are an AI assistant that generates stories for young children (ages 4-6) in a virtual pet application.
                Your stories should:
                - Use simple vocabulary appropriate for young readers
                - Have short sentences (5-8 words per sentence)
                - Be brief (2-3 very short paragraphs)
                - Include repetition and simple sentence structures
                - Focus on concrete concepts rather than abstract ones
                - Use sound words that children enjoy (like "splash", "zoom", "meow")
                - Be fun, engaging, and easy to understand
                """
            else:
                system_prompt = "You are an AI assistant that generates events for a virtual pet application."
            
            # Adjust the user prompt based on reading level
            if young_reader_mode:
                user_prompt = f"""
                Generate a simple story for young children (ages 4-6) about a {pet_type} named {pet_name}.
                
                Pet's current state:
                - Hunger: {pet_state['hunger']}/10
                - Energy: {pet_state['energy']}/10
                - Happiness: {pet_state['happiness']}/10
                
                {previous_events_context}
                
                - Make a very short story (2-3 small paragraphs) with simple words. 
                - Use short sentences that are easy for young children to understand.
                - Include fun sounds like "meow", "woof", or "splash".
                - Don't repeat the same words constantly.  Avoid repeating words like 'happy, happy, happy'.
                
                Create 2 very simple choices for the child to pick from.
                
                Return your response in this JSON format:
                {{
                    "title": "A short, fun title",
                    "description": "The story text here",
                    "image_prompt": "A short description for generating an image",
                    "options": [
                        {{
                            "text": "First choice (simple words)",
                            "effect": {{
                                "hunger": 0,
                                "energy": 0,
                                "happiness": 0
                            }}
                        }},
                        {{
                            "text": "Second choice (simple words)",
                            "effect": {{
                                "hunger": 0,
                                "energy": 0,
                                "happiness": 0
                            }}
                        }}
                    ]
                }}
                """
            else:
                user_prompt = f"""
                Generate an event for a {pet_type} named {pet_name} with the following state:
                - Hunger: {pet_state['hunger']}/10
                - Energy: {pet_state['energy']}/10
                - Happiness: {pet_state['happiness']}/10
                
                {previous_events_context}
                
                Create an engaging scenario with 2 options for the user to choose from.
                
                Return your response in this JSON format:
                {{
                    "title": "A descriptive title for the event",
                    "description": "A detailed description of the event (2-3 paragraphs)",
                    "image_prompt": "A detailed description for generating an image of this event",
                    "options": [
                        {{
                            "text": "First option description",
                            "effect": {{
                                "hunger": 0,
                                "energy": 0,
                                "happiness": 0
                            }}
                        }},
                        {{
                            "text": "Second option description",
                            "effect": {{
                                "hunger": 0,
                                "energy": 0,
                                "happiness": 0
                            }}
                        }}
                    ]
                }}
                """

            print(user_prompt)
            
            event_data = self.llm_service.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=PET_EVENT_SCHEMA
            )
            
            print(event_data)

            logger.info(f"Generated event: {event_data.get('title', 'Unknown event')}")
            
            # Generate an image for the event
            if event_data and "description" in event_data:
                try:
                    image_url = self.generate_image(
                        pet_type=pet_type,
                        pet_name=pet_name,
                        pet_state=pet_state.get("mood", "happy"),
                        event_description=event_data["description"]
                    )
                    if image_url:
                        event_data["image_url"] = image_url
                except Exception as e:
                    logger.error(f"Failed to generate image for event: {str(e)}")
            
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
    

    def generate_image(self, pet_type: str, pet_name: str, pet_state: str, event_description: str):
        """
        Generate an image based on the current pet state and event description.
        
        Args:
            pet_type: The type of pet (e.g., "cat", "dog")
            pet_name: The name of the pet
            pet_state: The current mood of the pet
            event_description: The description of the event
            
        Returns:
            The URL of the generated image, or None if generation fails
        """
        if not self.is_llm_available():
            logger.warning("LLM Service not available, cannot generate image")
            return None
        
        # Customize the image description based on pet type
        pet_description = ""
        if pet_type.lower() == "cat":
            pet_description = f"""A vibrant, energetic, and whimsical illustration of a cartoonish orange cat with a {pet_state} expression. 
            The cat has a fluffy fur coat, with individual strands sticking out playfully. 
            Its fur is a mix of warm orange and yellow hues, with subtle shading and highlights adding depth and texture. 
            The cat's face is highly expressive, with oversized, gleaming blue eyes that are wide open, exuding joy and excitement. 
            The whiskers are long and slightly curved, giving a sense of movement and liveliness."""
        elif pet_type.lower() == "dog":
            pet_description = f"a playful, friendly dog with a wagging tail and a {pet_state} expression"
        elif pet_type.lower() == "rabbit":
            pet_description = f"a small, furry rabbit with long ears and a {pet_state} expression"
        else:
            pet_description = f"a cute, animated {pet_type} with a {pet_state} expression"
        
        prompt = f"""Generate an image of {pet_name} the {pet_type} based on the following story.

        BASE IMAGE DESCRIPTION:
        {pet_description}s

        The scene should be colorful and engaging, with a light background that enhances the brightness of the overall image.
        The pet should be the main focus of the image, with its body language and facial expression conveying its current mood.
        The overall image should be fun and whimsical.  The pet should be cute and adorable.

        STORY CONTEXT:
        {event_description}
        
        Make sure the image reflects the story context and the pet's current mood ({pet_state}).
        """

        try:
            image_url = self.llm_service.generate_image(prompt)
            print(f"Generated image URL: {image_url}")
            return image_url
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None
    