# Virtual Pet Simulator

A Streamlit-based virtual pet application with LLM-powered interactions.

## Overview

This application allows users to interact with a virtual pet through guided choices rather than direct conversations. The pet's state changes based on user actions, and the interface updates dynamically to reflect the pet's needs and emotions.

## Features

- **Pet Selection & Customization**: Choose and name your virtual pet
- **Pet State Management**: Monitor and manage your pet's hunger, energy, and happiness
- **Dynamic Interactions**: Feed, play with, and let your pet rest
- **LLM-Powered Events**: Experience AI-generated scenarios and events based on your pet's state
- **Visual Feedback**: See your pet's mood reflected in its appearance

## Project Structure

```
virtual-pet/
├── app/                      # Main application package
│   ├── config/               # Configuration files
│   │   ├── __init__.py
│   │   ├── pet_config.json   # Pet type configurations
│   │   └── settings.py       # Application settings
│   ├── data/                 # Data storage
│   │   └── pet_data.json     # Saved pet data
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   └── schemas.py        # JSON schemas for LLM outputs
│   ├── services/             # Service modules
│   │   ├── __init__.py
│   │   ├── event_service.py  # Event generation and handling
│   │   ├── llm_service.py    # LLM integration
│   │   └── pet_service.py    # Pet state management
│   ├── static/               # Static assets
│   │   └── images/           # Pet images
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   └── file_helpers.py   # File operations
│   ├── __init__.py
│   └── main.py               # Main application entry point
├── docs/                     # Documentation
│   ├── project-doc.md        # Project documentation
│   └── project-log.md        # Development log
├── .env                      # Environment variables (not in version control)
├── .gitignore
├── README.md
├── requirements.txt          # Dependencies
└── run.py                    # Application launcher
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/virtual-pet.git
   cd virtual-pet
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the application:
```
python run.py
```

Or directly with Streamlit:
```
streamlit run app/main.py
```

## Development

- **Adding New Pet Types**: Add new entries to `app/config/pet_config.json`
- **Customizing Events**: Modify the event generation in `app/services/event_service.py`
- **Changing Pet Behavior**: Update the pet state management in `app/services/pet_service.py`

## License

[MIT License](LICENSE)

## Acknowledgements

- [Streamlit](https://streamlit.io/) for the web interface
- [OpenAI](https://openai.com/) for the LLM capabilities
