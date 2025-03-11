"""
Virtual Pet Application - Main Entry Point

This is the main entry point for the Virtual Pet Application.
It sets up the Streamlit UI and handles user interactions.
"""

import os
import sys
import json
import uuid
import base64
import logging
import threading
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

import streamlit as st
from PIL import Image

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import services
from app.services.tts_service import TTSService
from app.services.pet_service import PetService
from app.services.event_service import EventService
from app.services.llm_service import LLMService
from app.config.settings import APP_DIR, DEFAULT_PET_STATS
from app.data.pet_names import get_random_name

# Initialize services
tts_service = TTSService()
pet_service = PetService()
event_service = EventService()
llm_service = LLMService()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to play the generated audio
def generate_and_play_audio(event: Dict[str, Any]):
    """
    Generate and play audio for an event.
    
    Args:
        event: The current event containing description and options
    """
    try:
        # Set a flag to indicate we're generating audio
        # This will prevent the UI from going blank during generation
        st.session_state["generating_audio"] = True
        
        # Generate a unique identifier for this event
        event_id = f"{event.get('id', '')}"
        if not event_id:
            # If the event doesn't have an ID, create one from the description
            import hashlib
            event_id = hashlib.md5(event["description"].encode()).hexdigest()[:10]
        
        # Format the story text and options for speech
        options_to_include = event.get("options", [])
        formatted_text = tts_service.format_story_for_speech(
            description=event["description"],
            pet_name=st.session_state["pet_name"],
            options=options_to_include
        )
        
        # Generate the audio synchronously with a spinner
        with st.spinner("Generating audio..."):
            audio_path = tts_service.generate_speech(
                text=formatted_text,
                voice="sage",  # Use sage voice as requested
                use_cache=True  # Use caching
            )
            
            logger.info(f"Generated audio: {audio_path}")
        
        # Check if the file exists
        if not os.path.exists(audio_path):
            logger.error(f"Audio file does not exist: {audio_path}")
            st.error("Audio file not found. Please try again.")
            # Clear the generating flag
            st.session_state.pop("generating_audio", None)
            return
        
        # Get the file size for debugging
        file_size = os.path.getsize(audio_path)
        logger.info(f"Audio file size: {file_size} bytes")
        
        # Read the audio file and encode it as base64
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # Create an HTML audio element that autoplays without showing controls
        audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        
        # Display the audio player (hidden)
        st.markdown(audio_html, unsafe_allow_html=True)
        
        # Show a success message with more visibility
        st.markdown("<div style='text-align:center; padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; margin: 10px 0;'><h4>🔊 Playing audio narration...</h4></div>", unsafe_allow_html=True)
        
        # Clear the generating flag
        st.session_state.pop("generating_audio", None)
        
    except Exception as e:
        st.error(f"Error playing audio: {str(e)}")
        logger.error(f"Error playing audio: {str(e)}")
        # Clear the generating flag
        st.session_state.pop("generating_audio", None)

