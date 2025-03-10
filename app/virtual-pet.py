import streamlit as st
import json
import os

# Load pet configuration from JSON file
def load_pet_config():
    with open("./app/pet_config.json", "r") as file:
        return json.load(file)

# Initialize pet state
if "pet_state" not in st.session_state:
    st.session_state["pet_state"] = {
        "hunger": 5,
        "energy": 5,
        "happiness": 5,
        "mood": "neutral"
    }

pet_config = load_pet_config()
current_pet = pet_config["cat"]  # Default to cat

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

# Streamlit UI Layout
st.title("🐱 Virtual Pet Simulator")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Pet Status")
    st.text(f"Hunger: {st.session_state['pet_state']['hunger']}/10")
    st.text(f"Energy: {st.session_state['pet_state']['energy']}/10")
    st.text(f"Happiness: {st.session_state['pet_state']['happiness']}/10")
    
    st.button("Feed", on_click=update_pet_state, args=("feed",))
    st.button("Play", on_click=update_pet_state, args=("play",))
    st.button("Rest", on_click=update_pet_state, args=("rest",))

with col2:
    mood = st.session_state["pet_state"]["mood"]
    image_path = os.path.join("app", current_pet["images"][mood])
    st.image(image_path, use_container_width=True)
    st.subheader(f"Your pet looks {mood}!")
