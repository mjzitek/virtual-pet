"""
LLM Service Module for Virtual Pet Application

This module handles all interactions with OpenAI's API, specifically for generating
structured outputs for pet events and scenarios.
"""

import json
import logging
from typing import Dict, Any, Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config.settings import OPENAI_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE

# Configure logging
logger = logging.getLogger(__name__)

class LLMService:
    """
    Manages interactions with the OpenAI API for structured outputs.
    """
    
    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
        """
        Initialize the LLM Service.
        
        Args:
            model: The OpenAI model to use
            temperature: Controls randomness (0-1, lower is more deterministic)
        """
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"LLM Service initialized with model: {model}")
    
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
        temperature: Optional[float] = None
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
        if temperature is None:
            temperature = self.temperature
            
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