# Initialize session state
def initialize_session_state():
    """Initialize or restore session state."""
    # Check if we have a session ID in the session state or query parameters
    if 'session_id' not in st.session_state:
        # Check for existing session ID in query parameters
        session_id_from_params = st.query_params.get("session_id", None)
        
        if session_id_from_params:
            # Use the session ID from the query parameters
            st.session_state["session_id"] = session_id_from_params
            logger.info(f"Restored session ID from URL: {session_id_from_params}")
        else:
            # Generate a new session ID
            st.session_state["session_id"] = str(uuid.uuid4())
            # Update the URL with the session ID
            st.query_params["session_id"] = st.session_state["session_id"]
            logger.info(f"Generated new session ID: {st.session_state['session_id']}")
    
    # Check if we have saved pet data for this session
    saved_data = pet_service.load_pet_data(st.session_state["session_id"])
    print(f"Debug - Loaded saved data: {saved_data is not None}")
    
    if saved_data:
        # Restore from saved data
        for key, value in saved_data.items():
            if key != "last_updated":  # Skip the timestamp
                # Special handling for pet_type to ensure correct case
                if key == "pet_type" and value:
                    correct_pet_key = pet_service._get_pet_key(value)
                    if correct_pet_key:
                        st.session_state[key] = correct_pet_key
                    else:
                        st.session_state[key] = "cat"  # Default to cat if not found
                else:
                    st.session_state[key] = value
                    
        print(f"Debug - Restored story_title from saved data: {st.session_state.get('story_title', 'Not found')}")
        
        # Ensure current_event is initialized even if not in saved data
        if "current_event" not in st.session_state:
            st.session_state["current_event"] = None
            
        # Ensure previous_events is initialized
        if "previous_events" not in st.session_state:
            st.session_state["previous_events"] = []
            
        # Ensure event_summaries is initialized
        if "event_summaries" not in st.session_state:
            st.session_state["event_summaries"] = []
            
        # Ensure event_counter is initialized
        if "event_counter" not in st.session_state:
            st.session_state["event_counter"] = 0
            
        # Ensure story_title is initialized with a valid value
        if "story_title" not in st.session_state or not st.session_state["story_title"]:
            st.session_state["story_title"] = f"{st.session_state['pet_name']}'s Great Adventure"
            # Set flag to regenerate title on next cycle
            st.session_state["regenerate_title"] = True
            print("Debug - Set regenerate_title flag because story_title was missing or empty")
            
        if "base_storyline" not in st.session_state:
            st.session_state["base_storyline"] = ""
            
        if "story_location" not in st.session_state:
            st.session_state["story_location"] = ""
    else:
        # Default initialization
        if "setup_complete" not in st.session_state:
            st.session_state["setup_complete"] = False

        if "pet_name" not in st.session_state:
            st.session_state["pet_name"] = ""

        if "pet_type" not in st.session_state:
            st.session_state["pet_type"] = "cat"  # Default to cat

        if "pet_state" not in st.session_state:
            st.session_state["pet_state"] = DEFAULT_PET_STATS.copy()
            
        if "current_event" not in st.session_state:
            st.session_state["current_event"] = None
            
        # Ensure previous_events is initialized
        if "previous_events" not in st.session_state:
            st.session_state["previous_events"] = []
            
        # Ensure event_summaries is initialized
        if "event_summaries" not in st.session_state:
            st.session_state["event_summaries"] = []
            
        if "event_counter" not in st.session_state:
            st.session_state["event_counter"] = 0
            
        if "story_title" not in st.session_state:
            st.session_state["story_title"] = "Virtual Pet Simulator"
            
        if "regenerate_title" not in st.session_state:
            st.session_state["regenerate_title"] = False
            
        if "base_storyline" not in st.session_state:
            st.session_state["base_storyline"] = ""
            
        if "story_location" not in st.session_state:
            st.session_state["story_location"] = ""

# Function to handle pet setup completion
def complete_setup():
    """Handle pet setup completion."""
    # Get the pet name from the input field
    pet_name = st.session_state.get("pet_name_input", "").strip()
    
    # Validate pet name
    if not pet_name:
        st.error("Please enter a name for your pet.")
        return
    
    # Set the pet name in session state
    st.session_state["pet_name"] = pet_name
    
    # Set the pet type from the selection
    pet_type_display = st.session_state["pet_type_select"]
    available_pets = pet_service.get_available_pets()
    
    # Find the internal key for the selected pet type
    pet_key = None
    for key, display_name in available_pets.items():
        if display_name == pet_type_display:
            pet_key = key
            break
    
    if not pet_key:
        st.error("Invalid pet type selected.")
        return
    
    # Set the pet type in session state
    st.session_state["pet_type"] = pet_key
    
    # Mark setup as complete
    st.session_state["setup_complete"] = True
    
    # Initialize young reader mode if not set
    if "young_reader_mode" not in st.session_state:
        st.session_state["young_reader_mode"] = True
    
    # Generate an initial story for the pet
    try:
        st.session_state["current_event"] = event_service.generate_story(
            pet_state=st.session_state["pet_state"],
            pet_type=st.session_state["pet_type"],
            pet_name=st.session_state["pet_name"]
        )
        
        # Store the initial story description as the base storyline
        if "description" in st.session_state["current_event"]:
            st.session_state["base_storyline"] = st.session_state["current_event"]["description"]
        else:
            st.session_state["base_storyline"] = f"{st.session_state['pet_name']} the {st.session_state['pet_type']} is on an adventure."
        
        # Generate a title for the pet's adventure
        story_title = event_service.generate_story_title(
            pet_name=st.session_state["pet_name"],
            pet_type=st.session_state["pet_type"],
            current_event=st.session_state.get("current_event")
        )
        
        st.session_state["story_title"] = story_title
        print(f"Initial title generated: {story_title}")
        
        # Save the pet data
        pet_data = {
            "pet_name": st.session_state["pet_name"],
            "pet_type": st.session_state["pet_type"],
            "pet_state": st.session_state["pet_state"],
            "setup_complete": st.session_state["setup_complete"],
            "current_event": st.session_state["current_event"],
            "previous_events": st.session_state["previous_events"],
            "event_counter": st.session_state["event_counter"],
            "story_title": st.session_state["story_title"],
            "young_reader_mode": st.session_state.get("young_reader_mode", False),
            "base_storyline": st.session_state["base_storyline"],
            "story_location": st.session_state["story_location"]
        }
        pet_service.save_pet_data(pet_data, st.session_state["session_id"])
        
        # Force a rerun to update the UI with the initial story
        st.rerun()
    except Exception as e:
        st.error(f"Error generating initial story: {str(e)}")
        logger.error(f"Error generating initial story: {str(e)}")
        # Set a basic event to avoid errors
        st.session_state["current_event"] = {
            "description": f"{st.session_state['pet_name']} the {st.session_state['pet_type']} is ready for an adventure!",
            "options": []
        }

