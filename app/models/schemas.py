"""
JSON Schemas for LLM Structured Outputs

This module contains the JSON schemas used for structured outputs from the LLM.
These schemas define the expected structure of the responses for different types
of pet events and scenarios.
"""

# Schema for pet events
PET_EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "event_type": {
            "type": "string",
            "enum": ["random", "weather", "time_based", "stat_based"],
            "description": "The type of event being generated"
        },
        "title": {
            "type": "string",
            "description": "A short, engaging title for the event"
        },
        "description": {
            "type": "string",
            "description": "A detailed description of the event, written in a friendly tone appropriate for the pet type"
        },
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text of this choice option"
                    },
                    "effect": {
                        "type": "object",
                        "properties": {
                            "hunger": {
                                "type": "integer",
                                "description": "Effect on hunger (-5 to +5)"
                            },
                            "energy": {
                                "type": "integer",
                                "description": "Effect on energy (-5 to +5)"
                            },
                            "happiness": {
                                "type": "integer",
                                "description": "Effect on happiness (-5 to +5)"
                            }
                        },
                        "required": ["hunger", "energy", "happiness"]
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "A short description of the reasoning behind the story text and the choices"
                    }
                },
                "required": ["text", "effect", "reasoning"]
            },
            "minItems": 2,
            "maxItems": 4,
            "description": "A list of 2-4 options the user can choose from"
        }
    },
    "required": ["event_type", "title", "description", "options"]
}

# Schema for pet reactions
PET_REACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "reaction": {
            "type": "string",
            "description": "A short description of how the pet reacts to the user's choice"
        },
        "mood_change": {
            "type": "string",
            "enum": ["better", "worse", "same"],
            "description": "How the pet's mood changes as a result"
        }
    },
    "required": ["reaction", "mood_change"]
}

# Schema for daily tips
PET_TIP_SCHEMA = {
    "type": "object",
    "properties": {
        "tip_title": {
            "type": "string",
            "description": "A short title for the pet care tip"
        },
        "tip_content": {
            "type": "string",
            "description": "The actual pet care tip content, should be educational and helpful"
        },
        "relevance": {
            "type": "string",
            "enum": ["general", "hunger", "energy", "happiness"],
            "description": "Which aspect of pet care this tip is most relevant to"
        }
    },
    "required": ["tip_title", "tip_content", "relevance"]
}

# You can add more schemas as needed for different features 