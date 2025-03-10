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

# Add the parent directory to the Python path to allow imports from the app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from the app package
from app.services.pet_service import PetService
from app.services.event_service import EventService
from app.config.settings import DEFAULT_PET_STATS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize services
pet_service = PetService()
event_service = EventService()

# Initialize session state
def initialize_session_state():
    """Initialize or restore session state."""
    # Check if we have saved pet data
    saved_data = pet_service.load_pet_data()
    
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
        
        # Ensure current_event is initialized even if not in saved data
        if "current_event" not in st.session_state:
            st.session_state["current_event"] = None
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

# Function to handle pet setup completion
def complete_setup():
    """Handle pet setup completion."""
    if st.session_state["pet_name_input"] and len(st.session_state["pet_name_input"].strip()) > 0:
        st.session_state["pet_name"] = st.session_state["pet_name_input"]
        
        # Convert display name to internal key
        available_pets = pet_service.get_available_pets()
        pet_options = list(available_pets.keys())  # These are the internal keys like "cat"
        pet_display_names = list(available_pets.values())  # These are the display names like "Cat"
        
        selected_display_name = st.session_state["pet_type_select"]
        selected_index = pet_display_names.index(selected_display_name)
        st.session_state["pet_type"] = pet_options[selected_index]  # This is the internal key like "cat"
        
        st.session_state["setup_complete"] = True
        
        # Save the data after setup is complete
        pet_data = {
            "pet_name": st.session_state["pet_name"],
            "pet_type": st.session_state["pet_type"],
            "pet_state": st.session_state["pet_state"],
            "setup_complete": st.session_state["setup_complete"],
            "current_event": st.session_state["current_event"]
        }
        pet_service.save_pet_data(pet_data)

# Function to update pet state
def update_pet_state(action):
    """
    Update the pet state based on the specified action.
    
    Args:
        action: The action to perform (feed, play, rest)
    """
    # Update the pet state
    st.session_state["pet_state"] = pet_service.update_pet_state(
        st.session_state["pet_state"], 
        action
    )
    
    # Save the updated state
    pet_data = {
        "pet_name": st.session_state["pet_name"],
        "pet_type": st.session_state["pet_type"],
        "pet_state": st.session_state["pet_state"],
        "setup_complete": st.session_state["setup_complete"],
        "current_event": st.session_state["current_event"]
    }
    pet_service.save_pet_data(pet_data)
    
    # Check if an event should be triggered
    #if event_service.should_trigger_event(st.session_state["pet_state"]):
    st.session_state["current_event"] = event_service.generate_event(
        st.session_state["pet_state"],
        st.session_state["pet_type"],
        st.session_state["pet_name"]
    )

# Function to handle event choice
def handle_event_choice(choice_index):
    """
    Handle the user's choice for an event.
    
    Args:
        choice_index: The index of the chosen option
    """
    if st.session_state["current_event"]:
        # Get the effects of the choice
        effects = event_service.handle_event_choice(
            st.session_state["current_event"], 
            choice_index
        )
        
        # Apply the effects to the pet state
        st.session_state["pet_state"] = pet_service.apply_event_effects(
            st.session_state["pet_state"], 
            effects
        )
        
        # Clear the current event
        st.session_state["current_event"] = None
        
        # Save the updated state
        pet_data = {
            "pet_name": st.session_state["pet_name"],
            "pet_type": st.session_state["pet_type"],
            "pet_state": st.session_state["pet_state"],
            "setup_complete": st.session_state["setup_complete"],
            "current_event": st.session_state["current_event"]
        }
        pet_service.save_pet_data(pet_data)

# Function to reset pet
def reset_pet():
    """Reset the pet by deleting saved data and clearing session state."""
    pet_service.reset_pet_data()
    for key in ["setup_complete", "pet_name", "pet_type", "pet_state", "current_event"]:
        if key in st.session_state:
            del st.session_state[key]
    st.experimental_rerun()

# Main application UI
def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
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
                format_func=lambda x: x
            )
            
            # Show preview of selected pet
            selected_display_name = st.session_state["pet_type_select"]
            selected_index = pet_display_names.index(selected_display_name)
            selected_pet_type = pet_options[selected_index]  # This is the internal key like "cat"
            
            # Get the image path for the selected pet
            image_path = pet_service.get_pet_image_path(selected_pet_type, "neutral")
            st.image(image_path, width=200, caption=f"{selected_display_name} Preview")
        
        with col2:
            # Pet naming
            st.subheader("Name your pet:")
            st.text_input(
                "Pet Name",
                value=st.session_state.get("pet_name", ""),
                key="pet_name_input",
                placeholder="Enter a name for your pet"
            )
            
            # Pet description
            st.write("Your pet will need your care and attention. Make sure to feed it, play with it, and let it rest!")
        
        # Start button
        st.button("Start Your Pet Adventure!", on_click=complete_setup)
    
    # Main pet interface (only shown after setup is complete)
    else:
        # Check if there's an active event
        if "current_event" in st.session_state and st.session_state["current_event"]:
            # Display the event
            event = st.session_state["current_event"]
            st.header(event["title"])
            st.write(event["description"])
            
            # Display the options
            st.subheader("What will you do?")
            for i, option in enumerate(event["options"]):
                st.button(
                    option["text"],
                    key=f"option_{i}",
                    on_click=handle_event_choice,
                    args=(i,)
                )
        else:
            # Regular pet interface
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader(f"{st.session_state['pet_name']}'s Status")
                st.text(f"Hunger: {st.session_state['pet_state']['hunger']}/10")
                st.text(f"Energy: {st.session_state['pet_state']['energy']}/10")
                st.text(f"Happiness: {st.session_state['pet_state']['happiness']}/10")
                
                st.button("Feed", on_click=update_pet_state, args=("feed",))
                st.button("Play", on_click=update_pet_state, args=("play",))
                st.button("Rest", on_click=update_pet_state, args=("rest",))
                
                # Add a small separator
                st.markdown("---")
                # Add a reset button at the bottom (optional - for testing or if user wants to start over)
                st.button("Reset Pet", on_click=reset_pet, type="secondary", help="Start over with a new pet")

            with col2:
                mood = st.session_state["pet_state"]["mood"]
                image_path = pet_service.get_pet_image_path(st.session_state["pet_type"], mood)
                st.image(image_path, use_container_width=True)
                st.subheader(f"{st.session_state['pet_name']} looks {mood}!")

if __name__ == "__main__":
    main() 