# Function to update pet state
def update_pet_state(action):
    """Update the pet's state based on the action taken."""
    # Update the pet's state
    new_state = pet_service.update_pet_state(st.session_state["pet_state"], action)
    st.session_state["pet_state"] = new_state
    
    # Check if an event should be triggered
    should_trigger_event = event_service.should_trigger_event(
        pet_state=new_state,
        action=action,
        event_counter=st.session_state.get("event_counter", 0)
    )
    
    if should_trigger_event:
        # Increment the event counter
        st.session_state["event_counter"] = st.session_state.get("event_counter", 0) + 1
        
        # Generate a new event
        try:
            # Prepare event history context
            event_history = st.session_state.get("previous_events", [])
            event_summaries = st.session_state.get("event_summaries", [])
            
            event = event_service.generate_event(
                pet_state=new_state,
                pet_type=st.session_state["pet_type"],
                pet_name=st.session_state["pet_name"],
                action=action,
                previous_events=event_history,
                event_summaries=event_summaries
            )
            
            # Store the event
            st.session_state["current_event"] = event
            
            # Ensure we have a valid story title
            if "story_title" not in st.session_state or not st.session_state["story_title"]:
                st.session_state["story_title"] = f"{st.session_state['pet_name']}'s Great Adventure"
            
            # Save the updated pet data
            pet_data = {
                "pet_name": st.session_state["pet_name"],
                "pet_type": st.session_state["pet_type"],
                "pet_state": st.session_state["pet_state"],
                "setup_complete": st.session_state["setup_complete"],
                "current_event": st.session_state["current_event"],
                "previous_events": st.session_state.get("previous_events", []),
                "event_summaries": st.session_state.get("event_summaries", []),
                "story_title": st.session_state["story_title"],
                "event_counter": st.session_state.get("event_counter", 0),
                "young_reader_mode": st.session_state.get("young_reader_mode", False),
                "base_storyline": st.session_state.get("base_storyline", ""),
                "story_location": st.session_state["story_location"]
            }
            pet_service.save_pet_data(pet_data, st.session_state["session_id"])
        except Exception as e:
            st.error(f"Error generating event: {str(e)}")
            logger.error(f"Error generating event: {str(e)}")
    else:
        # Save the updated pet data without an event
        pet_data = {
            "pet_name": st.session_state["pet_name"],
            "pet_type": st.session_state["pet_type"],
            "pet_state": st.session_state["pet_state"],
            "setup_complete": st.session_state["setup_complete"],
            "current_event": st.session_state.get("current_event"),
            "previous_events": st.session_state.get("previous_events", []),
            "story_title": st.session_state.get("story_title", f"{st.session_state['pet_name']}'s Great Adventure"),
            "event_counter": st.session_state.get("event_counter", 0),
            "young_reader_mode": st.session_state.get("young_reader_mode", False),
            "base_storyline": st.session_state.get("base_storyline", ""),
            "story_location": st.session_state["story_location"]
        }
        pet_service.save_pet_data(pet_data, st.session_state["session_id"])
    
    # Force a rerun to update the UI
    st.rerun()

