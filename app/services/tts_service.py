"""
Text-to-Speech Service Module for Virtual Pet Application

This module handles interactions with OpenAI's Text-to-Speech API to convert
story text into audio that can be played back to the user.
"""

import logging
import os
import hashlib
from typing import Optional, Dict, Any, List
from pathlib import Path

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config.settings import OPENAI_API_KEY, APP_DIR

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
AUDIO_DIR = APP_DIR / "static" / "audio"
GENERATED_AUDIO_DIR = AUDIO_DIR / "generated"
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(GENERATED_AUDIO_DIR, exist_ok=True)

# Available voices for TTS - include all voices including sage
AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "sage"]
DEFAULT_VOICE = "sage"  # Use sage as the default voice
DEFAULT_MODEL = "tts-1"

class TTSService:
    """
    Manages interactions with the OpenAI Text-to-Speech API.
    """
    
    def __init__(self, model: str = DEFAULT_MODEL, voice: str = DEFAULT_VOICE):
        """
        Initialize the TTS Service.
        
        Args:
            model: The OpenAI TTS model to use
            voice: The voice to use for speech generation
        """
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.voice = voice
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"TTS Service initialized with model: {model}, voice: {voice}")
        
    def _generate_cache_key(self, text: str, voice: str) -> str:
        """
        Generate a cache key for the given text and voice.
        
        Args:
            text: The text to convert to speech
            voice: The voice to use
            
        Returns:
            A unique hash to use as a filename
        """
        # Create a hash of the text and voice to use as a cache key
        content_hash = hashlib.md5(f"{text}_{voice}".encode()).hexdigest()
        return content_hash
    
    def _get_cached_audio_path(self, cache_key: str) -> Optional[str]:
        """
        Check if an audio file exists in the cache for the given key.
        
        Args:
            cache_key: The cache key to check
            
        Returns:
            The path to the cached audio file if it exists, None otherwise
        """
        cached_file_path = GENERATED_AUDIO_DIR / f"{cache_key}.mp3"
        if cached_file_path.exists():
            logger.info(f"Found cached audio file: {cached_file_path}")
            return str(cached_file_path)
        return None
    
    def format_story_for_speech(
        self,
        description: str,
        pet_name: str,
        options: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Format the story description and options into a natural, conversational format.
        
        Args:
            description: The story description
            pet_name: The name of the pet
            options: List of options for the user to choose from
            
        Returns:
            Formatted text ready for speech conversion
        """
        try:
            # Create a system prompt for formatting the text
            system_prompt = """
            You are an expert at formatting text for text-to-speech systems. 
            Your task is to take a story description and options and format them 
            into a natural, conversational format that sounds good when read aloud.
            
            Make sure to:
            1. Keep the original meaning and content intact
            2. Format options as a clear question with numbered choices
            3. Use natural language and phrasing that sounds good when spoken
            4. Avoid complex punctuation that might confuse TTS systems
            5. Keep the text concise but engaging
            """
            
            # Create the user prompt with the story and options
            user_prompt = f"Story description: {description}\n\nPet name: {pet_name}"
            
            if options and len(options) > 0:
                user_prompt += "\n\nOptions for what to do next:"
                for i, option in enumerate(options):
                    user_prompt += f"\n{i+1}. {option['text']}"
                
                user_prompt += "\n\nPlease format this into a natural, conversational text that includes both the story and a question about what the pet should do next, with the numbered options."
            else:
                user_prompt += "\n\nPlease format this into a natural, conversational text that sounds good when read aloud."
            
            # Call the OpenAI API to format the text
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            formatted_text = response.choices[0].message.content
            logger.info("Successfully formatted story text for speech")
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting story for speech: {str(e)}")
            
            # Fallback to a simple format if the LLM call fails
            formatted_text = description
            
            if options and len(options) > 0:
                formatted_text += f"\n\nWhat should {pet_name} do next? "
                for i, option in enumerate(options):
                    formatted_text += f"\nOption {i+1}: {option['text']}"
            
            return formatted_text
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=True
    )
    def generate_speech(
        self, 
        text: str, 
        voice: Optional[str] = None,
        session_id: Optional[str] = None,
        filename: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Generate speech from text and save it to a file.
        
        Args:
            text: The text to convert to speech
            voice: The voice to use (defaults to the instance voice)
            session_id: Optional session ID to include in the filename
            filename: Optional custom filename
            use_cache: Whether to use cached audio files (default: True)
            
        Returns:
            The path to the generated audio file
        """
        if voice is None:
            voice = self.voice
            
        # For 'sage' voice, we'll force it even if it's not in our list
        # This is because the user specifically requested it
        if voice == "sage":
            # We'll use sage regardless of whether it's in our list
            pass
        elif voice not in AVAILABLE_VOICES:
            logger.warning(f"Voice {voice} not in available voices list {AVAILABLE_VOICES}, using default voice {DEFAULT_VOICE}")
            voice = DEFAULT_VOICE
            
        # Truncate text if it's too long (OpenAI has a limit)
        max_chars = 4096
        if len(text) > max_chars:
            logger.warning(f"Text exceeds maximum length of {max_chars} characters. Truncating.")
            text = text[:max_chars]
            
        try:
            # Check if we have a cached version of this audio
            if use_cache:
                cache_key = self._generate_cache_key(text, voice)
                cached_path = self._get_cached_audio_path(cache_key)
                if cached_path:
                    return cached_path
            
            # Generate a filename if not provided
            if not filename:
                if use_cache:
                    # Use the cache key as the filename
                    cache_key = self._generate_cache_key(text, voice)
                    filename = f"{cache_key}.mp3"
                elif session_id:
                    filename = f"story_{session_id}.mp3"
                else:
                    import uuid
                    filename = f"story_{uuid.uuid4()}.mp3"
            
            # Ensure filename has .mp3 extension
            if not filename.endswith('.mp3'):
                filename += '.mp3'
                
            file_path = GENERATED_AUDIO_DIR / filename
            
            # Generate speech and save to file
            logger.info(f"Generating speech with voice: {voice}")
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text
            )
            
            response.stream_to_file(str(file_path))
            
            logger.info(f"Generated speech saved to {file_path}")
            return str(file_path)
                
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            raise
    
    def get_available_voices(self) -> list:
        """
        Get the list of available voices.
        
        Returns:
            A list of available voice options
        """
        return AVAILABLE_VOICES 