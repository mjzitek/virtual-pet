"""
LLM Integration Module for Virtual Pet Application

This module handles all interactions with OpenAI's API, specifically for generating
structured outputs for pet events and scenarios.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class LLMManager:
    """
    Manages interactions with the OpenAI API for structured outputs.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM Manager.
        
        Args:
            model: The OpenAI model to use (default: gpt-4o-mini)
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"LLM Manager initialized with model: {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=True
    )
    def generate_structured_output(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        response_schema: Dict[str, Any],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a structured output from the LLM based on the provided schema.
        
        Args:
            system_prompt: The system prompt to guide the model's behavior
            user_prompt: The user prompt containing the specific request
            response_schema: JSON schema defining the structure of the expected response
            temperature: Controls randomness (0-1, lower is more deterministic)
            
        Returns:
            A dictionary containing the structured response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "generate_structured_output",
                        "description": "Generate a structured output based on the schema",
                        "parameters": response_schema
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "generate_structured_output"}}
            )
            
            # Extract the structured output from the response
            if response.choices and response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                structured_output = json.loads(tool_call.function.arguments)
                return structured_output
            else:
                # Fallback to parsing the content directly if tool calls aren't available
                content = response.choices[0].message.content
                if content:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse response as JSON: {content}")
                
                logger.error("No structured output found in response")
                return {"error": "No structured output found in response"}
                
        except Exception as e:
            logger.error(f"Error generating structured output: {str(e)}")
            raise
    
    def generate_pet_event(self, pet_state: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a pet event based on the current pet state.
        This is a placeholder method that will be implemented with specific prompts later.
        
        Args:
            pet_state: The current state of the pet
            schema: The schema for the structured output
            
        Returns:
            A structured event for the pet
        """
        # This is a placeholder - you'll implement the specific prompts later
        system_prompt = "You are an AI assistant that generates events for a virtual pet application."
        user_prompt = f"Generate an event for a pet with the following state: {json.dumps(pet_state)}"
        
        return self.generate_structured_output(system_prompt, user_prompt, schema)


# Example usage (for reference, not executed)
if __name__ == "__main__":
    # Example schema for a pet event
    example_schema = {
        "type": "object",
        "properties": {
            "event_type": {
                "type": "string",
                "enum": ["random", "weather", "time_based", "stat_based"]
            },
            "title": {"type": "string"},
            "description": {"type": "string"},
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "effect": {
                            "type": "object",
                            "properties": {
                                "hunger": {"type": "integer"},
                                "energy": {"type": "integer"},
                                "happiness": {"type": "integer"}
                            }
                        }
                    }
                }
            }
        },
        "required": ["event_type", "title", "description", "options"]
    }
    
    # Example pet state
    example_pet_state = {
        "hunger": 3,
        "energy": 7,
        "happiness": 5,
        "mood": "neutral"
    }
    
    # Example usage (commented out)
    # llm_manager = LLMManager()
    # event = llm_manager.generate_pet_event(example_pet_state, example_schema)
    # print(json.dumps(event, indent=2)) 