# Function to handle event choice
def handle_event_choice(choice_index):
    """Handle the user's choice for an event."""
    # Get the current event before clearing it
    if "current_event" in st.session_state:
        old_event = st.session_state["current_event"]
        
        # Completely remove the current event from session state
        st.session_state["current_event"] = None
        
        # Set a flag to indicate we're in a transition state
        # This will prevent any UI elements from showing during generation
        st.session_state["transitioning"] = True
        
        # Clear any existing generation state
        if "generating_next_content" in st.session_state:
            del st.session_state["generating_next_content"]
        
        # Set generation state to track progress
        st.session_state["generating_next_content"] = {
            "story": {"status": "pending", "message": "Generating next story segment..."},
            "image": {"status": "pending", "message": "Creating a custom image..."},
            "audio": {"status": "pending", "message": "Preparing audio narration..."}
        }
        
        # Get the selected option from the stored old event
        if "options" in old_event and 0 <= choice_index < len(old_event["options"]):
            selected_option = old_event["options"][choice_index]
            
            # Apply the effects of the choice
            if "effect" in selected_option:
                effects = selected_option["effect"]
                
                # Update the pet state with the effects
                for stat, value in effects.items():
                    if stat in st.session_state["pet_state"]:
                        st.session_state["pet_state"][stat] += value
                        
                        # Ensure the stat stays within bounds (0-10)
                        st.session_state["pet_state"][stat] = max(0, min(10, st.session_state["pet_state"][stat]))
            
            # Add the event to previous events
            if "previous_events" not in st.session_state:
                st.session_state["previous_events"] = []
                
            # Add a summary of the event and choice to previous events
            event_summary = f"{old_event['title']} - Description: {old_event['description']} - Chose: {selected_option['text']}"
            st.session_state["previous_events"].append(event_summary)
            
            # When we reach more than 10 events, generate a summary and store it
            if len(st.session_state["previous_events"]) > 10 and "event_summaries" not in st.session_state:
                st.session_state["event_summaries"] = []
                
            if len(st.session_state["previous_events"]) > 10 and len(st.session_state["previous_events"]) % 10 == 0:
                # Generate a summary of the last 10 events
                try:
                    summary = event_service.generate_summary(st.session_state["previous_events"][-10:])
                    st.session_state["event_summaries"].append(summary)
                    logger.info(f"Generated summary for events {len(st.session_state['previous_events'])-9}-{len(st.session_state['previous_events'])}")
                except Exception as e:
                    logger.error(f"Failed to generate event summary: {str(e)}")
            
            # Generate the next event based on the choice
            try:
                # Update story generation status
                st.session_state["generating_next_content"]["story"]["status"] = "in_progress"
                
                # Prepare event history context
                event_history = st.session_state.get("previous_events", [])
                event_summaries = st.session_state.get("event_summaries", [])
                
                # Use generate_event instead of generate_next_event
                next_event = event_service.generate_event(
                    pet_state=st.session_state["pet_state"],
                    pet_type=st.session_state["pet_type"],
                    pet_name=st.session_state["pet_name"],
                    previous_events=event_history,
                    event_summaries=event_summaries
                )
                
                # Update story generation status
                st.session_state["generating_next_content"]["story"]["status"] = "complete"
                st.session_state["generating_next_content"]["image"]["status"] = "in_progress"
                
                # Update the current event
                st.session_state["current_event"] = next_event
                
                # Ensure we have a valid story title
                if "story_title" not in st.session_state or not st.session_state["story_title"]:
                    st.session_state["story_title"] = f"{st.session_state['pet_name']}'s Great Adventure"
                
                # Image should be generated as part of the event generation
                if "image_url" in next_event:
                    st.session_state["generating_next_content"]["image"]["status"] = "complete"
                
                # Clear the transitioning flag when generation is complete
                st.session_state["transitioning"] = False
                
                # Save the updated pet data
                pet_data = {
                    "pet_name": st.session_state["pet_name"],
                    "pet_type": st.session_state["pet_type"],
                    "pet_state": st.session_state["pet_state"],
                    "setup_complete": st.session_state["setup_complete"],
                    "current_event": st.session_state["current_event"],
                    "previous_events": st.session_state["previous_events"],
                    "event_summaries": st.session_state.get("event_summaries", []),
                    "story_title": st.session_state["story_title"],
                    "event_counter": st.session_state.get("event_counter", 0),
                    "young_reader_mode": st.session_state.get("young_reader_mode", False),
                    "base_storyline": st.session_state.get("base_storyline", ""),
                    "story_location": st.session_state["story_location"]
                }
                pet_service.save_pet_data(pet_data, st.session_state["session_id"])
            except Exception as e:
                st.error(f"Error generating next event: {str(e)}")
                logger.error(f"Error generating next event: {str(e)}")
                # Mark story generation as failed
                st.session_state["generating_next_content"]["story"]["status"] = "failed"
                st.session_state["generating_next_content"]["story"]["message"] = f"Error: {str(e)}"
                # Clear the transitioning flag on error
                st.session_state["transitioning"] = False
    
    # Force a rerun to update the UI with the new event
    st.rerun()

