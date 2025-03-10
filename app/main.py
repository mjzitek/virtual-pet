"""
Virtual Pet Application - Main Entry Point

This is the main entry point for the Virtual Pet Application.
It sets up the Streamlit UI and handles user interactions.
"""

import os
import logging
import streamlit as st
from typing import Dict, Any, Optional
import sys
import uuid
import base64
import threading
import time as import_time
import time

# Add the parent directory to the Python path to allow imports from the app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from the app package
from app.services.pet_service import PetService
from app.services.event_service import EventService
from app.services.tts_service import TTSService
from app.config.settings import DEFAULT_PET_STATS
from app.data.pet_names import get_random_name

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize services
pet_service = PetService()
event_service = EventService()
tts_service = TTSService()

# Initialize session state
def initialize_session_state():
    """Initialize or restore session state."""
    # Generate a session ID if one doesn't exist
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
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
    # Set generation state to track progress
    st.session_state["generating_next_content"] = {
        "story": {"status": "pending", "message": "Generating next story segment..."},
        "image": {"status": "pending", "message": "Creating a custom image..."},
        "audio": {"status": "pending", "message": "Preparing audio narration..."}
    }
    
    # Get the current event
    event = st.session_state["current_event"]
    
    # Get the selected option
    if "options" in event and 0 <= choice_index < len(event["options"]):
        selected_option = event["options"][choice_index]
        
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
        event_summary = f"{event['title']} - Description: {event['description']} - Chose: {selected_option['text']}"
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
    
    # Force a rerun to update the UI with the new event
    st.rerun()

# Function to reset pet
def reset_pet():
    """Reset the pet by deleting saved data and clearing session state."""
    pet_service.reset_pet_data(st.session_state.get("session_id"))
    # Set a flag to indicate that we want to reset
    st.session_state["reset_requested"] = True

# Function to play the generated audio
def generate_and_play_audio(event: Dict[str, Any]):
    """
    Play the already-generated audio for an event.
    
    Args:
        event: The current event containing description and options
    """
    try:
        # Generate a unique identifier for this event
        event_id = f"{event.get('id', '')}"
        if not event_id:
            # If the event doesn't have an ID, create one from the description
            import hashlib
            event_id = hashlib.md5(event["description"].encode()).hexdigest()[:10]
        
        # Get the audio path from session state
        audio_cache_key = f"audio_path_{event_id}"
        if audio_cache_key not in st.session_state:
            logger.error("Audio path not found in session state")
            st.error("Audio not found. Please try again.")
            return
        
        audio_path = st.session_state[audio_cache_key]
        logger.info(f"Playing audio from path: {audio_path}")
        
        # Check if the file exists
        if not os.path.exists(audio_path):
            logger.error(f"Audio file does not exist: {audio_path}")
            st.error("Audio file not found. Please try generating it again.")
            # Remove the path from session state
            del st.session_state[audio_cache_key]
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
        
        # Show a success message
        st.success("🔊 Playing audio narration...")
        
    except Exception as e:
        st.error(f"Error playing audio: {str(e)}")
        logger.error(f"Error playing audio: {str(e)}")

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

