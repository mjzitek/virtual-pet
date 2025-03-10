import streamlit as st
import json
import os
import datetime

# File path for saving pet data
PET_DATA_FILE = "./app/pet_data.json"

# Load pet configuration from JSON file
def load_pet_config():
    with open("./app/pet_config.json", "r") as file:
        return json.load(file)

# Load saved pet data if it exists
def load_saved_pet_data():
    if os.path.exists(PET_DATA_FILE):
        try:
            with open(PET_DATA_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None

# Save pet data to file
def save_pet_data():
    data = {
        "pet_name": st.session_state["pet_name"],
        "pet_type": st.session_state["pet_type"],
        "pet_state": st.session_state["pet_state"],
        "setup_complete": st.session_state["setup_complete"],
        "last_updated": datetime.datetime.now().isoformat()
    }
    
    with open(PET_DATA_FILE, "w") as file:
        json.dump(data, file, indent=2)

# Initialize session state variables
saved_data = load_saved_pet_data()

if saved_data:
    # Restore from saved data
    for key, value in saved_data.items():
        if key != "last_updated":  # Skip the timestamp
            st.session_state[key] = value
else:
    # Default initialization
    if "setup_complete" not in st.session_state:
        st.session_state["setup_complete"] = False

    if "pet_name" not in st.session_state:
        st.session_state["pet_name"] = ""

    if "pet_type" not in st.session_state:
        st.session_state["pet_type"] = "cat"  # Default to cat

    if "pet_state" not in st.session_state:
        st.session_state["pet_state"] = {
            "hunger": 5,
            "energy": 5,
            "happiness": 5,
            "mood": "neutral"
        }

# Load pet configuration
pet_config = load_pet_config()

# Function to handle pet setup completion
def complete_setup():
    if st.session_state["pet_name_input"] and len(st.session_state["pet_name_input"].strip()) > 0:
        st.session_state["pet_name"] = st.session_state["pet_name_input"]
        # Get the actual key from the selected display name
        selected_display_name = st.session_state["pet_type_select"]
        selected_index = pet_display_names.index(selected_display_name)
        st.session_state["pet_type"] = pet_options[selected_index]
        st.session_state["setup_complete"] = True
        # Save the data after setup is complete
        save_pet_data()

# Function to update pet state
def update_pet_state(action):
    if action == "feed":
        st.session_state["pet_state"]["hunger"] = min(10, st.session_state["pet_state"]["hunger"] + 2)
    elif action == "play":
        st.session_state["pet_state"]["happiness"] = min(10, st.session_state["pet_state"]["happiness"] + 2)
    elif action == "rest":
        st.session_state["pet_state"]["energy"] = min(10, st.session_state["pet_state"]["energy"] + 2)

    # Determine mood
    if st.session_state["pet_state"]["hunger"] < 3:
        st.session_state["pet_state"]["mood"] = "hungry"
    elif st.session_state["pet_state"]["energy"] < 3:
        st.session_state["pet_state"]["mood"] = "tired"
    elif st.session_state["pet_state"]["happiness"] < 3:
        st.session_state["pet_state"]["mood"] = "sad"
    else:
        st.session_state["pet_state"]["mood"] = "happy"
    
    # Save the updated state
    save_pet_data()

# Function to reset pet (for testing or if user wants to start over)
def reset_pet():
    if os.path.exists(PET_DATA_FILE):
        os.remove(PET_DATA_FILE)
    for key in ["setup_complete", "pet_name", "pet_type", "pet_state"]:
        if key in st.session_state:
            del st.session_state[key]
    st.experimental_rerun()

# Main application UI
st.title("🐾 Virtual Pet Simulator")

# Welcome screen and pet setup
if not st.session_state["setup_complete"]:
    st.header("Welcome to Virtual Pet Simulator!")
    st.write("Let's set up your new virtual pet companion.")
    
    # Pet selection
    pet_options = list(pet_config.keys())
    pet_display_names = [pet_config[pet]["name"] for pet in pet_options]
    
    # Create columns for a nicer layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Pet type selection with preview images
        st.subheader("Choose your pet:")
        # Find the index of the current pet type in pet_options
        default_index = 0
        if st.session_state["pet_type"] in pet_options:
            default_index = pet_options.index(st.session_state["pet_type"])
        
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
        selected_pet_type = pet_options[selected_index]
        preview_image_path = os.path.join("app", pet_config[selected_pet_type]["images"]["neutral"])
        st.image(preview_image_path, width=200, caption=f"{selected_display_name} Preview")
    
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
    current_pet = pet_config[st.session_state["pet_type"]]
    
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
        image_path = os.path.join("app", current_pet["images"][mood])
        st.image(image_path, use_container_width=True)
        st.subheader(f"{st.session_state['pet_name']} looks {mood}!")