# Function to reset pet
def reset_pet():
    """Reset the pet by deleting saved data and clearing session state."""
    # Delete saved data file
    pet_service.reset_pet_data(st.session_state.get("session_id"))
    
    # Clear the query parameters
    st.query_params.clear()
    
    # Set a flag to indicate that we want to reset
    st.session_state["reset_requested"] = True

# Function to generate a random pet name
def generate_random_name():
    """Generate a random name for the selected pet type."""
    # Get the selected pet type
    pet_type_display = st.session_state.get("pet_type_select", "Cat")
    available_pets = pet_service.get_available_pets()
    
    # Find the internal key for the selected pet type
    pet_key = None
    pet_display_names = list(available_pets.values())
    pet_options = list(available_pets.keys())
    
    if pet_type_display in pet_display_names:
        selected_index = pet_display_names.index(pet_type_display)
        pet_key = pet_options[selected_index]
    else:
        # Default to cat if not found
        pet_key = "cat"
    
    # Generate a random name for the selected pet type
    random_name = get_random_name(pet_key)
    
    # Update the pet name input field
    st.session_state["pet_name_input"] = random_name

# Function to handle pet type change
def on_pet_type_change():
    """Handle pet type change by updating the pet preview image."""
    # This function is called when the pet type selection changes
    # The pet preview image is already updated automatically
    pass  # No additional action needed for now