# Function to start generating audio asynchronously
def start_audio_generation(event: Dict[str, Any]):
    """
    Start generating audio for an event in the background.
    
    Args:
        event: The current event containing description and options
    """
    # Generate a unique identifier for this event
    event_id = f"{event.get('id', '')}"
    if not event_id:
        # If the event doesn't have an ID, create one from the description
        import hashlib
        event_id = hashlib.md5(event["description"].encode()).hexdigest()[:10]
    
    logger.info(f"Generated event_id for audio: {event_id}")
    
    # Check if we already have the audio path in session state
    audio_cache_key = f"audio_path_{event_id}"
    audio_generating_key = f"audio_generating_{event_id}"
    audio_status_key = f"audio_status_{event_id}"
    
    # Clear any existing audio for this event to avoid using old audio
    if audio_cache_key in st.session_state:
        logger.info(f"Clearing existing audio for event: {event_id}")
        del st.session_state[audio_cache_key]
    
    # Clear any existing status file for this event
    import glob
    status_file = os.path.join(tts_service.get_audio_dir(), f"{event_id}_status.json")
    if os.path.exists(status_file):
        logger.info(f"Removing existing status file: {status_file}")
        os.remove(status_file)
    
    # Mark that we're generating audio for this event
    st.session_state[audio_generating_key] = True
    st.session_state[audio_status_key] = "in_progress"
    
    # Store the start time for timeout checking
    st.session_state["audio_start_time"] = import_time.time()
    
    # Update the generation status if it exists
    if "generating_next_content" in st.session_state:
        st.session_state["generating_next_content"]["audio"]["status"] = "in_progress"
    
    # Format the story text and options for speech
    options_to_include = event.get("options", [])
    formatted_text = tts_service.format_story_for_speech(
        description=event["description"],
        pet_name=st.session_state["pet_name"],
        options=options_to_include
    )
    
    # Store the event_id in session state for reference
    st.session_state["current_audio_event_id"] = event_id
    
    # Generate the audio in a separate thread
    def generate_audio_thread():
        try:
            # Generate the audio
            audio_path = tts_service.generate_speech(
                text=formatted_text,
                voice="sage",  # Use sage voice as requested
                use_cache=True  # Use caching
            )
            
            logger.info(f"Audio generation successful, path: {audio_path}")
            
            # Store the audio path and status in a file that can be checked later
            import json
            # Use the same directory as the audio file
            result_file = os.path.join(tts_service.get_audio_dir(), f"{event_id}_status.json")
            with open(result_file, 'w') as f:
                json.dump({
                    "status": "complete",
                    "path": audio_path,
                    "timestamp": import_time.time(),
                    "event_id": event_id,
                    "description": event["description"][:50]  # Store a snippet of the description for debugging
                }, f)
            
            logger.info(f"Audio generation complete, saved status to {result_file}")
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            # Store the error in a file that can be checked later
            import json
            result_file = os.path.join(tts_service.get_audio_dir(), f"{event_id}_status.json")
            with open(result_file, 'w') as f:
                json.dump({
                    "status": "failed",
                    "error": str(e),
                    "timestamp": import_time.time(),
                    "event_id": event_id,
                    "description": event["description"][:50]  # Store a snippet of the description for debugging
                }, f)
            logger.error(f"Saved error status to {result_file}")
    
    # Start the thread
    threading.Thread(target=generate_audio_thread).start()
    
    # Force a rerun to update the UI
    st.rerun()

