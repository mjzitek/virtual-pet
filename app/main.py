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
            
        if "previous_events" not in st.session_state:
            st.session_state["previous_events"] = []
            
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
            event = event_service.generate_event(
                pet_state=new_state,
                pet_type=st.session_state["pet_type"],
                pet_name=st.session_state["pet_name"],
                action=action,
                previous_events=st.session_state.get("previous_events", [])
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
        event_summary = f"{event['description']} {st.session_state['pet_name']} chose: {selected_option['text']}"
        st.session_state["previous_events"].append(event_summary)
        
        # Keep only the last 10 events to avoid context getting too long
        if len(st.session_state["previous_events"]) > 10:
            st.session_state["previous_events"] = st.session_state["previous_events"][-10:]
        
        # Generate the next event based on the choice
        try:
            # Use generate_event instead of generate_next_event
            next_event = event_service.generate_event(
                pet_state=st.session_state["pet_state"],
                pet_type=st.session_state["pet_type"],
                pet_name=st.session_state["pet_name"],
                previous_events=st.session_state["previous_events"]
            )
            
            # Update the current event
            st.session_state["current_event"] = next_event
            
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
                "previous_events": st.session_state["previous_events"],
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
    
    # Force a rerun to update the UI with the new event
    st.rerun()

# Function to reset pet
def reset_pet():
    """Reset the pet by deleting saved data and clearing session state."""
    pet_service.reset_pet_data(st.session_state.get("session_id"))
    # Set a flag to indicate that we want to reset
    st.session_state["reset_requested"] = True

# Function to generate and play audio
def generate_and_play_audio(event: Dict[str, Any]):
    """
    Generate audio from story text and options and play it.
    
    Args:
        event: The current event containing description and options
    """
    try:
        # Always include options in the speech
        options_to_include = event.get("options", [])
        
        # Format the story text and options for speech
        formatted_text = tts_service.format_story_for_speech(
            description=event["description"],
            pet_name=st.session_state["pet_name"],
            options=options_to_include
        )
        
        # Generate a unique identifier for this event to use in session state
        event_id = f"{event.get('id', '')}"
        if not event_id:
            # If the event doesn't have an ID, create one from the description
            import hashlib
            event_id = hashlib.md5(event["description"].encode()).hexdigest()[:10]
        
        # Check if we already have the audio path in session state
        audio_cache_key = f"audio_path_{event_id}"
        if audio_cache_key in st.session_state:
            # Use the cached audio path
            audio_path = st.session_state[audio_cache_key]
            logger.info(f"Using cached audio path from session state: {audio_path}")
        else:
            # Use the sage voice as specifically requested
            voice = "sage"  # Use sage voice as requested
            
            # Generate the audio file using the sage voice with caching
            audio_path = tts_service.generate_speech(
                text=formatted_text,
                voice=voice,
                use_cache=True  # Use caching
            )
            # Store the audio path in session state for future use
            st.session_state[audio_cache_key] = audio_path
            logger.info(f"Generated new audio and stored in session state: {audio_path}")
        
        # Read the audio file and encode it as base64
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
        # Create an HTML audio element that autoplays without showing controls
        audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        
        <div style="color: #4CAF50; padding: 10px; border-radius: 5px; display: inline-block;">
            <span style="vertical-align: middle;">🔊 Playing audio with sage voice...</span>
        </div>
        """
        
        # Display the audio player
        st.markdown(audio_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        logger.error(f"Error generating audio: {str(e)}")

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
                if "image_url" in event:
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
                
                # Display the story description
                st.markdown(f'<div style="font-size: 20px;">{event["description"]}</div>', unsafe_allow_html=True)
                
                # Generate a unique identifier for this event to check if audio exists
                event_id = f"{event.get('id', '')}"
                if not event_id:
                    # If the event doesn't have an ID, create one from the description
                    import hashlib
                    event_id = hashlib.md5(event["description"].encode()).hexdigest()[:10]
                
                # Check if we already have the audio path in session state
                audio_cache_key = f"audio_path_{event_id}"
                
                # Determine button text based on whether audio has been generated
                button_text = "🔊 Replay Story Audio" if audio_cache_key in st.session_state else "🔊 Play Story Audio"
                
                # Add text-to-speech button - more prominent and descriptive
                st.button(button_text, 
                          help="Listen to the story and options read aloud",
                          on_click=generate_and_play_audio,
                          args=(event,))
                
                # Add extra space between description and options
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Display the event options
                if "options" in event:
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

if __name__ == "__main__":
    main() 