# Main application UI
def main():
    """Main application function."""
    # Print a message to indicate this file is being run
    logger.info("Starting Virtual Pet application")
    
    # Set page config
    st.set_page_config(
        page_title="Virtual Pet",
        page_icon="🐾",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state if needed
    initialize_session_state()
    
    # Check if reset was requested
    if st.session_state.get("reset_requested", False):
        # Clear the session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Use rerun outside of a callback
        st.rerun()
    
    # Create a placeholder for the entire UI
    # This allows us to clear and replace the entire UI when needed
    main_container = st.empty()
    
    # Check if we're in a transition state (generating new content)
    if st.session_state.get("transitioning", False):
        # Show only a spinner in the main container
        with main_container.container():
            st.markdown("<div style='text-align:center; margin-top:100px;'>", unsafe_allow_html=True)
            st.spinner("Generating your next adventure...")
            st.markdown("<h3 style='text-align:center;'>Please wait...</h3>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Check if generation is complete
        if "generating_next_content" in st.session_state:
            gen_status = st.session_state["generating_next_content"]
            if all(status["status"] == "complete" for status in gen_status.values()):
                # Clear the transition state and generation state
                st.session_state.pop("transitioning", None)
                st.session_state.pop("generating_next_content", None)
                # Force a rerun to update the UI
                st.rerun()
        
        # Don't show any other UI elements during transition
        return
    
    # Render the main UI in the container
    with main_container.container():
        # Check if we're generating audio - if so, show a spinner at the top
        if st.session_state.get("generating_audio", False):
            st.spinner("Generating audio...")
            st.markdown("<div style='text-align:center;'><h4>Creating audio narration, please wait...</h4></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Dynamic title based on setup status
        if st.session_state["setup_complete"]:
            # Generate a dynamic title for the pet's adventure
            print(f"Debug - setup_complete: {st.session_state['setup_complete']}")
            print(f"Debug - story_title in session: {'story_title' in st.session_state}")
            print(f"Debug - current story_title: {st.session_state.get('story_title', 'Not set')}")
            
            # Only generate a title if one doesn't exist
            if "story_title" not in st.session_state or not st.session_state.get("story_title"):
                print(f"Debug - Generating new title for {st.session_state['pet_name']} the {st.session_state['pet_type']}")
                
                # Generate a title for the pet's adventure
                story_title = event_service.generate_story_title(
                    pet_name=st.session_state["pet_name"],
                    pet_type=st.session_state["pet_type"],
                    current_event=st.session_state.get("current_event")
                )
                
                print(f"Debug - Generated title: {story_title}")
                
                # Store the title in session state
                st.session_state["story_title"] = story_title
                
                # Save the updated title to pet data
                pet_data = pet_service.load_pet_data(st.session_state["session_id"]) or {}
                pet_data["story_title"] = story_title
                pet_data["story_location"] = st.session_state["story_location"]
                pet_service.save_pet_data(pet_data, st.session_state["session_id"])
                print(f"Debug - Saved title to pet data: {story_title}")
            
            # Display the title
            st.title(st.session_state["story_title"])
            
            # Create a layout with two columns
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader(f"{st.session_state['pet_name']}'s Status")
                
                # Enhanced stats display with custom styling
                stats = [
                    {"name": "Hunger", "value": st.session_state['pet_state']['hunger'], "max": 10},
                    {"name": "Energy", "value": st.session_state['pet_state']['energy'], "max": 10},
                    {"name": "Happiness", "value": st.session_state['pet_state']['happiness'], "max": 10}
                ]
                
                for stat in stats:
                    # Calculate percentage for the progress bar
                    percentage = (stat["value"] / stat["max"]) * 100
                    
                    # Choose color based on value (red if low, green if high)
                    color = "#ff4b4b" if percentage < 30 else "#4bb543" if percentage > 70 else "#f9c846"
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 20px;">
                        <div style="font-size: 18px; font-weight: 500; margin-bottom: 5px;">{stat["name"]}: {stat["value"]}/{stat["max"]}</div>
                        <div style="background-color: #e0e0e0; border-radius: 10px; height: 10px; width: 100%;">
                            <div style="background-color: {color}; width: {percentage}%; height: 10px; border-radius: 10px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Only show action buttons if there's no active event
                if not st.session_state.get("current_event"):
                    st.button("Feed", on_click=update_pet_state, args=("feed",))
                    st.button("Play", on_click=update_pet_state, args=("play",))
                    st.button("Rest", on_click=update_pet_state, args=("rest",))
                

            with col2:
                # Display the pet image
                mood = st.session_state["pet_state"]["mood"]
                
                # Check if there's an active event with an image URL
                if "current_event" in st.session_state and st.session_state["current_event"]:
                    event = st.session_state["current_event"]
                    
                    if "image_url" in event:
                        # Display the event-specific image
                        st.image(event["image_url"], width=450)
                    else:
                        # If there's an event but no image yet, show the default image
                        image_path = pet_service.get_pet_image_path(st.session_state["pet_type"], mood)
                        st.image(image_path, width=450)
                else:
                    # Fall back to the static mood-based image
                    image_path = pet_service.get_pet_image_path(st.session_state["pet_type"], mood)
                    st.image(image_path, width=450)
                
                # If there's no event, show the pet's mood
                if not st.session_state.get("current_event"):
                    st.subheader(f"{st.session_state['pet_name']} looks {mood}!")
                
            # Check if there's an active event - display it below the pet image
            if "current_event" in st.session_state and st.session_state["current_event"]:
                event = st.session_state["current_event"]
                
                # Create a container for the event
                with st.container():
                    st.markdown("---")
                    
                    # Display the story description
                    st.markdown(f'<div style="font-size: 20px;">{event["description"]}</div>', unsafe_allow_html=True)
                    
                    # Generate a unique identifier for this event
                    event_id = f"{event.get('id', '')}"
                    if not event_id:
                        # If the event doesn't have an ID, create one from the description
                        import hashlib
                        event_id = hashlib.md5(event["description"].encode()).hexdigest()[:10]
                    
                    # Add a button to play audio
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        # Change button text if audio is generating
                        button_text = "⏳ Generating..." if st.session_state.get("generating_audio", False) else "🔊 Play Story Audio"
                        button_help = "Audio is being generated, please wait..." if st.session_state.get("generating_audio", False) else "Listen to the story and options read aloud"
                        
                        # Disable the button if audio is already generating
                        if st.button(button_text, 
                                    help=button_help,
                                    on_click=generate_and_play_audio,
                                    args=(event,),
                                    disabled=st.session_state.get("generating_audio", False)):
                            pass  # The on_click handler will take care of playing the audio
                    
                    # Add extra space between description and options
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Display the event options
                    if "options" in event:
                        # Always show options regardless of generating state
                        st.write("---")
                        st.subheader(f"What should {st.session_state['pet_name']} do next?")
                        
                        # Add some space after the header
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Create a custom component for each option
                        for i, option in enumerate(event["options"]):
                            # Format the option text with effects
                            effects = option["effect"]
                            effects_text = []
                            if effects["hunger"] != 0:
                                effects_text.append(f"Hunger {'+' if effects['hunger'] > 0 else ''}{effects['hunger']}")
                            if effects["energy"] != 0:
                                effects_text.append(f"Energy {'+' if effects['energy'] > 0 else ''}{effects['energy']}")
                            if effects["happiness"] != 0:
                                effects_text.append(f"Happiness {'+' if effects['happiness'] > 0 else ''}{effects['happiness']}")
                            
                            # Format the effects text
                            effects_str = f" ({', '.join(effects_text)})" if effects_text else ""
                            
                            # Create a custom component with columns
                            cols = st.columns([1, 15])
                            
                            # Number in the first column
                            with cols[0]:
                                # Create a circular container for the number
                                st.markdown(f"""
                                <div style="
                                    width: 30px;
                                    height: 30px;
                                    border-radius: 50%;
                                    background-color: #f0f2f6;
                                    border: 1px solid #ccc;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-weight: bold;
                                    margin-top: 5px;
                                ">
                                    {i+1}
                                </div>
                                """, unsafe_allow_html=True)
                                
                            # Option text in the second column
                            with cols[1]:
                                # Create a button that looks like text
                                if st.button(f"{option['text']}{effects_str}", key=f"option_{i}"):
                                    handle_event_choice(i)
                            
                            # Add some space between options
                            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

            # Add the reset button at the very bottom of the page
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.button("Reset Pet", on_click=reset_pet, type="secondary", help="Start over with a new pet")
        else:
            # Setup screen
            st.title("Virtual Pet Setup")
            
            # Welcome screen and pet setup
            st.header("Welcome to Virtual Pet Simulator!")
            st.write("Let's set up your new virtual pet companion.")
            
            # Pet selection
            available_pets = pet_service.get_available_pets()
            pet_options = list(available_pets.keys())  # These are the internal keys like "cat"
            pet_display_names = list(available_pets.values())  # These are the display names like "Cat"
            
            # Create columns for a nicer layout
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Pet type selection with preview images
                st.subheader("Choose your pet:")
                
                # Find the index of the current pet type's display name
                default_index = 0
                if st.session_state["pet_type"] in pet_options:
                    pet_key_index = pet_options.index(st.session_state["pet_type"])
                    default_index = pet_key_index
                
                st.selectbox(
                    "Pet Type",
                    options=pet_display_names,
                    index=default_index,
                    key="pet_type_select",
                    format_func=lambda x: x,
                    on_change=on_pet_type_change
                )
                
                # Show preview of selected pet
                selected_display_name = st.session_state["pet_type_select"]
                selected_index = pet_display_names.index(selected_display_name)
                selected_pet_type = pet_options[selected_index]  # This is the internal key like "cat"
                
                # Get the image path for the selected pet
                image_path = pet_service.get_pet_image_path(selected_pet_type, "happy")
                st.image(image_path, width=200, caption=f"{selected_display_name} Preview")
            
            with col2:
                # Pet naming
                st.subheader("Name your pet:")
                
                # Create a row with the text input and random name button
                name_col1, name_col2 = st.columns([3, 1])
                
                with name_col1:
                    st.text_input(
                        "Pet Name",
                        value=st.session_state.get("pet_name", ""),
                        key="pet_name_input",
                        placeholder="Enter a name for your pet"
                    )
                
                with name_col2:
                    st.button("🎲 Random", on_click=generate_random_name, help="Generate a random name for your pet")
                
                # Pet description
                st.write("Your pet will need your care and attention. Make sure to feed it, play with it, and let it rest!")
                
                # Young Reader Mode toggle
                st.write("---")
                st.subheader("Reading Level")
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.toggle(
                        "Young Reader Mode",
                        key="young_reader_mode_checkbox",
                        help="Simplifies text for young readers (ages 4-6)",
                        value=st.session_state.get("young_reader_mode", True)
                    )
                with col_b:
                    if st.session_state.get("young_reader_mode_checkbox", False):
                        st.markdown("✅ **Simple words and shorter stories for young readers!**")
                    else:
                        st.markdown("📚 **Standard reading level**")
            
            # Start button
            st.button("Start Your Pet Adventure!", on_click=complete_setup)

if __name__ == "__main__":
    main() 