# Function to check audio generation status
def check_audio_generation_status(event: Dict[str, Any]):
    """
    Check the status of audio generation for an event.
    
    Args:
        event: The current event
    """
    # Generate a unique identifier for this event
    event_id = f"{event.get('id', '')}"
    if not event_id:
        # If the event doesn't have an ID, create one from the description
        import hashlib
        event_id = hashlib.md5(event["description"].encode()).hexdigest()[:10]
    
    logger.info(f"Checking audio status for event_id: {event_id}")
    
    # Check if we already have the audio path in session state
    audio_cache_key = f"audio_path_{event_id}"
    audio_generating_key = f"audio_generating_{event_id}"
    audio_status_key = f"audio_status_{event_id}"
    
    # If audio is already in session state, we're done
    if audio_cache_key in st.session_state:
        logger.info(f"Audio already in session state: {st.session_state[audio_cache_key]}")
        return
    
    # Check if we have a status file
    import json
    import time
    import glob
    
    # Look for any status files in the directory
    status_files = glob.glob(os.path.join(tts_service.get_audio_dir(), "*_status.json"))
    logger.info(f"Found {len(status_files)} status files: {status_files}")
    
    # First try the exact event_id
    result_file = os.path.join(tts_service.get_audio_dir(), f"{event_id}_status.json")
    logger.info(f"Checking for status file: {result_file}")
    
    if not os.path.exists(result_file):
        # If the exact file doesn't exist, check if we have a stored event_id
        stored_event_id = st.session_state.get("current_audio_event_id")
        if stored_event_id and stored_event_id == event_id:
            logger.info(f"Using stored event_id: {stored_event_id}")
            result_file = os.path.join(tts_service.get_audio_dir(), f"{stored_event_id}_status.json")
            logger.info(f"Checking for status file with stored ID: {result_file}")
    
    if os.path.exists(result_file):
        logger.info(f"Status file found: {result_file}")
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            logger.info(f"Status file contents: {result}")
            
            # Check the status
            if result["status"] == "complete":
                # Audio generation is complete
                logger.info(f"Audio generation complete, setting session state")
                
                # Verify this is the correct event by checking the event_id
                if "event_id" in result and result["event_id"] == event_id:
                    st.session_state[audio_cache_key] = result["path"]
                    st.session_state[audio_generating_key] = False
                    st.session_state[audio_status_key] = "complete"
                    
                    # Update the generation status if it exists
                    if "generating_next_content" in st.session_state:
                        st.session_state["generating_next_content"]["audio"]["status"] = "complete"
                    
                    # Remove the status file
                    os.remove(result_file)
                    logger.info(f"Removed status file after processing")
                    
                    # Force a rerun to update the UI
                    logger.info(f"Forcing rerun to update UI")
                    st.rerun()
                else:
                    logger.warning(f"Status file event_id mismatch: {result.get('event_id', 'None')} != {event_id}")
                    # Remove the status file as it's for a different event
                    os.remove(result_file)
                    
            elif result["status"] == "failed":
                # Audio generation failed
                logger.info(f"Audio generation failed, setting session state")
                
                # Verify this is the correct event
                if "event_id" in result and result["event_id"] == event_id:
                    st.session_state[audio_generating_key] = False
                    st.session_state[audio_status_key] = "failed"
                    
                    # Update the generation status if it exists
                    if "generating_next_content" in st.session_state:
                        st.session_state["generating_next_content"]["audio"]["status"] = "failed"
                        st.session_state["generating_next_content"]["audio"]["message"] = f"Error: {result.get('error', 'Unknown error')}"
                    
                    # Remove the status file
                    os.remove(result_file)
                    logger.info(f"Removed status file after processing")
                    
                    # Force a rerun to update the UI
                    logger.info(f"Forcing rerun to update UI")
                    st.rerun()
                else:
                    logger.warning(f"Status file event_id mismatch: {result.get('event_id', 'None')} != {event_id}")
                    # Remove the status file as it's for a different event
                    os.remove(result_file)
        except Exception as e:
            logger.error(f"Error checking audio status: {str(e)}")
    else:
        logger.info(f"Status file not found: {result_file}")
    
    # If we're generating audio and it's been more than 60 seconds, assume it failed
    if audio_generating_key in st.session_state and st.session_state[audio_generating_key]:
        # Check if we have a timestamp
        if "audio_start_time" in st.session_state:
            elapsed = time.time() - st.session_state["audio_start_time"]
            if elapsed > 60:  # 60 seconds timeout
                # Audio generation timed out
                logger.warning(f"Audio generation timed out after {elapsed} seconds")
                st.session_state[audio_generating_key] = False
                st.session_state[audio_status_key] = "failed"
                
                # Update the generation status if it exists
                if "generating_next_content" in st.session_state:
                    st.session_state["generating_next_content"]["audio"]["status"] = "failed"
                    st.session_state["generating_next_content"]["audio"]["message"] = "Error: Audio generation timed out"
                
                # Force a rerun to update the UI
                st.rerun()

