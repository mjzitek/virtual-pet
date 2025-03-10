"""
Application settings and configuration.

This module centralizes all configuration parameters for the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = BASE_DIR / "app"

# File paths
PET_CONFIG_FILE = APP_DIR / "config" / "pet_config.json"
PET_DATA_FILE = APP_DIR / "data" / "pet_data.json"
IMAGES_DIR = APP_DIR / "static" / "images"

# Ensure directories exist
os.makedirs(APP_DIR / "data", exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7

# Application settings
DEFAULT_PET_TYPE = "cat"
DEFAULT_PET_STATS = {
    "hunger": 5,
    "energy": 5,
    "happiness": 5,
    "mood": "neutral"
}

# Event settings
EVENT_COOLDOWN_MIN = 3
EVENT_COOLDOWN_MAX = 5
EVENT_CHANCE_NORMAL = 0.2
EVENT_CHANCE_CRITICAL = 0.4
CRITICAL_STAT_THRESHOLD = 3 