# Main application UI
def main():
    """Main application function."""
    # Print a message to indicate this file is being run
    print("Running app/main.py - Virtual Pet Application with Event System")
    
    # Check if reset was requested
    if st.session_state.get("reset_requested", False):
        # Clear the session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Use rerun outside of a callback
        st.rerun()
    
    # Initialize session state
    initialize_session_state()
    
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
        
        # Display the title - use a default if somehow still not set
        title_to_display = st.session_state.get("story_title", f"{st.session_state['pet_name']}'s Great Adventure")
        print(f"Debug - Displaying title: {title_to_display}")
        st.title(f"🐾 {title_to_display}")
    else:
        st.title("🐾 Virtual Pet Simulator")
    
    # Welcome screen and pet setup
    if not st.session_state["setup_complete"]:
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
    
    # Main pet interface (only shown after setup is complete)
    else:
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
                
                # Check if we're in the process of generating content
                if "generating_next_content" in st.session_state and st.session_state["generating_next_content"]["image"]["status"] in ["pending", "in_progress"]:
                    # Show a loading indicator for the image
                    with st.container():
                        # Display a placeholder image with a loading overlay
                        image_path = pet_service.get_pet_image_path(st.session_state["pet_type"], mood)
                        st.image(image_path, width=450)
                        
                        # Add a loading overlay
                        st.markdown("""
                        <div style="position: relative; margin-top: -300px; margin-bottom: 300px; text-align: center;">
                            <div style="background-color: rgba(255, 255, 255, 0.7); padding: 20px; border-radius: 10px; display: inline-block;">
                                <div style="display: flex; flex-direction: column; align-items: center;">
                                    <div class="spinner"></div>
                                    <p style="margin-top: 10px; font-weight: bold;">Creating a custom image for this adventure...</p>
                                </div>
                            </div>
                        </div>
                        
                        <style>
                        .spinner {
                            border: 5px solid rgba(0, 0, 0, 0.1);
                            width: 50px;
                            height: 50px;
                            border-radius: 50%;
                            border-left-color: #09f;
                            animation: spin 1s linear infinite;
                        }
                        
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                        </style>
                        """, unsafe_allow_html=True)
                elif "image_url" in event:
                    # Display the event-specific image
                    st.image(event["image_url"], width=450)
                else:
                    # If there's an event but no image yet, show a loading indicator and the default image
                    with st.spinner("Generating a custom image for this event..."):
                        # Fall back to the static mood-based image while loading
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
                
                # Check if we're in the process of generating content
                if "generating_next_content" in st.session_state:
                    gen_status = st.session_state["generating_next_content"]
                    
                    # Create a progress container
                    with st.container():
                        st.markdown("<h3>Generating your next adventure...</h3>", unsafe_allow_html=True)
                        
                        # Create a stylish progress display
                        progress_html = """
                        <div style="padding: 20px; border-radius: 10px; background-color: #f8f9fa; margin-bottom: 20px;">
                        """
                        
                        # Story generation status
                        story_status = gen_status["story"]["status"]
                        story_icon = "⏳" if story_status == "pending" else "🔄" if story_status == "in_progress" else "✅" if story_status == "complete" else "❌"
                        story_color = "#6c757d" if story_status == "pending" else "#007bff" if story_status == "in_progress" else "#28a745" if story_status == "complete" else "#dc3545"
                        progress_html += f"""
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                                <span style="font-size: 24px; margin-right: 10px;">{story_icon}</span>
                                <span style="font-weight: bold; color: {story_color};">Story</span>
                                <span style="margin-left: auto; color: {story_color};">{story_status.replace("_", " ").title()}</span>
                            </div>
                            <div style="color: #6c757d; font-size: 14px; margin-left: 34px;">{gen_status["story"]["message"]}</div>
                        </div>
                        """
                        
                        # Image generation status
                        image_status = gen_status["image"]["status"]
                        image_icon = "⏳" if image_status == "pending" else "🔄" if image_status == "in_progress" else "✅" if image_status == "complete" else "❌"
                        image_color = "#6c757d" if image_status == "pending" else "#007bff" if image_status == "in_progress" else "#28a745" if image_status == "complete" else "#dc3545"
                        progress_html += f"""
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                                <span style="font-size: 24px; margin-right: 10px;">{image_icon}</span>
                                <span style="font-weight: bold; color: {image_color};">Image</span>
                                <span style="margin-left: auto; color: {image_color};">{image_status.replace("_", " ").title()}</span>
                            </div>
                            <div style="color: #6c757d; font-size: 14px; margin-left: 34px;">{gen_status["image"]["message"]}</div>
                        </div>
                        """
                        
                        # Audio generation status
                        audio_status = gen_status["audio"]["status"]
                        audio_icon = "⏳" if audio_status == "pending" else "🔄" if audio_status == "in_progress" else "✅" if audio_status == "complete" else "❌"
                        audio_color = "#6c757d" if audio_status == "pending" else "#007bff" if audio_status == "in_progress" else "#28a745" if audio_status == "complete" else "#dc3545"
                        progress_html += f"""
                        <div>
                            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                                <span style="font-size: 24px; margin-right: 10px;">{audio_icon}</span>
                                <span style="font-weight: bold; color: {audio_color};">Audio</span>
                                <span style="margin-left: auto; color: {audio_color};">{audio_status.replace("_", " ").title()}</span>
                            </div>
                            <div style="color: #6c757d; font-size: 14px; margin-left: 34px;">{gen_status["audio"]["message"]}</div>
                        </div>
                        """
                        
                        progress_html += """
                        </div>
                        """
                        
                        # Display the progress
                        st.markdown(progress_html, unsafe_allow_html=True)
                        
                        # Add a fun message while waiting
                        if not all(status["status"] == "complete" for status in gen_status.values()):
                            messages = [
                                "Your pet is thinking of the next adventure...",
                                "Creating a magical world just for you...",
                                "Brewing up something exciting...",
                                "Gathering stardust for your story...",
                                "Weaving a tale of wonder and excitement..."
                            ]
                            import random
                            st.markdown(f"<div style='text-align: center; font-style: italic;'>{random.choice(messages)}</div>", unsafe_allow_html=True)
                        
                        # If all content is generated, remove the generating state
                        if all(status["status"] == "complete" for status in gen_status.values()):
                            # Clear the generating state after a short delay
                            st.session_state.pop("generating_next_content", None)
                            # Force a rerun to update the UI
                            st.rerun()
                
                # Display the story description
                st.markdown(f'<div style="font-size: 20px;">{event["description"]}</div>', unsafe_allow_html=True)
                
                # Generate a unique identifier for this event
                event_id = f"{event.get('id', '')}"
                if not event_id:
                    # If the event doesn't have an ID, create one from the description
                    import hashlib
                    event_id = hashlib.md5(event["description"].encode()).hexdigest()[:10]
                
                # Check if we already have the audio path in session state
                audio_cache_key = f"audio_path_{event_id}"
                audio_generating_key = f"audio_generating_{event_id}"
                audio_status_key = f"audio_status_{event_id}"
                
                # Log the current state for debugging
                logger.info(f"Audio status - cache_key in session: {audio_cache_key in st.session_state}, generating_key: {st.session_state.get(audio_generating_key, False)}")
                
                # Check the status of audio generation
                check_audio_generation_status(event)
                
                # Start generating audio if it hasn't been generated yet
                if audio_cache_key not in st.session_state and not st.session_state.get(audio_generating_key, False):
                    logger.info("Starting audio generation")
                    # Start generating audio in the background
                    start_audio_generation(event)
                    # Force a rerun to update the UI
                    st.rerun()
                
                # Determine button state based on audio generation status
                if audio_cache_key in st.session_state:
                    # Audio is ready, show play button
                    logger.info(f"Audio is ready, showing play button. Path: {st.session_state[audio_cache_key]}")
                    if st.button("🔊 Play Story Audio", 
                                help="Listen to the story and options read aloud",
                                on_click=generate_and_play_audio,
                                args=(event,)):
                        pass  # The on_click handler will take care of playing the audio
                elif st.session_state.get(audio_generating_key, False):
                    # Audio is being generated, show spinner instead of disabled button
                    logger.info("Audio is being generated, showing spinner")
                    with st.spinner("Generating Audio..."):
                        st.info("🔄 Generating audio for this story...", icon="🔊")
                else:
                    # Something went wrong or we haven't started generating yet, show retry button
                    logger.info("Audio generation not started or failed, showing generate button")
                    if st.button("🔄 Generate Audio", 
                                help="Generate audio for this story",
                                on_click=start_audio_generation,
                                args=(event,)):
                        pass  # The on_click handler will take care of starting audio generation
                
                # Add extra space between description and options
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Display the event options
                if "options" in event:
                    # Only show options if we're not in the middle of generating content
                    if "generating_next_content" not in st.session_state:
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
        
        # Add an expandable section for event history
        if "previous_events" in st.session_state and len(st.session_state["previous_events"]) > 0:
            with st.expander("Event History"):
                # Display event summaries if available
                if "event_summaries" in st.session_state and len(st.session_state["event_summaries"]) > 0:
                    st.subheader("Story Summaries")
                    for i, summary in enumerate(st.session_state["event_summaries"]):
                        with st.container():
                            st.markdown(f"**Chapter {i+1}**")
                            st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 15px;">{summary}</div>', unsafe_allow_html=True)
                    st.markdown("---")
                
                # Display recent events
                st.subheader("Recent Events")
                # Show the most recent events first
                for event in reversed(st.session_state["previous_events"]):
                    st.markdown(f"• {event}")
                
                # Display event count
                total_events = len(st.session_state["previous_events"])
                st.caption(f"Total events: {total_events}")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.button("Reset Pet", on_click=reset_pet, type="secondary", help="Start over with a new pet")

if __name__ == "__main__":
    main() 